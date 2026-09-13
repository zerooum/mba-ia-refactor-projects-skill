from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.infra.database import Database
from src.infra.notificador import NotificadorConsole
from src.infra.schema import init_db
from src.middlewares.error_handler import register_error_handlers
from src.models.pedido_repository import PedidoRepository
from src.models.produto_repository import ProdutoRepository
from src.models.sistema_repository import SistemaRepository
from src.models.usuario_repository import UsuarioRepository
from src.views.admin_routes import make_admin_routes
from src.views.pedido_routes import make_pedido_routes
from src.views.produto_routes import make_produto_routes
from src.views.relatorio_routes import make_relatorio_routes
from src.views.sistema_routes import make_sistema_routes
from src.views.usuario_routes import make_usuario_routes


def create_app(settings=None):
    """Composition root: monta o grafo de dependências e registra rotas e middlewares."""
    settings = settings or Settings()

    app = Flask(__name__)
    app.config.from_object(settings)
    CORS(app, origins=settings.CORS_ORIGINS)

    db = Database(settings.DB_PATH)
    db.init_app(app)
    init_db(db, settings.SEED_SENHAS)

    produtos = ProdutoRepository(db)
    usuarios = UsuarioRepository(db)
    pedidos = PedidoRepository(db)
    sistema = SistemaController(SistemaRepository(db), produtos, usuarios, pedidos)

    register_error_handlers(app)
    app.register_blueprint(make_produto_routes(ProdutoController(produtos)))
    app.register_blueprint(make_usuario_routes(UsuarioController(usuarios)))
    app.register_blueprint(make_pedido_routes(PedidoController(pedidos, usuarios, NotificadorConsole())))
    app.register_blueprint(make_relatorio_routes(RelatorioController(pedidos)))
    app.register_blueprint(make_sistema_routes(sistema, settings))
    app.register_blueprint(make_admin_routes(sistema, settings.ADMIN_TOKEN))
    return app
