from routes.category_routes import build_category_bp
from routes.report_routes import build_report_bp
from routes.task_routes import build_task_bp
from routes.user_routes import build_user_bp


def register_routes(app, controllers):
    app.register_blueprint(build_task_bp(controllers.tasks))
    app.register_blueprint(build_user_bp(controllers.users))
    app.register_blueprint(build_category_bp(controllers.categories))
    app.register_blueprint(build_report_bp(controllers.reports))
