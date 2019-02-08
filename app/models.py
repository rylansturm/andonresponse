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

# area_shift table for linking Area models and Shift models
area_shift = db.Table('area_shift',
                      db.Column('id_area', db.Integer, db.ForeignKey('area.id'), primary_key=True),
                      db.Column('id_shift', db.Integer, db.ForeignKey('shift.id'), primary_key=True)
                      )
# TODO: user_shift table to connect users to their allowed shifts


class User(UserMixin, db.Model):  # TODO: make admin and superadmin columns (or see if flask_login provides)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    kpi = db.relationship('KPI', backref='planner', lazy='dynamic')
    areas = db.relationship(
        'Area', secondary=user_area,
        primaryjoin=(user_area.c.id_user == id),
        backref=db.backref('user', lazy='dynamic'), lazy='dynamic')
    # TODO: relationship to user_shift

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def add_area(self, area):
        if not self.is_assigned_area(area):
            self.areas.append(area)

    def rm_area(self, area):
        if self.is_assigned_area(area):
            self.areas.remove(area)

    def is_assigned_area(self, area):
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
    id_shift = db.Column(db.Integer, db.ForeignKey('shift.id'))
    # TODO: id_schedule
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

    def add_shift(self, shift):
        self.id_shift = Shift.query.filter_by(name=shift).first().id

    def add_user(self, user):
        self.user = user


class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24), unique=True)
    kpi = db.relationship('KPI', backref='area', lazy='dynamic')
    users = db.relationship(
        'User', secondary=user_area,
        primaryjoin=(user_area.c.id_area == id),
        backref=db.backref('assigned_areas', lazy='dynamic'), lazy='dynamic')
    shifts = db.relationship(
        'Shift', secondary=area_shift,
        primaryjoin=(area_shift.c.id_area == id),
        backref=db.backref('shift_areas', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<Area {}>'.format(self.name)

    def add_user(self, user):
        if not self.is_assigned_user(user):
            self.users.append(user)

    def rm_user(self, user):
        if self.is_assigned_user(user):
            self.users.remove(user)

    def is_assigned_user(self, user):
        return self.users.filter(
            user_area.c.id_user == user.id).count() > 0

    def add_shift(self, shift):
        if not self.is_associated_with_shift(shift):
            self.shifts.append(shift)

    def rm_shift(self, shift):
        if self.is_associated_with_shift(shift):
            self.shifts.remove(shift)

    def is_associated_with_shift(self, shift):
        return self.shifts.filter(
            user_area.c.id_shift == shift.id).count() > 0


class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(8), unique=True)
    start = db.Column(db.Time)
    end = db.Column(db.Time)
    kpi = db.relationship('KPI', backref='shift', lazy='dynamic')
    # TODO: relationship to schedule
    areas = db.relationship(
        'Area', secondary=area_shift,
        primaryjoin=(area_shift.c.id_shift == id),
        backref=db.backref('area_shifts', lazy='dynamic'), lazy='dynamic')
    # TODO: relationship to user_shift

    def add_area(self, area):
        if not self.is_associated_with_area(area):
            self.areas.append(area)

    def rm_area(self, area):
        if self.is_associated_with_area(area):
            self.areas.remove(area)

    def is_associated_with_area(self, area):
        return self.areas.filter(
            area_shift.c.id_area == area.id).count() > 0

# TODO: Schedule Class
# TODO: Cycle Class
# TODO: Andon Class
# TODO: Process Class
# TODO: Operator Class
