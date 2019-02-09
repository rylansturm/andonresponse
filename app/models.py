from time import time
import jwt
from app import db, login
from functions.dates import datetime_from_string as dtfs
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

# area_shift table for linking Area models and Shift models
user_shift = db.Table('user_shift',
                      db.Column('id_user', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                      db.Column('id_shift', db.Integer, db.ForeignKey('shift.id'), primary_key=True)
                      )


class User(UserMixin, db.Model):  # TODO: make admin and superadmin columns (or see if flask_login provides)
    """ all users of the site. contains credentials and permissions """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    kpi = db.relationship('KPI', backref='planner', lazy='dynamic')
    areas = db.relationship(
        'Area', secondary=user_area,
        primaryjoin=(user_area.c.id_user == id),
        backref=db.backref('user', lazy='dynamic'), lazy='dynamic')
    shifts = db.relationship(
        'Shift', secondary=user_shift,
        primaryjoin=(user_shift.c.id_user == id),
        backref=db.backref('shift_users', lazy='dynamic'), lazy='dynamic')

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

    def add_shift(self, shift):
        if not self.is_associated_with_shift(shift):
            self.shifts.append(shift)

    def rm_shift(self, shift):
        if self.is_associated_with_shift(shift):
            self.shifts.remove(shift)

    def is_associated_with_shift(self, shift):
        return self.shifts.filter(
            user_shift.c.id_shift == shift.id).count() > 0

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
    """ shift plans. organized by shift and date, contains schedule, demand, pct """
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_area = db.Column(db.Integer, db.ForeignKey('area.id'))
    id_shift = db.Column(db.Integer, db.ForeignKey('shift.id'))
    id_schedule = db.Column(db.Integer, db.ForeignKey('schedule.id'))
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
    """ all areas with timers """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24), unique=True)
    kpi = db.relationship('KPI', backref='area', lazy='dynamic')
    schedule = db.relationship('Schedule', backref='schedule_area', lazy='dynamic')
    users = db.relationship(
        'User', secondary=user_area,
        primaryjoin=(user_area.c.id_area == id),
        backref=db.backref('assigned_areas', lazy='dynamic'), lazy='dynamic')
    shifts = db.relationship(
        'Shift', secondary=area_shift,
        primaryjoin=(area_shift.c.id_area == id),
        backref=db.backref('shift_areas', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<{} Area>'.format(self.name)

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
            area_shift.c.id_shift == shift.id).count() > 0


class Shift(db.Model):
    """ each separation of the work day. expandable for 8- or 12-hour shifts. date is when shift ends """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(8), unique=True)
    start = db.Column(db.Time)
    end = db.Column(db.Time)
    kpi = db.relationship('KPI', backref='shift', lazy='dynamic')
    schedule = db.relationship('Schedule', backref='schedule_shift', lazy='dynamic')
    areas = db.relationship(
        'Area', secondary=area_shift,
        primaryjoin=(area_shift.c.id_shift == id),
        backref=db.backref('area_shifts', lazy='dynamic'), lazy='dynamic')
    users = db.relationship(
        'User', secondary=user_shift,
        primaryjoin=(user_shift.c.id_shift == id),
        backref=db.backref('assigned_users', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<{} Shift ({}, {})>'.format(self.name, self.start, self.end)

    def add_user(self, user):
        if not self.is_assigned_user(user):
            self.users.append(user)

    def rm_user(self, user):
        if self.is_assigned_user(user):
            self.users.remove(user)

    def is_assigned_user(self, user):
        return self.users.filter(
            user_shift.c.id_user == user.id).count() > 0

    def add_area(self, area):
        if not self.is_associated_with_area(area):
            self.areas.append(area)

    def rm_area(self, area):
        if self.is_associated_with_area(area):
            self.areas.remove(area)

    def is_associated_with_area(self, area):
        return self.areas.filter(
            area_shift.c.id_area == area.id).count() > 0


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_area = db.Column(db.Integer, db.ForeignKey('area.id'))
    id_shift = db.Column(db.Integer, db.ForeignKey('shift.id'))
    kpi = db.relationship('KPI', backref='schedule', lazy='dynamic')
    name = db.Column(db.String(24))
    available_time = db.Column(db.Integer)
    start1 = db.Column(db.DateTime)
    start2 = db.Column(db.DateTime)
    start3 = db.Column(db.DateTime)
    start4 = db.Column(db.DateTime)
    end1 = db.Column(db.DateTime)
    end2 = db.Column(db.DateTime)
    end3 = db.Column(db.DateTime)
    end4 = db.Column(db.DateTime)

    def __repr__(self):
        return '<{} {} Schedule {}>'.format(self.schedule_area, self.schedule_shift, self.kpi.d)

    def return_times_list(self):
        return [self.start1, self.end1, self.start2, self.end2,
                self.start3, self.end3, self.start4, self.end4]

    def get_times_list(self, **kwargs):
        for key, value in kwargs.items():
            exec('self.{} = dtfs{}'.format(key, value))

# TODO: Cycle Class
# TODO: Andon Class
# TODO: Process Class
# TODO: Operator Class
