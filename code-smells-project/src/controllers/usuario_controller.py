from src.models.errors import ValidationError
from src.models.usuario import gerar_hash_senha


class UsuarioController:
    def __init__(self, usuarios):
        self.usuarios = usuarios

    def listar(self):
        return self.usuarios.listar()

    def buscar(self, usuario_id):
        return self.usuarios.buscar_por_id(usuario_id)

    def criar(self, dados):
        if not dados or not isinstance(dados, dict):
            raise ValidationError("Dados inválidos")

        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")
        if not all(isinstance(v, str) for v in (nome, email, senha)):
            raise ValidationError("Nome, email e senha devem ser texto")
        if self.usuarios.existe_email(email):
            raise ValidationError("Email já cadastrado")

        return self.usuarios.inserir(nome, email, gerar_hash_senha(senha))

    def autenticar(self, dados):
        """Devolve o usuário autenticado ou None."""
        if not dados or not isinstance(dados, dict):
            raise ValidationError("Dados inválidos")

        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")
        if not isinstance(email, str) or not isinstance(senha, str):
            raise ValidationError("Email e senha devem ser texto")

        # Bancos antigos podem ter email duplicado: vale o primeiro cuja senha confere, como antes.
        for usuario in self.usuarios.listar_por_email(email):
            if usuario.senha_confere(senha):
                return usuario
        return None
