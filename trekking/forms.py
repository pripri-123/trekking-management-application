from flask_wtf import FlaskForm
from wtforms import FloatField, DateField, IntegerField, StringField, PasswordField, SelectField, SubmitField, TextAreaField
from wtforms.validators import InputRequired, DataRequired, Length, NumberRange, Optional, EqualTo, Email, NumberRange, ValidationError
from trekking.models import Trek, Staff, User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    submit = SubmitField('Login')

class TrekkerRegisterForm(FlaskForm):
    full_name = StringField('Full Name', validators=[InputRequired(), Length(min=2,max=100)])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    email = StringField('Email',validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Create Account')

    def validate_username(self, username_to_check):
        user = User.query.filter_by(username=username_to_check.data).first()
        if user:
            raise ValidationError('Username already exists! Please try a different username or login with exisiting username.')
    
    def validate_email(self, email_to_check):
            email = User.query.filter_by(email=email_to_check.data).first()
            if email:
                raise ValidationError('Email already exists! Please try a differen email or login with exisiting email.')
        
class StaffRegisterForm(FlaskForm):
    full_name = StringField('Full Name', validators=[InputRequired(), Length(min=2,max=100)])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    email = StringField('Email',validators=[InputRequired(), Email()])
    phone = StringField('Phone Number',validators=[InputRequired(),Length(min=10,max=10)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

    def validate_username(self, username_to_check):
        user = User.query.filter_by(username=username_to_check.data).first()
        if user:
            raise ValidationError('Username already exists! Please try a different username or login with exisiting username.')
    
    def validate_email(self, email_to_check):
            email = User.query.filter_by(email=email_to_check.data).first()
            if email:
                raise ValidationError('Email already exists! Please try a differen email or login with exisiting email.')
        
class TrekReviewForm(FlaskForm):
    rating = FloatField('Rating', validators=[NumberRange(min=0, max=5, message="Rating must be between 0 and 5.")])
    review = TextAreaField('Review',validators=[DataRequired(),Length(max=500)])
    submit = SubmitField('Submit Review')

class TrekSearchForm(FlaskForm):
    search_type = SelectField('Search Type', choices=[('name', 'Trek Name'),('location', 'Location'),('difficulty', 'Difficulty')])
    search_text = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

    def validate_search_text(self, field):
        if self.search_type.data == 'difficulty':
            valid_levels = ['easy', 'moderate', 'hard']
            if field.data.lower() not in valid_levels:
                raise ValidationError('Difficulty must be Easy, Moderate or Hard.')
            
class TrekForm(FlaskForm):
    name = StringField('Trek Name', validators=[DataRequired(), Length(max=30)])
    location = StringField('Location', validators=[DataRequired(), Length(max=40)])
    difficulty = SelectField('Difficulty', choices=[('Easy', 'Easy'), ('Moderate', 'Moderate'), ('Hard', 'Hard')], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=1000)])
    assigned_staff = SelectField('Assigned Staff', coerce=int, choices=[])
    status = SelectField('Status', choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Open', 'Open'), ('Closed', 'Closed')])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    total_slots = IntegerField('Total Slots', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Save Trek')

    def __init__(self, *args, **kwargs):
        super(TrekForm, self).__init__(*args, **kwargs)
        self.assigned_staff.choices = [
            (staff.id, staff.user.full_name)
            for staff in Staff.query.filter_by(status='Approved').all()
        ]

    def validate_name(self, field):
        trek = Trek.query.filter_by(name=field.data).first()
        if trek and (not hasattr(self, 'trek') or trek.id != self.trek.id):
            raise ValidationError('A trek with this name already exists.')
        
    def validate_end_date(self, end_date):
        if self.start_date.data and end_date.data:
            if end_date.data <= self.start_date.data:
                raise ValidationError('End date must be after start date.')

            
class AssignStaffForm(FlaskForm):
    staff = SelectField('Staff',coerce=int)
    submit=SubmitField('Assign Staff')


class StaffProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=10)])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=8, message='Password must be at least 8 characters long.')])
    confirm_password = PasswordField('Confirm Password', validators=[Optional(), EqualTo('new_password', message='Passwords must match.'), Length(min=8, message='Password must be at least 8 characters long.')])
    submit = SubmitField('Update Profile')


class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=8, message='Password must be at least 8 characters long.')])
    confirm_password = PasswordField('Confirm Password', validators=[Optional(), EqualTo('new_password', message='Passwords must match.'), Length(min=8, message='Password must be at least 8 characters long.')])
    submit = SubmitField('Update Profile')

    