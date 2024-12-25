from datetime import datetime
from enum import Enum as AccountEnum
from enum import Enum as TicketEnum
from flask_login import UserMixin
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship, backref
from cnpmapp import db, app


class AccountRole(AccountEnum):
    SALE = 0
    ADMIN = 1


class TicketRole(TicketEnum):
    RESERVED = 0
    BOOKING = 1


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)


class Pricing(BaseModel):
    name = Column(String(50), nullable=False)
    cost_cap = Column(Integer, nullable=False)
    surcharge = Column(Float, nullable=False)
    abroad_coefficient = Column(Float, nullable=False)
    domestic_coefficient = Column(Float, nullable=False)

    # relationship
    rooms = relationship('Room', backref='pricing', lazy=True)

    def __str__(self):
        return self.name


class Category(BaseModel):
    name = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)

    # relationship
    rooms = relationship('Room', backref='category', lazy=True)

    def __str__(self):
        return self.name


class Room(BaseModel):
    name = Column(String(100), nullable=False)
    cost = Column(Float, nullable=False)
    image = Column(String(200), nullable=False)
    description = Column(Text, default='')
    active = Column(Boolean, default=True)

    # foreign key
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    pricing_id = Column(Integer, ForeignKey(Pricing.id), nullable=False)

    # relationship
    tickets = relationship('Ticket', backref='room', lazy=True)

    def __str__(self):
        return self.name


class Customer(BaseModel):
    name = Column(String(100), nullable=False)
    is_domestic = Column(Boolean, nullable=False)
    uid = Column(String(15), nullable=False)
    phone = Column(String(15), nullable=False)
    address = Column(String(200), nullable=False)

    # relationship
    tickets = relationship('Ticket', secondary='order', lazy='subquery', backref=backref('customers', lazy=True))


class Ticket(BaseModel):
    role = Column(Enum(TicketRole), default=TicketRole.RESERVED)
    pricing = Column(Float, nullable=False)
    checkin = Column(DateTime, nullable=False)
    checkout = Column(DateTime, nullable=False)
    create_date = Column(DateTime, default=datetime.now())
    update_date = Column(DateTime, default=datetime.now())
    active = Column(Boolean, default=True)

    # foreign key
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)

    # relationship
    payment = relationship('Payment', backref='ticket', lazy=True, uselist=False)

    def __str__(self):
        return f'{self.checkin} - {self.checkout}'


class Order(db.Model):
    ticket_id = Column(Integer, ForeignKey(Ticket.id), primary_key=True)
    customer_id = Column(Integer, ForeignKey(Customer.id), primary_key=True)


class Payment(BaseModel):
    cost = Column(Float, nullable=False)
    create_date = Column(DateTime, default=datetime.now())

    # foreign key
    ticket_id = Column(Integer, ForeignKey(Ticket.id), nullable=False)


class Account(BaseModel, UserMixin):
    name = Column(String(100), nullable=False)
    username = Column(String(15), nullable=False)
    password = Column(String(50), nullable=False)
    avatar = Column(String(200), nullable=False)
    active = Column(Boolean, default=True)
    role = Column(Enum(AccountRole), default=AccountRole.SALE)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # import hashlib
        # password = str(hashlib.md5('123'.encode('utf-8')).digest())
        # user = Account(role=AccountRole.ADMIN, name="admin", username="admin", password=password,
        #                avatar="https://res.cloudinary.com/dokoicpvp/image/upload/v1734599548/business-professional-icon_zyomq5.png")
        # db.session.add(user)
        # db.session.commit()
        #
        # p = Pricing(name='quy định giá 1', cost_cap=2, surcharge=0.25, abroad_coefficient=1.5, domestic_coefficient=1)
        # db.session.add(p)
        # db.session.commit()
        #
        # c1 = Category(name='1 giường đôi', capacity=3)
        # c2 = Category(name='2 giường đơn', capacity=3)
        # c3 = Category(name='1 giường đôi, 1 giường đơn', capacity=3)
        # db.session.add_all([c1, c2, c3])
        # db.session.commit()
        #
        # r1 = Room(name='001', cost=20000,
        #           image='https://res.cloudinary.com/dokoicpvp/image/upload/v1732952298/PHONGVIP1_xikcru.jpg',
        #           description='phòng tầng trệt', category_id=1, pricing_id=1)
        # r2 = Room(name='002', cost=30000,
        #           image='https://res.cloudinary.com/dokoicpvp/image/upload/v1732952298/PHONGVIP1_xikcru.jpg',
        #           description='phòng tầng trệt', category_id=2, pricing_id=1)
        # r3 = Room(name='003', cost=40000,
        #           image='https://res.cloudinary.com/dokoicpvp/image/upload/v1732952298/PHONGVIP1_xikcru.jpg',
        #           description='phòng tầng trệt', category_id=3, pricing_id=1)
        # db.session.add_all([r1, r2, r3])
        # db.session.commit()
