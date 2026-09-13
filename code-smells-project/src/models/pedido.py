from dataclasses import dataclass, field

from src.models.errors import ValidationError

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO]


@dataclass
class ItemPedido:
    produto_id: int
    produto_nome: str
    quantidade: int
    preco_unitario: float


@dataclass
class Pedido:
    id: int
    usuario_id: int
    status: str
    total: float
    criado_em: str
    itens: list = field(default_factory=list)

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            usuario_id=row["usuario_id"],
            status=row["status"],
            total=row["total"],
            criado_em=row["criado_em"],
        )


def _eh_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_itens(itens):
    if not isinstance(itens, list):
        raise ValidationError("Itens do pedido inválidos")
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Itens do pedido inválidos")
        if not _eh_inteiro(item.get("produto_id")) or not _eh_inteiro(item.get("quantidade")):
            raise ValidationError("Cada item precisa de produto_id e quantidade inteiros")
        if item["quantidade"] <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")
