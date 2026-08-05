from trekking import db, login_manager
from datetime import datetime
from trekking import bcrypt
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin): #Superclass, subclasses: trekker, staff, admin
    id = db.Column(db.Integer(),primary_key=True)
    full_name = db.Column(db.String(100),nullable=False)
    username = db.Column(db.String(length=30),nullable=False,unique=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    blacklisted = db.Column(db.Boolean, default=False)
    role = db.Column(db.Enum('ADMIN','STAFF','TREKKER',name='role_enum'),nullable=False)
    bookings = db.relationship('Booking',backref='user',lazy=True,cascade="all, delete-orphan") # backend logic will not allow staff to have bookings
    staff_profile = db.relationship('Staff',backref='user',uselist=False)

    @property
    def password(self):
        raise AttributeError('Password not readable')

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def verify_password(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

    def update_last_login(self):
        self.last_login = datetime.now()
        db.session.commit()

class Booking(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False) 
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'),nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.now)
    booking_status = db.Column(db.Enum('Booked','Cancelled','Completed'),default='Booked')
    history = db.relationship('TrekHistory',backref='booking',uselist=False,cascade="all, delete-orphan")
    __table_args__ = (
    db.UniqueConstraint(
        'user_id',
        'trek_id',
        name='unique_booking'
        ),
    )

class TrekHistory(db.Model):
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'),primary_key=True) 
    completion_date = db.Column(db.Date)
    rating = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text, nullable=True)
    __table_args__ = (
        db.CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="check_rating_range"
        ),
    )

class Staff(db.Model):
    id = db.Column(db.Integer(),db.ForeignKey('user.id'),primary_key=True)
    phone=db.Column(db.String(10))
    status = db.Column(db.Enum('Approved','Rejected','Pending'),default='Pending')
    assigned_treks = db.relationship('Trek',backref='staff_assigned')


class Trek(db.Model):
    id = db.Column(db.Integer(),primary_key=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    location = db.Column(db.String(length=40),nullable=False)
    duration = db.Column(db.Integer(),nullable=False)
    difficulty = db.Column(db.Enum('Easy','Moderate','Hard'),nullable=False)
    description = db.Column(db.Text,nullable=False)
    assigned_staff = db.Column(db.Integer,db.ForeignKey('staff.id'),nullable=False)
    status = db.Column(db.Enum('Pending','Open','Closed','Completed', 'Ongoing'),default='Pending')
    start_date = db.Column(db.Date, nullable = False)
    end_date = db.Column(db.Date, nullable = False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    total_slots = db.Column(db.Integer,nullable=False)
    available_slots = db.Column(db.Integer,nullable=False)
    bookings = db.relationship('Booking',backref='trek',cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'{self.name} Trek'

