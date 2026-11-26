PUBLIC_COLUMNS = "id, nome, email, tipo, criado_em"


class UsuarioModel:
    """Acesso à tabela usuarios. O hash da senha nunca sai daqui, exceto em buscar_credenciais."""

    def __init__(self, get_db):
        self._db = get_db

    def listar(self):
        rows = self._db().execute(f"SELECT {PUBLIC_COLUMNS} FROM usuarios ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def buscar_por_id(self, usuario_id):
        row = self._db().execute(f"SELECT {PUBLIC_COLUMNS} FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return dict(row) if row else None

    def buscar_credenciais(self, email):
        # o schema não tem UNIQUE em email, então pode vir mais de um
        rows = self._db().execute(
            "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ? ORDER BY id", (email,)
        ).fetchall()
        return [dict(r) for r in rows]

    def criar(self, nome, email, senha_hash, tipo="cliente"):
        db = self._db()
        with db:
            cur = db.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
        return cur.lastrowid

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
