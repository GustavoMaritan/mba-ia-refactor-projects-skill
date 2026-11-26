from flask import Blueprint


def build_task_bp(c):
    bp = Blueprint('tasks', __name__)
    bp.add_url_rule('/tasks', 'get_tasks', c.list, methods=['GET'])
    bp.add_url_rule('/tasks/<int:task_id>', 'get_task', c.get, methods=['GET'])
    bp.add_url_rule('/tasks', 'create_task', c.create, methods=['POST'])
    bp.add_url_rule('/tasks/<int:task_id>', 'update_task', c.update, methods=['PUT'])
    bp.add_url_rule('/tasks/<int:task_id>', 'delete_task', c.delete, methods=['DELETE'])
    bp.add_url_rule('/tasks/search', 'search_tasks', c.search, methods=['GET'])
    bp.add_url_rule('/tasks/stats', 'task_stats', c.stats, methods=['GET'])
    return bp
