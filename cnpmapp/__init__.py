from urllib.parse import quote
from flask import Flask
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
import cloudinary.api

app = Flask(__name__)
app.config['SECRET_KEY'] = 'czx4c34xz3c523499-0930@##%1324&&^^%^^@#@#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%s@localhost/cnpm?charset=utf8mb4' % quote('0868656710')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SCHEDULER_API_ENABLED'] = True

db = SQLAlchemy(app=app)
login = LoginManager(app=app)
cloudinary.config(
    cloud_name='dokoicpvp',
    api_key='416817646635116',
    api_secret='QtYBWib1_k5wgFH7Ehn_KCfnIlM',
    secure=True
)

scheduler = APScheduler()
scheduler.init_app(app)


def get_locale():
    return 'vi'

babel = Babel(app, locale_selector=get_locale)
