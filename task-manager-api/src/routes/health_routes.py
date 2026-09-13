import datetime

from flask import Blueprint

API_VERSION = '1.0'


def make_health_routes():
    bp = Blueprint('health', __name__)

    @bp.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}

    @bp.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': API_VERSION}

    return bp
