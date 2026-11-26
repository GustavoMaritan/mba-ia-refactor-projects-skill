from flask import Blueprint


def build_user_bp(c):
    bp = Blueprint('users', __name__)
    bp.add_url_rule('/users', 'get_users', c.list, methods=['GET'])
    bp.add_url_rule('/users/<int:user_id>', 'get_user', c.get, methods=['GET'])
    bp.add_url_rule('/users', 'create_user', c.create, methods=['POST'])
    bp.add_url_rule('/users/<int:user_id>', 'update_user', c.update, methods=['PUT'])
    bp.add_url_rule('/users/<int:user_id>', 'delete_user', c.delete, methods=['DELETE'])
    bp.add_url_rule('/users/<int:user_id>/tasks', 'get_user_tasks', c.tasks, methods=['GET'])
    bp.add_url_rule('/login', 'login', c.login, methods=['POST'])
    return bp
