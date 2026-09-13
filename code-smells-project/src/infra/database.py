import sqlite3
from contextlib import contextmanager

from flask import g


class Database:
    """Uma conexão SQLite por request (em flask.g), fechada no teardown. Sem estado global."""

    def __init__(self, path):
        self.path = path

    def conectar(self):
        # isolation_level=None: autocommit; transações só onde abertas explicitamente.
        conn = sqlite3.connect(self.path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    def conexao(self):
        if "db_conn" not in g:
            g.db_conn = self.conectar()
        return g.db_conn

    def fechar(self, _exc=None):
        conn = g.pop("db_conn", None)
        if conn is not None:
            conn.close()

    def init_app(self, app):
        app.teardown_appcontext(self.fechar)

    def consultar(self, sql, params=()):
        return self.conexao().execute(sql, params).fetchall()

    def consultar_um(self, sql, params=()):
        return self.conexao().execute(sql, params).fetchone()

    def executar(self, sql, params=()):
        return self.conexao().execute(sql, params)

    @contextmanager
    def transacao(self):
        conn = self.conexao()
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        conn.execute("COMMIT")
