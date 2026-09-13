from src.models.errors import PedidoRecusadoError
from src.models.pedido import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE, ItemPedido, Pedido


class PedidoRepository:
    def __init__(self, db):
        self.db = db

    def criar(self, usuario_id, itens):
        """Checkout atômico: valida estoque, grava pedido + itens e baixa estoque numa transação só."""
        with self.db.transacao() as conn:
            total = 0
            produtos = []
            for item in itens:
                produto = conn.execute(
                    "SELECT * FROM produtos WHERE id = ?", (item["produto_id"],)
                ).fetchone()
                if produto is None:
                    raise PedidoRecusadoError(f"Produto {item['produto_id']} não encontrado")
                if produto["estoque"] < item["quantidade"]:
                    raise PedidoRecusadoError(f"Estoque insuficiente para {produto['nome']}")
                total += produto["preco"] * item["quantidade"]
                produtos.append(produto)

            pedido_id = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            ).lastrowid

            for item, produto in zip(itens, produtos):
                conn.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
                )
                # Decremento condicional: fecha a corrida entre checar e baixar estoque.
                afetadas = conn.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                ).rowcount
                if afetadas == 0:
                    raise PedidoRecusadoError(f"Estoque insuficiente para {produto['nome']}")

        return pedido_id, total

    # Uma query só (antes: 1 + N + N*M). LEFT JOIN preserva pedido sem item e item de produto removido.
    _SQL_PEDIDOS_COM_ITENS = """
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
               pr.id AS produto_existente, pr.nome AS produto_nome
          FROM pedidos p
          LEFT JOIN itens_pedido i ON i.pedido_id = p.id
          LEFT JOIN produtos pr ON pr.id = i.produto_id
         {where}
         ORDER BY p.id, i.id
    """

    def _listar_com_itens(self, where="", params=()):
        pedidos = {}
        for row in self.db.consultar(self._SQL_PEDIDOS_COM_ITENS.format(where=where), params):
            pedido = pedidos.get(row["id"])
            if pedido is None:
                pedido = pedidos[row["id"]] = Pedido.from_row(row)
            if row["item_id"] is not None:
                pedido.itens.append(ItemPedido(
                    produto_id=row["produto_id"],
                    produto_nome=row["produto_nome"] if row["produto_existente"] is not None else "Desconhecido",
                    quantidade=row["quantidade"],
                    preco_unitario=row["preco_unitario"],
                ))
        return list(pedidos.values())

    def listar_por_usuario(self, usuario_id):
        return self._listar_com_itens("WHERE p.usuario_id = ?", (usuario_id,))

    def listar_todos(self):
        return self._listar_com_itens()

    def existe(self, pedido_id):
        return self.db.consultar_um("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)) is not None

    def atualizar_status(self, pedido_id, novo_status):
        self.db.executar("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))

    def estatisticas_vendas(self):
        row = self.db.consultar_um("""
            SELECT COUNT(*) AS total_pedidos,
                   SUM(total) AS faturamento,
                   COUNT(CASE WHEN status = ? THEN 1 END) AS pendentes,
                   COUNT(CASE WHEN status = ? THEN 1 END) AS aprovados,
                   COUNT(CASE WHEN status = ? THEN 1 END) AS cancelados
              FROM pedidos
        """, (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO))
        return dict(row)

    def contar(self):
        return self.db.consultar_um("SELECT COUNT(*) FROM pedidos")[0]
