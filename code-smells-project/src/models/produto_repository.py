from src.models.produto import Produto


class ProdutoRepository:
    def __init__(self, db):
        self.db = db

    def listar(self):
        rows = self.db.consultar("SELECT * FROM produtos")
        return [Produto.from_row(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self.db.consultar_um("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        return Produto.from_row(row) if row else None

    def buscar(self, termo, categoria=None, preco_min=None, preco_max=None):
        sql = "SELECT * FROM produtos WHERE 1=1"
        params = []
        if termo:
            sql += " AND (nome LIKE ? OR descricao LIKE ?)"
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            sql += " AND categoria = ?"
            params.append(categoria)
        if preco_min:
            sql += " AND preco >= ?"
            params.append(preco_min)
        if preco_max:
            sql += " AND preco <= ?"
            params.append(preco_max)
        rows = self.db.consultar(sql, params)
        return [Produto.from_row(row) for row in rows]

    def inserir(self, nome, descricao, preco, estoque, categoria):
        cursor = self.db.executar(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        self.db.executar(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )

    def remover(self, produto_id):
        self.db.executar("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def contar(self):
        return self.db.consultar_um("SELECT COUNT(*) FROM produtos")[0]
