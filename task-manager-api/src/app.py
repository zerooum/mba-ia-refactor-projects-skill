import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from infra.database import db
from middlewares.auth import AuthMiddleware
from middlewares.error_handler import register_error_handlers
from models.category_repository import CategoryRepository
from models.task_repository import TaskRepository
from models.user_repository import UserRepository
from routes.category_routes import make_category_routes
from routes.health_routes import make_health_routes
from routes.report_routes import make_report_routes
from routes.task_routes import make_task_routes
from routes.user_routes import make_user_routes
from services.auth_service import AuthService
from services.category_service import CategoryService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService


def create_app(settings=None):
    """Composition root: monta config, banco, repositórios, serviços e rotas."""
    settings = settings or Settings()

    app = Flask(__name__, instance_path=settings.INSTANCE_PATH)
    app.config.from_object(settings)

    CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)
    register_error_handlers(app)

    tasks = TaskRepository(db.session)
    users = UserRepository(db.session)
    categories = CategoryRepository(db.session)
    auth_service = AuthService(users, settings.SECRET_KEY, settings.TOKEN_MAX_AGE)
    auth = AuthMiddleware(auth_service)

    app.register_blueprint(make_health_routes())
    app.register_blueprint(make_task_routes(TaskService(tasks, users, categories), auth))
    app.register_blueprint(make_user_routes(UserService(users, tasks), auth_service, auth))
    app.register_blueprint(make_report_routes(ReportService(tasks, users, categories), auth))
    app.register_blueprint(make_category_routes(CategoryService(categories, tasks), auth))

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    settings = Settings()
    create_app(settings).run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
