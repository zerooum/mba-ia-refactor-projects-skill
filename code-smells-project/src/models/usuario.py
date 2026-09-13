from dataclasses import dataclass

from werkzeug.security import check_password_hash, generate_password_hash

_PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


@dataclass
class Usuario:
    id: int
    nome: str
    email: str
    senha: str  # hash, nunca texto puro
    tipo: str
    criado_em: str

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            nome=row["nome"],
            email=row["email"],
            senha=row["senha"],
            tipo=row["tipo"],
            criado_em=row["criado_em"],
        )

    def senha_confere(self, senha):
        return bool(self.senha) and eh_hash_senha(self.senha) and check_password_hash(self.senha, senha)


def gerar_hash_senha(senha):
    return generate_password_hash(senha)  # salt embutido


def eh_hash_senha(valor):
    return isinstance(valor, str) and valor.startswith(_PREFIXOS_HASH) and "$" in valor
