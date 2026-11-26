from flask import Blueprint


def build_category_bp(c):
    bp = Blueprint('categories', __name__)
    bp.add_url_rule('/categories', 'get_categories', c.list, methods=['GET'])
    bp.add_url_rule('/categories', 'create_category', c.create, methods=['POST'])
    bp.add_url_rule('/categories/<int:cat_id>', 'update_category', c.update, methods=['PUT'])
    bp.add_url_rule('/categories/<int:cat_id>', 'delete_category', c.delete, methods=['DELETE'])
    return bp
