from flask import Flask
from dotenv import load_dotenv
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
import os
from flask_mail import Mail

load_dotenv()

application = Flask(__name__)
application.config.from_object(__name__)

application.secret_key = os.getenv("SECRET_KEY")
application.permanent_session_lifetime = timedelta(days=365)

application.config['UPLOAD_FOLDER'] = 'uploads'
application.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.config['JSON_AS_ASCII'] = False

application.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
application.config['MAIL_PORT'] = os.getenv("MAIL_PORT")
# application.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS")
application.config['MAIL_USE_SSL'] = os.getenv("MAIL_USE_SSL")
application.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
application.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")
application.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

db = SQLAlchemy(application)

login_manager = LoginManager(application)
login_manager.login_view = 'login'

mail = Mail(application)