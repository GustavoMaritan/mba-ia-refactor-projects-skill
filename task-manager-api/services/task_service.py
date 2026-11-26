from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import db
from errors import NotFoundError, ValidationError
from models.category import Category
from models.constants import (
    CLOSED_STATUSES, DATE_FORMAT, DEFAULT_PRIORITY, DEFAULT_STATUS, MAX_PRIORITY,
    MAX_TITLE_LENGTH, MIN_PRIORITY, MIN_TITLE_LENGTH, VALID_STATUSES,
)
from models.task import Task
from models.user import User
from services.base import commit_or_fail, get_or_404
from utils.helpers import calculate_percentage, parse_date, utcnow


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _check_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')


def _check_status(status):
    if status not in VALID_STATUSES:
        raise ValidationError('Status inválido')


def _check_priority(priority):
    if not _is_int(priority):
        raise ValidationError('Prioridade inválida')
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre 1 e 5')


def _check_user(user_id):
    if user_id and db.session.get(User, user_id) is None:
        raise NotFoundError('Usuário não encontrado')


def _check_category(category_id):
    if category_id and db.session.get(Category, category_id) is None:
        raise NotFoundError('Categoria não encontrada')


class TaskService:
    def __init__(self, notifier):
        self.notifier = notifier

    def get(self, task_id):
        return get_or_404(Task, task_id, 'Task não encontrada')

    def list_with_details(self):
        # joinedload evita 2 queries por task (usuário e categoria)
        tasks = db.session.scalars(
            db.select(Task).options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id)
        ).unique().all()
        now = utcnow()
        result = []
        for t in tasks:
            data = t.to_dict()
            data['overdue'] = t.is_overdue(now)
            data['user_name'] = t.user.name if t.user else None
            data['category_name'] = t.category.name if t.category else None
            result.append(data)
        return result

    def get_detail(self, task_id):
        task = self.get(task_id)
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data

    def create(self, data):
        if not data:
            raise ValidationError('Dados inválidos')
        title = data.get('title')
        if not title:
            raise ValidationError('Título é obrigatório')
        _check_title(title)

        status = data.get('status', DEFAULT_STATUS)
        priority = data.get('priority', DEFAULT_PRIORITY)
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        _check_status(status)
        _check_priority(priority)
        _check_user(user_id)
        _check_category(category_id)

        task = Task(
            title=title,
            description=data.get('description', ''),
            status=status,
            priority=priority,
            user_id=user_id,
            category_id=category_id,
        )
        if data.get('due_date'):
            task.due_date = parse_date(data['due_date'], DATE_FORMAT)
            if task.due_date is None:
                raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')
        if data.get('tags'):
            task.set_tags(data['tags'])

        db.session.add(task)
        commit_or_fail('Erro ao criar task')
        if task.user:
            self.notifier.notify_task_assigned(task.user, task)
        return task.to_dict()

    def update(self, task_id, data):
        task = self.get(task_id)
        if not data:
            raise ValidationError('Dados inválidos')

        if 'title' in data:
            _check_title(data['title'])
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            _check_status(data['status'])
            task.status = data['status']
        if 'priority' in data:
            _check_priority(data['priority'])
            task.priority = data['priority']
        if 'user_id' in data:
            _check_user(data['user_id'])
            task.user_id = data['user_id']
        if 'category_id' in data:
            _check_category(data['category_id'])
            task.category_id = data['category_id']
        if 'due_date' in data:
            if data['due_date']:
                parsed = parse_date(data['due_date'], DATE_FORMAT)
                if parsed is None:
                    raise ValidationError('Formato de data inválido')
                task.due_date = parsed
            else:
                task.due_date = None
        if 'tags' in data:
            task.set_tags(data['tags'])

        task.updated_at = utcnow()
        commit_or_fail('Erro ao atualizar')
        return task.to_dict()

    def delete(self, task_id):
        task = self.get(task_id)
        db.session.delete(task)
        commit_or_fail('Erro ao deletar')

    def search(self, query='', status='', priority=None, user_id=None):
        stmt = db.select(Task)
        if query:
            stmt = stmt.where(db.or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%')))
        if status:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        return [t.to_dict() for t in db.session.scalars(stmt.order_by(Task.id))]

    def count_by_status(self):
        rows = db.session.execute(db.select(Task.status, func.count()).group_by(Task.status)).all()
        counts = dict(rows)
        return {s: counts.get(s, 0) for s in VALID_STATUSES}

    def count_overdue(self, now=None):
        now = now or utcnow()
        return db.session.scalar(
            db.select(func.count()).select_from(Task).where(
                Task.due_date.is_not(None), Task.due_date < now, Task.status.not_in(CLOSED_STATUSES)
            )
        )

    def stats(self):
        by_status = self.count_by_status()
        total = db.session.scalar(db.select(func.count()).select_from(Task))
        return {
            'total': total,
            'pending': by_status['pending'],
            'in_progress': by_status['in_progress'],
            'done': by_status['done'],
            'cancelled': by_status['cancelled'],
            'overdue': self.count_overdue(),
            'completion_rate': calculate_percentage(by_status['done'], total),
        }
