from flask import Blueprint


def register_routes(app, c):
    """Mapa URL -> controller. Os nomes de endpoint são os mesmos da versão anterior."""
    bp = Blueprint("api", __name__)
    rule = bp.add_url_rule

    rule("/", "index", c.admin.index, methods=["GET"])
    rule("/health", "health_check", c.admin.health, methods=["GET"])

    rule("/produtos", "listar_produtos", c.produtos.listar, methods=["GET"])
    rule("/produtos/busca", "buscar_produtos", c.produtos.buscar, methods=["GET"])
    rule("/produtos/<int:id>", "buscar_produto", c.produtos.buscar_por_id, methods=["GET"])
    rule("/produtos", "criar_produto", c.produtos.criar, methods=["POST"])
    rule("/produtos/<int:id>", "atualizar_produto", c.produtos.atualizar, methods=["PUT"])
    rule("/produtos/<int:id>", "deletar_produto", c.produtos.deletar, methods=["DELETE"])

    rule("/usuarios", "listar_usuarios", c.usuarios.listar, methods=["GET"])
    rule("/usuarios/<int:id>", "buscar_usuario", c.usuarios.buscar_por_id, methods=["GET"])
    rule("/usuarios", "criar_usuario", c.usuarios.criar, methods=["POST"])
    rule("/login", "login", c.usuarios.login, methods=["POST"])

    rule("/pedidos", "criar_pedido", c.pedidos.criar, methods=["POST"])
    rule("/pedidos", "listar_todos_pedidos", c.pedidos.listar_todos, methods=["GET"])
    rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", c.pedidos.listar_por_usuario, methods=["GET"])
    rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", c.pedidos.atualizar_status, methods=["PUT"])

    rule("/relatorios/vendas", "relatorio_vendas", c.pedidos.relatorio_vendas, methods=["GET"])

    rule("/admin/reset-db", "reset_database", c.admin.reset_db, methods=["POST"])
    rule("/admin/query", "executar_query", c.admin.executar_query, methods=["POST"])

    app.register_blueprint(bp)
