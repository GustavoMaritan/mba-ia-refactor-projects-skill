from src.errors import NotFoundError, ValidationError
from src.models import domain


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


class ProdutoService:
    def __init__(self, produtos):
        self.produtos = produtos

    def listar(self):
        return self.produtos.listar()

    def buscar_por_id(self, produto_id):
        produto = self.produtos.buscar_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado", sucesso=False)
        return produto

    def buscar(self, termo, categoria, preco_min, preco_max):
        return self.produtos.buscar(termo, categoria, preco_min, preco_max)

    def criar(self, dados):
        campos = self._validar(dados)
        return self.produtos.criar(**campos)

    def atualizar(self, produto_id, dados):
        if not self.produtos.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        campos = self._validar(dados)
        self.produtos.atualizar(produto_id, **campos)

    def deletar(self, produto_id):
        if not self.produtos.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        self.produtos.deletar(produto_id)

    def _validar(self, dados):
        # mesma ordem e mensagens da API original; vale para criar e atualizar
        if not dados:
            raise ValidationError("Dados inválidos")
        if "nome" not in dados:
            raise ValidationError("Nome é obrigatório")
        if "preco" not in dados:
            raise ValidationError("Preço é obrigatório")
        if "estoque" not in dados:
            raise ValidationError("Estoque é obrigatório")

        nome, preco, estoque = dados["nome"], dados["preco"], dados["estoque"]
        descricao = dados.get("descricao", "")
        categoria = dados.get("categoria", domain.CATEGORIA_PADRAO)

        if not isinstance(nome, str):
            raise ValidationError("Nome inválido")
        if not _numero(preco):
            raise ValidationError("Preço inválido")
        if not _numero(estoque):
            raise ValidationError("Estoque inválido")
        if preco < 0:
            raise ValidationError("Preço não pode ser negativo")
        if estoque < 0:
            raise ValidationError("Estoque não pode ser negativo")
        if len(nome) < domain.NOME_PRODUTO_MIN:
            raise ValidationError("Nome muito curto")
        if len(nome) > domain.NOME_PRODUTO_MAX:
            raise ValidationError("Nome muito longo")
        if categoria not in domain.CATEGORIAS_VALIDAS:
            raise ValidationError("Categoria inválida. Válidas: " + str(domain.CATEGORIAS_VALIDAS))

        return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}
