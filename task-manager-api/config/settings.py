import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


class Settings:
    """Configuração da API lida do ambiente (ou de um .env local, fora do git)."""

    APP_VERSION = "1.0"

    def __init__(self):
        self.SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
        self.SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.DEBUG = _env_bool("FLASK_DEBUG")
        self.HOST = os.environ.get("HOST", "127.0.0.1")
        self.PORT = int(os.environ.get("PORT", "5000"))
        self.CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

        # SMTP: sem SMTP_HOST as notificações só vão para o log
        self.SMTP_HOST = os.environ.get("SMTP_HOST", "")
        self.SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
        self.SMTP_USER = os.environ.get("SMTP_USER", "")
        self.SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

    def flask_config(self):
        return {
            "SECRET_KEY": self.SECRET_KEY,
            "SQLALCHEMY_DATABASE_URI": self.SQLALCHEMY_DATABASE_URI,
            "SQLALCHEMY_TRACK_MODIFICATIONS": self.SQLALCHEMY_TRACK_MODIFICATIONS,
            "DEBUG": self.DEBUG,
        }
