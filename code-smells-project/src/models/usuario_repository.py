from src.models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, db):
        self.db = db

    def listar(self):
        rows = self.db.consultar("SELECT * FROM usuarios")
        return [Usuario.from_row(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self.db.consultar_um("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
        return Usuario.from_row(row) if row else None

    def listar_por_email(self, email):
        rows = self.db.consultar("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,))
        return [Usuario.from_row(row) for row in rows]

    def existe_email(self, email):
        return self.db.consultar_um("SELECT 1 FROM usuarios WHERE email = ?", (email,)) is not None

    def inserir(self, nome, email, senha_hash, tipo="cliente"):
        cursor = self.db.executar(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
        return cursor.lastrowid

    def contar(self):
        return self.db.consultar_um("SELECT COUNT(*) FROM usuarios")[0]
