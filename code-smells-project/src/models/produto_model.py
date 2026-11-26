class ProdutoModel:
    def __init__(self, get_db):
        self._db = get_db

    def listar(self):
        rows = self._db().execute("SELECT * FROM produtos ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def buscar_por_id(self, produto_id):
        row = self._db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return dict(row) if row else None

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        clauses, params = [], []
        if termo:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clauses.append("categoria = ?")
            params.append(categoria)
        if preco_min:
            clauses.append("preco >= ?")
            params.append(preco_min)
        if preco_max:
            clauses.append("preco <= ?")
            params.append(preco_max)
        where = " AND ".join(clauses) if clauses else "1=1"
        rows = self._db().execute(f"SELECT * FROM produtos WHERE {where} ORDER BY id", params).fetchall()
        return [dict(r) for r in rows]

    def criar(self, nome, descricao, preco, estoque, categoria):
        db = self._db()
        with db:
            cur = db.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cur.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        db = self._db()
        with db:
            db.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def deletar(self, produto_id):
        db = self._db()
        with db:
            db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
