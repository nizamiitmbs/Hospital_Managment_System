from .database import db

class Paitient(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String,unique=True,nullable=False)
    password=db.Column(db.String,nullable=False)
    fs_uniquifier = db.Column(db.String,unique=True,nullabel=False)
    active=db.Column(db.Boolean,nullable=False)
    roles=db.relationship('Role',backref ='bearer',secondary = 'users_roles')


class Role(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String,unique=True,nullable=False)
    description=db.Column(db.String)


class UsersRoles(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    used_id=db.Column(db.Integer,db.ForignKey('user.id'))
    role_id=db.Column(db.Integer,db.ForignKey('role.id'))

