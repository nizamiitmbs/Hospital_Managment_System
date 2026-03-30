from flask_restful import Api, Resource, reqparse
from application.models import Treatment, db, Appointment, User
from flask_security import auth_required, roles_required, roles_accepted, current_user

api = Api()

# Define the parser to safely capture JSON request body data
appointment_parser = reqparse.RequestParser()
appointment_parser.add_argument('doctor_id', type=int)
appointment_parser.add_argument('date', type=str)
appointment_parser.add_argument('time', type=str)
appointment_parser.add_argument('status', type=str)

# Helper function to extract role strings (from previous conversations)
def roles_list(roles):
    return [role.name for role in roles]

class AppointmentApi(Resource):
    
    @auth_required('token')
    @roles_accepted('patient', 'doctor', 'admin')
    def get(self):
        appointments = []
        appt_jsons = []
        user_roles = roles_list(current_user.roles)
        
        # Admin gets everything, doctors/patients get only their own history
        if "admin" in user_roles: 
            appointments = Appointment.query.all()
        elif "doctor" in user_roles:
            appointments = Appointment.query.filter_by(doctor_id=current_user.id).all()
        else:
            appointments = Appointment.query.filter_by(patient_id=current_user.id).all()
            
        for appt in appointments:
            this_appt = {}
            this_appt["id"] = appt.id
            this_appt["doctor_id"] = appt.doctor_id
            this_appt["patient_id"] = appt.patient_id
            this_appt["date"] = appt.date
            this_appt["time"] = appt.time
            this_appt["status"] = appt.status
            appt_jsons.append(this_appt)
        
        if appt_jsons:
            return appt_jsons, 200
        
        return {"message": "No appointments found"}, 404
    
    @auth_required('token')
    @roles_required('patient')
    def post(self):
        args = appointment_parser.parse_args()
        
        # HMS Requirement: Prevent double-booking for the same doctor
        existing_appt = Appointment.query.filter_by(
            doctor_id=args['doctor_id'], 
            date=args['date'], 
            time=args['time']
        ).first()
        
        if existing_appt:
            return {"message": "This doctor is already booked for this slot."}, 400

        try:
            new_appt = Appointment(
                patient_id=current_user.id,
                doctor_id=args['doctor_id'],
                date=args['date'],
                time=args['time'],
                status="Booked"
            )
            db.session.add(new_appt)
            db.session.commit()
            return {"message": "Appointment created successfully!"}, 201
        except:
            return {"message": "One or more required fields are missing"}, 400

    @auth_required('token')
    @roles_accepted('patient', 'doctor', 'admin')   
    def put(self, appt_id):
        args = appointment_parser.parse_args()
        appt = Appointment.query.get(appt_id)
        
        if not appt:
            return {"message": "Appointment not found"}, 404
            
        # Update details if provided
        if args.get('date'): appt.date = args['date']
        if args.get('time'): appt.time = args['time']
        if args.get('status'): appt.status = args['status']
        
        db.session.commit()
        return {"message": "Appointment updated successfully!"}, 200
    
    @auth_required('token')
    @roles_accepted('admin', 'patient')   
    def delete(self, appt_id):
        appt = Appointment.query.get(appt_id)
        if appt:
            db.session.delete(appt)
            db.session.commit()
            return {"message": "Appointment deleted successfully!"}, 200
        else:
            return {"message": "Appointment not found!"}, 404

# Map the endpoints to the API class
api.add_resource(AppointmentApi, 
                 '/api/appointments/get', 
                 '/api/appointments/create', 
                 '/api/appointments/update/<int:appt_id>', 
                 '/api/appointments/delete/<int:appt_id>')


availability_parser = reqparse.RequestParser()
availability_parser.add_argument('date', type=str, required=True)
availability_parser.add_argument('time_slot', type=str, required=True)

class AvailabilityApi(Resource):
    
    # 1. GET Method: Used by Patients to view free slots before booking
    @auth_required('token')
    @roles_accepted('patient', 'doctor', 'admin')
    def get(self, doctor_id):
        # Concept: The frontend passes the specific doctor's ID in the URL.
        # Why: Because a patient is looking at a specific doctor's profile and wants to see ONLY their schedule.
        slots = Availability.query.filter_by(doctor_id=doctor_id).all()
        
        if not slots:
            return {"message": "No availability found for this doctor"}, 404
            
        return [
            {
                "id": slot.id,
                "date": slot.date,
                "time_slot": slot.time_slot
            } for slot in slots
        ], 200

    # 2. POST Method: Used by Doctors to set their free time
    @auth_required('token')
    @roles_required('doctor')
    def post(self):
        # Concept: A doctor clicks "save" on their 7-day availability calendar on the frontend.
        args = availability_parser.parse_args()
        
        # Why current_user.id? We do not trust the frontend to send the correct doctor's ID in the JSON body. 
        # We securely pull the ID from the logged-in doctor's authentication token to prevent forgery.
        new_slot = Availability(
            doctor_id=current_user.id,
            date=args['date'],
            time_slot=args['time_slot']
        )
        
        db.session.add(new_slot)
        db.session.commit()
        return {"message": "Availability added successfully"}, 201
    


api.add_resource(AvailabilityApi, 
                 '/api/availability/get/<int:doctor_id>', 
                 '/api/availability/create')

treatment_parser = reqparse.RequestParser()
treatment_parser.add_argument('appointment_id', type=int, required=True, help="Appointment ID is required to link the treatment.")
treatment_parser.add_argument('diagnosis', type=str, required=True, help="Diagnosis cannot be blank.")
treatment_parser.add_argument('prescription', type=str, required=True)
treatment_parser.add_argument('medicines', type=str)

class TreatmentApi(Resource):
    @auth_required('token')
    @roles_required('doctor')
    def post(self, appt_id):
        args = availability_parser.parse_args()
        appt = Appointment.query.get(args['appointment_id'])
        if not appt:
            return {"message": "Appointment not found"}, 404
            
        # Step B: Strict Security Check
        if appt.doctor_id != current_user.id:
            return {"message": "Unauthorized: You cannot add treatments for another doctor's patient."}, 403
            
        # Step C: Create the actual Treatment record
        new_treatment = Treatment(
            appointment_id=args['appointment_id'],
            diagnosis=args['diagnosis'],
            prescription=args['prescription'],
            medicines=args.get('medicines')
        )
        
        # Step D: Dynamic Status Update
        appt.status = "Completed"
        
        # Step E: Save to Database
        db.session.add(new_treatment)
        db.session.commit()
        
        return {"message": "Patient history updated and appointment marked as completed!"}, 201

    def put(self,appt_id ):
        # This method can be used to update an existing treatment record if needed.
        args = treatment_parser.parse_args()
        appt = Treatment.query.get(appt_id)
        
        if not appt:
            return {"message": "Appointment not found"}, 404
            
        # Update details if provided
        if args.get('diagnosis '): appt.date = args['diagnosis ']
        if args.get('prescription'): appt.time = args['prescription']
        if args.get('medicines'): appt.status = args['medicines']
        
        db.session.commit()
        return {"message": "Appointment updated successfully!"}, 200
    
api.add_resource(TreatmentApi, '/api/treatment/create')
api.add_resource(TreatmentApi, '/api/treatment/update/<int:appt_id>')

doctor_parser = reqparse.RequestParser()
doctor_parser.add_argument('email', type=str, required=True)
doctor_parser.add_argument('username', type=str, required=True)
doctor_parser.add_argument('password', type=str, required=True)
doctor_parser.add_argument('department_id', type=int, required=True)
doctor_parser.add_argument('experience_years', type=int)

class DoctorApi(Resource):
    @auth_required('token')
    @roles_required('admin')
    def get(self, doctor_id=None):
        if doctor_id:
            doctor = User.query.get(doctor_id)
            if not doctor:
                return {"message": "Doctor not found"}, 404
            return {
                "id": doctor.id,
                "email": doctor.email,
                "username": doctor.username,
                "department_id": doctor.department_id,
                "experience_years": doctor.experience_years
            }, 200
        else:
            doctors = User.query.filter(User.roles.any(name='doctor')).all()
            if not doctors:
                return {"message": "No doctors found"}, 404

            return [
            {
                "id": doc.id,
                "email": doc.email,
                "username": doc.username,
                "department_id": doc.department_id,
                "experience_years": doc.experience_years
            } for doc in doctors
        ], 200
    
    @auth_required('token')
    @roles_required('admin')
    def post(self):
        args = doctor_parser.parse_args()
        
        if app.security.datastore.find_user(email=args['email']):
            return {"message": "A user with this email already exists."}, 400
        
        new_doctor = app.security.datastore.create_user(
            email=args['email'],
            username=args['username'],
            password=hash_password(args['password']),
            roles=['doctor']
        )
        
        # Set doctor-specific fields
        new_doctor.department_id = args['department_id']
        new_doctor.experience_years = args.get('experience_years', 0)
        
        db.session.commit()
        return {"message": "Doctor account created successfully!"}, 201

    @auth_required('token')
    @roles_required('admin')
    def delete(self, doctor_id):
        doctor = User.query.get(doctor_id)
        if not doctor:
            return {"message": "Doctor not found"}, 404
        doctor.active = False
        db.session.commit()
        return {"message": "Doctor profile has been deactivated"}, 200
    

api.add_resource(DoctorApi, '/api/doctors/get', '/api/doctors/get/<int:doctor_id>', '/api/doctors/create', '/api/doctors/delete/<int:doctor_id>')

Department_parser = reqparse.RequestParser()
Department_parser.add_argument('name', type=str, required=True)
Department_parser.add_argument('description', type=str, required=True)

class DepartmentApi(Resource):
    
    @auth_required('token')
    @roles_accepted('admin', 'patient', 'doctor')
    def get(self):
        departments = Department.query.all()
        result = []
        for dept in departments:
            result.append({
                "id": dept.id,
                "name": dept.name,
                "description": dept.description
            })
            
        if not result:
            return {"message": "No departments found"}, 404
            
        return result, 200
    def post(self):
        args = Department_parser.parse_args()

        if Department.query.filter_by(name=args['name']).first():
            return {"message": "A department with this name already exists."}, 400
        
        new_department = Department(
            name=args['name'],
            description=args['description']
        )
        db.session.add(new_department)
        db.session.commit()
        return {"message": "Department created successfully!"}, 201

api.add_resource(DepartmentApi, '/api/departments/get', '/api/departments/create')


class PatientHistoryApi(Resource):
    
    @auth_required('token')
    @roles_accepted('patient', 'doctor')
    def get(self, patient_id=None):
        # Determine who is asking for the history based on their role token
        roles = [role.name for role in current_user.roles]
        
        if 'patient' in roles:
            # The Why: A patient should ONLY ever see their own history.
            # We completely ignore the patient_id in the URL and force the query 
            # to use current_user.id. This prevents a hacker from guessing another patient's ID.
            appointments = Appointment.query.filter_by(patient_id=current_user.id, status='Completed').all()
            
        elif 'doctor' in roles:
            # The Why: A doctor clicked on a specific patient's profile to view their history.
            if not patient_id:
                return {"message": "Patient ID is required for doctors to view history"}, 400
                
            # Extra Security Check: Did this doctor actually treat this patient?
            # You query to ensure a relationship exists before exposing medical data.
            valid_doctor = Appointment.query.filter_by(patient_id=patient_id, doctor_id=current_user.id).first()
            if not valid_doctor:
                return {"message": "Unauthorized: You have never treated this patient."}, 403
                
            appointments = Appointment.query.filter_by(patient_id=patient_id, status='Completed').all()

        # The Serialization Step: Gathering the treatments linked to the completed appointments
        history_list = []
        for appt in appointments:
            # Assuming a One-to-One relationship where appt.treatment holds the treatment notes
            treatment = Treatment.query.filter_by(appointment_id=appt.id).first()
            if treatment:
                history_list.append({
                    "date": appt.date,
                    "doctor_name": appt.doctor.username,
                    "diagnosis": treatment.diagnosis,
                    "prescription": treatment.prescription,
                    "notes": treatment.notes
                })
                
        return history_list, 200
    
api.add_resource(PatientHistoryApi, '/api/history/get', '/api/history/get/<int:patient_id>')

search_parser = reqparse.RequestParser()
search_parser.add_argument('query_string', type=str, required=True)
search_parser.add_argument('search_type', type=str, required=True, help="Must be 'doctor', 'patient', or 'specialization'")

class SearchApi(Resource):
    
    @auth_required('token')
    def post(self):
        args = search_parser.parse_args()
        search_term = f"%{args['query_string']}%"
        
        # The Concept: Using ILIKE for partial matching
        # If the user searches for "Cardio", we use SQLAlchemy's .ilike() to find "Cardiology".
        # The '%' signs act as wildcards meaning "anything before or after".
        
        if args['search_type'] == 'specialization':
            depts = Department.query.filter(Department.name.ilike(search_term)).all()
            return [{"id": d.id, "name": d.name} for d in depts], 200
            
        elif args['search_type'] == 'doctor':
            # We join the User and Department tables to search by doctor name OR department name simultaneously
            doctors = User.query.filter(
                User.roles.any(Role.name == 'doctor'),
                User.username.ilike(search_term)
            ).all()
            return [{"id": doc.id, "name": doc.username, "dept": doc.department_id} for doc in doctors], 200
        
api.add_resource(SearchApi, '/api/search')