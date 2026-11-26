class EstoqueInsuficiente(Exception):
    def __init__(self, produto_id):
        super().__init__(produto_id)
        self.produto_id = produto_id


class PedidoModel:
    def __init__(self, get_db):
        self._db = get_db

    def criar(self, usuario_id, itens, total):
        """Grava pedido, itens e baixa de estoque numa transação só.

        itens: lista de dicts com produto_id, quantidade e preco_unitario.
        """
        db = self._db()
        with db:
            cur = db.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                (usuario_id, total),
            )
            pedido_id = cur.lastrowid
            db.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                [(pedido_id, i["produto_id"], i["quantidade"], i["preco_unitario"]) for i in itens],
            )
            for i in itens:
                # baixa condicional: se outro pedido levou o estoque antes, desfaz tudo
                cur = db.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (i["quantidade"], i["produto_id"], i["quantidade"]),
                )
                if cur.rowcount == 0:
                    raise EstoqueInsuficiente(i["produto_id"])
        return pedido_id

    def listar(self, usuario_id=None):
        # 2 queries no total (pedidos + itens com JOIN), em vez de 1 + N + N*M
        where, params = ("WHERE p.usuario_id = ?", (usuario_id,)) if usuario_id is not None else ("", ())
        db = self._db()
        pedidos = db.execute(
            f"SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em FROM pedidos p {where} ORDER BY p.id",
            params,
        ).fetchall()
        itens = db.execute(
            f"""SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
                       pr.id AS produto_existe, pr.nome AS produto_nome
                FROM itens_pedido i
                JOIN pedidos p ON p.id = i.pedido_id
                LEFT JOIN produtos pr ON pr.id = i.produto_id
                {where}
                ORDER BY i.id""",
            params,
        ).fetchall()

        por_pedido = {}
        for i in itens:
            por_pedido.setdefault(i["pedido_id"], []).append({
                "produto_id": i["produto_id"],
                "produto_nome": i["produto_nome"] if i["produto_existe"] is not None else "Desconhecido",
                "quantidade": i["quantidade"],
                "preco_unitario": i["preco_unitario"],
            })
        return [dict(p) | {"itens": por_pedido.get(p["id"], [])} for p in pedidos]

    def atualizar_status(self, pedido_id, status):
        db = self._db()
        with db:
            db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))

    def resumo_vendas(self):
        row = self._db().execute(
            """SELECT COUNT(*) AS total_pedidos,
                      COALESCE(SUM(total), 0) AS faturamento,
                      COALESCE(SUM(status = 'pendente'), 0) AS pendentes,
                      COALESCE(SUM(status = 'aprovado'), 0) AS aprovados,
                      COALESCE(SUM(status = 'cancelado'), 0) AS cancelados
               FROM pedidos"""
        ).fetchone()
        return dict(row)

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
