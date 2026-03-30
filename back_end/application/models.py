from .database import db
from flask_security import UserMixin, RoleMixin
from datetime import datetime

class UsersRoles(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

class Role(db.Model, RoleMixin):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String)

class Department(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String)
    # 'doctors' backref lives on User side — don't define relationship here

class User(db.Model, UserMixin):
    id             = db.Column(db.Integer, primary_key=True)
    email          = db.Column(db.String, unique=True, nullable=False)
    username       = db.Column(db.String, unique=True, nullable=False)
    password       = db.Column(db.String, nullable=False)
    fs_uniquifier  = db.Column(db.String, unique=True, nullable=False)
    active         = db.Column(db.Boolean, nullable=False, default=True)
    roles          = db.relationship('Role', backref='bearer', secondary='users_roles')

    # doctor-specific (nullable for non-doctors)
    department_id    = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    department       = db.relationship('Department', backref='doctors')  # ← moved here
    experience_years = db.Column(db.Integer, nullable=True)

class Appointment(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date       = db.Column(db.Date, nullable=False)     # ← use Date not String
    time       = db.Column(db.Time, nullable=False)     # ← use Time not String
    status     = db.Column(db.String, nullable=False, default="Booked")

    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor  = db.relationship('User', foreign_keys=[doctor_id])

class Treatment(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    diagnosis      = db.Column(db.String, nullable=False)
    prescription   = db.Column(db.String, nullable=False)
    medicines      = db.Column(db.String, nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)  # ← good to add

    appointment = db.relationship('Appointment', backref='treatment')  # ← add this

class Availability(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date      = db.Column(db.Date, nullable=False)       # ← use Date
    time_slot = db.Column(db.Time, nullable=False)       # ← use Time
    is_booked = db.Column(db.Boolean, default=False)     # ← add this flag

    doctor = db.relationship('User', backref='availability')  # ← add this