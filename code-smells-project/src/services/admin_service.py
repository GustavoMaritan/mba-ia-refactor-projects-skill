import logging

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, get_db, produtos, usuarios, pedidos, settings):
        self._db = get_db
        self.produtos = produtos
        self.usuarios = usuarios
        self.pedidos = pedidos
        self.settings = settings

    def health(self):
        self._db().execute("SELECT 1")
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self.produtos.contar(),
                "usuarios": self.usuarios.contar(),
                "pedidos": self.pedidos.contar(),
            },
            "versao": self.settings.APP_VERSION,
            "ambiente": self.settings.APP_ENV,
            "db_path": self.settings.DATABASE_PATH,
            "debug": self.settings.DEBUG,
        }

    def reset_db(self):
        db = self._db()
        with db:
            for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
                db.execute(f"DELETE FROM {tabela}")
        logger.warning("banco de dados resetado via /admin/reset-db")

    def executar_query(self, sql):
        """Console SQL de administração. Só acessível com ADMIN_TOKEN (ver middlewares/auth.py)."""
        db = self._db()
        logger.warning("query administrativa executada")
        cur = db.execute(sql)
        if sql.strip().upper().startswith("SELECT"):
            return [dict(r) for r in cur.fetchall()]
        db.commit()
        return None
