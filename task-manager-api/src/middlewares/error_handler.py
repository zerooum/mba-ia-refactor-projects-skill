import logging

from flask import jsonify, request
from werkzeug.exceptions import HTTPException

from models.errors import DomainError

log = logging.getLogger(__name__)

GENERIC_ERROR = 'Erro interno'


def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def handle_domain_error(error):
        return jsonify({'error': error.message}), error.status

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({'error': error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # detalhe vai para o log; o cliente recebe só a mensagem genérica
        log.exception('Erro não tratado em %s %s', request.method, request.path)
        return jsonify({'error': GENERIC_ERROR}), 500
