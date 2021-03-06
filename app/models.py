from time import time
import jwt
from app import db, login
import datetime
from functions.dates import time_from_string as tfs, \
    get_available_time as gat, \
    datetime_from_time as dft, \
    date_from_string as dfs
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app, url_for
import base64
import os


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
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
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

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'areas': [a.name for a in self.areas.all()],
            'shifts': [s.name for s in self.shifts.all()],
            '_links': {
                'self': url_for('api.get_user', id=self.id)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.datetime.utcnow()
        if self.token and self.token_expiration > now + datetime.timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + datetime.timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.datetime.utcnow():
            return None
        return user


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class KPI(db.Model):
    """ shift plans. organized by shift and date, contains schedule, demand, pct, and relations to cycles & andons """
    __tablename__ = 'kpi'
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_area = db.Column(db.Integer, db.ForeignKey('area.id'))
    id_shift = db.Column(db.Integer, db.ForeignKey('shift.id'))
    id_schedule = db.Column(db.Integer, db.ForeignKey('schedule.id'))
    d = db.Column(db.Date, index=True)
    demand = db.Column(db.Integer)
    plan_cycle_time = db.Column(db.Integer)
    cycles = db.relationship('Cycle', backref='kpi', lazy='dynamic')
    andons = db.relationship('Andon', backref='kpi', lazy='dynamic')

    def __repr__(self):
        return '<KPI for {} {} {}>'.format(self.d, self.area.name, self.shift.name)

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
        self.planner = user

    def add_schedule(self, schedule):
        self.id_schedule = Schedule.query.filter_by(name=schedule, id_area=self.id_area,
                                                    id_shift=self.id_shift).first().id

    def get_time_elapsed(self, d=datetime.datetime.now()):
        sched = self.schedule.return_schedule(self.d)
        now = datetime.datetime.now()
        if d > sched[-1]:
            return datetime.timedelta(seconds=self.schedule.get_available_time())
        elif d < sched[0]:
            return datetime.timedelta(seconds=0)
        else:
            t = now - sched[0]
            for item in sched:
                index = sched.index(item)
                if now > item and index % 2 != 0:
                    if now > sched[index+1]:
                        t -= sched[index+1] - item
                    else:
                        t -= now - item
            return t

    def get_sequences(self):
        return list(set([c.sequence for c in self.cycles.all()]))

    def to_dict(self):
        data = {
            'id': self.id,
            'area': self.area.name if self.area else None,
            'shift': self.shift.name if self.shift else None,
            'schedule': self.schedule.name if self.schedule else None,
            'd': str(self.d),
            'demand': self.demand,
            'plan_cycle_time': self.plan_cycle_time
        }
        return data

    def from_dict(self, data):
        for field in ['area', 'shift', 'schedule', 'd', 'demand', 'plan_cycle_time']:
            if field in data:
                setattr(self, field, data[field])

    @staticmethod
    def get_kpi(area, shift, date):
        a = Area.query.filter_by(name=area).first()
        s = Shift.query.filter_by(name=shift).first()
        d = dfs(date)
        kpi = KPI.query.filter_by(area=a, shift=s, d=d).first()
        return kpi

    @staticmethod
    def get_block_data_dict(area, shift, date, block):
        kpi = KPI.get_kpi(area, shift, date)
        if not kpi:
            return {"error": "No KPI matches the request"}
        if not int(block):
            block = kpi.schedule.get_current_block(kpi.d) or 1
        pct = kpi.plan_cycle_time
        schedule = kpi.schedule.return_schedule(kpi_d=kpi.d)
        start = schedule[int(block)*2-2]
        end = schedule[int(block)*2-1]
        available_time = int((end-start).total_seconds())
        cycles = kpi.cycles.filter(Cycle.id_kpi == kpi.id,
                                   Cycle.d > start,
                                   Cycle.d < end)
        sequences = kpi.get_sequences()
        data = {}
        for sequence in sequences:
            s = kpi.cycles.filter(Cycle.sequence == sequence,
                                  Cycle.d >= start,
                                  Cycle.d <= end)
            if not s.first():
                parts_per = kpi.cycles.filter(Cycle.sequence == sequence).order_by(Cycle.d.desc()).first().parts_per
            else:
                parts_per = s.order_by(Cycle.d.desc()).first().parts_per
            data[sequence] = {'Cycles': s.count(),
                              'Expected': available_time // (pct * parts_per),
                              'Andons': kpi.andons.filter(Andon.sequence == sequence,
                                                          Andon.d > start,
                                                          Andon.d < end).count(),
                              'Responded': True if kpi.andons.filter(Andon.sequence == sequence).count() == 0 else
                              True if kpi.andons.filter(Andon.sequence == sequence).order_by(
                                  Andon.d.desc()).first().responded else False,
                              'Andon_Type': None
                              }
            andon_type_list = [a.andon_type for a in kpi.andons.filter(Andon.sequence == sequence,
                                                                       Andon.responded == 0).all()]
            data[sequence]['Andon_Type'] = None if data[sequence]['Responded'] else \
                'Safety' if 'Safety' in andon_type_list else \
                'Quality' if 'Quality' in andon_type_list else \
                'Delivery' if 'Delivery' in andon_type_list else 'NoType'
        # data = {s.first.sequence():
        #             {'Cycles': s.count(),
        #              'Expected': available_time // (kpi.plan_cycle_time * s.first().parts_per),
        #              'Andons': kpi.andons.filter(Andon.sequence == s.first().sequence,
        #                                          Andon.d > start,
        #                                          Andon.d < end).count(),
        #              'Responded': True if kpi.andons.filter(Andon.sequence == s.first().sequence).count() == 0 else
        #              True if kpi.andons.filter(
        #                  Andon.sequence == s.first().sequence).order_by(
        #                  Andon.d.desc()).first().responded else False,
        #              }
        #         for s in [kpi.cycles.filter(Cycle.sequence == sequence,
        #                                     Cycle.d >= start,
        #                                     Cycle.d <= end)
        #                   for sequence in sequences]}
        return data


class Area(db.Model):
    """ all areas with timers """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24), unique=True)
    kpi = db.relationship('KPI', backref='area', lazy='dynamic')
    schedules = db.relationship('Schedule', backref='schedule_area', lazy='dynamic')
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
    """ This model defines a generic schedule, unaware of date, used for assignment. """
    id = db.Column(db.Integer, primary_key=True)
    id_area = db.Column(db.Integer, db.ForeignKey('area.id'))
    id_shift = db.Column(db.Integer, db.ForeignKey('shift.id'))
    name = db.Column(db.String(24))
    start1 = db.Column(db.Time)
    start2 = db.Column(db.Time)
    start3 = db.Column(db.Time)
    start4 = db.Column(db.Time)
    end1 = db.Column(db.Time)
    end2 = db.Column(db.Time)
    end3 = db.Column(db.Time)
    end4 = db.Column(db.Time)
    kpi = db.relationship('KPI', backref='schedule', lazy='dynamic')

    def __repr__(self):
        return '<{} {} {} Schedule>'.format(self.schedule_area.name, self.schedule_shift.name, self.name)

    def return_times_list(self):
        return [self.start1, self.end1, self.start2, self.end2,
                self.start3, self.end3, self.start4, self.end4]

    def return_schedule(self, kpi_d: datetime.date = datetime.date.today()):
        times = self.return_times_list()
        new_times = []
        for i in range(len(times)):
            time = times[i]
            if type(time) == datetime.time:
                """ changed logic for swing kpi_d; 
                    usually same result, but allows available time to start after midnight """
                if self.schedule_shift.name == 'Swing' and time.hour <= 3:
                    new_times.append(dft(time, kpi_d + datetime.timedelta(1)))
                else:
                    new_times.append(dft(time, kpi_d))
                """ old code caused errors if schedule.start1 was after midnight """
                # if i == 0:
                #     new_times.append(dft(time, kpi_d))
                # else:
                #     if time < times[i-1]:
                #         kpi_d += datetime.timedelta(1)
                #     new_times.append(dft(time, kpi_d))
        return new_times

    def make_times_list(self, **kwargs):
        for key, value in kwargs.items():
            exec("self.{} = tfs('{}')".format(key, value))

    def get_available_time(self):
        return int(gat(self.return_times_list()).total_seconds())

    def add_area(self, area):
        self.schedule_area = area

    def add_shift(self, shift):
        self.schedule_shift = shift

    def get_current_block(self, kpi_d=datetime.date.today()):
        block = 0
        for time in self.return_schedule(kpi_d)[0::2]:
            if datetime.datetime.now() > time:
                block += 1
        block = 1 if block == 0 else block
        return block

    def from_dict(self, data):
        for field in ['schedule_area', 'schedule_shift', 'name',
                      'start1', 'start2', 'start3', 'start4',
                      'end1', 'end2', 'end3', 'end4'
                      ]:
            if field in data:
                setattr(self, field, data[field])

    def to_dict(self):
        data = {
            'id': self.id,
            'id_area': self.id_area,
            'id_shift': self.id_shift,
            'name': self.name,
            'start1': str(self.start1),
            'start2': str(self.start2),
            'start3': str(self.start3),
            'start4': str(self.start4),
            'end1': str(self.end1),
            'end2': str(self.end2),
            'end3': str(self.end3),
            'end4': str(self.end4),
        }
        return data


class Cycle(db.Model):
    """ Each cycle from the operator is logged in this format """
    id = db.Column(db.Integer, primary_key=True)
    id_kpi = db.Column(db.Integer, db.ForeignKey('kpi.id'))
    d = db.Column(db.DateTime)
    sequence = db.Column(db.Integer)
    cycle_time = db.Column(db.Integer)
    parts_per = db.Column(db.Integer)
    delivered = db.Column(db.Integer)
    code = db.Column(db.Integer)       # early (0), on time (1), late (2)

    def from_dict(self, data):
        for field in ['id_kpi', 'd', 'sequence', 'cycle_time', 'parts_per', 'delivered', 'code']:
            if field in data:
                setattr(self, field, data[field])

    def to_dict(self):
        data = {
            'id': self.id,
            'd': self.d,
            'sequence': self.sequence,
            'cycle_time': self.cycle_time,
            'parts_per': self.parts_per,
            'delivered': self.delivered,
            'code': self.code
        }
        return data


class Andon(db.Model):
    """ Keeps track of the number of andons and type of andons """
    id = db.Column(db.Integer, primary_key=True)
    id_kpi = db.Column(db.Integer, db.ForeignKey('kpi.id'))
    d = db.Column(db.DateTime)
    sequence = db.Column(db.Integer)
    andon_type = db.Column(db.String(10))
    responded = db.Column(db.Boolean)
    response_d = db.Column(db.DateTime)

    def from_dict(self, data):
        for field in ['id_kpi', 'd', 'sequence', 'andon_type', 'responded']:
            if field in data:
                setattr(self, field, data[field])

    def to_dict(self):
        data = {
            'id': self.id,
            'id_kpi': self.id_kpi,
            'd': self.d,
            'sequence': self.sequence,
            'andon_type': self.andon_type,
            'responded': self.responded
        }
        return data

    @staticmethod
    def respond(data):
        id_kpi = data['id_kpi'] or None
        sequence = data['sequence'] or None
        response_d = data['response_d'] or None
        for andon in Andon.query.filter_by(id_kpi=id_kpi, sequence=sequence, responded=0).all():
            andon.responded = 1
            andon.response_d = response_d
        db.session.commit()

# TODO: Process Class
# TODO: Operator Class
