from flask import request, jsonify, url_for
from app.models import Andon
from app.api import bp
from app import db


@bp.route('/andon', methods=['POST'])
def create_andon():
    data = request.get_json() or {}
    andon = Andon()
    data['responded'] = int(data['responded'])
    andon.from_dict(data)
    db.session.add(andon)
    db.session.commit()
    response = jsonify(andon.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_andon', id=andon.id)
    return response


@bp.route('/andon/respond', methods=['POST'])
def andon_response():
    data = request.get_json() or {}
    Andon.respond(data)
    return jsonify(data)


@bp.route('/andon/<int:id>', methods=['GET'])
def get_andon(id):
    return jsonify(Andon.query.get_or_404(id).to_dict())
