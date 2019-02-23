from flask import request, jsonify, url_for
from app.models import Cycle, KPI
from app.api import bp
from app import db


@bp.route('/cycles', methods=['POST'])
def create_cycle():
    data = request.get_json() or {}
    cycle = Cycle()
    cycle.from_dict(data)
    db.session.add(cycle)
    db.session.commit()
    response = jsonify(cycle.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_cycle', id=cycle.id)
    return response


@bp.route('/cycles/<int:id>', methods=['GET'])
def get_cycle(id):
    return jsonify(Cycle.query.get_or_404(id).to_dict())


@bp.route('/cycles/block_tracker/<area>/<shift>/<date>/<block>', methods=['GET'])
def block_tracker(area, shift, date, block):
    return jsonify(KPI.get_block_data_dict(area, shift, date, block))
