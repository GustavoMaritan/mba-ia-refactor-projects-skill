from src.errors import BusinessRuleError, ValidationError
from src.models import domain
from src.models.pedido_model import EstoqueInsuficiente


class PedidoService:
    def __init__(self, pedidos, produtos, notifier):
        self.pedidos = pedidos
        self.produtos = produtos
        self.notifier = notifier

    def criar(self, usuario_id, itens):
        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")
        if not itens:
            raise ValidationError("Pedido deve ter pelo menos 1 item")

        total = 0
        linhas = []
        for item in itens:
            if not isinstance(item, dict) or "produto_id" not in item or "quantidade" not in item:
                raise ValidationError("Item inválido")
            quantidade = item["quantidade"]
            if isinstance(quantidade, bool) or not isinstance(quantidade, int) or quantidade <= 0:
                # quantidade negativa aumentava o estoque
                raise ValidationError("Quantidade inválida")
            produto = self.produtos.buscar_por_id(item["produto_id"])
            if produto is None:
                raise BusinessRuleError(f"Produto {item['produto_id']} não encontrado", sucesso=False)
            if produto["estoque"] < item["quantidade"]:
                raise BusinessRuleError(f"Estoque insuficiente para {produto['nome']}", sucesso=False)
            total = total + (produto["preco"] * item["quantidade"])
            linhas.append({
                "produto_id": item["produto_id"],
                "quantidade": item["quantidade"],
                "preco_unitario": produto["preco"],
            })

        try:
            pedido_id = self.pedidos.criar(usuario_id, linhas, total)
        except EstoqueInsuficiente as e:
            nome = self.produtos.buscar_por_id(e.produto_id)["nome"]
            raise BusinessRuleError(f"Estoque insuficiente para {nome}", sucesso=False)
        self.notifier.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar(self, usuario_id=None):
        return self.pedidos.listar(usuario_id)

    def atualizar_status(self, pedido_id, status):
        if status not in domain.STATUS_PEDIDO:
            raise ValidationError("Status inválido")
        self.pedidos.atualizar_status(pedido_id, status)
        self.notifier.status_alterado(pedido_id, status)

    def relatorio_vendas(self):
        r = self.pedidos.resumo_vendas()
        faturamento = r["faturamento"]
        total_pedidos = r["total_pedidos"]
        desconto = next((faturamento * pct for limite, pct in domain.FAIXAS_DESCONTO if faturamento > limite), 0)
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": r["pendentes"],
            "pedidos_aprovados": r["aprovados"],
            "pedidos_cancelados": r["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
