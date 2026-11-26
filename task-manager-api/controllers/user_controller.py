from flask import jsonify, request


class UserController:
    def __init__(self, service):
        self.service = service

    def list(self):
        return jsonify(self.service.list_with_task_count()), 200

    def get(self, user_id):
        return jsonify(self.service.get_with_tasks(user_id)), 200

    def create(self):
        return jsonify(self.service.create(request.get_json(silent=True))), 201

    def update(self, user_id):
        return jsonify(self.service.update(user_id, request.get_json(silent=True))), 200

    def delete(self, user_id):
        self.service.delete(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    def tasks(self, user_id):
        return jsonify(self.service.tasks_summary(user_id)), 200

    def login(self):
        return jsonify(self.service.authenticate(request.get_json(silent=True))), 200
