from src.models.errors import NotFoundError, ValidationError
from src.models.pedido import STATUS_APROVADO, STATUS_CANCELADO, STATUS_VALIDOS, validar_itens


class PedidoController:
    def __init__(self, pedidos, usuarios, notificador):
        self.pedidos = pedidos
        self.usuarios = usuarios
        self.notificador = notificador

    def criar(self, dados):
        if not dados or not isinstance(dados, dict):
            raise ValidationError("Dados inválidos")

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")
        if not isinstance(usuario_id, int) or isinstance(usuario_id, bool):
            raise ValidationError("Usuario ID inválido")
        if not itens:
            raise ValidationError("Pedido deve ter pelo menos 1 item")
        validar_itens(itens)
        if not self.usuarios.buscar_por_id(usuario_id):
            raise ValidationError("Usuário não encontrado")

        pedido_id, total = self.pedidos.criar(usuario_id, itens)
        self.notificador.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_por_usuario(self, usuario_id):
        return self.pedidos.listar_por_usuario(usuario_id)

    def listar_todos(self):
        return self.pedidos.listar_todos()

    def atualizar_status(self, pedido_id, dados):
        if not dados or not isinstance(dados, dict):
            raise ValidationError("Dados inválidos")

        novo_status = dados.get("status", "")

        if novo_status not in STATUS_VALIDOS:
            raise ValidationError("Status inválido")
        if not self.pedidos.existe(pedido_id):
            raise NotFoundError("Pedido não encontrado")

        self.pedidos.atualizar_status(pedido_id, novo_status)

        if novo_status == STATUS_APROVADO:
            self.notificador.pedido_aprovado(pedido_id)
        if novo_status == STATUS_CANCELADO:
            self.notificador.pedido_cancelado(pedido_id)
