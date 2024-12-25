from datetime import datetime
from flask import request, render_template, jsonify, redirect, session, send_file
from flask_login import login_user, logout_user
from cnpmapp import app, utils, scheduler, login, sms, admin
from cnpmapp.models import AccountRole, TicketRole
from cnpmapp.authentication import login_required, anonymous_user
import cloudinary.uploader


@app.route('/', methods=['get'])
def index():
    sd = request.args.get('checkin')
    ed = request.args.get('checkout')
    rt = request.args.get('room_type')
    rooms = utils.load_rooms(rt, sd, ed) if rt and sd and ed else utils.load_rooms()
    if sd is None: sd = datetime.today().strftime('%Y-%m-%d')
    if ed is None: ed = datetime.today().strftime('%Y-%m-%d')
    return render_template('index.html', rooms=rooms, checkin=sd, checkout=ed)


@app.route('/booking', methods=['get', 'post'])
@login_required
def booking():
    if request.method == 'POST':
        try:
            ticket_id = request.json['ticket_id']
            status = utils.booking_ticket(ticket_id)
        except Exception as ex:
            print(str(ex))
            return jsonify({'status': 'error', 'message': 'Lỗi hệ thống, hãy thử lại'})
        if status:
            return jsonify({'status': 'success', 'message': 'Lập phiếu thuê phòng thành công'})
        return jsonify({'status': 'error', 'message': 'Lập phiếu thuê phòng không thành công'})

    role = TicketRole.RESERVED
    name = request.args.get('cus_name')
    uid = request.args.get('cus_uid')
    rooms = utils.load_rooms()

    if name and uid:
        return render_template('booking.html', rooms=rooms, tickets=utils.get_tickets_by_customer(name, uid, role, False))
    return render_template('booking.html', rooms=rooms, tickets=utils.get_active_tickets(role))


@app.route('/payment', methods=['get', 'post'])
@login_required
def payment():
    if request.method == 'POST':
        try:
            ticket_id = request.json['ticket_id']
            status = utils.save_payment(ticket_id)
        except Exception as ex:
            print(str(ex))
            return jsonify({'status': 'error', 'message': 'Lỗi hệ thống, hãy thử lại'})
        if status:
            return jsonify({'status': 'success', 'message': 'Xác nhận thanh toán thành công'})
        return jsonify({'status': 'error', 'message': 'Xác nhận thanh toán không thành công'})

    role = TicketRole.BOOKING
    name = request.args.get('cus_name')
    uid = request.args.get('cus_uid')
    rooms = utils.load_rooms()

    if name and uid:
        return render_template('payment.html', rooms=rooms, bookings=utils.get_tickets_by_customer(name,uid,role))
    return render_template('payment.html', rooms=rooms, bookings=utils.get_active_tickets(role))


@app.route('/invoice/<int:payment_id>')
@login_required
def invoice(payment_id):
    pdf = utils.generate_invoice(payment_id)
    return send_file(pdf, as_attachment=True)


@app.route('/reservation/<int:room_id>&<string:checkin>&<string:checkout>', methods=['get'])
def reservation(room_id, checkin, checkout):
    keyword = 'confirm_reservation'
    room = utils.load_room(room_id)
    category = utils.load_category(room.category_id)
    nums = range(1, category.capacity + 1)

    if session.get(keyword) and session[keyword].get('status'):
        if session[keyword]['status'].__eq__('success'):
            m_success = session[keyword]['message']
            del session[keyword]
            return render_template('reservation.html', m_success=m_success,
                                   room=room, room_type=category.name, nums=nums, checkin=checkin, checkout=checkout)
        if session[keyword]['status'].__eq__('error'):
            m_error = session[keyword]['message']
            del session[keyword]
            return render_template('reservation.html', m_error=m_error,
                                   room=room, room_type=category.name, nums=nums, checkin=checkin, checkout=checkout)
    return render_template('reservation.html',
                           room=room, room_type=category.name, nums=nums, checkin=checkin, checkout=checkout)


@app.route('/reservation/pricing', methods=['post'])
def get_total_price():
    data = request.json
    room_id = data['room_id']
    num_people = data['num_people']
    is_domestic = data['is_domestic']
    checkin = datetime.strptime(data['start_date'], "%Y-%m-%d")
    checkout = datetime.strptime(data['end_date'], "%Y-%m-%d")
    return jsonify({'total_price': utils.calculate_pricing(room_id, num_people, is_domestic, checkin, checkout)})


@app.route('/reservation/confirm', methods=['get', 'post'])
def reservation_confirm():
    room = utils.load_room(int(request.form['room_id']))
    checkin = request.form['checkin']
    checkout = request.form['checkout']
    phonenumbers = request.form['phone_1']
    keyword = 'confirm_reservation'
    session[keyword] = {
        'status': None,
        'message': None
    }

    try:
        status = utils.save_order(request.form)
    except Exception as ex:
        print(str(ex))
        session[keyword]['status'] = 'error'
        session[keyword]['message'] = 'Invalid data'
    else:
        session[keyword]['status'] = 'success' if status else 'error'
        session[keyword]['message'] = 'Đặt phòng thành công' if status else 'Đặt phòng không thành công, hãy thử lại'
        if status:
            mess = utils.get_sms(room.name, phonenumbers, checkin, checkout)
            sms.send(mess['phone'], mess['message'])
    finally:
        return redirect(f'/reservation/{room.id}&{checkin}&{checkout}')


@app.route('/login-admin', methods=['post'])
def login_admin():
    username = request.form['username']
    password = request.form['password']
    account = utils.login(username, password)

    if account and account.role is AccountRole.ADMIN:
        account.is_admin = True
        login_user(user=account)

    return redirect('/admin')


@app.route('/logout')
def logout_sale():
    logout_user()
    return redirect('/')


@app.route('/login', methods=['get', 'post'])
@anonymous_user
def login_sale():
    if request.method.__eq__('POST'):
        username = request.form['username']
        password = request.form['password']
        account = utils.login(username, password)
        if account:
            account.is_sale = True
            login_user(user=account)
            return redirect('/')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    keyword = 'register_message'
    session[keyword] = None
    if request.method.__eq__('POST'):
        pw = request.form['password']
        cf = request.form['confirm']
        file = request.files['avatar']
        if pw.__eq__(cf):
            try:
                avatar = cloudinary.uploader.upload(file)['secure_url'] if file else ''
                utils.register(name=request.form['fullname'],
                               username=request.form['username'],
                               password=request.form['password'],
                               avatar=avatar)
                session[keyword] = 'success'
            except Exception as ex:
                print(str(ex))
                session[keyword] = 'sys_error'
                return redirect('/admin/registerview/')
        else:
            session[keyword] = 'pass_error'
    return redirect('/admin/registerview/')


@login.user_loader
def load_account(aid):
    return utils.load_account(aid)


@app.context_processor
def common_attr():
    categories = utils.load_categories()
    return dict(categories=categories)


if __name__ == '__main__':
    scheduler.start()
    app.run(debug=True)
