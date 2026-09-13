import logging

from flask import Blueprint, jsonify

log = logging.getLogger(__name__)

API_VERSION = "1.0.0"


def make_sistema_routes(controller, settings):
    bp = Blueprint("sistema", __name__)

    @bp.get("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": API_VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health"
            }
        })

    @bp.get("/health")
    def health_check():
        try:
            counts = controller.contagens()
        except Exception:
            log.exception("healthcheck falhou")
            return jsonify({"status": "erro", "detalhes": "Banco de dados indisponível"}), 500
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": counts,
            "versao": API_VERSION,
            "ambiente": settings.AMBIENTE,
            "debug": settings.DEBUG,
        }), 200

    return bp
