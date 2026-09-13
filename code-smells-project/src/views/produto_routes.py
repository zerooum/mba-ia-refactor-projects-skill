import logging

from flask import Blueprint, jsonify, request

from src.models.errors import ValidationError
from src.views.serializers import produto_publico

log = logging.getLogger(__name__)


def _float_param(nome, valor):
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"Parâmetro {nome} inválido") from None


def make_produto_routes(controller):
    bp = Blueprint("produtos", __name__)

    @bp.get("/produtos")
    def listar_produtos():
        produtos = [produto_publico(p) for p in controller.listar()]
        log.info("Listando %d produtos", len(produtos))
        return jsonify({"dados": produtos, "sucesso": True}), 200

    @bp.get("/produtos/busca")
    def buscar_produtos():
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)
        if preco_min:
            preco_min = _float_param("preco_min", preco_min)
        if preco_max:
            preco_max = _float_param("preco_max", preco_max)
        resultados = [produto_publico(p) for p in controller.pesquisar(termo, categoria, preco_min, preco_max)]
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    @bp.get("/produtos/<int:produto_id>")
    def buscar_produto(produto_id):
        produto = controller.buscar(produto_id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
        return jsonify({"dados": produto_publico(produto), "sucesso": True}), 200

    @bp.post("/produtos")
    def criar_produto():
        produto_id = controller.criar(request.get_json(silent=True))
        log.info("Produto criado com ID: %s", produto_id)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    @bp.put("/produtos/<int:produto_id>")
    def atualizar_produto(produto_id):
        controller.atualizar(produto_id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @bp.delete("/produtos/<int:produto_id>")
    def deletar_produto(produto_id):
        controller.remover(produto_id)
        log.info("Produto %s deletado", produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    return bp
