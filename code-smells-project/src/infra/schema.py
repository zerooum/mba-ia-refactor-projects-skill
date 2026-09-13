import logging
import secrets

from src.models.usuario import eh_hash_senha, gerar_hash_senha

log = logging.getLogger(__name__)


def init_db(db, seed_senhas):
    """Cria as tabelas e semeia dados de exemplo se o banco estiver vazio. Chamado uma vez no boot."""
    conn = db.conectar()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                descricao TEXT,
                preco REAL,
                estoque INTEGER,
                categoria TEXT,
                ativo INTEGER DEFAULT 1,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT,
                senha TEXT,
                tipo TEXT DEFAULT 'cliente',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                status TEXT DEFAULT 'pendente',
                total REAL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_pedido (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER,
                produto_id INTEGER,
                quantidade INTEGER,
                preco_unitario REAL
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM produtos")
        if cursor.fetchone()[0] == 0:
            cursor.execute("BEGIN")
            produtos = [
                ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
                ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
                ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
                ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
                ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
                ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
                ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
                ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
                ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
                ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
            ]
            cursor.executemany(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                produtos
            )

            usuarios = [
                ("Admin", "admin@loja.com", "admin"),
                ("João Silva", "joao@email.com", "cliente"),
                ("Maria Santos", "maria@email.com", "cliente"),
            ]
            usuarios = [
                (nome, email, gerar_hash_senha(seed_senhas.get(email) or secrets.token_urlsafe(32)), tipo)
                for nome, email, tipo in usuarios
            ]
            cursor.executemany(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                usuarios
            )
            cursor.execute("COMMIT")

        _migrar_senhas_texto_puro(conn)
    finally:
        conn.close()


def _migrar_senhas_texto_puro(conn):
    """Bancos criados antes do hash guardam a senha em texto puro: converte para hash, uma vez."""
    pendentes = [
        (gerar_hash_senha(row["senha"]), row["id"])
        for row in conn.execute("SELECT id, senha FROM usuarios").fetchall()
        if row["senha"] and not eh_hash_senha(row["senha"])
    ]
    if pendentes:
        conn.execute("BEGIN")
        conn.executemany("UPDATE usuarios SET senha = ? WHERE id = ?", pendentes)
        conn.execute("COMMIT")
        log.warning("%d senha(s) em texto puro convertida(s) para hash", len(pendentes))
