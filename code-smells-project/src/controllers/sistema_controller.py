class SistemaController:
    def __init__(self, sistema, produtos, usuarios, pedidos):
        self.sistema = sistema
        self.produtos = produtos
        self.usuarios = usuarios
        self.pedidos = pedidos

    def contagens(self):
        self.sistema.ping()
        return {
            "produtos": self.produtos.contar(),
            "usuarios": self.usuarios.contar(),
            "pedidos": self.pedidos.contar(),
        }

    def resetar_banco(self):
        self.sistema.resetar()

    def executar_sql(self, sql):
        """Devolve (eh_select, linhas)."""
        eh_select = sql.strip().upper().startswith("SELECT")
        return eh_select, self.sistema.executar_sql(sql, eh_select)
