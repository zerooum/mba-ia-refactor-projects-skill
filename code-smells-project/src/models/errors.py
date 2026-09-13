class DomainError(Exception):
    """Erro de domínio. O error handler central traduz para HTTP usando `status`."""

    status = 400
    # Algumas respostas de erro do contrato original carregam "sucesso": false.
    inclui_sucesso = False

    @property
    def mensagem(self):
        return self.args[0] if self.args else ""


class ValidationError(DomainError):
    status = 400


class NotFoundError(DomainError):
    status = 404


class UnauthorizedError(DomainError):
    status = 401


class PedidoRecusadoError(ValidationError):
    """Pedido recusado por regra de estoque/produto."""

    inclui_sucesso = True
