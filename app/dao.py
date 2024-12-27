from app.models import *
from app import app, db, utils
import hashlib, hmac, threading, urllib
from datetime import datetime
import cloudinary.uploader, smtplib, math
from flask_login import current_user

from flask_login import current_user, AnonymousUserMixin
from sqlalchemy import func, Numeric, extract, or_, and_, case, desc, text
from sqlalchemy.orm import aliased

#Thanh toán
def get_first_customer(room_id):
    query = Customer.query \
        .join(CustomerRoomRental, Customer.id == CustomerRoomRental.c.customer_id) \
        .join(RoomRental, RoomRental.id == CustomerRoomRental.c.room_rental_id) \
        .filter(RoomRental.room_id == room_id) \
        .first()
    return query.name
def count_customer(room_id):
    customer_count = Customer.query \
        .join(CustomerRoomRental, Customer.id == CustomerRoomRental.c.customer_id) \
        .join(RoomRental, RoomRental.id == CustomerRoomRental.c.room_rental_id) \
        .filter(RoomRental.room_id == room_id) \
        .count()
    return customer_count

def get_all_customer(room_id):
    query = Customer.query \
        .join(CustomerRoomRental, Customer.id == CustomerRoomRental.c.customer_id) \
        .join(RoomRental, RoomRental.id == CustomerRoomRental.c.room_rental_id) \
        .filter(RoomRental.room_id == room_id) \
        .all()
    return query

def check_foreign(room_id):
    query = Customer.query \
        .join(CustomerRoomRental, Customer.id == CustomerRoomRental.c.customer_id) \
        .join(RoomRental, RoomRental.id == CustomerRoomRental.c.room_rental_id) \
        .filter(RoomRental.room_id == room_id) \
        .filter(Customer.customer_type.name == 'FOREIGN') \
        .all()
    return query

def get_room_rental(room_id):
    query = RoomRental.query.join(CustomerRoomRental, RoomRental.id == CustomerRoomRental.c.room_rental_id) \
        .filter(RoomRental.room_id == room_id).first()
    return query

def get_total(room_id):
    query = RoomTypeRegulation.query.join(RoomType, RoomTypeRegulation.room_type_id == RoomType.id) \
        .join(Room, Room.room_type_id ==  RoomType.id)\
        .filter(Room.id==room_id).first()
    room = query.price
    delta = get_room_rental(room_id).checkout_date - get_room_rental(room_id).checkin_date
    day = math.ceil(delta.total_seconds() / (24 * 3600))
    count_cus = int(count_customer(room_id))
    print(count_cus)
    sr = db.session.query(SurchargeRegulation).first()
    if count_cus > sr.default_customer_count:
        room = room*(1+sr.surcharge_rate)
    cus_type = 1
    ctr = db.session.query(CustomerTypeRegulation).first()
    if check_foreign(room_id):
        cus_type = ctr.rate
    return  day * room * count_cus



def get_customers():
    # result = db.session.query(Customer, reservation_customer).join(reservation_customer,
    #                                                                reservation_customer.c.customer_id == Customer.id).all()
    return Customer.query.all()

    return result

def get_rooms():
    return Room.query.all()

def load_rooms(status=None, page=1):
    query = Room.query

    if status:
        query = query.filter(Room.status == status)

    page_size = app.config.get('PAGE_SIZE')
    start = (page - 1) * page_size
    query = query.slice(start, start + page_size)

    return query.all()

def count_rooms(status=None):
    if (status):
        return Room.query.filter(Room.status == status).count()
    return Room.query.count()

def load_customers(criteria=None, kw=None):
    if criteria == 'reservation':
        query = Reservation.query.join(ReservationCustomer).join(Customer)
    elif criteria == 'room_rental':
        query = RoomRental.query.join(CustomerRoomRental).join(Customer)
    # elif criteria == 'receipt':
    #     query = receipt.query
    if kw:
        query = query.filter(Customer.name.contains(kw))
    else :
        return

    return query.all()

def auth_user(username, password, role=None):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())

    u = User.query.filter(User.username.__eq__(username),
                          User.password.__eq__(password))
    if role:
        u = u.filter(User.user_role.__eq__(role))
    return u.first()

def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    return User.query.filter(User.username.__eq__(username.strip()),
                             User.password.__eq__(password)).first()


def get_user_by_id(id):
    return User.query.get(id)

def update_room_status(id, new_status):
        # Tìm phòng có id tương ứng
    room = Room.query.filter_by(id=id).first()
        # Kiểm tra xem phòng có tồn tại không
    if room:
            # Cập nhật trạng thái phòng
        room.status = new_status
        db.session.commit()


def get_user_id_by_cmnd(cmnd):
    cus = Customer.query.filter_by(cmnd=cmnd).first()
    if cus:
        return cus.id
    return None  # Trả về None nếu không tìm thấy người dùng

def add_user(name, username, password, avatar=None):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())

    u = User(name=name, username=username, password=password)

    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.avatar = res.get('secure_url')

    db.session.add(u)
    db.session.commit()

def add_roomrental(checkin_date, checkout_date, room_id, deposit=None):
    if not deposit:
        deposit=0
    roomrental = RoomRental(receptionist_id=current_user.id, checkin_date=checkin_date, checkout_date=checkout_date
                            , room_id=room_id, deposit=deposit)
    db.session.add(roomrental)
    db.session.commit()
    return roomrental

def add_customer(name, customer_type, cmnd, address):
    customer = Customer(name=name, customer_type=customer_type, cmnd=cmnd, address=address)
    db.session.add(customer)
    db.session.commit()
    return customer
def add_customer_roomrental(customer_id, room_rental_id):
    query = CustomerRoomRental.insert().values(customer_id=customer_id, room_rental_id=room_rental_id)
    db.session.execute(query)
    db.session.commit()
def get_price(roomtype_id):
    u = RoomTypeRegulation.query.filter_by(RoomTypeRegulation.room_type_id==(roomtype_id)).first()
    return u.price
def load_roomtype_regulation():
    return  RoomTypeRegulation.query.all()


def get_room_types():
    with app.app_context():
        room_types = RoomType.query.all()
        return room_types

def get_user_by_id(user_id=None):
    with app.app_context():
        user = User.query.get(id)
        return user

def get_rooms():
    with app.app_context():
        rooms = Room.query.all()
        return rooms

# Quy định phòng
def get_room_type_regulation():
    # if current_user.is_authenticated and current_user.role.__eq__(UserRole.ADMIN):
    with app.app_context():
        room_type_regulation = db.session.query(RoomType.name.label('rome_type_name'),
                                           User.username.label('user_name'),
                                           RoomTypeRegulation.room_quanity,
                                           RoomTypeRegulation.price) \
            .join(Administrator, Administrator.id == RoomTypeRegulation.admin_id) \
            .join(RoomType, RoomType.id == RoomTypeRegulation.room_type_id) \
            .join(User, User.id == Administrator.id)

        return room_type_regulation.all()

# Quy định khách hàng
def get_customer_type_regulation():
    # if current_user.is_authenticated and current_user.role.__eq__(UserRole.ADMIN):
    with app.app_context():
        customer_type_regulation = db.session.query(CustomerTypeRegulation.id,
                                                    CustomerTypeRegulation.customer_type,
                                                    Administrator.name.label('name_admin'),
                                                    CustomerTypeRegulation.rate) \
            .join(Administrator, Administrator.id == CustomerTypeRegulation.admin_id)  \
            .group_by(CustomerTypeRegulation.id,
                      CustomerTypeRegulation.customer_type,
                      Administrator.name.label('name_admin'),
                      CustomerTypeRegulation.rate) \
            .all()

        # print(customer_type_regulation)
        return customer_type_regulation
# Thay đổi phụ thu
def get_surcharge_regulation():
    # if current_user.is_authenticated and current_user.role.__eq__(UserRole.ADMIN):
    with app.app_context():
        surcharge_regulation = db.session.query(SurchargeRegulation.id,
                                                    SurchargeRegulation.surcharge_rate,
                                                    Administrator.name.label('name_admin'),
                                                    SurchargeRegulation.default_customer_count,) \
            .join(Administrator, Administrator.id == SurchargeRegulation.admin_id) \
            .group_by(SurchargeRegulation.id,
                      SurchargeRegulation.surcharge_rate,
                      Administrator.name.label('name_admin'),
                      SurchargeRegulation.default_customer_count) \
            .all()

        return surcharge_regulation
# Thống kê doanh thu
def month_sale_statistic(month=None, year=None, kw=None, from_date=None, to_date=None, **kwargs):
    with app.app_context():
        if not kw and not from_date and not to_date and not month and not year:
            count_receipt = Receipt.query.count()
        elif from_date:
            count_receipt = Receipt.query.filter(
                Receipt.created_date.__ge__(from_date)).count()
        elif to_date:
            count_receipt = Receipt.query.filter(
                Receipt.created_date.__le__(to_date)).count()
        elif kw:
            count_receipt = Receipt.query.count()
        elif month:
            count_receipt = Receipt.query.filter(
                extract('month', Receipt.created_date) == month)
            if year:
                count_receipt = count_receipt.filter(
                    extract('year', Receipt.created_date) == year)
            count_receipt = count_receipt.count()
        else:
            count_receipt = Receipt.query.filter(
                extract('year', Receipt.created_date) == year).count()

        month_sale_statistic = db.session.query(RoomType.name,
                                                func.coalesce(func.sum(Receipt.total_price), 0),
                                                func.coalesce(func.count(Receipt.id), 0),
                                                func.cast((func.count(Receipt.id) / count_receipt) * 100
                                                          , Numeric(5, 2))) \
            .join(Room, Room.room_type_id.__eq__(RoomType.id), isouter=True) \
            .join(RoomRental, RoomRental.room_id.__eq__(Room.id), isouter=True) \
            .join(Receipt, Receipt.rental_room_id.__eq__(RoomRental.id), isouter=True) \
            .group_by(RoomType.name) \
            .order_by(RoomType.id)

        if month:
            month_sale_statistic = month_sale_statistic.filter(
                extract('month', Receipt.created_date) == month)

        if year:
            month_sale_statistic = month_sale_statistic.filter(
                extract('year', Receipt.created_date) == year)

        if kw:
            month_sale_statistic = month_sale_statistic.filter(
                RoomType.name.contains(kw))

        if from_date:
            month_sale_statistic = month_sale_statistic.filter(
                Receipt.created_date.__ge__(from_date))

        if to_date:
            month_sale_statistic = month_sale_statistic.filter(
                Receipt.created_date.__le__(to_date))

        return month_sale_statistic.all()

# Báo cáo tần suất sử dụng phòng
def room_utilization_report(month=None, year=None, room_name=None, **kwargs):
    with app.app_context():
        checkout_date_column = RoomRental.checkout_date  # Định rõ cột 'checkout_date' để sử dụng trong câu truy vấn

        room_rental = RoomRental.query
        if month and year and room_name:
            room_rental = room_rental.join(Room, Room.id.__eq__(RoomRental.room_id)) \
                .filter(extract('month', checkout_date_column) == month and
                        extract('year', checkout_date_column) == year and
                        Room.name.__eq__(room_name))
        elif month:
            room_rental = room_rental.filter(extract('month', checkout_date_column) == month)
            if year:
                room_rental = room_rental.filter(extract('year', checkout_date_column) == year)
        elif year:
            room_rental = room_rental.filter(extract('year', checkout_date_column) == year)

        count = room_rental.count()

        result = db.session.query(
            Room.name,
            func.sum(func.datediff(RoomRental.checkout_date, RoomRental.checkin_date)),
            func.cast((func.count() / count) * 100
                      , Numeric(5, 2))
        ).join(RoomRental, RoomRental.room_id.__eq__(Room.id)).group_by(Room.name).order_by(Room.id)

        if month:
            # Thống kê theo tháng
            result = result.filter(extract('month', checkout_date_column) == month)
        if year:
            # Thống kê theo năm
            result = result.filter(extract('year', checkout_date_column) == year)
        if room_name:
            # Thống kê theo tên phòng
            result = result.filter(Room.name == room_name)

        return result.all()

def get_all_res(room_id):
        return Reservation.query.filter(Reservation.room_id == room_id).all()
        return Reservation.query.filter(Reservation.room_id == room_id).all()

def add_reservation(checkin_date, checkout_date, room_id, booker_name, deposit=None):
        if not deposit:
            deposit = 0
        reservation = Reservation(receptionist_id=current_user.id, booker_name=booker_name,
                                  checkin_date=checkin_date, checkout_date=checkout_date
                                  , room_id=room_id, deposit=deposit)
        db.session.add(reservation)
        db.session.commit()
        return reservation

def add_reservation_customer(customer_id, reservation_id):
        query = ReservationCustomer.insert().values(customer_id=customer_id, reservation_id=reservation_id)
        db.session.execute(query)
        db.session.commit()

if __name__ == '__main__':
    print()