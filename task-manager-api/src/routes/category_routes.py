from flask import Blueprint, jsonify

from routes.params import json_body
from routes.serializers import category_dict


def make_category_routes(category_service, auth):
    bp = Blueprint('categories', __name__)

    @bp.route('/categories', methods=['GET'])
    @auth.required
    def get_categories():
        return jsonify([
            {**category_dict(c), 'task_count': count} for c, count in category_service.list_categories()
        ]), 200

    @bp.route('/categories', methods=['POST'])
    @auth.required
    def create_category():
        return jsonify(category_dict(category_service.create_category(json_body()))), 201

    @bp.route('/categories/<int:cat_id>', methods=['PUT'])
    @auth.required
    def update_category(cat_id):
        category_service.get_category(cat_id)  # 404 antes de ler o corpo, como no contrato original
        return jsonify(category_dict(category_service.update_category(cat_id, json_body()))), 200

    @bp.route('/categories/<int:cat_id>', methods=['DELETE'])
    @auth.required
    def delete_category(cat_id):
        category_service.delete_category(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200

    return bp
