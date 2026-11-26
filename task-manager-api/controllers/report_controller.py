from datetime import datetime

from flask import jsonify


class ReportController:
    def __init__(self, service, settings):
        self.service = service
        self.settings = settings

    def summary(self):
        return jsonify(self.service.summary()), 200

    def user(self, user_id):
        return jsonify(self.service.user_report(user_id)), 200

    def health(self):
        return {'status': 'ok', 'timestamp': str(datetime.now())}

    def index(self):
        return {'message': 'Task Manager API', 'version': self.settings.APP_VERSION}
