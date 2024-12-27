from flask import Flask
from urllib.parse import quote
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary

app = Flask(__name__)
app.secret_key = 'HKJHFAKHFA2%$^452DSA%#%^653BJHB'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/hoteldb?charset=utf8mb4" % quote('123456')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 8

db = SQLAlchemy(app=app)
login = LoginManager(app=app)

cloudinary.config(
    cloud_name="dxxwcby8l",
    api_key="448651448423589",
    api_secret="ftGud0r1TTqp0CGp5tjwNmkAm-A",  # Click 'View API Keys' above to copy your API secret
    secure=True
)

VNPAY_CONFIG = {
        'vnp_TmnCode': 'JTUTARBA',
        'vnp_HashSecret': 'YGOTOHGJS772HDGA1KE690H64UK3SQTV',
        'vnp_Url': 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html',
        "vnp_ReturnUrl": "http://localhost:5000/vnpay_return"
    }