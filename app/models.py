from datetime import datetime
from time import time
import jwt
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app


"""
This file defines all of the database tables, and handles the relationships between them.
Most of the class objects (Models) have methods within them for help with defining, returning, etc.
"""

# user_area table for linking User models and Area models
user_area = db.Table('user_area',
                     db.Column('id_user', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                     db.Column('id_area', db.Integer, db.ForeignKey('area.id'), primary_key=True)
                     )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    kpi = db.relationship('KPI', backref='planner', lazy='dynamic')
    areas = db.relationship(
        'Area', secondary=user_area,
        primaryjoin=(user_area.c.id_user == id),
        backref=db.backref('user', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def add_area(self, area):
        if not self.is_assigned(area):
            self.areas.append(area)

    def rm_area(self, area):
        if self.is_assigned(area):
            self.areas.remove(area)

    def is_assigned(self, area):
        return self.areas.filter(
            user_area.c.id_area == area.id).count() > 0

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class KPI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_area = db.Column(db.Integer, db.ForeignKey('area.id'))
    d = db.Column(db.Date, index=True)
    demand = db.Column(db.Integer)
    plan_cycle_time = db.Column(db.Integer)

    def __repr__(self):
        return '<KPI for {} {}>'.format(self.d, self.area.name)

    def return_details(self):
        return 'area={}' \
               'date={}' \
               'demand={}' \
               'plan_cycle_time={}'.format(self.area, self.d, self.demand, self.plan_cycle_time)

    def add_area(self, area):
        self.id_area = Area.query.filter_by(name=area).first().id

    def add_user(self, user):
        self.user = user


class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24))
    users = db.relationship(
        'User', secondary=user_area,
        primaryjoin=(user_area.c.id_area == id),
        backref=db.backref('assigned_areas', lazy='dynamic'), lazy='dynamic')
    kpi = db.relationship('KPI', backref='area', lazy='dynamic')

    def __repr__(self):
        return '<Area {}>'.format(self.name)

    def add_user(self, user):
        if not self.is_assigned(user):
            self.users.append(user)

    def rm_user(self, user):
        if self.is_assigned(user):
            self.users.remove(user)

    def is_assigned(self, user):
        return self.users.filter(
            user_area.c.id_user == user.id).count() > 0
