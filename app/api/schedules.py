from flask import request, jsonify, url_for
from app.models import Schedule, Area, Shift
from app.api import bp
from app import db
from functions.dates import datetime_from_string as dfs
import datetime


@bp.route('/schedules/config', methods=['POST'])
def create_schedule():
    data = request.get_json() or {}
    data['schedule_area'] = Area.query.filter_by(name=data['schedule_area'] or None).first()
    data['schedule_shift'] = Shift.query.filter_by(name=data['schedule_shift'] or None).first()
    for time in ['start1', 'start2', 'start3', 'start4', 'end1', 'end2', 'end3', 'end4']:
        data[time] = dfs(data[time])
    if data['name'] == 'Regular':
        schedule = Schedule.query.filter_by(schedule_area=data['schedule_area'], schedule_shift=data['schedule_shift'],
                                            name=data['name']).first()
    else:
        schedule = Schedule.query.filter_by(schedule_area=data['schedule_area'], schedule_shift=data['schedule_shift'],
                                            start1=data['start1'], start2=data['start2'], start3=data['start3'],
                                            start4=data['start4'], end1=data['end1'], end2=data['end2'],
                                            end3=data['end3'], end4=data['end4']).first()
    if schedule:
        s = schedule
    else:
        s = Schedule()
        s.name = 'Custom {}'.format(str(datetime.date.today()))
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
