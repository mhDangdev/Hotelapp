import math, hashlib, json, random
from flask import render_template, request, url_for, redirect, session, jsonify, flash
from datetime import datetime, timedelta
from app import app, login, dao, login, utils, db, VNPAY_CONFIG
from flask_login import login_user, logout_user, current_user, login_required
from app.models import UserRole, User, RoomRental, Receipt
import cloudinary.uploader

# Trang chủ
@app.route("/")
def index():
    return render_template('index.html')

# Trang xem phòng
@app.route('/rooms')
def rooms():
    status = request.args.get('status')
    cr_rental = request.args.get('cr_rental')
    page = request.args.get('page', 1)
    rooms = dao.load_rooms(status=status, page=int(page))
    page_size = app.config.get('PAGE_SIZE', 8)
    total = dao.count_rooms(status)
    roomtype_regulation = dao.load_roomtype_regulation()
    return render_template('rooms.html', rooms=rooms,
                           cr_rental=cr_rental, roomtype_regulation=roomtype_regulation,
                           pages=math.ceil(total / page_size))


@app.route('/booking')
def booking():
    return render_template('booking.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about-us')
def about_us():
    return render_template('about-us.html')


@app.route('/reception_room')
def reception_room():
    status = request.args.get('status')
    cr_rental = request.args.get('cr_rental')
    cr_res = request.args.get('cr_res')
    page = request.args.get('page', 1)
    rooms = dao.load_rooms(status=status, page=int(page))
    page_size = app.config.get('PAGE_SIZE', 8)
    total = dao.count_rooms(status)
    roomtype_regulation = dao.load_roomtype_regulation()
    return render_template('reception/reception_room.html', rooms=rooms,
                           cr_rental=cr_rental,cr_res=cr_res,roomtype_regulation=roomtype_regulation,
                           pages=math.ceil(total/page_size))

@app.route('/reception')
def reception_home():
    kw = request.args.get("kw")
    criteria = request.args.get("criteria")
    cus = dao.get_customers()
    rooms = dao.get_rooms()
    # if not result:
    #     return redirect(request.referrer)
    result = dao.load_customers(criteria=criteria, kw=kw)

    return render_template('reception/reception_home.html'
                           ,result = result, customers = cus, rooms = rooms, criteria = criteria)
# #VNPay
# @app.route('/payment_process',methods=['GET','POST'])
# def paymentprocess():
#     if request.method == 'POST':
#         reservation = session.get('ticket_info')
#         amount = ticket_info.get('quantity') * ticket_info.get('price')
#         order_id = ticket_info.get('order_id')
#         vnp = dao.vnpay()
#         vnp.requestData['vnp_Version'] = '2.1.0'
#         vnp.requestData['vnp_Command'] = 'pay'
#         vnp.requestData['vnp_TmnCode'] = VNPAY_CONFIG['vnp_TmnCode']
#         vnp.requestData['vnp_Amount'] = str(int(amount * 100))
#         vnp.requestData['vnp_CurrCode'] = 'VND'
#         vnp.requestData['vnp_TxnRef'] = order_id
#         vnp.requestData['vnp_OrderInfo'] = 'Thanhtoan'  # Nội dung thanh toán
#         vnp.requestData['vnp_OrderType'] = 'ticket'
#
#         vnp.requestData['vnp_Locale'] = 'vn'
#
#         vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
#         vnp.requestData['vnp_IpAddr'] = "127.0.0.1"
#         vnp.requestData['vnp_ReturnUrl'] = url_for('vnpay_return', _external=True)
#
#         vnp_payment_url = vnp.get_payment_url(VNPAY_CONFIG['vnp_Url'], VNPAY_CONFIG['vnp_HashSecret'])
#
#         print(vnp_payment_url)
#
#         return redirect(vnp_payment_url)
#
# @app.route('/vnpay_return')
# def vnpay_return():
#     vnp_ResponseCode = request.args.get('vnp_ResponseCode')
#     if vnp_ResponseCode == '00':
#         utils.add_ticket(session.get('ticket_info'))
#         utils.send_ticket_email(session.get('ticket_info'))
#         del session['ticket_info']
#         flash(message="Đặt vé thành công", category="Thông báo")
#     return redirect('/')
# Thanh toán
@app.route("/reception_payment")
def payment_process():
    room_id = request.args.get('room_id')
    room_name = request.args.get('room_name')
    cus_name = dao.get_first_customer(room_id)
    roomrental = dao.get_room_rental(room_id)
    total = dao.get_total(room_id)
    return render_template('reception/reception_payment.html', room_name=room_name, cus_name=cus_name
                           ,roomrental=roomrental, total=total)

# user
@app.route("/login", methods=['get', 'post'])
def login_process():
    err_msg = ''
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        u = dao.auth_user(username=username, password=password)
        if u:
            login_user(u)
            if u.role == UserRole.RECEPTION:
                return redirect('/reception')
            elif u.role == UserRole.ADMIN:
                return redirect('/admin')
            return redirect('/')
        else:
            err_msg = 'Username or Password is incorrect!!!'
    return render_template('login.html', err_msg=err_msg)



@app.route('/login-admin', methods=['get', 'post'])
def user_signin():
    err_msg = ''
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        user = utils.check_login(username=username, password=password)
        if user:
            login_user(user=user)

            if current_user.role == UserRole.ADMIN:
                return redirect('/admin')
            elif current_user.role == UserRole.RECEPTIONIST:
                return redirect(url_for('room_renting'))
            else:
                return redirect(url_for('home'))
        else:
            err_msg = 'Username or Password is incorrect!!!'

    return render_template('login_admin.html', err_msg=err_msg)


@login.user_loader
def get_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route("/logout")
def logout_process():
    logout_user()
    return redirect('/login')


@app.route('/register', methods=['get', 'post'])
def register_process():
    err_msg = None
    if request.method.__eq__('POST'):
        confirm = request.form.get('confirm')
        password = request.form.get('password')
        if password.__eq__(confirm):
            data = request.form.copy()
            del data['confirm']

            avatar = request.files.get('avatar')
            dao.add_user(avatar=avatar, **data)
            return redirect('/login')
        else:
            err_msg = 'Mật khẩu KHÔNG khớp!'

    return render_template('register.html', err_msg=err_msg)

@app.route('/reception_rental', methods=['GET', 'POST'])
def reception_rental():
    room_id = request.args.get('room_id')
    room_name = request.args.get('room_name')
    err_msg = None
    if request.method == 'POST':
        checkin_date = request.form.get('checkin_date')
        checkout_date = request.form.get('checkout_date')
        room_id = request.form.get('room_id')
        guest_count = int(request.form.get('guest_count', 0))
        guests = []
        for i in range(1, guest_count + 1):
            guest = {
                'name': request.form.get(f'guest{i}_name'),
                'type': request.form.get(f'guest{i}_type'),
                'cmnd': request.form.get(f'guest{i}_cmnd'),
                'address': request.form.get(f'guest{i}_address')
            }
            guests.append(guest)

        # Kiểm tra dữ liệu hợp lệ
        if checkin_date and checkout_date and guest_count != 0:
            for guest in guests:
                if guest['name'] and guest['type'] and guest['cmnd'] and guest['address']:
                    dao.add_customer(name=guest['name'], customer_type=guest['type'],
                                     cmnd=guest['cmnd'], address=guest['address'])
                else:
                    err_msg = 'VUI LÒNG ĐIỀN ĐẦY ĐỦ THÔNG TIN!'
            if not err_msg :
                r = dao.add_roomrental(checkin_date=checkin_date, checkout_date=checkout_date, room_id=room_id)
                dao.update_room_status(room_id, 'đã được thuê')
                for guest in guests:
                    dao.add_customer_roomrental(customer_id=dao.get_user_id_by_cmnd(guest['cmnd']), room_rental_id=r.id)
                return redirect('/reception')
    return render_template('reception/reception_rental.html',
                           room_id=room_id, room_name=room_name, err_msg=err_msg)

@app.route('/reception_reservation', methods=['GET', 'POST'])
def reception_reservation():
    room_id = request.args.get('room_id')
    room_name = request.args.get('room_name')
    err_msg = None
    if request.method == 'POST':
        booker_name = request.form.get('booker_name')
        checkin_date = request.form.get('checkin_date')
        checkout_date = request.form.get('checkout_date')
        room_id = request.form.get('room_id')
        room_name = request.form.get('room_name')
        guest_count = int(request.form.get('guest_count', 0))
        guests = []
        for i in range(1, guest_count + 1):
            guest = {
                'name': request.form.get(f'guest{i}_name'),
                'type': request.form.get(f'guest{i}_type'),
                'cmnd': request.form.get(f'guest{i}_cmnd'),
                'address': request.form.get(f'guest{i}_address')
            }
            guests.append(guest)

        # Kiểm tra dữ liệu hợp lệ
        checkin_date = datetime.strptime(checkin_date, "%Y-%m-%d")
        checkout_date = datetime.strptime(checkout_date, "%Y-%m-%d")
        if checkin_date and checkout_date and guest_count != 0 and booker_name:
            if checkin_date > datetime.now() + timedelta(days=28):
                err_msg = 'THỜI GIAN THUÊ KHÔNG HỢP LỆ!, KHÔNG CÁCH HIỆN TẠI QUÁ 28 NGÀY'
            if checkin_date > checkout_date:
                err_msg = 'THỜI GIAN THUÊ KHÔNG HỢP LỆ!'
            for r in dao.get_all_res(room_id):
                if r.checkin_date < checkin_date and r.checkout_date > checkout_date:
                    err_msg = 'THỜI GIAN THUÊ KHÔNG HỢP LỆ!'
                if r.checkin_date > checkin_date and r.checkout_date < checkout_date:
                    err_msg = 'THỜI GIAN THUÊ KHÔNG HỢP LỆ!'
            for guest in guests:
                if guest['name'] and guest['type'] and guest['cmnd'] and guest['address']:
                    dao.add_customer(name=guest['name'], customer_type=guest['type'],
                                     cmnd=guest['cmnd'], address=guest['address'])
                else:
                    err_msg = 'VUI LÒNG ĐIỀN ĐẦY ĐỦ THÔNG TIN!'
            if not err_msg :
                r = dao.add_reservation(booker_name=booker_name, checkin_date=checkin_date,
                                        checkout_date=checkout_date, room_id=room_id)
                for guest in guests:
                    dao.add_reservation_customer(customer_id=dao.get_user_id_by_cmnd(guest['cmnd'])
                                                 , reservation_id=r.id)
                return redirect('/reception')
    return render_template('reception/reception_reservation.html',
                           room_id=room_id, room_name=room_name, err_msg=err_msg)


@app.route('/api/carts', methods=['post'])
def add_to_cart():
    cart = session.get('cart')
    if not cart:
        cart = {}

    id = str(request.json.get("id"))
    name = request.json.get("name")
    price = request.json.get("price")

    if id in cart:
        cart[id]["quantity"] += 1
    else:
        cart[id] = {
            "id": id,
            "name": name,
            "price": price,
            "quantity": 1
        }

    session['cart'] = cart

    return jsonify(utils.stats_cart(cart))


@app.route('/cart')
def cart():
    return render_template('cart.html')


# admin
@app.route('/user-logout')
def user_signout():
    logout_user()
    return redirect(url_for('user_signin'))

@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)



if __name__ == '__main__':
    from app import admin
    app.run(debug=True)
