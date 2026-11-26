from datetime import timedelta

from sqlalchemy import case, func

from database import db
from models.category import Category
from models.constants import CLOSED_STATUSES, HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS
from models.task import Task
from models.user import User
from services.base import get_or_404
from utils.helpers import calculate_percentage, utcnow


def _count(stmt):
    return db.session.scalar(stmt)


class ReportService:
    def __init__(self, task_service):
        self.tasks = task_service

    def summary(self):
        now = utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

        by_priority = dict(db.session.execute(db.select(Task.priority, func.count()).group_by(Task.priority)).all())

        overdue_tasks = db.session.scalars(
            db.select(Task)
            .where(Task.due_date.is_not(None), Task.due_date < now, Task.status.not_in(CLOSED_STATUSES))
            .order_by(Task.id)
        ).all()

        # produtividade por usuário em uma query (antes: 1 query por usuário)
        productivity = db.session.execute(
            db.select(
                User.id,
                User.name,
                func.count(Task.id),
                func.coalesce(func.sum(case((Task.status == 'done', 1), else_=0)), 0),
            )
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        ).all()

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': _count(db.select(func.count()).select_from(Task)),
                'total_users': _count(db.select(func.count()).select_from(User)),
                'total_categories': _count(db.select(func.count()).select_from(Category)),
            },
            'tasks_by_status': self.tasks.count_by_status(),
            'tasks_by_priority': {label: by_priority.get(p, 0) for p, label in PRIORITY_LABELS.items()},
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [
                    {
                        'id': t.id,
                        'title': t.title,
                        'due_date': str(t.due_date),
                        'days_overdue': (now - t.due_date).days,
                    }
                    for t in overdue_tasks
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': _count(
                    db.select(func.count()).select_from(Task).where(Task.created_at >= since)
                ),
                'tasks_completed_last_7_days': _count(
                    db.select(func.count()).select_from(Task).where(Task.status == 'done', Task.updated_at >= since)
                ),
            },
            'user_productivity': [
                {
                    'user_id': user_id,
                    'user_name': name,
                    'total_tasks': total,
                    'completed_tasks': completed,
                    'completion_rate': calculate_percentage(completed, total),
                }
                for user_id, name, total, completed in productivity
            ],
        }

    def user_report(self, user_id):
        user = get_or_404(User, user_id, 'Usuário não encontrado')
        tasks = db.session.scalars(db.select(Task).filter_by(user_id=user_id)).all()
        now = utcnow()

        stats = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
        for t in tasks:
            if t.status in stats:
                stats[t.status] += 1

        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': len(tasks),
                'done': stats['done'],
                'pending': stats['pending'],
                'in_progress': stats['in_progress'],
                'cancelled': stats['cancelled'],
                'overdue': sum(1 for t in tasks if t.is_overdue(now)),
                'high_priority': sum(1 for t in tasks if t.priority <= HIGH_PRIORITY_MAX),
                'completion_rate': calculate_percentage(stats['done'], len(tasks)),
            },
        }
