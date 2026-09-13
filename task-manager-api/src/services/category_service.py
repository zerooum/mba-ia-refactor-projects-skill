from models.category import Category
from models.constants import DEFAULT_COLOR
from models.errors import NotFoundError, ValidationError


class CategoryService:
    def __init__(self, categories, tasks):
        self.categories = categories
        self.tasks = tasks

    def list_categories(self):
        """[(categoria, nº de tasks)] — contagem agregada numa query só."""
        counts = self.tasks.count_by_category()
        return [(category, counts.get(category.id, 0)) for category in self.categories.list_all()]

    def get_category(self, category_id):
        category = self.categories.get(category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        return category

    def create_category(self, data):
        if not data:
            raise ValidationError('Dados inválidos')
        name = self._require_name(data.get('name'))

        category = Category(
            name=name,
            description=data.get('description', ''),
            color=data.get('color', DEFAULT_COLOR),
        )
        return self.categories.add(category)

    def update_category(self, category_id, data):
        category = self.get_category(category_id)
        if data is None:
            raise ValidationError('Dados inválidos')
        if 'name' in data:
            self._require_name(data['name'])

        for field in ('name', 'description', 'color'):
            if field in data:
                setattr(category, field, data[field])
        return self.categories.save(category)

    def delete_category(self, category_id):
        self.categories.delete(self.get_category(category_id))

    @staticmethod
    def _require_name(name):
        if not name:
            raise ValidationError('Nome é obrigatório')
        return name
