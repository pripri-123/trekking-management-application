from trekking import app
from flask import render_template, redirect, url_for, flash, get_flashed_messages, request
from trekking.models import TrekHistory, Trek, User, Staff, Booking
from trekking.forms import TrekkerRegisterForm, LoginForm, StaffRegisterForm, TrekForm, StaffProfileForm, ProfileForm
from trekking import db
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from datetime import date

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
    search = request.args.get('search', '').strip()
    difficulty = request.args.get('difficulty', '')
    query = Trek.query.filter(Trek.status == 'Open')
    if search:
        query = query.filter(
            or_(
                Trek.name.ilike(f"%{search}%"),
                Trek.location.ilike(f"%{search}%")
            )
        )
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    treks = query.all()
    return render_template('treks.html', treks=treks, search=search, difficulty=difficulty)

@app.route('/book_trek/<int:trek_id>', methods=['POST'])
@login_required
def book_trek(trek_id):
    if current_user.role != 'TREKKER':
        flash('Only trekkers can book treks.', 'danger')
        return redirect(url_for('home_page'))

    trek = Trek.query.get_or_404(trek_id)
    if trek.status != 'Open':
        flash('Bookings are closed for this trek. Sorry!', 'danger')
        return redirect(url_for('treks_page'))
    
    if trek.available_slots <= 0:
        flash('No slots available.', 'danger')
        return redirect(url_for('treks_page'))
    
    existing = Booking.query.filter_by(user_id=current_user.id, trek_id=trek.id).first()
    if existing:
        flash('You have already booked this trek.', 'warning')
        return redirect(url_for('treks_page'))
    booking = Booking(user_id=current_user.id, trek_id=trek.id)
    trek.available_slots -= 1
    db.session.add(booking)
    db.session.commit()
    flash('Trek booked successfully!', 'success')
    return redirect(url_for('my_bookings'))

@app.route('/my_bookings')
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('user/my_bookings.html', bookings=bookings)

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Access Denied.', 'danger')
        return redirect(url_for('home_page'))

    booking.trek.available_slots += 1
    db.session.delete(booking)
    db.session.commit()

    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('my_bookings'))

@app.route('/my_history')
def my_history():
    histories = TrekHistory.query.join(Booking).filter(Booking.user_id == current_user.id).all()
    return render_template('user/my_history.html', histories=histories)

@app.route('/profile', methods=['GET','POST'])
def profile():
    form = ProfileForm()
    if request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.username.data = current_user.username
        form.email.data = current_user.email

    if form.validate_on_submit():
        existing_user = User.query.filter(User.id != current_user.id, ((User.username == form.username.data) | (User.email == form.email.data))).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return render_template('profile.html', form=form)

        current_user.full_name = form.full_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('user/profile.html', form=form)


@app.route('/rate_trek/<int:booking_id>', methods=['GET', 'POST'])
def rate_trek(booking_id):

    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Access Denied.', 'danger')
        return redirect(url_for('home_page'))

    history = booking.history
    if not history:
        flash('Trek has not been completed yet.', 'warning')
        return redirect(url_for('my_history'))

    if request.method == 'POST':
        history.rating = int(request.form.get('rating'))
        history.review = request.form.get('review')
        db.session.commit()
        flash('Review submitted successfully.', 'success')
        return redirect(url_for('my_history'))
    
    return render_template('user/rate_trek.html', booking=booking, history=history)

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
        if attempted_user and attempted_user.verify_password(attempted_password=form.password.data):
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
            flash('Invalid username or password.', 'danger')

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
    staffs = Staff.query.filter_by(status='Approved').count()
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
                User.id == int(search) if search.isdigit() else False
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

@app.route('/admin/treks',methods=['GET','POST'])
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
            duration=(form.end_date.data-form.start_date.data).days,
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
        trek.duration=(form.end_date.data-form.start_date.data).days,
        trek.difficulty = form.difficulty.data
        trek.description = form.description.data
        trek.assigned_staff = form.assigned_staff.data
        trek.status = form.status.data
        difference = form.total_slots.data - trek.total_slots
        trek.total_slots = form.total_slots.data
        trek.available_slots += difference
        trek.start_date = form.start_date.data
        trek.end_date = form.end_date.data

        db.session.commit()
        flash("Trek updated successfully!", "success")
        return redirect(url_for('manage_treks'))

    return render_template('edit_trek.html', form=form, trek=trek, title="Edit Trek")

@app.route('/admin/delete_trek/<int:trek_id>', methods=['POST'])
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

@app.route('/admin/complete_trek/<int:trek_id>', methods=['POST'])
@login_required
def complete_trek(trek_id):
    if current_user.role != 'ADMIN':
            return redirect(url_for('home_page'))
    
    trek = Trek.query.get_or_404(trek_id)
    if trek.status == 'Completed':
        flash('Trek already completed.', 'warning')
        return redirect(url_for('manage_treks'))
    trek.status = 'Completed'
    for booking in trek.bookings:
        booking.booking_status = 'Completed'
        if not booking.history:
            history = TrekHistory(booking_id=booking.id, completion_date=date.today())
            db.session.add(history)
    db.session.commit()
    flash('Trek marked as completed!', 'success')
    return redirect(url_for('manage_treks'))

@app.route('/admin/history')
@login_required
def trek_history():
    if current_user.role != 'ADMIN':
        return redirect(url_for('home_page'))
    histories = TrekHistory.query.all()

    return render_template('trek_history.html', histories=histories)


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

@app.route('/admin/approve_staff/<int:staff_id>', methods=['GET','POST'])
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

@app.route('/admin/reject_staff/<int:staff_id>', methods=['POST'])
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

    staff = Staff.query.get(current_user.id)
    if not staff or staff.status != 'Approved':
        flash('Account not approved.', 'danger')
        return redirect(url_for('home_page'))

    assigned_treks = Trek.query.filter_by(assigned_staff=staff.id).all()
    total_treks = len(assigned_treks)
    trekker_count = sum(len(trek.bookings) for trek in assigned_treks)
    open_treks = sum(1 for trek in assigned_treks if trek.status=='Open')
    return render_template('staff_dashboard.html', assigned_treks=assigned_treks, total_treks=total_treks, total_participants=trekker_count, open_treks=open_treks)


@app.route('/staff/treks')
@login_required
def my_treks():
    staff = Staff.query.get(current_user.id)
    if not staff or staff.status != 'Approved':
        flash('Account not approved.', 'danger')
        return redirect(url_for('home_page'))
    
    treks = Trek.query.filter_by(assigned_staff=staff.id).all()
    return render_template('staff/staff_treks.html',treks=treks)

def is_assigned_staff(trek):
    return (current_user.role == 'STAFF' and trek.assigned_staff == current_user.id)


@app.route('/staff/trek/<int:trek_id>')
@login_required
def manage_staff_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if not is_assigned_staff(trek):
        flash('Access Denied.', 'danger')
        return redirect(url_for('staff_dashboard'))

    return render_template('staff/manage_staff_trek.html', trek=trek)

@app.route('/staff/update_slots/<int:trek_id>', methods=['POST'])
@login_required
def update_slots(trek_id):

    trek = Trek.query.get_or_404(trek_id)

    if not is_assigned_staff(trek):
        flash('Access Denied.', 'danger')
        return redirect(url_for('staff_dashboard'))

    trek.available_slots = int(request.form.get('available_slots'))
    db.session.commit()
    flash('Available slots updated.', 'success')
    return redirect(url_for('manage_staff_trek', trek_id=trek.id))


@app.route('/staff/start_trek/<int:trek_id>', methods=['POST'])
@login_required
def start_trek(trek_id):

    trek = Trek.query.get_or_404(trek_id)

    if not is_assigned_staff(trek):
        flash('Access Denied.', 'danger')
        return redirect(url_for('staff_dashboard'))

    if trek.status != 'Open':
        flash('Only open treks can be started.', 'warning')
        return redirect(url_for('manage_staff_trek',trek_id=trek.id))

    trek.status = 'Ongoing'
    db.session.commit()
    flash('Trek started successfully.', 'success')

    return redirect(url_for('manage_staff_trek', trek_id=trek.id))

@app.route('/staff/complete_trek/<int:trek_id>', methods=['POST'])
@login_required
def complete_staff_trek(trek_id):

    trek = Trek.query.get_or_404(trek_id)

    if not is_assigned_staff(trek):
        flash('Access Denied.', 'danger')
        return redirect(url_for('staff_dashboard'))

    if trek.status == 'Completed':
        flash('Trek already completed.', 'warning')
        return redirect(url_for('manage_staff_trek', trek_id=trek.id))

    trek.status = 'Completed'
    for booking in trek.bookings:
        booking.booking_status = 'Completed'
        if not booking.history:
            history = TrekHistory(booking_id=booking.id, completion_date=date.today())
            db.session.add(history)
    db.session.commit()

    flash('Trek completed successfully.', 'success')
    return redirect(url_for('manage_staff_trek', trek_id=trek.id))

@app.route('/staff/trek/<int:trek_id>/participants')
@login_required
def view_participants(trek_id):

    trek = Trek.query.get_or_404(trek_id)
    if not is_assigned_staff(trek):
        flash('Access Denied.', 'danger')
        return redirect(url_for('staff_dashboard'))

    return render_template('participants.html', trek=trek, bookings=trek.bookings)

@app.route('/staff/profile', methods=['GET', 'POST'])
@login_required
def staff_profile():

    staff = Staff.query.get(current_user.id)
    if not staff or staff.status != 'Approved':
        flash('Account not approved.', 'danger')
        return redirect(url_for('home_page'))

    form = StaffProfileForm()
    if request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.email.data = current_user.email
        form.phone.data = staff.phone

    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        staff.phone = form.phone.data
        db.session.commit()

        flash('Profile updated successfully.', 'success')
        return redirect(url_for('staff_profile'))
    return render_template('staff/staff_profile.html', form=form)


@app.route('/staff/remove_participant/<int:booking_id>', methods=['POST'])
@login_required
def remove_participant(booking_id):

    booking = Booking.query.get_or_404(booking_id)
    trek = booking.trek
    if not is_assigned_staff(trek):
        flash('Access Denied.', 'danger')
        return redirect(url_for('staff_dashboard'))

    trek.available_slots += 1
    db.session.delete(booking)
    db.session.commit()
    flash('Participant removed successfully.', 'success')
    return redirect(url_for('manage_staff_trek', trek_id=trek.id))

@app.route('/trekker/dashboard')
@login_required
def trekker_dashboard():
    if current_user.role != 'TREKKER':
        flash('Access Denied.',category='danger')
        return redirect(url_for('home_page'))
    return render_template('home.html')


@app.route('/dashboard')
@login_required
def dashboard():

    if current_user.role == 'ADMIN':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'STAFF':
        return redirect(url_for('staff_dashboard'))
    else:
        return redirect(url_for('trekker_dashboard'))

