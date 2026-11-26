from flask import jsonify, request

from errors import ValidationError


def _int_arg(name, message):
    value = request.args.get(name, '')
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(message)


class TaskController:
    def __init__(self, service):
        self.service = service

    def list(self):
        return jsonify(self.service.list_with_details()), 200

    def get(self, task_id):
        return jsonify(self.service.get_detail(task_id)), 200

    def create(self):
        return jsonify(self.service.create(request.get_json(silent=True))), 201

    def update(self, task_id):
        return jsonify(self.service.update(task_id, request.get_json(silent=True))), 200

    def delete(self, task_id):
        self.service.delete(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    def search(self):
        results = self.service.search(
            query=request.args.get('q', ''),
            status=request.args.get('status', ''),
            priority=_int_arg('priority', 'Prioridade inválida'),
            user_id=_int_arg('user_id', 'user_id inválido'),
        )
        return jsonify(results), 200

    def stats(self):
        return jsonify(self.service.stats()), 200
