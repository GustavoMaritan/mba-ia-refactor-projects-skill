import sqlite3

from flask import jsonify, request

from src.middlewares.auth import admin_required


class AdminController:
    def __init__(self, service):
        self.service = service

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": self.service.settings.APP_VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    def health(self):
        try:
            return jsonify(self.service.health()), 200
        except sqlite3.Error:
            return jsonify({"status": "erro", "detalhes": "banco indisponível"}), 500

    @admin_required
    def reset_db(self):
        self.service.reset_db()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @admin_required
    def executar_query(self):
        dados = request.get_json(silent=True) or {}
        sql = dados.get("sql", "")
        if not sql:
            return jsonify({"erro": "Query não informada"}), 400
        try:
            linhas = self.service.executar_query(sql)
        except sqlite3.Error as e:
            return jsonify({"erro": str(e)}), 500
        if linhas is None:
            return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
        return jsonify({"dados": linhas, "sucesso": True}), 200
