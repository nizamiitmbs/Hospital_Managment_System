from flask import current_app as app,jsonify,request
from flask_security import auth_required,roles_required,hash_password,current_user
from .models import *

@app.route('/',methods=['GET'])
def home():

    return jsonify({
        "name" : Role.query.all() 
    }) 

@app.route('/api/admin')
@auth_required('token')
@roles_required('admin')
def admin_home():
    return "<h1>skjvbskjnv</h1>"

@app.route('/api/home')
@auth_required('token')
@roles_required(['user','admin'])
def user_home(user_id):
   
    user=current_user()
    return jsonify({
        "username":user.username,
        "email":user.email,
        "password":user.password
    })

@app.route('/api/register',methods=['POST'])
def registration():
    credentials=request.get_json()
    if not app.security.datastore.find_user(email="user1@user.com"):
        app.security.datastore.create_user(email="user1@user.com",
                                           username ="user01",
                                           password=hash_password(),
                                           roles=['user'])
        db.session.commit()
        return jsonify({
            "messgae":"user created"
        }),201
        
    return jsonify({
            "messgae":"baigan"
        }),400
        



