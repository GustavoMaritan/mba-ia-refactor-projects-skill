import logging
import smtplib

from utils.helpers import utcnow

logger = logging.getLogger(__name__)


class NotificationService:
    """Notificações por e-mail. Sem SMTP configurado, só registra no log."""

    def __init__(self, settings, smtp_factory=smtplib.SMTP):
        self.settings = settings
        self.smtp_factory = smtp_factory
        self.notifications = []

    @property
    def enabled(self):
        return bool(self.settings.SMTP_HOST)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info('email (simulado) para usuário: %s', subject)
            return False
        try:
            with self.smtp_factory(self.settings.SMTP_HOST, self.settings.SMTP_PORT) as server:
                server.starttls()
                server.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)
                server.sendmail(self.settings.SMTP_USER, to, f"Subject: {subject}\n\n{body}")
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception('falha ao enviar email')
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utcnow(),
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]
