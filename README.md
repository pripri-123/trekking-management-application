# Trekking Management Application

## Overview

The Trekking Management Application is a role-based web application developed using Flask that enables efficient management of trekking events, participants, staff, bookings, and trekking history.

The system supports three types of users:

* **Administrator**
* **Trek Staff**
* **Trekker (User)**

The application provides secure authentication, trek management, booking management, participant tracking, trekking history, and role-based access control.


## Features

### Administrator

* Manage treks (Add, Edit, Delete)
* Manage staff requests
* Approve or reject staff registrations
* Blacklist or unblacklist users and staff
* View all bookings
* View complete trekking history
* Search users, staff, and treks
* Assign staff members to treks

### Trek Staff

* View assigned treks
* View trek participants
* Manage trek status
* Mark treks as ongoing or completed
* Remove participants
* Update profile information

### Trekker

* Register and log in
* Update profile information
* Browse available treks
* Search treks by name, location, and difficulty
* Book treks
* Cancel bookings
* View booking history
* View trekking history
* Rate and review completed treks

## Technologies Used

### Backend

* Flask
* Flask-Login
* Flask-WTF
* Flask-Bcrypt
* SQLAlchemy

### Frontend

* HTML5
* CSS
* Bootstrap
* Jinja2 Templates

### Database

* SQLite

## Project Structure

```text
trekking-management-application/
│
├── trekking/
│   ├── __init__.py
│   ├── models.py
│   ├── forms.py
│   ├── routes.py
│   └── templates/
│
├── myenv/
├── requirements.txt
├── run.py
├── README.md
├── keys.env
└── .gitignore
```

## Database Design

The application consists of the following entities:

* User
* Staff
* Trek
* Booking
* TrekHistory

### Relationships

* One User can have multiple Bookings.
* One Trek can have multiple Bookings.
* One Booking can have one TrekHistory record.
* One Staff member can manage multiple Treks.
* Staff is a specialization of User.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/24f2004973/trekking-management-application.git

cd trekking-management-application
```

### 2. Create a Virtual Environment

Windows:

```bash
python -m venv myenv
```

Activate:

```bash
myenv\Scripts\activate
```

Linux/Mac:

```bash
python3 -m venv myenv

source myenv/bin/activate
```


### 3. Install Dependencies

```bash
pip install -r requirements.txt
```


### 4. Configure Environment Variables

Create a file named `keys.env` in the project root.

Example:

```env
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///trekking.db
```

### 5. Run the Application

```bash
python run.py
```

On first startup:

* SQLite database will be created automatically.
* All tables will be created automatically.
* A default administrator account will be created automatically.

### Default Admin Credentials

```text
Username: admin
Password: admin123
```

The application will be available at:

```text
http://127.0.0.1:5000
```

## User Roles

### Admin

Responsible for managing the entire application including users, staff, treks, bookings, and trekking history.

### Staff

Responsible for managing assigned treks and participants.

### Trekker

Responsible for booking treks, viewing history, and submitting ratings and reviews.


## Security Features

The application implements multiple security measures to protect user accounts, trekking data, and system functionality.

### Authentication and Session Management

* User authentication is implemented using **Flask-Login**.
* Protected routes require users to be logged in before access is granted.
* Unauthorized users are automatically redirected to the login page.
* User sessions are securely maintained throughout application usage.

### Password Security

* Passwords are never stored in plain text.
* Password hashing is implemented using **Flask-Bcrypt**.
* Password verification is performed using secure hash comparison.
* Password updates require confirmation before changes are applied.

### Role-Based Access Control

The system enforces strict role-based permissions:

#### Administrator

* Manage users, staff, treks, bookings, and trekking history.
* Approve or reject staff registrations.
* Blacklist or unblacklist users and staff.

#### Trek Staff

* Access only treks assigned to them.
* Manage participants of assigned treks.
* Update trek status and trek records.

#### Trekker

* View and book available treks.
* Access only their own bookings and trekking history.
* Submit ratings and reviews for completed treks.

### Data Validation and Integrity

* Unique usernames and email addresses are enforced.
* Duplicate trek bookings are prevented through database constraints.
* Trek bookings are allowed only when:

  * Trek status is **Open**
  * Available slots are greater than zero
* Overbooking is prevented by tracking available slots.
* Trek ratings are restricted to values between **1 and 5**.
* Date validation ensures trek duration matches the selected start and end dates.

### Trek Access Protection

* Staff members can manage only treks assigned to them.
* Users can view only their own booking and trekking history.
* Trek completion records are generated only for completed treks.
* Participant management is restricted to the assigned trek staff.

### Environment Configuration

* Application secrets are stored in the **keys.env** file.
* Sensitive configuration values are loaded using **python-dotenv**.
* Database connection settings and secret keys are not hardcoded in the source code.

### Account Protection

* User and staff accounts can be blacklisted by administrators.
* Blacklisted users are prevented from accessing protected application functionality.
* Role verification is performed before executing sensitive operations.


## Validation Rules

* Unique usernames and emails
* Unique booking per user per trek
* Trek booking allowed only when status is Open
* Trek booking blocked when slots are full
* Ratings restricted to values between 1 and 5
* Password updates require confirmation and minimum length validation


## Future Enhancements

* REST API support
* Analytics dashboard
* Email notifications
* Trek image uploads
* Advanced reporting and statistics

## Author

**Priyadarshini Palani Rajan**
**24f2004973**


## License

This project was developed for educational purposes as part of an Application Development project.
