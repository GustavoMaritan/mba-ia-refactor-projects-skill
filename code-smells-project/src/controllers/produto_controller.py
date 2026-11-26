from flask import jsonify, request

from src.errors import ValidationError


def _float_ou_none(valor, campo):
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"{campo} inválido")


class ProdutoController:
    def __init__(self, service):
        self.service = service

    def listar(self):
        return jsonify({"dados": self.service.listar(), "sucesso": True}), 200

    def buscar_por_id(self, id):
        return jsonify({"dados": self.service.buscar_por_id(id), "sucesso": True}), 200

    def buscar(self):
        args = request.args
        resultados = self.service.buscar(
            args.get("q", ""),
            args.get("categoria"),
            _float_ou_none(args.get("preco_min"), "preco_min"),
            _float_ou_none(args.get("preco_max"), "preco_max"),
        )
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def criar(self):
        produto_id = self.service.criar(request.get_json(silent=True))
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, id):
        self.service.atualizar(id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, id):
        self.service.deletar(id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
