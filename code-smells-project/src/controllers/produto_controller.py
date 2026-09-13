from src.models.errors import NotFoundError
from src.models.produto import validar_produto


class ProdutoController:
    def __init__(self, produtos):
        self.produtos = produtos

    def listar(self):
        return self.produtos.listar()

    def buscar(self, produto_id):
        return self.produtos.buscar_por_id(produto_id)

    def pesquisar(self, termo, categoria, preco_min, preco_max):
        return self.produtos.buscar(termo, categoria, preco_min, preco_max)

    def criar(self, dados):
        return self.produtos.inserir(*validar_produto(dados))

    def atualizar(self, produto_id, dados):
        self._garantir_existe(produto_id)
        self.produtos.atualizar(produto_id, *validar_produto(dados))

    def remover(self, produto_id):
        self._garantir_existe(produto_id)
        self.produtos.remover(produto_id)

    def _garantir_existe(self, produto_id):
        if not self.produtos.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
