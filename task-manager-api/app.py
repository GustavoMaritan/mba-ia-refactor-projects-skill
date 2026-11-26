"""Entry point e composition root da Task Manager API."""
import logging
from types import SimpleNamespace

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401  registra os models antes do create_all
from config.settings import Settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.error_handler import register_error_handlers
from routes import register_routes
from services.category_service import CategoryService
from services.notification_service import NotificationService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService


def create_app(settings=None):
    settings = settings or Settings()
    logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config.update(settings.flask_config())
    CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)

    task_service = TaskService(NotificationService(settings))
    controllers = SimpleNamespace(
        tasks=TaskController(task_service),
        users=UserController(UserService()),
        categories=CategoryController(CategoryService()),
        reports=ReportController(ReportService(task_service), settings),
    )
    register_routes(app, controllers)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    app.extensions['settings'] = settings
    return app


if __name__ == '__main__':
    application = create_app()
    s = application.extensions['settings']
    application.run(host=s.HOST, port=s.PORT, debug=s.DEBUG)
