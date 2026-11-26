# Análise de projeto — heurísticas

Objetivo: descobrir stack, banco, domínio, arquitetura e endpoints **a partir de evidências** do código. Nunca chute: cada item do resumo deve vir de um arquivo que você leu.

## 1. Linguagem (pelo manifesto e extensões)

| Evidência | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `*.py` | Python |
| `package.json`, `*.js`, `*.mjs`, `*.cjs` | JavaScript (Node.js) |
| `tsconfig.json`, `*.ts` | TypeScript (Node.js) |
| `pom.xml`, `build.gradle`, `*.java`, `*.kt` | Java / Kotlin |
| `go.mod`, `*.go` | Go |
| `composer.json`, `*.php` | PHP |
| `Gemfile`, `*.rb` | Ruby |
| `*.csproj`, `*.cs` | C# |

Versão: `python_requires`/`.python-version`, `engines.node`, `<java.version>`, diretiva `go` do `go.mod`. Se não houver, escreva "não declarada".

## 2. Framework e versão

Procure no manifesto/lockfile e confirme no import do entry point.

| Dependência | Framework | Como as rotas aparecem |
|---|---|---|
| `flask` | Flask | `@app.route`, `app.add_url_rule`, `Blueprint(...)` + `@bp.route` |
| `fastapi` | FastAPI | `@app.get/post`, `APIRouter` |
| `django` | Django | `urls.py` → `path(...)`, views |
| `express` | Express | `app.get/post/put/delete`, `express.Router()` |
| `fastify`, `koa`, `@nestjs/core` | Fastify / Koa / NestJS | `fastify.get`, `router.get`, `@Get()` |
| `spring-boot-starter-web` | Spring Boot | `@RestController`, `@GetMapping` |
| `laravel/framework` | Laravel | `routes/api.php` |
| `gin-gonic/gin`, `net/http` | Gin / stdlib | `r.GET`, `http.HandleFunc` |
| `rails` | Rails | `config/routes.rb` |

Versão: use a fixada (`flask==3.1.1`) ou o range (`^4.18.2`) e, se existir lockfile, a versão resolvida.

## 3. Banco de dados

| Sinal | Banco / acesso |
|---|---|
| `import sqlite3`, `sqlite3.connect`, pacote `sqlite3` (npm) | SQLite, SQL cru |
| `flask_sqlalchemy`, `sqlalchemy`, `db.Model` | SQLAlchemy ORM |
| `pg`, `psycopg2`, `mysql2`, `PyMySQL` | Postgres / MySQL, SQL cru |
| `sequelize`, `typeorm`, `prisma`, `knex`, `mongoose` | ORM/ODM Node |
| `':memory:'` | banco em memória (dados somem no restart) |

Tabelas: procure `CREATE TABLE`, `__tablename__`, classes de model, migrations, schemas. Liste todas.

## 4. Domínio

Deduza pelo vocabulário de tabelas, rotas e entidades. Ex.: `produtos/pedidos/usuarios` → e-commerce; `courses/enrollments/payments` → LMS com checkout; `tasks/categories/users` → gerenciador de tarefas. Escreva uma linha: "<tipo de sistema> (<entidades principais>)".

## 5. Classificação da arquitetura

| Classificação | Sinais |
|---|---|
| **Monolítica sem camadas** | poucos arquivos fazem tudo; SQL, regra de negócio e HTTP no mesmo módulo |
| **God Class / God File** | uma classe ou arquivo com conexão de banco + schema + seed + rotas + regra de negócio (ex.: `AppManager` com `initDb()` e `setupRoutes()`) |
| **Pseudo-camadas** | arquivos chamados `models`/`controllers`, mas `models` monta SQL e regra, `controllers` acessa banco direto ou faz `print` de notificação |
| **Parcialmente em camadas** | pastas `models/`, `routes/`, `services/` existem, mas rotas têm regra de negócio e queries, services são pouco usados, config está hardcoded |
| **Em camadas (MVC/Clean)** | config isolada, models só com dados/queries, controllers finos, services com regra, error handler central, composition root |

Justifique em uma frase com o arquivo que comprova.

## 6. Entry point e boot

- Python: arquivo com `app = Flask(__name__)` / `if __name__ == "__main__": app.run(...)`; app factory `create_app()`.
- Node: `main` e `scripts.start` do `package.json`; arquivo com `app.listen(...)`.
- Registre a porta e se ela é configurável (env) ou fixa no código.
- Registre pré-requisitos de boot (seed, migrations, variáveis).

## 7. Inventário de endpoints

Monte uma tabela `MÉTODO  ROTA  → handler (arquivo:linha)`. Comandos úteis:

```bash
# Flask
grep -rnE "@(app|[a-z_]+_bp|bp)\.route|add_url_rule" --include=*.py .
# Express
grep -rnE "(app|router)\.(get|post|put|patch|delete)\(" --include=*.js --include=*.ts . | grep -v node_modules
# FastAPI / Spring / Gin
grep -rnE "@(app|router)\.(get|post|put|delete)|@(Get|Post|Put|Delete)Mapping|\.(GET|POST|PUT|DELETE)\(" .
```

Esse inventário é o contrato que a Fase 3 precisa preservar.

## 8. Contagem

- Arquivos-fonte: só código da aplicação (sem lockfiles, deps, `.claude`, dados).
- Linhas: `wc -l` nos arquivos-fonte; arredonde com `~`.
