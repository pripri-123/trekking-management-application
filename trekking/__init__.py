from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from dotenv import load_dotenv
import os

load_dotenv("keys.env")
app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///trekking.db')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message_category = 'info'
from trekking import routes  

from trekking.models import User
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role='ADMIN').first()
    if not admin:
        admin = User(full_name='System Admin', username='admin', email='admin@trek.com', role='ADMIN')
        admin.password = 'admin123'
        db.session.add(admin)
        db.session.commit()
