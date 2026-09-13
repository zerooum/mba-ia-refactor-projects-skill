import sqlite3

from src.models.errors import ValidationError


class SistemaRepository:
    """Operações sobre o banco inteiro: healthcheck e ferramentas administrativas."""

    def __init__(self, db):
        self.db = db

    def ping(self):
        self.db.consultar_um("SELECT 1")

    def resetar(self):
        with self.db.transacao() as conn:
            conn.execute("DELETE FROM itens_pedido")
            conn.execute("DELETE FROM pedidos")
            conn.execute("DELETE FROM produtos")
            conn.execute("DELETE FROM usuarios")

    def executar_sql(self, sql, retorna_linhas):
        # Console SQL administrativo (rota protegida por token): o erro do SQLite é a resposta útil ao admin.
        try:
            cursor = self.db.executar(sql)
            linhas = [dict(row) for row in cursor.fetchall()] if retorna_linhas else None
        except sqlite3.Error as erro:
            raise ValidationError(f"Erro na query: {erro}") from erro
        return linhas
