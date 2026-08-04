from trekking import app
from flask import render_template, redirect, url_for, flash, get_flashed_messages, request
from trekking.models import TrekHistory, Trek, User, Staff, Booking
from trekking.forms import TrekkerRegisterForm, LoginForm, StaffRegisterForm, TrekForm
from trekking import db
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_

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

@app.route('/book_trek/<int:trek_id>', methods=['POST'])
@login_required
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.available_slots <= 0:
        flash("No slots available.", "danger")
        return redirect(url_for('treks_page'))
    booking = Booking(user_id=current_user.id, trek_id=trek.id)
    trek.available_slots -= 1
    db.session.add(booking)
    db.session.commit()
    flash("Trek booked successfully!", "success")
    return redirect(url_for('treks_page'))

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
                        if attempted_user.staff_profile.status == "Pending":
                            flash("Waiting for admin approval.", category='warning')
                            return redirect(url_for('login_page'))
                        if attempted_user.staff_profile.status == "Rejected":
                            flash("Admin has rejected your staff request.", category='danger')
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

    users = User.query.filter_by(role='TREKKER').count()
    treks = Trek.query.count()
    staffs = User.query.filter_by(role='STAFF').count()
    bookings = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    return render_template('admin_dashboard.html',users=users, treks=treks, staffs=staffs,bookings=bookings,recent_bookings=recent_bookings)

@app.route('/admin/users')
@login_required
def manage_users():
    if current_user.role != 'ADMIN':    
        flash('Access Denied.',category='danger')
        return redirect(url_for('home_page'))
    
    search = request.args.get('search')
    if search:
        users = User.query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.id == search if search.isdigit() else False
            )
        ).all()
    else:
        users = User.query.filter(User.role=='TREKKER').all()

    return render_template('manage_users.html', users=users)

@app.route('/admin/blacklist_user/<int:user_id>', methods=['POST'])
@login_required
def blacklist_user(user_id):
    if current_user.role != 'ADMIN':
        flash("Access Denied", "danger")
        return redirect(url_for('home_page'))
    user = User.query.get_or_404(user_id)
    user.blacklisted = True
    db.session.commit()
    flash('User blacklisted successfully!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/unblacklist_user/<int:user_id>', methods=['POST'])
@login_required
def unblacklist_user(user_id):
    if current_user.role != 'ADMIN':
        flash("Access Denied", "danger")
        return redirect(url_for('home_page'))
    user = User.query.get_or_404(user_id)
    user.blacklisted = False
    db.session.commit()
    flash('User unblacklisted successfully!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/treks')
@login_required
def manage_treks():
    if current_user.role != 'ADMIN':
        return redirect(url_for('home_page'))

    search = request.args.get('search')
    if search:
        treks = Trek.query.filter(
            or_(
                Trek.name.ilike(f"%{search}%"),
                Trek.location.ilike(f"%{search}%"),
                Trek.id == search if search.isdigit() else False
            )
        ).all()
    else:
        treks = Trek.query.all()
    return render_template('manage_treks.html', treks=treks)

@app.route('/admin/add_trek', methods=['GET','POST'])
@login_required
def add_trek():
    if current_user.role != 'ADMIN':
        flash('Access Denied.',category='danger')
        return redirect(url_for('home_page'))

    form = TrekForm()
    form.assigned_staff.choices = [(staff.id, staff.user.username) for staff in Staff.query.filter_by(status='Approved').all()]
    if form.validate_on_submit():
        trek = Trek(
            name=form.name.data,
            location=form.location.data,
            duration=form.duration.data,
            difficulty=form.difficulty.data,
            description=form.description.data,
            assigned_staff=form.assigned_staff.data,
            status=form.status.data,
            total_slots=form.total_slots.data,
            available_slots=form.total_slots.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data
        )

        db.session.add(trek)
        db.session.commit()
        flash('Trek created successfully','success')
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_trek.html',form=form, title="Add Trek")

@app.route('/admin/edit_trek/<int:trek_id>', methods=['GET', 'POST'])
@login_required
def edit_trek(trek_id):
    if current_user.role != 'ADMIN':
        flash("Access Denied", "danger")
        return redirect(url_for('home_page'))

    trek = Trek.query.get_or_404(trek_id)
    form = TrekForm(obj=trek)

    form.assigned_staff.choices = [(staff.id, staff.user.username) for staff in Staff.query.filter_by(status='Approved').all()]

    if form.validate_on_submit():
        trek.name = form.name.data
        trek.location = form.location.data
        trek.duration = form.duration.data
        trek.difficulty = form.difficulty.data
        trek.description = form.description.data
        trek.assigned_staff = form.assigned_staff.data
        trek.status = form.status.data
        trek.start_date = form.start_date.data
        trek.end_date = form.end_date.data

        db.session.commit()
        flash("Trek updated successfully!", "success")
        return redirect(url_for('manage_treks'))

    return render_template('edit_trek.html', form=form, trek=trek, title="Edit Trek")

@app.route('/admin/delete_trek/<int:trek_id>')
@login_required
def delete_trek(trek_id):

    if current_user.role != 'ADMIN':
        flash("Access Denied", "danger")
        return redirect(url_for('home_page'))

    trek = Trek.query.get_or_404(trek_id)

    db.session.delete(trek)
    db.session.commit()

    flash("Trek deleted successfully!", "success")

    return redirect(url_for('manage_treks'))

@app.route('/admin/bookings')
@login_required
def view_bookings():
    if current_user.role != 'ADMIN':
            return redirect(url_for('home_page'))
    bookings = Booking.query.all()
    return render_template('bookings.html', bookings=bookings)

@app.route('/admin/history')
@login_required
def trek_history():
    if current_user.role != 'ADMIN':
            return redirect(url_for('home_page'))
    histories = TrekHistory.query.all()

    return render_template('trek_history.html', histories=histories)

@app.route('/admin/staff')
@login_required
def pending_staff():
    if current_user.role != 'ADMIN':
        return redirect(url_for('home_page'))

    pending_staff = Staff.query.filter_by(status='Pending').all()
    return render_template('pending_staff.html', pending_staff=pending_staff)

@app.route('/admin/manage_staff')
@login_required
def manage_staff():
    if current_user.role != 'ADMIN':
        flash("Access Denied", "danger")
        return redirect(url_for('home_page'))
    
    pending_staff = Staff.query.filter_by(status='Pending').all()
    approved_staff = Staff.query.filter_by(status='Approved').all()
    rejected_staff = Staff.query.filter_by(status='Rejected').all()
    search = request.args.get('search')

    query = db.session.query(Staff, User).join(User)
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                Staff.id == search if search.isdigit() else False
            )
        )
    staffs = query.all()
    return render_template('manage_staff.html', staffs=staffs, pending_staff=pending_staff, approved_staff=approved_staff, rejected_staff=rejected_staff)

@app.route('/admin/approve_staff/<int:staff_id>')
@login_required
def approve_staff(staff_id):
    if current_user.role != 'ADMIN':
        flash('Access Denied')
        return redirect(url_for('home_page'))

    staff = Staff.query.get_or_404(staff_id)
    staff.status = 'Approved'
    db.session.commit()

    flash('Staff approved successfully.', category='success')
    return redirect(url_for('manage_staff'))

@app.route('/admin/reject_staff/<int:staff_id>')
@login_required
def reject_staff(staff_id):
    if current_user.role != 'ADMIN':
        flash('Access Denied')
        return redirect(url_for('home_page'))

    staff = Staff.query.get_or_404(staff_id)
    staff.status = 'Rejected'
    db.session.commit()

    flash('Staff rejected successfully.', category='success')
    return redirect(url_for('manage_staff'))

@app.route('/admin/blacklist_staff/<int:staff_id>', methods=['POST'])
@login_required
def blacklist_staff(staff_id):
    if current_user.role != 'ADMIN':
        flash("Access Denied", "danger")
        return redirect(url_for('home_page'))

    staff = Staff.query.get_or_404(staff_id)
    staff.user.blacklisted = True
    db.session.commit()

    flash("Staff has been blacklisted.", "success")
    return redirect(url_for('manage_staff'))

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

