from contextlib import contextmanager

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


@contextmanager
def transaction(session):
    """Commit ao fim do bloco; rollback e re-raise em qualquer erro."""
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
