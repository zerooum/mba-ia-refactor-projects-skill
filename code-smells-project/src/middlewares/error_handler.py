import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.models.errors import DomainError

log = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def handle_domain(e):
        corpo = {"erro": e.mensagem}
        if e.inclui_sucesso:
            corpo["sucesso"] = False
        return jsonify(corpo), e.status

    @app.errorhandler(HTTPException)
    def handle_http(e):
        return jsonify({"erro": e.description}), e.code

    @app.errorhandler(Exception)
    def handle_unexpected(_e):
        log.exception("erro não tratado")  # detalhe só no log
        return jsonify({"erro": "Erro interno do servidor"}), 500
