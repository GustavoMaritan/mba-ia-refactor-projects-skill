import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Notificações da loja. Por enquanto só registra no log (e-mail/SMS/push são simulados)."""

    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("email: pedido %s criado para usuario %s", pedido_id, usuario_id)
        logger.info("sms: seu pedido foi recebido")
        logger.info("push: novo pedido recebido pelo sistema")

    def status_alterado(self, pedido_id, status):
        if status == "aprovado":
            logger.info("pedido %s aprovado, preparar envio", pedido_id)
        elif status == "cancelado":
            logger.info("pedido %s cancelado, devolver estoque", pedido_id)
