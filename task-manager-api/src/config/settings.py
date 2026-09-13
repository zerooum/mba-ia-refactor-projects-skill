"""Configuração lida do ambiente. Um `.env` na raiz do projeto é carregado se existir."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # src/config/settings.py -> raiz do projeto

load_dotenv(PROJECT_ROOT / '.env')

PLACEHOLDER = 'CHANGE_ME'


def _env_bool(name, default):
    return os.getenv(name, default).strip().lower() in ('1', 'true', 'yes', 'on')


def _env_list(name, default):
    value = os.getenv(name, default).strip()
    return '*' if value == '*' else [item.strip() for item in value.split(',') if item.strip()]


class Settings:
    def __init__(self):
        secret_key = os.getenv('SECRET_KEY', '')
        if not secret_key or secret_key == PLACEHOLDER:
            raise RuntimeError('SECRET_KEY não definida: copie .env.example para .env e defina um valor')

        self.SECRET_KEY = secret_key
        # instance/ na raiz (e não em src/instance/): sqlite:///tasks.db continua em instance/tasks.db
        self.INSTANCE_PATH = str(PROJECT_ROOT / 'instance')
        self.SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.DEBUG = _env_bool('DEBUG', 'false')
        self.HOST = os.getenv('HOST', '0.0.0.0')
        self.PORT = int(os.getenv('PORT', '5000'))
        self.CORS_ORIGINS = _env_list('CORS_ORIGINS', '*')
        self.MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', str(1024 * 1024)))
        self.TOKEN_MAX_AGE = int(os.getenv('TOKEN_MAX_AGE', str(8 * 60 * 60)))
