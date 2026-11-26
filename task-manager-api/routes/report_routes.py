from flask import Blueprint


def build_report_bp(c):
    bp = Blueprint('reports', __name__)
    bp.add_url_rule('/', 'index', c.index, methods=['GET'])
    bp.add_url_rule('/health', 'health', c.health, methods=['GET'])
    bp.add_url_rule('/reports/summary', 'summary_report', c.summary, methods=['GET'])
    bp.add_url_rule('/reports/user/<int:user_id>', 'user_report', c.user, methods=['GET'])
    return bp
