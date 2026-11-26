import os
import secrets


def _env_bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


class Settings:
    """Configuração lida do ambiente. Nada de segredo fixo no código."""

    APP_VERSION = "1.0.0"

    def __init__(self):
        # sem SECRET_KEY no ambiente, gera uma aleatória por processo
        self.SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
        self.DEBUG = _env_bool("FLASK_DEBUG")
        self.HOST = os.environ.get("HOST", "127.0.0.1")
        self.PORT = int(os.environ.get("PORT", "5000"))
        self.DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
        self.APP_ENV = os.environ.get("APP_ENV", "producao")
        self.CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
        # rotas /admin/* ficam bloqueadas enquanto ADMIN_TOKEN não for definido
        self.ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
