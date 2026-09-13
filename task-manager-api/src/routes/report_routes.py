from flask import Blueprint, jsonify


def make_report_routes(report_service, auth):
    bp = Blueprint('reports', __name__)

    @bp.route('/reports/summary', methods=['GET'])
    @auth.required
    def summary_report():
        return jsonify(report_service.summary()), 200

    @bp.route('/reports/user/<int:user_id>', methods=['GET'])
    @auth.required
    def user_report(user_id):
        return jsonify(report_service.user_report(user_id)), 200

    return bp
