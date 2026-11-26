from flask import jsonify, request


class CategoryController:
    def __init__(self, service):
        self.service = service

    def list(self):
        return jsonify(self.service.list_with_task_count()), 200

    def create(self):
        return jsonify(self.service.create(request.get_json(silent=True))), 201

    def update(self, cat_id):
        return jsonify(self.service.update(cat_id, request.get_json(silent=True))), 200

    def delete(self, cat_id):
        self.service.delete(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200
