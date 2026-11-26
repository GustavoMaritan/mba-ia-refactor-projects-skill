"""Smoke test dos endpoints dos 3 projetos.

Uso:
  python scripts/smoke_test.py run <projeto> <base_url> [--out arquivo.json]
  python scripts/smoke_test.py diff <antes.json> <depois.json>

<projeto>: code-smells | ecommerce | task-manager
Só usa a stdlib. Campos voláteis (datas/timestamps) são normalizados para dar
para comparar a execução antes e depois da refatoração.
"""
import json
import os
import sys
import urllib.error
import urllib.request

VOLATILE_KEYS = {"criado_em", "created_at", "updated_at", "generated_at", "timestamp", "due_date"}

ADMIN_HEADERS = {"X-Admin-Token": os.environ.get("ADMIN_TOKEN", "")}

SCENARIOS = {
    "code-smells": [
        ("GET", "/", None),
        ("GET", "/health", None),
        ("GET", "/produtos", None),
        ("GET", "/produtos/busca?q=gamer", None),
        ("GET", "/produtos/busca?categoria=informatica&preco_min=100&preco_max=500", None),
        ("GET", "/produtos/1", None),
        ("GET", "/produtos/999", None),
        ("POST", "/produtos", {"nome": "Livro Python", "descricao": "Livro de Python", "preco": 99.9, "estoque": 5, "categoria": "livros"}),
        ("POST", "/produtos", {}),
        ("POST", "/produtos", {"nome": "X", "preco": 1, "estoque": 1}),
        ("POST", "/produtos", {"nome": "Produto", "preco": 1, "estoque": 1, "categoria": "nada"}),
        ("POST", "/produtos", {"nome": "Produto", "preco": -1, "estoque": 1}),
        ("PUT", "/produtos/11", {"nome": "Livro Python 2a ed", "descricao": "Atualizado", "preco": 120.0, "estoque": 7, "categoria": "livros"}),
        ("PUT", "/produtos/999", {"nome": "Nada", "preco": 1, "estoque": 1}),
        ("GET", "/produtos/11", None),
        ("GET", "/usuarios", None),
        ("GET", "/usuarios/1", None),
        ("GET", "/usuarios/999", None),
        ("POST", "/usuarios", {"nome": "Ana Teste", "email": "ana@teste.com", "senha": "segredo1"}),
        ("POST", "/usuarios", {"nome": "Sem email"}),
        ("POST", "/login", {"email": "admin@loja.com", "senha": "admin123"}),
        ("POST", "/login", {"email": "ana@teste.com", "senha": "segredo1"}),
        ("POST", "/login", {"email": "admin@loja.com", "senha": "errada"}),
        ("POST", "/login", {"email": "admin@loja.com"}),
        # tentativa de SQL injection no login (original deixa entrar)
        ("POST", "/login", {"email": "admin@loja.com' --", "senha": "x"}),
        ("POST", "/pedidos", {"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 1}, {"produto_id": 2, "quantidade": 2}]}),
        ("POST", "/pedidos", {"usuario_id": 3, "itens": [{"produto_id": 3, "quantidade": 1}]}),
        ("POST", "/pedidos", {"usuario_id": 2, "itens": [{"produto_id": 6, "quantidade": 999}]}),
        ("POST", "/pedidos", {"usuario_id": 2, "itens": [{"produto_id": 999, "quantidade": 1}]}),
        ("POST", "/pedidos", {"usuario_id": 2, "itens": []}),
        ("GET", "/pedidos", None),
        ("GET", "/pedidos/usuario/2", None),
        ("PUT", "/pedidos/1/status", {"status": "aprovado"}),
        ("PUT", "/pedidos/2/status", {"status": "voando"}),
        ("GET", "/relatorios/vendas", None),
        # tentativa de SQL injection na busca
        ("GET", "/produtos/busca?q=%27%20OR%20%271%27%3D%271", None),
        ("DELETE", "/produtos/11", None),
        ("DELETE", "/produtos/999", None),
        ("POST", "/admin/query", {"sql": "SELECT COUNT(*) AS n FROM produtos"}, ADMIN_HEADERS),
        ("POST", "/admin/reset-db", None, ADMIN_HEADERS),
        ("GET", "/health", None),
    ],
    "ecommerce": [
        ("POST", "/api/checkout", {"usr": "Guilherme", "eml": "gui@fullcycle.com.br", "pwd": "senhaforte", "c_id": 2, "card": "4111222233334444"}),
        ("POST", "/api/checkout", {"usr": "João", "eml": "joao@teste.com", "pwd": "123", "c_id": 1, "card": "5111222233334444"}),
        ("POST", "/api/checkout", {}),
        ("POST", "/api/checkout", {"usr": "Ana", "eml": "ana@teste.com", "pwd": "x", "c_id": 99, "card": "4111222233334444"}),
        ("POST", "/api/checkout", {"usr": "Leonan", "eml": "leonan@fullcycle.com.br", "c_id": 2, "card": "4000111122223333"}),
        ("GET", "/api/admin/financial-report", None, ADMIN_HEADERS),
        ("DELETE", "/api/users/1", None, ADMIN_HEADERS),
        ("GET", "/api/admin/financial-report", None, ADMIN_HEADERS),
    ],
    "task-manager": [
        ("GET", "/", None),
        ("GET", "/health", None),
        ("GET", "/tasks", None),
        ("GET", "/tasks/1", None),
        ("GET", "/tasks/999", None),
        ("GET", "/tasks/search?q=API", None),
        ("GET", "/tasks/search?status=pending&priority=1", None),
        ("GET", "/tasks/stats", None),
        ("POST", "/tasks", {"title": "Nova task", "description": "desc", "priority": 2, "user_id": 1, "category_id": 1, "due_date": "2030-01-01", "tags": ["a", "b"]}),
        ("POST", "/tasks", {"title": "ab"}),
        ("POST", "/tasks", {"title": "Task status", "status": "xpto"}),
        ("POST", "/tasks", {"title": "Task prioridade", "priority": 9}),
        ("POST", "/tasks", {"title": "Task user", "user_id": 999}),
        ("POST", "/tasks", {"title": "Task data", "due_date": "01-01-2030"}),
        ("PUT", "/tasks/11", {"status": "done", "tags": "x,y"}),
        ("PUT", "/tasks/11", {"priority": 0}),
        ("PUT", "/tasks/999", {"status": "done"}),
        ("GET", "/tasks/11", None),
        ("DELETE", "/tasks/11", None),
        ("DELETE", "/tasks/11", None),
        ("GET", "/users", None),
        ("GET", "/users/1", None),
        ("GET", "/users/999", None),
        ("GET", "/users/1/tasks", None),
        ("POST", "/users", {"name": "Ana", "email": "ana@email.com", "password": "segredo", "role": "user"}),
        ("POST", "/users", {"name": "Ana", "email": "ana@email.com", "password": "segredo"}),
        ("POST", "/users", {"name": "Bia", "email": "bia-invalido", "password": "segredo"}),
        ("POST", "/users", {"name": "Bia", "email": "bia@email.com", "password": "123"}),
        ("POST", "/users", {"name": "Bia", "email": "bia@email.com", "password": "segredo", "role": "root"}),
        ("PUT", "/users/4", {"name": "Ana Paula", "role": "manager"}),
        ("POST", "/login", {"email": "joao@email.com", "password": "1234"}),
        ("POST", "/login", {"email": "ana@email.com", "password": "segredo"}),
        ("POST", "/login", {"email": "joao@email.com", "password": "errada"}),
        ("POST", "/login", {"email": "joao@email.com"}),
        ("DELETE", "/users/4", None),
        ("GET", "/reports/summary", None),
        ("GET", "/reports/user/1", None),
        ("GET", "/reports/user/999", None),
        ("GET", "/categories", None),
        ("POST", "/categories", {"name": "QA", "description": "Testes", "color": "#123456"}),
        ("POST", "/categories", {"description": "sem nome"}),
        ("PUT", "/categories/5", {"name": "QA e Testes"}),
        ("PUT", "/categories/999", {"name": "x"}),
        ("DELETE", "/categories/5", None),
    ],
}


def normalize(value):
    if isinstance(value, dict):
        return {k: ("<ts>" if k in VOLATILE_KEYS and v is not None else normalize(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def call(base_url, method, path, body, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base_url + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        if v:
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status, raw = resp.status, resp.read().decode()
    except urllib.error.HTTPError as err:
        status, raw = err.code, err.read().decode()
    try:
        parsed = normalize(json.loads(raw))
    except ValueError:
        parsed = raw.strip()[:200]
    return status, parsed


def run(project, base_url, out=None):
    results = []
    for step in SCENARIOS[project]:
        method, path, body = step[:3]
        headers = step[3] if len(step) > 3 else None
        status, parsed = call(base_url, method, path, body, headers)
        results.append({"req": f"{method} {path}", "status": status, "body": parsed})
        print(f"{status}  {method} {path}")
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, ensure_ascii=False, indent=1)
    ok = sum(1 for r in results if r["status"] < 500)
    print(f"-- {ok}/{len(results)} respostas sem erro 5xx")


def diff(before_file, after_file):
    with open(before_file, encoding="utf-8") as fh:
        before = json.load(fh)
    with open(after_file, encoding="utf-8") as fh:
        after = json.load(fh)
    same = 0
    for b, a in zip(before, after):
        if b == a:
            same += 1
            continue
        print(f"DIFERENTE  {b['req']}")
        if b["status"] != a["status"]:
            print(f"   status: {b['status']} -> {a['status']}")
        if b["body"] != a["body"]:
            print(f"   antes : {json.dumps(b['body'], ensure_ascii=False)[:300]}")
            print(f"   depois: {json.dumps(a['body'], ensure_ascii=False)[:300]}")
    print(f"-- {same}/{len(before)} respostas idênticas")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "run":
        out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
        run(sys.argv[2], sys.argv[3].rstrip("/"), out)
    elif len(sys.argv) == 4 and sys.argv[1] == "diff":
        diff(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)
