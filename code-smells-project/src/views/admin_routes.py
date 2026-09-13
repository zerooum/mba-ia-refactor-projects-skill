import logging

from flask import Blueprint, jsonify, request

from src.middlewares.auth import requer_token_admin

log = logging.getLogger(__name__)


def make_admin_routes(controller, admin_token):
    bp = Blueprint("admin", __name__)
    requer_admin = requer_token_admin(admin_token)

    @bp.post("/admin/reset-db")
    @requer_admin
    def reset_database():
        controller.resetar_banco()
        log.warning("!!! BANCO DE DADOS RESETADO !!!")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @bp.post("/admin/query")
    @requer_admin
    def executar_query():
        dados = request.get_json(silent=True)
        query = dados.get("sql", "") if isinstance(dados, dict) else ""
        if not query or not isinstance(query, str):
            return jsonify({"erro": "Query não informada"}), 400
        eh_select, linhas = controller.executar_sql(query)
        if eh_select:
            return jsonify({"dados": linhas, "sucesso": True}), 200
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200

    return bp
