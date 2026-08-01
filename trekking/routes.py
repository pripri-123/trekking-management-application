from trekking import app
from flask import render_template, redirect, url_for, flash, get_flashed_messages
from trekking.models import Trek, User, Staff
from trekking.forms import TrekkerRegisterForm, LoginForm, StaffRegisterForm
from trekking import db
from flask_login import login_user, logout_user, login_required, current_user

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

"""
@app.route('/about/<username>')
def about_page(username):
    return f'<h2>About Page of {username}</h2>'
"""

@app.route('/treks')
@login_required
def treks_page():
    treks = Trek.query.all()
    return render_template('treks.html', treks=treks)

@app.route('/register', methods=['GET','POST'])
def register_page():
    form = TrekkerRegisterForm()
    if form.validate_on_submit():
        user_to_create = User(full_name=form.full_name.data, username=form.username.data, email=form.email.data, role='TREKKER')

        user_to_create.password = form.password.data

        db.session.add(user_to_create)
        db.session.commit()

        login_user(user_to_create)
        flash(f'Account created successfully! You are now logged in as: {user_to_create.username} ', category='success')
        user_to_create.update_last_login()

        return redirect(url_for('dashboard'))
    
    if form.errors != {}:
        for err_message in form.errors.values():
            flash(f'There was an error with creating a user: {err_message}', category='danger')
    return render_template('register.html',form=form)


@app.route('/staff/register', methods=['GET', 'POST'])
def staff_register_page():

    form = StaffRegisterForm()

    if form.validate_on_submit():

        user = User(full_name=form.full_name.data, username=form.username.data, email=form.email.data, role='STAFF')

        user.password = form.password.data

        db.session.add(user)
        db.session.flush()

        staff = Staff(id=user.id, phone=form.phone.data, status='Pending')

        db.session.add(staff)
        db.session.commit()

        flash('Registration successful. Waiting for admin approval.', category='info')
        return redirect(url_for('login_page'))

    return render_template('staff_register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.verify_password(
            attempted_password=form.password.data
        ):
            if attempted_user.blacklisted:
                flash('Account blocked.', category='danger')
                return redirect(url_for('login_page'))
            
            if attempted_user.role == "STAFF":
                        if attempted_user.staff_profile.status != "Approved":
                            flash("Waiting for admin approval.", category='warning')
                            return redirect(url_for('login_page'))
                        
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.username} ', category='success')
            attempted_user.update_last_login()

            return redirect(url_for('dashboard'))
        else:
            flash('Username not found! Please create an account first.', category='danger')

    return render_template('login.html',form=form)


@app.route('/logout')
def logout_page():
    logout_user()
    flash('You have been logged out!',category='info')
    return redirect(url_for('home_page'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():

    if current_user.role != 'ADMIN':
        flash('Access Denied.',category='danger')
        return redirect(url_for('home_page'))

    return render_template('admin_dashboard.html')

@app.route('/staff/dashboard')
@login_required
def staff_dashboard():

    if current_user.role != 'STAFF':
        flash('Access Denied.',category='danger')
        return redirect(url_for('home_page'))

    return render_template('staff_dashboard.html')


@app.route('/trekker/dashboard')
@login_required
def trekker_dashboard():

    if current_user.role != 'TREKKER':
        flash('Access Denied.',category='danger')
        return redirect(url_for('home_page'))

    return render_template('trekker_dashboard.html')


@app.route('/dashboard')
@login_required
def dashboard():

    if current_user.role == 'ADMIN':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'STAFF':
        return redirect(url_for('staff_dashboard'))
    else:
        return redirect(url_for('trekker_dashboard'))

@app.route('/approve_staff/<int:staff_id>')
@login_required
def approve_staff(staff_id):

    if current_user.role != 'ADMIN':
        flash('Access Denied')
        return redirect(url_for('home_page'))

    staff = Staff.query.get_or_404(staff_id)

    staff.status = 'Approved'
    db.session.commit()

    flash('Staff approved successfully.', category='success')
    return redirect(url_for('admin_dashboard'))

@app.route('/pending_staff')
@login_required
def pending_staff():

    if current_user.role != 'ADMIN':
        flash('Access Denied', 'danger')
        return redirect(url_for('home_page'))

    staff_members = Staff.query.filter_by(status='Pending').all()
    return render_template('pending_staff.html', staff_members=staff_members)
