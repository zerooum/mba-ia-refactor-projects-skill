"""Extração de entrada HTTP: formato errado vira ValidationError (400), nunca 500."""
from flask import request

from models.errors import ValidationError


def json_body():
    """Corpo JSON como dict, ou None se vier `null`. Qualquer outro tipo é rejeitado."""
    data = request.get_json()
    if data is not None and not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def int_arg(name):
    """Query param inteiro opcional: ausente/vazio → None."""
    value = request.args.get(name, '')
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(f'Parâmetro {name} inválido') from None
