import logging

from sqlalchemy import func

from database import db
from errors import ConflictError, ForbiddenError, UnauthorizedError, ValidationError
from models.constants import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, VALID_ROLES
from models.task import Task
from models.user import User
from services.base import commit_or_fail, get_or_404
from utils.helpers import utcnow, validate_email

logger = logging.getLogger(__name__)


class UserService:
    def get(self, user_id):
        return get_or_404(User, user_id, 'Usuário não encontrado')

    def list_with_task_count(self):
        # contagem numa query só (antes: len(u.tasks) carregava as tasks de cada usuário)
        task_count = (
            db.select(Task.user_id, func.count(Task.id).label('n')).group_by(Task.user_id).subquery()
        )
        rows = db.session.execute(
            db.select(User, func.coalesce(task_count.c.n, 0))
            .outerjoin(task_count, task_count.c.user_id == User.id)
            .order_by(User.id)
        ).all()
        result = []
        for user, count in rows:
            data = user.to_dict()
            data['task_count'] = count
            result.append(data)
        return result

    def get_with_tasks(self, user_id):
        user = self.get(user_id)
        data = user.to_dict()
        data['tasks'] = [t.to_dict() for t in self._tasks_of(user_id)]
        return data

    def tasks_summary(self, user_id):
        self.get(user_id)
        now = utcnow()
        return [
            {
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'created_at': str(t.created_at),
                'due_date': str(t.due_date) if t.due_date else None,
                'overdue': t.is_overdue(now),
            }
            for t in self._tasks_of(user_id)
        ]

    def create(self, data):
        if not data:
            raise ValidationError('Dados inválidos')
        name, email, password = data.get('name'), data.get('email'), data.get('password')
        role = data.get('role', DEFAULT_ROLE)
        if not name:
            raise ValidationError('Nome é obrigatório')
        if not email:
            raise ValidationError('Email é obrigatório')
        if not password:
            raise ValidationError('Senha é obrigatória')
        if not validate_email(email):
            raise ValidationError('Email inválido')
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha deve ter no mínimo 4 caracteres')
        if self._find_by_email(email):
            raise ConflictError('Email já cadastrado')
        if role not in VALID_ROLES:
            raise ValidationError('Role inválido')

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        commit_or_fail('Erro ao criar usuário')
        logger.info('usuário criado: %s', user.id)
        return user.to_dict()

    def update(self, user_id, data):
        user = self.get(user_id)
        if not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            if not validate_email(data['email']):
                raise ValidationError('Email inválido')
            existing = self._find_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']
        if 'password' in data:
            if not isinstance(data['password'], str) or len(data['password']) < MIN_PASSWORD_LENGTH:
                raise ValidationError('Senha muito curta')
            user.set_password(data['password'])
        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                raise ValidationError('Role inválido')
            user.role = data['role']
        if 'active' in data:
            user.active = data['active']

        commit_or_fail('Erro ao atualizar')
        return user.to_dict()

    def delete(self, user_id):
        user = self.get(user_id)
        # tasks do usuário vão junto, na mesma transação
        db.session.execute(db.delete(Task).where(Task.user_id == user_id))
        db.session.delete(user)
        commit_or_fail('Erro ao deletar')
        logger.info('usuário deletado: %s', user_id)

    def authenticate(self, data):
        if not data:
            raise ValidationError('Dados inválidos')
        email, password = data.get('email'), data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = self._find_by_email(email)
        if not user or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')

        if user.uses_legacy_hash():
            user.set_password(password)
            commit_or_fail('Erro ao atualizar')

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            # TODO: trocar por JWT de verdade; mantido para não quebrar clientes
            'token': 'fake-jwt-token-' + str(user.id),
        }

    def _find_by_email(self, email):
        return db.session.scalar(db.select(User).filter_by(email=email))

    def _tasks_of(self, user_id):
        return db.session.scalars(db.select(Task).filter_by(user_id=user_id).order_by(Task.id)).all()
