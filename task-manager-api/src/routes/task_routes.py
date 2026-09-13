from flask import Blueprint, request, jsonify

from routes.params import int_arg, json_body
from routes.serializers import task_dict, task_with_names, task_with_overdue


def make_task_routes(task_service, auth):
    bp = Blueprint('tasks', __name__)

    @bp.route('/tasks', methods=['GET'])
    @auth.required
    def get_tasks():
        return jsonify([task_with_names(t) for t in task_service.list_tasks()]), 200

    @bp.route('/tasks/<int:task_id>', methods=['GET'])
    @auth.required
    def get_task(task_id):
        return jsonify(task_with_overdue(task_service.get_task(task_id))), 200

    @bp.route('/tasks', methods=['POST'])
    @auth.required
    def create_task():
        return jsonify(task_dict(task_service.create_task(json_body()))), 201

    @bp.route('/tasks/<int:task_id>', methods=['PUT'])
    @auth.required
    def update_task(task_id):
        task_service.get_task(task_id)  # 404 antes de ler o corpo, como no contrato original
        return jsonify(task_dict(task_service.update_task(task_id, json_body()))), 200

    @bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    @auth.required
    def delete_task(task_id):
        task_service.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    @bp.route('/tasks/search', methods=['GET'])
    @auth.required
    def search_tasks():
        results = task_service.search(
            text=request.args.get('q', ''),
            status=request.args.get('status', ''),
            priority=int_arg('priority'),
            user_id=int_arg('user_id'),
        )
        return jsonify([task_dict(t) for t in results]), 200

    @bp.route('/tasks/stats', methods=['GET'])
    @auth.required
    def task_stats():
        return jsonify(task_service.stats()), 200

    return bp
