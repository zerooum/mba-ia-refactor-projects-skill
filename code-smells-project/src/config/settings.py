import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(nome, padrao):
    valor = os.getenv(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "on")


def _env_obrigatoria(nome):
    valor = os.getenv(nome, "").strip()
    if not valor:
        raise RuntimeError(
            f"Variável de ambiente {nome} não definida. Copie .env.example para .env e preencha."
        )
    return valor


class Settings:
    """Configuração lida do ambiente (e do .env, se existir). Nenhum segredo literal aqui."""

    def __init__(self):
        self.SECRET_KEY = _env_obrigatoria("SECRET_KEY")
        self.DEBUG = _env_bool("DEBUG", False)
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "5000"))
        self.DB_PATH = os.getenv("DB_PATH", "loja.db")
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
        self.AMBIENTE = os.getenv("AMBIENTE", "producao")
        # Vazio = rotas /admin/* desabilitadas (sempre 401).
        self.ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
        # Senhas dos usuários de exemplo criados no seed. Ausente = senha aleatória (login desabilitado).
        self.SEED_SENHAS = {
            "admin@loja.com": os.getenv("SEED_SENHA_ADMIN"),
            "joao@email.com": os.getenv("SEED_SENHA_JOAO"),
            "maria@email.com": os.getenv("SEED_SENHA_MARIA"),
        }
