from flask import request, jsonify, url_for
from app.models import Schedule, Area, Shift
from app.api import bp
from app import db
from functions.dates import datetime_from_string as dfs


@bp.route('/schedules/config', methods=['POST'])
def create_schedule():
    data = request.get_json() or {}
    data['schedule_area'] = Area.query.filter_by(name=data['schedule_area'] or None).first()
    data['schedule_shift'] = Shift.query.filter_by(name=data['schedule_shift'] or None).first()
    for time in ['start1', 'start2', 'start3', 'start4', 'end1', 'end2', 'end3', 'end4']:
        data[time] = dfs(data[time])
    schedule = Schedule.query.filter_by(schedule_area=data['schedule_area'], schedule_shift=data['schedule_shift'],
                                        name=data['name']).first()
    if schedule:
        s = schedule
    else:
        s = Schedule()
    s.from_dict(data)
    db.session.add(s)
    db.session.commit()
    response = jsonify(s.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_kpi', id=s.id)
    return response


@bp.route('/schedules/<int:id>', methods=['GET'])
def get_schedule(id):
    schedule = Schedule.query.get_or_404(id)
    return jsonify(schedule.to_dict())


@bp.route('/schedules/<area>/<shift>/<name>')
def real_get_schedule(area, shift, name):
    a = Area.query.filter_by(name=area).first()
    s = Shift.query.filter_by(name=shift).first()
    schedule = Schedule.query.filter_by(schedule_area=a, schedule_shift=s, name=name).first()
    return get_schedule(schedule.id)


@bp.route('/schedules/list/<area>/<shift>')
def get_schedule_list(area, shift):
    a = Area.query.filter_by(name=area).first()
    s = Shift.query.filter_by(name=shift).first()
    schedule_name_list = [schedule.name for schedule in Schedule.query.filter_by(
        schedule_area=a, schedule_shift=s).all()]
    data = {}
    for name in schedule_name_list:
        data[name] = real_get_schedule(area, shift, name)
    return jsonify(data)