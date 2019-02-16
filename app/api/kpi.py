from flask import request, jsonify, url_for, redirect
from app.models import KPI, Area, Shift, Schedule
from app.api import bp
from app import db
from functions.dates import date_from_string as dfs


@bp.route('/kpi', methods=['POST'])
def create_kpi():
    data = request.get_json() or {}
    data['area'] = Area.query.filter_by(name=data['area'] or None).first()
    data['shift'] = Shift.query.filter_by(name=data['shift'] or None).first()
    data['schedule'] = Schedule.query.filter_by(name=data['schedule'] or None,
                                                schedule_area=data['area'] or None,
                                                schedule_shift=data['shift'] or None).first()
    data['d'] = dfs(data['d'])
    kpi = KPI.query.filter_by(area=data['area'], shift=data['shift'], d=data['d']).first()
    if kpi:
        k = kpi
    else:
        k = KPI()
    k.from_dict(data)
    db.session.add(k)
    db.session.commit()
    response = jsonify(k.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_kpi', id=k.id)
    return response


@bp.route('/kpi/<int:id>', methods=['GET'])
def get_kpi(id):
    kpi = KPI.query.get_or_404(id)
    return redirect(url_for('api.real_get_kpi', area=kpi.area.name, shift=kpi.shift.name, d=str(kpi.d)))


@bp.route('/kpi/<area>/<shift>/<d>', methods=['GET'])
def real_get_kpi(area, shift, d):
    a = Area.query.filter_by(name=area).first()
    s = Shift.query.filter_by(name=shift).first()
    d = dfs(d)
    return jsonify(KPI.query.filter_by(area=a, shift=s, d=d).first().to_dict())
