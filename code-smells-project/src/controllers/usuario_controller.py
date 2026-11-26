from flask import jsonify, request

from src.errors import ValidationError


class UsuarioController:
    def __init__(self, service):
        self.service = service

    def listar(self):
        return jsonify({"dados": self.service.listar(), "sucesso": True}), 200

    def buscar_por_id(self, id):
        return jsonify({"dados": self.service.buscar_por_id(id), "sucesso": True}), 200

    def criar(self):
        dados = request.get_json(silent=True)
        if not dados:
            raise ValidationError("Dados inválidos")
        usuario_id = self.service.criar(dados.get("nome", ""), dados.get("email", ""), dados.get("senha", ""))
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        dados = request.get_json(silent=True) or {}
        usuario = self.service.autenticar(dados.get("email", ""), dados.get("senha", ""))
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
