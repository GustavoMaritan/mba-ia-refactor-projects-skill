import logging

from sqlalchemy.exc import SQLAlchemyError

from database import db
from errors import AppError, NotFoundError

logger = logging.getLogger(__name__)


def commit_or_fail(message):
    """Commit da sessão; em erro faz rollback e devolve 500 com a mensagem da rota."""
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception(message)
        raise AppError(message, status=500)


def get_or_404(model, obj_id, message):
    obj = db.session.get(model, obj_id)
    if obj is None:
        raise NotFoundError(message)
    return obj
