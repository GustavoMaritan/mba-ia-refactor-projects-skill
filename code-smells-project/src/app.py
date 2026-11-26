"""Composition root: monta config, banco, models, services, controllers e rotas."""
import logging
from types import SimpleNamespace

from flask import Flask
from flask_cors import CORS

from src import database
from src.config.settings import Settings
from src.controllers.admin_controller import AdminController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.usuario_controller import UsuarioController
from src.middlewares.error_handler import register_error_handlers
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.admin_service import AdminService
from src.services.notification_service import NotificationService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.usuario_service import UsuarioService
from src.views.routes import register_routes


def create_app(settings=None):
    settings = settings or Settings()
    logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.SECRET_KEY,
        DEBUG=settings.DEBUG,
        DATABASE_PATH=settings.DATABASE_PATH,
        ADMIN_TOKEN=settings.ADMIN_TOKEN,
    )
    CORS(app, origins=settings.CORS_ORIGINS)
    database.init_app(app)

    produtos = ProdutoModel(database.get_db)
    usuarios = UsuarioModel(database.get_db)
    pedidos = PedidoModel(database.get_db)

    controllers = SimpleNamespace(
        produtos=ProdutoController(ProdutoService(produtos)),
        usuarios=UsuarioController(UsuarioService(usuarios)),
        pedidos=PedidoController(PedidoService(pedidos, produtos, NotificationService())),
        admin=AdminController(AdminService(database.get_db, produtos, usuarios, pedidos, settings)),
    )

    register_routes(app, controllers)
    register_error_handlers(app)
    app.extensions["settings"] = settings
    return app
