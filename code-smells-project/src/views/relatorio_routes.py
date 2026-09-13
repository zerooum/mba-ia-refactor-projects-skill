from flask import Blueprint, jsonify


def make_relatorio_routes(controller):
    bp = Blueprint("relatorios", __name__)

    @bp.get("/relatorios/vendas")
    def relatorio_vendas():
        return jsonify({"dados": controller.vendas(), "sucesso": True}), 200

    return bp
