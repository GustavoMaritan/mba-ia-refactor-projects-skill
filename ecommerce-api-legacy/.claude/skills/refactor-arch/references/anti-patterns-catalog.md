# Catálogo de anti-patterns

Cada item tem: severidade padrão, sinais de detecção (agnósticos + exemplos por stack), por que é problema e a transformação do playbook que resolve (`T#` em `refactoring-playbook.md`).

Severidades:
- **CRITICAL** — falha grave de segurança ou arquitetura que expõe dados, permite ataque ou torna o sistema impossível de evoluir.
- **HIGH** — violação forte de MVC/SOLID que trava manutenção e testes.
- **MEDIUM** — padronização, duplicação, performance moderada, validação.
- **LOW** — legibilidade, nomes, constantes mágicas, código morto.

Índice:

| ID | Anti-pattern | Severidade |
|---|---|---|
| AP01 | Credenciais e segredos hardcoded | CRITICAL |
| AP02 | SQL Injection (query montada com concatenação) | CRITICAL |
| AP03 | God Class / God File | CRITICAL |
| AP04 | Endpoint administrativo perigoso sem autenticação | CRITICAL |
| AP05 | Senha sem hash ou com hash fraco | CRITICAL |
| AP06 | Exposição de dados sensíveis (resposta ou log) | CRITICAL / HIGH |
| AP07 | Regra de negócio no controller/rota (Fat Controller) | HIGH |
| AP08 | Estado global mutável / conexão singleton global | HIGH |
| AP09 | Acoplamento forte, sem injeção de dependência | HIGH |
| AP10 | Escrita em várias etapas sem transação / integridade | HIGH |
| AP11 | Configuração insegura de execução (debug, CORS aberto) | HIGH |
| AP12 | Callback hell / aninhamento profundo de I/O | MEDIUM |
| AP13 | Consultas N+1 | MEDIUM |
| AP14 | Código duplicado (validação, serialização, regra) | MEDIUM |
| AP15 | Validação de entrada ausente ou inconsistente | MEDIUM |
| AP16 | Tratamento de erro espalhado / exceções engolidas | MEDIUM |
| AP17 | Uso de APIs deprecated | MEDIUM |
| AP18 | Efeitos colaterais acoplados ao fluxo (notificação inline) | MEDIUM |
| AP19 | Números e strings mágicos | LOW |
| AP20 | Nomes ruins / abreviações obscuras | LOW |
| AP21 | Imports não usados e código morto | LOW |
| AP22 | `print`/`console.log` como sistema de log | LOW |
| AP23 | Condicionais aninhadas no lugar de expressão simples | LOW |

---

## AP01 — Credenciais e segredos hardcoded · CRITICAL
**Sinais:** literais atribuídos a chaves como `SECRET_KEY`, `password`, `pass`, `dbPass`, `api_key`, `token`, `paymentGatewayKey`, `pk_live_`, `sk_live_`, strings de conexão com usuário/senha; objetos `config = {...}` com segredos no código.
```bash
grep -rnEi "(secret|passw|pwd|pass|api_?key|token|gateway)[a-z_]*\"?\s*[:=]\s*['\"][^'\"]+['\"]" --include=*.py --include=*.js --include=*.ts .
```
**Por quê:** vai para o git, vale para todos os ambientes, não dá para rotacionar sem deploy.
**Resolve:** T1 (config via env) — segredo sem valor padrão no código; em dev, gerar valor aleatório ou exigir `.env` fora do git.

## AP02 — SQL Injection · CRITICAL
**Sinais:** SQL montado com `+`, f-string, `%`, template literal ou `.format` com dado vindo de request: `"... WHERE id = " + str(id)`, `f"... '{email}'"`, `` `... ${id}` ``. Inclui LIKE com termo concatenado e `ORDER BY` dinâmico.
```bash
grep -rnE "execute\(.*(\+|%|f\"|\.format)|\"(SELECT|INSERT|UPDATE|DELETE)[^\"]*\"\s*\+" --include=*.py .
grep -rnE "(query|run|get|all|exec)\(\s*\`[^\`]*\\$\{" --include=*.js --include=*.ts .
```
**Por quê:** permite bypass de login (`' --`), leitura e destruição de dados.
**Resolve:** T2 (queries parametrizadas / ORM).

## AP03 — God Class / God File · CRITICAL
**Sinais:** um arquivo/classe com mais de uma destas responsabilidades: abrir conexão, criar schema, seed, registrar rotas, regra de negócio, formatação de resposta. Ex.: classe `AppManager` com `initDb()` + `setupRoutes()`; `models.py` com 300+ linhas fazendo SQL + cálculo de desconto + montagem de pedidos.
**Por quê:** impossível testar ou mudar uma parte sem tocar nas outras; viola SRP.
**Resolve:** T3 (extrair models/repositories) + T4 (services) + T5 (controllers/rotas).

## AP04 — Endpoint administrativo perigoso sem autenticação · CRITICAL
**Sinais:** rotas como `/admin/query` que executam SQL recebido no body, `/admin/reset-db`, `DELETE` em massa, `eval`/`exec`, relatórios financeiros abertos, sem checagem de auth/role.
**Por quê:** qualquer pessoa na rede lê ou apaga o banco.
**Resolve:** T6b (middleware de autorização) — exigir token de admin vindo de config; desabilitado por padrão quando o token não está configurado.

## AP05 — Senha sem hash ou com hash fraco · CRITICAL
**Sinais:** senha gravada como veio (`INSERT ... senha`), comparação `WHERE senha = ?`, `hashlib.md5`/`sha1` sem salt, função caseira (`base64` repetido, `badCrypto`), senha padrão fixa (`p || "123456"`).
**Por quê:** vazamento do banco expõe senhas reais; MD5 quebra em segundos.
**Resolve:** T9 (hash com algoritmo adaptativo: `werkzeug.security`/`bcrypt`/`argon2` em Python, `crypto.scrypt`/`bcrypt` em Node).

## AP06 — Exposição de dados sensíveis · CRITICAL (segredo/senha) ou HIGH (dados pessoais)
**Sinais:** `to_dict()`/serializers que incluem `password`/`senha`; health check devolvendo `secret_key`, `db_path`, `debug`; logs com número de cartão, chave de gateway, senha, e-mail em claro; `str(e)` de exceção do banco devolvido ao cliente.
**Por quê:** vaza credenciais e dados de cartão (PCI) para clientes e para o log.
**Resolve:** T14 (serialização explícita sem campos sensíveis) + T6 (erro genérico ao cliente, detalhe só no log) + mascarar dados no log.

## AP07 — Regra de negócio no controller/rota (Fat Controller) · HIGH
**Sinais:** handler HTTP com cálculo de total, desconto, estoque, status, overdue, regras de permissão, laços sobre resultados do banco, mais de ~30 linhas; queries ORM/SQL direto dentro da rota.
**Por quê:** regra presa ao HTTP não é reaproveitada nem testada isoladamente; duplica entre rotas.
**Resolve:** T4 (service layer) + T5 (controller fino).

## AP08 — Estado global mutável / conexão singleton global · HIGH
**Sinais:** `global db_connection`, `let globalCache = {}`, `let totalRevenue = 0` exportado, listas de módulo usadas como "banco", conexão SQLite compartilhada com `check_same_thread=False`.
**Por quê:** condições de corrida entre requisições, testes que vazam estado, impossível trocar implementação.
**Resolve:** T7 (composition root / DI) — conexão por requisição (ou pool) gerenciada pela app; caches como objetos injetados.

## AP09 — Acoplamento forte, sem injeção de dependência · HIGH
**Sinais:** handlers que fazem `new sqlite3.Database(...)`, `smtplib.SMTP(...)`, `NotificationService()` instanciado dentro da função; módulos importando a conexão global; rotas chamando o banco diretamente.
**Por quê:** não dá para substituir por fake em teste nem trocar infraestrutura.
**Resolve:** T7.

## AP10 — Escrita em várias etapas sem transação / integridade · HIGH
**Sinais:** pedido + itens + baixa de estoque em `execute` separados sem rollback; matrícula + pagamento + auditoria em callbacks sem `BEGIN/COMMIT`; `DELETE` de pai deixando filhos órfãos (o próprio código às vezes admite: "ficaram sujos no banco").
**Por quê:** falha no meio deixa o banco inconsistente (estoque baixado sem pedido, pagamento sem matrícula).
**Resolve:** T10 (transação no service) + cascata explícita.

## AP11 — Configuração insegura de execução · HIGH
**Sinais:** `debug=True`/`app.config["DEBUG"] = True` junto com `host="0.0.0.0"` (expõe o debugger do Werkzeug = execução remota de código); `CORS(app)` liberando qualquer origem em API com dados sensíveis; porta fixa no código.
**Resolve:** T1 (debug e origens via env, padrão seguro).

## AP12 — Callback hell / aninhamento profundo de I/O · MEDIUM
**Sinais (JS):** 3+ níveis de callbacks de banco aninhados, contadores manuais (`pending--`) para saber quando responder, `res.json` dentro do callback mais interno; erros de callback ignorados (`(err, row) =>` sem checar `err`).
**Por quê:** ordem de execução imprevisível, erros perdidos, resposta duplicada ou nunca enviada.
**Resolve:** T12 (promisificar + `async/await` + `Promise.all`).

## AP13 — Consultas N+1 · MEDIUM
**Sinais:** query dentro de laço sobre resultado de outra query (`for row in rows: cursor.execute(... row["id"])`, `User.query.get(t.user_id)` dentro de loop, `len(u.tasks)` com lazy load, `forEach` com `db.get`).
**Por quê:** 1 + N idas ao banco; degrada linearmente com o volume.
**Resolve:** T8 (JOIN, `IN (...)`, eager loading, agregação `GROUP BY`).

## AP14 — Código duplicado · MEDIUM
**Sinais:** mesmo bloco de serialização copiado em várias funções; mesma validação em criar/atualizar; mesmo cálculo (ex.: "está atrasada?") repetido em várias rotas; listas de valores válidos repetidas.
**Resolve:** T4/T14 (um ponto de verdade: método no model, serializer, validador compartilhado) + T13 (constantes).

## AP15 — Validação de entrada ausente ou inconsistente · MEDIUM
**Sinais:** tipos não checados (`preco < 0` com string → 500), `request.get_json()` usado sem checar `None`, campos obrigatórios só em uma das rotas, regras diferentes entre criar e atualizar, e-mail sem validação, sem limite de tamanho.
**Resolve:** T15 (validação na borda com mensagens previsíveis; 400 em vez de 500).

## AP16 — Tratamento de erro espalhado / exceções engolidas · MEDIUM
**Sinais:** `try/except Exception` copiado em todo handler devolvendo `str(e)`; `except:` sem tipo; callbacks que ignoram `err`; respostas de erro com formatos diferentes.
**Resolve:** T6 (error handler centralizado + exceções de domínio).

## AP17 — Uso de APIs deprecated · MEDIUM
Verifique a versão detectada na Fase 1 e procure os padrões abaixo. Reporte a API, a linha e o equivalente moderno.

| Stack | Deprecated | Equivalente moderno |
|---|---|---|
| Python ≥ 3.12 | `datetime.utcnow()` / `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` / `datetime.fromtimestamp(ts, timezone.utc)` |
| SQLAlchemy ≥ 2.0 / Flask-SQLAlchemy ≥ 3 | `Model.query.get(id)` (Legacy Query API) | `db.session.get(Model, id)` |
| SQLAlchemy ≥ 2.0 | `Model.query.filter_by(...).all()` em código novo | `db.session.execute(db.select(Model).filter_by(...)).scalars().all()` |
| Flask ≥ 2.3 | `@app.before_first_request`, `flask.json.JSONEncoder`, `app.json_encoder` | código no app factory, `app.json` provider |
| Flask ≥ 2.2 | `send_file(..., attachment_filename=)` | `download_name=` |
| Python | `imp`, `distutils`, `asyncio.get_event_loop()` fora de loop | `importlib`, `setuptools`/`packaging`, `asyncio.run()` |
| Python sqlite3 ≥ 3.12 | adaptadores padrão de `datetime` | registrar adaptadores explícitos ou gravar ISO string |
| Node.js | `new Buffer()` | `Buffer.from()` / `Buffer.alloc()` |
| Node.js | `url.parse()`, `querystring` | `new URL()`, `URLSearchParams` |
| Node.js | `fs.exists()`, `util.isArray()` etc. | `fs.access()`/`fs.existsSync()`, `Array.isArray()` |
| Node.js | `crypto.createCipher()` | `crypto.createCipheriv()` |
| Express 4 → 5 | `body-parser` separado, `req.param()`, `res.send(status)`, `res.json(status, obj)`, `app.del()` | `express.json()`, `req.params/query/body`, `res.status(s).send()`, `app.delete()` |
| Express | `res.sendfile()` | `res.sendFile()` |
| JS | `var` + callbacks em código novo (não deprecated formal, mas legado) | `const/let` + `async/await` |

```bash
grep -rnE "utcnow\(|\.query\.get\(|before_first_request|attachment_filename" --include=*.py .
grep -rnE "new Buffer\(|url\.parse\(|fs\.exists\(|createCipher\(|req\.param\(|bodyParser" --include=*.js --include=*.ts . | grep -v node_modules
```
**Resolve:** T11.

## AP18 — Efeitos colaterais acoplados ao fluxo · MEDIUM
**Sinais:** "envio" de e-mail/SMS/push com `print` dentro do controller após salvar; SMTP síncrono dentro do request; credenciais SMTP no serviço.
**Resolve:** T4 — mover para um serviço de notificação injetado (interface), chamado pelo service de domínio.

## AP19 — Números e strings mágicos · LOW
**Sinais:** `if faturamento > 10000: desconto = faturamento * 0.1`, `priority <= 2`, `range(10000)`, listas de status/categorias/roles literais repetidas, porta `5000`/`3000` fixa.
**Resolve:** T13 (constantes nomeadas / enums em um módulo de domínio).

## AP20 — Nomes ruins / abreviações obscuras · LOW
**Sinais:** `u`, `e`, `p`, `cc`, `cid`, `usr`, `eml`, `pwd`, `d`, `x`, `badCrypto`, `AppManager`, `cursor2`/`cursor3`, funções com nome que não diz o que fazem.
**Resolve:** renomear internamente (mantendo os nomes dos campos do contrato HTTP).

## AP21 — Imports não usados e código morto · LOW
**Sinais:** `import os, sys, json, time` sem uso; funções utilitárias nunca chamadas; variáveis exportadas e não usadas (`totalRevenue`); métodos de validação no model que ninguém chama.
**Resolve:** remover; quando a função for útil, passar a usá-la no lugar da duplicação.

## AP22 — `print`/`console.log` como sistema de log · LOW
**Sinais:** `print("ERRO: " + str(e))`, `console.log` espalhados, banners no boot.
**Resolve:** `logging`/logger estruturado configurado no composition root, com nível por ambiente.

## AP23 — Condicionais aninhadas no lugar de expressão simples · LOW
**Sinais:** `if x: if y: if z: return True else: return False` (escada de 3+ níveis para um booleano), `if cond: return True else: return False`.
**Resolve:** guard clauses / expressão booleana direta (`return a and b and not c`).

---

## Como decidir a severidade em casos de dúvida
- Afeta segurança de dados ou permite ataque → CRITICAL.
- Impede testar/trocar uma camada ou mistura responsabilidades de camadas diferentes → HIGH.
- Funciona, mas custa performance, consistência ou manutenção → MEDIUM.
- Só legibilidade → LOW.
