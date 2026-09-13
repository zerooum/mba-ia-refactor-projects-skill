import logging

from flask import Blueprint, jsonify, request

from src.views.serializers import usuario_login, usuario_publico

log = logging.getLogger(__name__)


def make_usuario_routes(controller):
    bp = Blueprint("usuarios", __name__)

    @bp.get("/usuarios")
    def listar_usuarios():
        return jsonify({"dados": [usuario_publico(u) for u in controller.listar()], "sucesso": True}), 200

    @bp.get("/usuarios/<int:usuario_id>")
    def buscar_usuario(usuario_id):
        usuario = controller.buscar(usuario_id)
        if not usuario:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        return jsonify({"dados": usuario_publico(usuario), "sucesso": True}), 200

    @bp.post("/usuarios")
    def criar_usuario():
        usuario_id = controller.criar(request.get_json(silent=True))
        log.info("Usuário criado: id=%s", usuario_id)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    @bp.post("/login")
    def login():
        usuario = controller.autenticar(request.get_json(silent=True))
        if not usuario:
            log.info("Login falhou")
            return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
        log.info("Login bem-sucedido: id=%s", usuario.id)
        return jsonify({"dados": usuario_login(usuario), "sucesso": True, "mensagem": "Login OK"}), 200

    return bp
