from flask import Flask
from flask_security import Security
from back_end.application.database import db
from back_end.application.models import User, Role
from back_end.application.config import LocalDevelopmentConfig
from flask_security import datastore,SQLAlchemyUserDatastore
from flask_security import hash_password

def create_app():
    app=Flask(__name__)
    app.config.from_object(LocalDevelopmentConfig)
    db.init_app(app)
    datastore = SQLAlchemyUserDatastore(db, User,Role)
    app.security=Security(app,datastore)
    app.app_context().push()
    return app

app=create_app()

with app.app_context():
    db.create_all()

    app.security.datastore.find_or_create_role(name ="admin",description="super user of application")
    app.security.datastore.find_or_create_role(name ="user",description="general user of application")
    db.session.commit()

    if not app.security.datastore.find_user(email="user@admin.com"):
        app.security.datastore.create_user(email="user@admin.com",username ="admin01",password=hash_password("1234"),roles=['admin'])

    if not app.security.datastore.find_user(email="user1@user.com"):
        app.security.datastore.create_user(email="user1@user.com",username ="user01",password=hash_password("1234"),roles=['user'])
        db.session.commit()

#hashed_password = bcrypt(password,salt)

from back_end.application.routes import *

if __name__ == "__main__":
    app.run()
