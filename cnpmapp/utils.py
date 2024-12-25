import hashlib, phonenumbers
import os.path
import tempfile
from io import BytesIO

from fpdf import FPDF
from datetime import datetime, timedelta
from calendar import monthrange

from reportlab.pdfgen import canvas
from sqlalchemy import and_, func, DateTime
from cnpmapp import db, scheduler, app
from cnpmapp.models import Room, Ticket, Category, TicketRole, Pricing, Customer, Account, Payment


def load_pricing(pri_id):
    return Pricing.query.filter_by(id=pri_id).first()


def load_categories():
    return Category.query.all()


def load_category(cate_id):
    return Category.query.filter_by(id=cate_id).first()


def load_room(room_id):
    return Room.query.filter_by(id=room_id).first()


def load_rooms(cate_id=None, checkin=None, checkout=None):
    query = Room.query
    if cate_id:
        query = query.filter(Room.category_id == cate_id)
    if checkin and checkout:
        s_day = datetime.strptime(checkin, "%Y-%m-%d").replace(hour=6, minute=0, second=0, microsecond=0)
        e_day = datetime.strptime(checkout, "%Y-%m-%d").replace(hour=18, minute=0, second=0, microsecond=0)
        query = query.filter(~Room.tickets.any(and_(Ticket.checkin <= s_day, Ticket.checkout >= e_day)))
    return query.all()


def get_active_tickets(role):
    return Ticket.query.filter_by(active=True, role=role, payment=None).all()


def get_tickets_by_customer(name, uid, role, check_active=True):
    customer = Customer.query.filter_by(name=name, uid=uid).first()
    if customer and customer.tickets:
        return list(filter(lambda ticket: ticket.active and ticket.role==role, customer.tickets))\
            if check_active else list(filter(lambda ticket: ticket.role==role, customer.tickets))
    return None


def calculate_pricing(room_id, per_num, is_domestic, checkin, checkout):
    room = load_room(room_id)
    pricing = load_pricing(room.pricing_id)
    days_difference = (checkout - checkin).days + 1
    final_price = days_difference * room.cost

    if int(per_num) > pricing.cost_cap:
        final_price += ((int(per_num) - pricing.cost_cap) * pricing.surcharge * final_price)
    if int(is_domestic) == 1:
        final_price *= pricing.domestic_coefficient
    else:
        final_price *= pricing.abroad_coefficient
    return final_price


def save_order(data):
    rid = int(data['room_id'])
    num_people = int(data['num_people'])
    cost = float(str(data['pricing']))
    checkin = datetime.strptime(data['checkin'], "%Y-%m-%d").replace(hour=6)
    checkout = datetime.strptime(data['checkout'], "%Y-%m-%d").replace(hour=18)

    if check_ticket(rid, checkin, checkout):
        return False

    ticket = Ticket(room_id=rid, pricing=cost, checkin=checkin, checkout=checkout)
    db.session.add(ticket)

    customers = []
    for person in range(1, num_people + 1):
        cus_name = data[f'person_{person}']
        cus_type = int(data[f'country_{person}']) == 1
        cus_uid = data[f'uid_{person}']
        cus_tel = data[f'phone_{person}']
        cus_address = data[f'address_{person}']

        customer = Customer.query.filter(
            and_(
                Customer.name == cus_name,
                Customer.uid == cus_uid
            )
        ).first()

        if len(customers) > 0:
            for cus in customers:
                if cus['name'].__eq__(cus_name) and cus['uid'].__eq__(cus_uid):
                    raise Exception("Trùng thông tin")

        customers.append({
            'name': cus_name,
            'uid': cus_uid,
        })

        if customer is not None:
            customer.is_domestic = cus_type
            customer.phone = cus_tel
            customer.address = cus_address
        else:
            customer = Customer(
                name=cus_name,
                is_domestic=cus_type,
                uid=cus_uid,
                phone=cus_tel,
                address=cus_address
            )
            db.session.add(customer)
        customer.tickets.append(ticket)

    db.session.commit()
    return True


def check_ticket(rid, checkin, checkout):
    existing_ticket = Ticket.query.filter(
        and_(
            Ticket.room_id == rid,
            Ticket.checkin <= checkout,
            Ticket.checkout >= checkin,
            Ticket.active
        )
    ).first()
    return existing_ticket is not None


def get_sms(room_name, phone_number, checkin, checkout):
    parsed_number = phonenumbers.parse(phone_number, 'VN')
    international_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    international_number_no_plus = international_number.replace("+", "")
    return {
        'phone': international_number_no_plus,
        'message': f"Quý khách đã đặt thành công phòng {room_name}, thời gian từ sáng {checkin} đến tối {checkout}."}


def booking_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if ticket is None or ticket.active is False:
        return False

    room = load_room(ticket.room_id)
    if room is None or room.tickets is None or room.tickets.__len__() == 0:
        return False

    for t in room.tickets:
        if t.active and t.role is TicketRole.BOOKING and\
                t.checkin <= ticket.checkin and t.checkout >= ticket.checkout:
            return False

    ticket.role = TicketRole.BOOKING
    ticket.update_date = datetime.now()
    db.session.commit()
    return True


def save_payment(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if ticket is None or ticket.active is False or ticket.role != TicketRole.BOOKING:
        return False

    payment = Payment.query.filter_by(ticket_id=ticket_id).first()
    if payment:
        return False

    payment = Payment(cost=ticket.pricing, ticket_id=ticket_id)
    db.session.add(payment)
    db.session.commit()
    return True


def login(username, password):
    has_pass = str(hashlib.md5(password.strip().encode('utf-8')).digest())
    return Account.query.filter(Account.username.__eq__(username.strip()),
                                Account.password.__eq__(has_pass)).first()


def register(name, username, password, avatar):
    pw = str(hashlib.md5(password.strip().encode('utf-8')).digest())
    account = Account(name=name, username=username.strip(), password=pw, avatar=avatar)
    db.session.add(account)
    db.session.commit()


def load_account(aid):
    return Account.query.get(aid)


def pricing_stats(month, year):
    stats = []
    cate_s = load_categories()

    for cate in cate_s:
        counter = stats_by_cate(cate.id, month, year)
        stat = [cate.id, cate.name, counter[0], counter[1], 0]
        stats.append(stat)

    total = 0
    for stat in stats:
        total += stat[2]
    for stat in stats:
        stat[4] = stat[2] * 100 / total if total > 0 else 0

    stats = [tuple(stat) for stat in stats]
    t_stats = {
        'stats': stats,
        'total': total
    }
    return t_stats


def density_stats(month, year):
    stats = []
    rooms = load_rooms()
    checkin = datetime(year, month, 1, 0, 0, 0)
    checkout = datetime(year, month, monthrange(year, month)[1], 23, 59, 59)
    for room in rooms:
        stat = [room.id, room.name, 0, 0]
        for ticket in room.tickets:
            if ticket.role is TicketRole.BOOKING and \
                    (ticket.checkin > checkout or ticket.checkout < checkin) is False:
                stat[2] += (ticket.checkin.date() - ticket.checkin.date()).days + 1
        stats.append(stat)

    total = 0
    for stat in stats:
        total += stat[2]
    for stat in stats:
        stat[3] = stat[2] * 100 / total if total > 0 else 0

    stats = [tuple(stat) for stat in stats]
    t_stats = {
        'stats': stats,
        'total': total
    }
    return t_stats


def stats_by_cate(cid, month, year):
    count = 0
    pricing = 0
    rooms = Room.query.filter(Room.category_id == cid).all()
    checkin = datetime(year, month, 1, 0, 0, 0)
    checkout = datetime(year, month, monthrange(year, month)[1], 23, 59, 59)
    for room in rooms:
        for ticket in room.tickets:
            if ticket.role is TicketRole.BOOKING and \
                    (ticket.checkin > checkout or ticket.checkout < checkin) is False:
                count += 1
                pricing += ticket.pricing

    return pricing, count


def generate_invoice(payment_id):
    payment = Payment.query.get(payment_id)
    ticket = Ticket.query.get(payment.ticket_id)
    room = Room.query.get(ticket.room_id)
    category = Category.query.get(room.category_id)

    pdf = InvoicePDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '','dejavu-sans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)
    pdf.cell(0, 10, f'Tên phòng: {room.name}', ln=1)
    pdf.cell(0, 10, f'loại phòng: {category.name}', ln=1)
    pdf.cell(0, 10, f'Ngày thuê phòng: {ticket.checkin} - {ticket.checkout}', ln=1)
    pdf.cell(0, 5, ln=1)
    pdf.cell(50, 10, 'Tên khách hàng', border=1)
    pdf.cell(30, 10, 'Loại khách', border=1)
    pdf.cell(50, 10, '(cccd, cmnd)', border=1)
    pdf.cell(50, 10, 'số điện thoại', border=1, ln=1)

    for customer in ticket.customers:
        pdf.cell(50, 10, f'{customer.name}', align='center', border=1)
        pdf.cell(30, 10, 'Trong nước' if customer.is_domestic else 'Nước ngoài', border=1)
        pdf.cell(50, 10, f'{customer.uid}', border=1)
        pdf.cell(50, 10, f'{customer.phone}', border=1, ln=1)

    pricing = f"{payment.cost:,.0f} VNĐ".replace(",", ".")

    pdf.cell(0, 5, ln=1)
    pdf.cell(0, 10, f'Chi phí: {pricing}', ln=1)
    pdf.cell(0, 10, f'xác nhận thanh toán ngày: {payment.create_date}')

    temp_file = os.path.join(tempfile.gettempdir(), f'invoice_{payment_id}.pdf')
    pdf.output(temp_file)
    return temp_file


@scheduler.task('interval', id='delete_old_items_job', minutes=1)
def scheduled_task():
    with app.app_context():
        expired_date = datetime.now()
        tickets = Ticket.query.filter(Ticket.active, Ticket.role==TicketRole.RESERVED).all()
        for ticket in tickets:
            if ticket.active and ticket.checkout < expired_date:
                ticket.active = False
        db.session.commit()


class InvoicePDF(FPDF):
    def header(self):
        self.add_font('DejaVu', '', 'dejavu-sans.ttf', uni=True)
        self.set_font('DejaVu', '', 12)
        self.cell(0, 10, 'Hóa đơn thanh toán', align='C', ln=1)