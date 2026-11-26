import hmac
from functools import wraps

from flask import current_app, jsonify, request


def admin_required(fn):
    """Exige o header X-Admin-Token igual ao ADMIN_TOKEN da config.

    Sem ADMIN_TOKEN configurado a rota fica sempre bloqueada.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN", "")
        sent = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(sent, expected):
            return jsonify({"erro": "Acesso negado"}), 403
        return fn(*args, **kwargs)

    return wrapper
