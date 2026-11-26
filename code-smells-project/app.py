"""Entry point da API da loja."""
from src.app import create_app

app = create_app()

if __name__ == "__main__":
    settings = app.extensions["settings"]
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
