from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum, DateTime, Table
from sqlalchemy.orm import relationship, backref
from app import db, app
from enum import Enum as RoleEnum
from flask_login import UserMixin


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)


####CÁC BẢNG TRUNG GIAN####

ReservationCustomer = db.Table(
    'ReservationCustomer',
    Column('reservation_id', Integer, ForeignKey('Reservation.id'), primary_key=True),
    Column('customer_id', Integer, ForeignKey('Customer.id'), primary_key=True)
)

CustomerRoomRental = db.Table(
    'CustomerRoomRental',
    Column('customer_id', Integer, ForeignKey('Customer.id'), primary_key=True),
    Column('room_rental_id', Integer, ForeignKey('RoomRental.id'), primary_key=True)
)


####CÁC BẢNG TRUNG GIAN####

class UserRole(RoleEnum):
    ADMIN = 1
    CUSTOMER = 2
    RECEPTION = 3


class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=True)
    phone = Column(String(50), nullable=True, unique=True)
    gender = Column(Boolean, default=True)  # True = 1 is 'Man'
    avatar = Column(String(100),
                    default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1646729533/zuur9gzztcekmyfenkfr.jpg')
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)


class Administrator(db.Model):
    id = Column(Integer, ForeignKey(User.id), nullable=False, primary_key=True)
    name = Column(String(50), nullable=False)


class Receptionist(db.Model):
    id = Column(Integer, ForeignKey(User.id), nullable=False, primary_key=True)
    name = Column(String(50), nullable=False)
    reservations = relationship('Reservation', backref='receptionist', lazy=True)
    room_rentals = relationship('RoomRental', backref='receptionist', lazy=True)


class CustomerType(RoleEnum):
    DOMESTIC = 1
    FOREIGN = 2


class Customer(BaseModel):
    __tablename__ = 'Customer'
    name = Column(String(100), nullable=False)
    customer_type = Column(Enum(CustomerType), default=CustomerType.DOMESTIC)
    cmnd = Column(String(100), nullable=False)
    address = Column(String(500), nullable=False)
    comments = relationship('Comment', lazy=True)

    # Mối quan hệ với RoomRental thông qua bảng trung gian
    room_rentals = relationship('RoomRental',
                                secondary=CustomerRoomRental,  # Updated to PascalCase
                                backref=backref('customers', lazy='subquery'),
                                lazy='subquery')


class RoomType(BaseModel):
    __tablename__ = 'RoomType'
    name = Column(String(50), nullable=False, unique=True)
    rooms = relationship('Room', backref='room_type', lazy=True)
    room_type_regulations = relationship('RoomTypeRegulation', backref='room_type', lazy=True)
    def __str__(self):
        return self.name


class Room(BaseModel):
    __tablename__ = 'Room'
    name = Column(String(100), nullable=False, unique=True)
    image = Column(String(500), default='static/images/phong1.jpg')
    room_type_id = Column(Integer, ForeignKey('RoomType.id'), nullable=False)
    status = Column(String(100), nullable=True)
    room_rentals = relationship('RoomRental', backref='room', lazy='subquery')
    reservation = relationship('Reservation', backref='room', lazy='subquery')
    comments = relationship('Comment', lazy=True)

    def __str__(self):
        return self.name


class RoomRental(BaseModel):
    __tablename__ = 'RoomRental'
    room_id = Column(Integer, ForeignKey('Room.id'), nullable=False)
    receptionist_id = Column(Integer, ForeignKey(Receptionist.id), nullable=False)
    checkin_date = Column(DateTime, nullable=False)
    checkout_date = Column(DateTime, nullable=False)
    deposit = Column(Float)
    is_paid = Column(Boolean, default=False)
    receipt_id = relationship('Receipt', backref='room', lazy='subquery')


class Reservation(BaseModel):
    __tablename__ = 'Reservation'
    room_id = Column(Integer, ForeignKey('Room.id'), nullable=False)
    receptionist_id = Column(Integer, ForeignKey(Receptionist.id), nullable=False)
    checkin_date = Column(DateTime)
    checkout_date = Column(DateTime)
    booker_name = Column(String(100), nullable=False)
    is_checkin = Column(Boolean, default=False)
    deposit = Column(Float, nullable=False)
    # Mối quan hệ Many-to-Many với Customer
    customers = relationship('Customer',
                             secondary=ReservationCustomer,  # Updated to PascalCase
                             backref=backref('reservations', lazy='subquery'),
                             lazy='subquery')


class Receipt(BaseModel):
    receptionist_id = Column(Integer, ForeignKey(Receptionist.id), nullable=False)
    rental_room_id = Column(Integer, ForeignKey(RoomRental.id), nullable=False, primary_key=True)
    total_price = Column(Float, nullable=False)
    created_date = Column(DateTime, nullable=False, default=datetime.now())


class Comment(BaseModel):
    customer_id = Column(Integer, ForeignKey('Customer.id'), nullable=False, primary_key=True)
    content = Column(String(1000), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False, primary_key=True)
    created_date = Column(DateTime, default=datetime.now())


class CustomerTypeRegulation(BaseModel):
    __tablename__ = 'CustomerTypeRegulation'
    rate = Column(Float, default=1.0, nullable=False)
    admin_id = Column(Integer, ForeignKey(Administrator.id), nullable=False)
    customer_type = Column(Enum(CustomerType), default=CustomerType.DOMESTIC)


class RoomTypeRegulation(BaseModel):  # THAY ĐỔI ĐƠN GIÁ PHÒNG
    __tablename__ = 'RoomTypeRegulation'
    room_type_id = Column(Integer, ForeignKey('RoomType.id'), nullable=False)
    room_quanity = Column(Integer, nullable=True)
    price = Column(Float, nullable=False)
    admin_id = Column(Integer, ForeignKey(Administrator.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now())

class RoomCustomerRegulation(BaseModel):
    __tablename__ = 'RoomCustomerRegulation'
    room_type_id = Column(Integer, ForeignKey('RoomType.id'), nullable=False)
    max_customers = Column(Integer, nullable=False, default=3)  # Số khách tối đa/phòng
    admin_id = Column(Integer, ForeignKey(Administrator.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now())


class SurchargeRegulation(BaseModel):
    __tablename__ = 'SurchargeRegulation'
    default_customer_count = Column(Integer, default=2)  # Mặc định 2 người
    surcharge_rate = Column(Float, default=0.25)  # Phụ thu 25% cho người thứ 3
    admin_id = Column(Integer, ForeignKey(Administrator.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now())


class Category(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    products = relationship('Product', backref='category', lazy=True)

    def __str__(self):
        return self.name


class Product(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    price = Column(Float, default=0)
    image = Column(String(100), nullable=True)
    active = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)


    def __str__(self):
        return self.name



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        import hashlib
        users = [
            User(name="Admin User", username="admin", password=str(hashlib.md5('123'.encode('utf-8')).hexdigest())
                 , email="admin@example.com", phone="0123456789", gender=True, avatar="[URL]", role=UserRole.ADMIN),
            User(name="John Doe", username="johndoe", password=str(hashlib.md5('123'.encode('utf-8')).hexdigest())
                 , email="johndoe@example.com", phone="0987654321", gender=True, avatar="[URL]",
                 role=UserRole.CUSTOMER),
            User(name="Jane Smith", username="janesmith", password=str(hashlib.md5('123'.encode('utf-8')).hexdigest())
                 , email="janesmith@example.com", phone="0978123456", gender=False, avatar="[URL]",
                 role=UserRole.CUSTOMER),
            User(name="Receptionist", username="reception", password=str(hashlib.md5('123'.encode('utf-8')).hexdigest())
                 , email="reception@example.com", phone="0123987654", gender=True, avatar="[URL]",
                 role=UserRole.RECEPTION),
            User(name="David Lee", username="davidlee", password=str(hashlib.md5('123'.encode('utf-8')).hexdigest())
                 , email="davidlee@example.com", phone="0167890123", gender=True, avatar="[URL]",
                 role=UserRole.RECEPTION),
        ]
        db.session.bulk_save_objects(users)
        db.session.commit()


        administrators = [
            Administrator(id=1, name="Admin User"),
        ]
        db.session.bulk_save_objects(administrators)
        db.session.commit()
        receptionists = [
            Receptionist(id=4, name="Receptionist"),
            Receptionist(id=5, name="David Lee"),
        ]
        db.session.bulk_save_objects(receptionists)
        db.session.commit()


        customers = [
            Customer(name="Alice Nguyen", customer_type=CustomerType.DOMESTIC, cmnd="123456789", address="123 Main St"),
            Customer(name="Bob Smith", customer_type=CustomerType.FOREIGN, cmnd="987654321", address="456 Elm St"),
            Customer(name="Charlie Brown", customer_type=CustomerType.DOMESTIC, cmnd="112233445", address="789 Oak St"),
            Customer(name="Diana Prince", customer_type=CustomerType.FOREIGN, cmnd="556677889", address="321 Pine St"),
            Customer(name="Edward King", customer_type=CustomerType.DOMESTIC, cmnd="998877665", address="654 Maple St"),
        ]
        db.session.bulk_save_objects(customers)
        db.session.commit()

        room_types = [
            RoomType(name="Deluxe"),
            RoomType(name="Standard"),
            RoomType(name="Suite"),
            RoomType(name="Family"),
            RoomType(name="Single"),
        ]
        db.session.bulk_save_objects(room_types)
        db.session.commit()
        #
        rooms = [
            Room(name="Room101", image="static/images/phong1.jpg", room_type_id=1, status="đã được thuê"),
            Room(name="Room102", image="static/images/phong2.jpg", room_type_id=2, status="còn trống"),
            Room(name="Room103", image="static/images/phong1.jpg", room_type_id=3, status="đã được thuê"),
            Room(name="Room104", image="static/images/phong1.jpg", room_type_id=4, status="còn trống"),
            Room(name="Room105", image="static/images/phong2.jpg", room_type_id=5, status="còn trống"),
            Room(name="Room201", image="static/images/phong1.jpg", room_type_id=1, status="đã được thuê"),
            Room(name="Room202", image="static/images/phong2.jpg", room_type_id=2, status="còn trống"),
            Room(name="Room203", image="static/images/phong1.jpg", room_type_id=3, status="đã được thuê"),
            Room(name="Room204", image="static/images/phong1.jpg", room_type_id=4, status="còn trống"),
            Room(name="Room205", image="static/images/phong2.jpg", room_type_id=5, status="đã được thuê"),
        ]
        db.session.bulk_save_objects(rooms)
        db.session.commit()

        comments = [
            Comment(customer_id=1, content='Phòng sạch sẽ, dịch vụ tốt.', room_id=1,
                    created_date=datetime(2024, 12, 24, 8, 0)),
            Comment(customer_id=2, content='Nhân viên nhiệt tình, phòng thoáng mát.', room_id=2,
                    created_date=datetime(2024, 12, 24, 9, 30)),
            Comment(customer_id=3, content='Cần cải thiện hệ thống nước trong phòng.', room_id=3,
                    created_date=datetime(2024, 12, 24, 10, 15)),
            Comment(customer_id=1, content='Lần sau sẽ quay lại.', room_id=1,
                    created_date=datetime(2024, 12, 24, 11, 0))
        ]
        db.session.add_all(comments)
        db.session.commit()

        room_rentals = [
            RoomRental(room_id=1, receptionist_id=4, checkin_date=datetime(2024, 12, 1, 14, 0), checkout_date=datetime(2024, 12, 5, 12, 0), deposit=500.0, is_paid=False),
            RoomRental(room_id=2, receptionist_id=4, checkin_date=datetime(2024, 12, 2, 14, 0), checkout_date=datetime(2024, 12, 6, 12, 0), deposit=700.0, is_paid=True),
            RoomRental(room_id=3, receptionist_id=5, checkin_date=datetime(2024, 12, 3, 14, 0), checkout_date=datetime(2024, 12, 7, 12, 0), deposit=800.0, is_paid=False),
            RoomRental(room_id=4, receptionist_id=5, checkin_date=datetime(2024, 12, 4, 14, 0), checkout_date=datetime(2024, 12, 8, 12, 0), deposit=900.0, is_paid=True),
            RoomRental(room_id=5, receptionist_id=4, checkin_date=datetime(2024, 12, 5, 14, 0), checkout_date=datetime(2024, 12, 9, 12, 0), deposit=1000.0, is_paid=False),
        ]
        db.session.bulk_save_objects(room_rentals)
        db.session.commit()

        reservations = [
            Reservation(room_id=1, receptionist_id=4, checkin_date=datetime(2024, 12, 3, 15, 0), checkout_date=datetime(2024, 12, 4, 11, 0), booker_name="Alice Nguyen", is_checkin=False, deposit=200.0),
            Reservation(room_id=2, receptionist_id=4, checkin_date=datetime(2024, 12, 4, 15, 0), checkout_date=datetime(2024, 12, 5, 11, 0), booker_name="Bob Smith", is_checkin=True, deposit=300.0),
            Reservation(room_id=3, receptionist_id=5, checkin_date=datetime(2024, 12, 5, 15, 0), checkout_date=datetime(2024, 12, 6, 11, 0), booker_name="Charlie Brown", is_checkin=False, deposit=400.0),
            Reservation(room_id=4, receptionist_id=5, checkin_date=datetime(2024, 12, 6, 15, 0), checkout_date=datetime(2024, 12, 7, 11, 0), booker_name="Diana Prince", is_checkin=True, deposit=500.0),
            Reservation(room_id=5, receptionist_id=4, checkin_date=datetime(2024, 12, 7, 15, 0), checkout_date=datetime(2024, 12, 8, 11, 0), booker_name="Edward King", is_checkin=False, deposit=600.0),
        ]
        db.session.bulk_save_objects(reservations)
        db.session.commit()

        receipts = [
            Receipt(receptionist_id=4, rental_room_id=1, total_price=1500.0, created_date=datetime(2024, 12, 5, 12, 0)),
            Receipt(receptionist_id=4, rental_room_id=2, total_price=2000.0, created_date=datetime(2024, 12, 6, 12, 0)),
            Receipt(receptionist_id=5, rental_room_id=3, total_price=2500.0, created_date=datetime(2024, 12, 7, 12, 0)),
            Receipt(receptionist_id=5, rental_room_id=4, total_price=3000.0, created_date=datetime(2024, 12, 8, 12, 0)),
            Receipt(receptionist_id=4, rental_room_id=5, total_price=3500.0, created_date=datetime(2024, 12, 9, 12, 0)),
        ]

        db.session.bulk_save_objects(receipts)
        db.session.commit()

        customer_type_regulations = [
            CustomerTypeRegulation(rate=1.0, admin_id=1, customer_type=CustomerType.DOMESTIC),
            CustomerTypeRegulation(rate=1.2, admin_id=1, customer_type=CustomerType.FOREIGN),
        ]

        db.session.bulk_save_objects(customer_type_regulations)
        db.session.commit()

        room_type_regulations = [
            RoomTypeRegulation(room_type_id=1, price=500000, admin_id=1, created_date=datetime.now()),
            RoomTypeRegulation(room_type_id=2, price=700000, admin_id=1, created_date=datetime.now()),
            RoomTypeRegulation(room_type_id=3, price=1000000, admin_id=1, created_date=datetime.now()),
        ]

        db.session.bulk_save_objects(room_type_regulations)
        db.session.commit()

        room_customer_regulations = [
            RoomCustomerRegulation(room_type_id=1, max_customers=3, admin_id=1, created_date=datetime.now()),
            RoomCustomerRegulation(room_type_id=2, max_customers=4, admin_id=1, created_date=datetime.now()),
            RoomCustomerRegulation(room_type_id=3, max_customers=2, admin_id=1, created_date=datetime.now()),
        ]

        db.session.bulk_save_objects(room_customer_regulations)
        db.session.commit()

        surcharge_regulations = [
            SurchargeRegulation(default_customer_count=2, surcharge_rate=0.25, admin_id=1, created_date=datetime.now()),
            SurchargeRegulation(default_customer_count=2, surcharge_rate=0.30, admin_id=1, created_date=datetime.now()),
        ]

        db.session.bulk_save_objects(surcharge_regulations)
        db.session.commit()

        reservation_customers_data = [
            {"reservation_id": 1, "customer_id": 1},
            {"reservation_id": 1, "customer_id": 2},
            {"reservation_id": 2, "customer_id": 3},
        ]

        customer_room_rentals_data = [
            {"customer_id": 1, "room_rental_id": 1},
            {"customer_id": 2, "room_rental_id": 2},
            {"customer_id": 3, "room_rental_id": 3},
        ]

        for entry in reservation_customers_data:
            db.session.execute(ReservationCustomer.insert().values(**entry))


        for entry in customer_room_rentals_data:
            db.session.execute(CustomerRoomRental.insert().values(**entry))

        db.session.commit()
