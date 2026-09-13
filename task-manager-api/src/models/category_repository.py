from sqlalchemy import func, select

from infra.database import transaction
from models.category import Category


class CategoryRepository:
    def __init__(self, session):
        self.session = session

    def get(self, category_id):
        return self.session.get(Category, category_id)

    def list_all(self):
        return self.session.scalars(select(Category).order_by(Category.id)).all()

    def count(self):
        return self.session.scalar(select(func.count()).select_from(Category))

    def add(self, category):
        with transaction(self.session):
            self.session.add(category)
        return category

    def save(self, category):
        with transaction(self.session):
            pass
        return category

    def delete(self, category):
        with transaction(self.session):
            self.session.delete(category)
