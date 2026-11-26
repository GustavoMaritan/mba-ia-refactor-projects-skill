from sqlalchemy import func

from database import db
from errors import ValidationError
from models.category import Category
from models.constants import DEFAULT_COLOR
from models.task import Task
from services.base import commit_or_fail, get_or_404
from utils.helpers import is_valid_color


def _check_color(color):
    if not is_valid_color(color):
        raise ValidationError('Cor inválida')


class CategoryService:
    def get(self, category_id):
        return get_or_404(Category, category_id, 'Categoria não encontrada')

    def list_with_task_count(self):
        task_count = (
            db.select(Task.category_id, func.count(Task.id).label('n')).group_by(Task.category_id).subquery()
        )
        rows = db.session.execute(
            db.select(Category, func.coalesce(task_count.c.n, 0))
            .outerjoin(task_count, task_count.c.category_id == Category.id)
            .order_by(Category.id)
        ).all()
        return [category.to_dict() | {'task_count': count} for category, count in rows]

    def create(self, data):
        if not data:
            raise ValidationError('Dados inválidos')
        if not data.get('name'):
            raise ValidationError('Nome é obrigatório')
        color = data.get('color', DEFAULT_COLOR)
        _check_color(color)

        category = Category(name=data['name'], description=data.get('description', ''), color=color)
        db.session.add(category)
        commit_or_fail('Erro ao criar categoria')
        return category.to_dict()

    def update(self, category_id, data):
        category = self.get(category_id)
        if data is None:
            raise ValidationError('Dados inválidos')
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            _check_color(data['color'])
            category.color = data['color']
        commit_or_fail('Erro ao atualizar')
        return category.to_dict()

    def delete(self, category_id):
        category = self.get(category_id)
        # desvincula as tasks antes de apagar (antes ficavam com category_id inválido)
        db.session.execute(db.update(Task).where(Task.category_id == category_id).values(category_id=None))
        db.session.delete(category)
        commit_or_fail('Erro ao deletar')
