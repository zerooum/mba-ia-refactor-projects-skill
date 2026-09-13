# (faturamento mínimo, taxa) — da maior faixa para a menor
FAIXAS_DESCONTO = (
    (10_000, 0.10),
    (5_000, 0.05),
    (1_000, 0.02),
)


def calcular_desconto(faturamento):
    for minimo, taxa in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * taxa
    return 0


class RelatorioController:
    def __init__(self, pedidos):
        self.pedidos = pedidos

    def vendas(self):
        stats = self.pedidos.estatisticas_vendas()
        total_pedidos = stats["total_pedidos"]
        faturamento = stats["faturamento"]
        if faturamento is None:
            faturamento = 0
        desconto = calcular_desconto(faturamento)

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": stats["pendentes"],
            "pedidos_aprovados": stats["aprovados"],
            "pedidos_cancelados": stats["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
