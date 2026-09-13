from flask import Blueprint, g, jsonify

from routes.params import json_body
from routes.serializers import task_dict, task_summary, user_dict, user_list_item


def make_user_routes(user_service, auth_service, auth):
    bp = Blueprint('users', __name__)

    @bp.route('/users', methods=['GET'])
    @auth.required
    def get_users():
        return jsonify([user_list_item(u, count) for u, count in user_service.list_users()]), 200

    @bp.route('/users/<int:user_id>', methods=['GET'])
    @auth.required
    def get_user(user_id):
        data = user_dict(user_service.get_user(user_id))
        data['tasks'] = [task_dict(t) for t in user_service.get_user_tasks(user_id)]
        return jsonify(data), 200

    @bp.route('/users', methods=['POST'])
    @auth.optional
    def create_user():
        return jsonify(user_dict(user_service.create_user(json_body(), actor=g.current_user))), 201

    @bp.route('/users/<int:user_id>', methods=['PUT'])
    @auth.required
    def update_user(user_id):
        user_service.get_user(user_id)  # 404 antes de ler o corpo, como no contrato original
        return jsonify(user_dict(user_service.update_user(user_id, json_body(), actor=g.current_user))), 200

    @bp.route('/users/<int:user_id>', methods=['DELETE'])
    @auth.required
    def delete_user(user_id):
        user_service.delete_user(user_id, actor=g.current_user)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    @bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    @auth.required
    def get_user_tasks(user_id):
        return jsonify([task_summary(t) for t in user_service.get_user_tasks(user_id)]), 200

    @bp.route('/login', methods=['POST'])
    def login():
        user, token = auth_service.login(json_body())
        return jsonify({'message': 'Login realizado com sucesso', 'user': user_dict(user), 'token': token}), 200

    return bp
