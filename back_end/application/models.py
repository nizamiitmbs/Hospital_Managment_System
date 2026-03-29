from .database import db
from flask_security import UserMixin, RoleMixin

# ---------------------------------------------------------
# 1. SECURITY & AUTHENTICATION MODELS (RBAC)
# ---------------------------------------------------------

class UsersRoles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    fs_uniquifier = db.Column(db.String, unique=True, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    roles = db.relationship('Role', backref='bearer', secondary='users_roles')
    
    # Extra fields for HMS (nullable=True because they don't apply to all roles)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)

# ---------------------------------------------------------
# 2. HOSPITAL BUSINESS LOGIC MODELS
# ---------------------------------------------------------

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String)
    
    # Virtual link to find all doctors in this department
    doctors = db.relationship('User', backref='department')

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False, default="Booked")
    
    # Relationships to easily fetch full user details
    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('User', foreign_keys=[doctor_id])

class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    diagnosis = db.Column(db.String, nullable=False)
    prescription = db.Column(db.String, nullable=False)
    medicines = db.Column(db.String, nullable=True)

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String, nullable=False)
    time_slot = db.Column(db.String, nullable=False)