# Skill `refactor-arch` — auditoria e refatoração arquitetural

Skill do Claude Code que analisa um projeto backend, audita anti-patterns com arquivo e linha, gera um relatório e, depois de confirmação, refatora o projeto para MVC validando que a API continua respondendo igual.

- Skill: `code-smells-project/.claude/skills/refactor-arch/` (cópias idênticas em `ecommerce-api-legacy/` e `task-manager-api/`)
- Relatórios da Fase 2: `reports/audit-project-1.md`, `reports/audit-project-2.md`, `reports/audit-project-3.md`
- Evidência de validação (respostas antes/depois e diffs): `reports/validation/`
- Smoke test usado na validação: `scripts/smoke_test.py`

O enunciado original do desafio está no repositório base: https://github.com/devfullcycle/mba-ia-refactor-projects-skill

---

## A) Análise manual

Feita lendo o código original antes de escrever a skill. Linhas referem-se aos arquivos **originais** (commit inicial).

### Projeto 1 — code-smells-project (Python/Flask, e-commerce)

| # | Severidade | Problema | Local | Justificativa |
|---|---|---|---|---|
| 1 | CRITICAL | SQL Injection em quase todas as queries | models.py:28, 47-50, 57-61, 109-111, 126-129, 280, 289-297 | Concatenação de dados do request. Testei: `{"email": "admin@loja.com' --", "senha": "x"}` em `/login` entrava como admin (status 200 na baseline) |
| 2 | CRITICAL | Console SQL e reset do banco abertos | app.py:47-57, app.py:59-78 | `/admin/query` executa qualquer SQL do body e `/admin/reset-db` apaga tudo, sem autenticação |
| 3 | CRITICAL | Segredo hardcoded e exposto | app.py:7, controllers.py:285-289 | `SECRET_KEY` literal e devolvida pelo `/health` junto com `debug` e `db_path` |
| 4 | CRITICAL | Senha em texto puro e devolvida pela API | database.py:75-79, models.py:126-129, models.py:83, models.py:99 | Seed e cadastro gravam a senha como veio; `GET /usuarios` lista as senhas |
| 5 | HIGH | Debug ligado em 0.0.0.0 | app.py:8, app.py:88 | Debugger do Werkzeug acessível na rede = execução remota de código |
| 6 | HIGH | Conexão SQLite global compartilhada entre threads | database.py:4-11 | `global db_connection` + `check_same_thread=False`; estado mutável global sem controle de transação |
| 7 | HIGH | Pedido sem transação e com corrida de estoque | models.py:133-169 | Valida estoque, depois insere pedido/itens e baixa estoque em `execute` separados; quantidade negativa aumenta o estoque |
| 8 | MEDIUM | N+1 e duplicação na listagem de pedidos | models.py:171-201, models.py:203-233 | 1 + N + N×M queries; as duas funções são cópias |
| 9 | MEDIUM | Notificações com `print` dentro do controller | controllers.py:208-210, controllers.py:247-250 | Efeito colateral acoplado ao fluxo HTTP |
| 10 | MEDIUM | Validação de tipo ausente | controllers.py:43-46, controllers.py:169-170 | `preco: "abc"` vira 500; login sem body vira 500 |
| 11 | LOW | Números mágicos no desconto | models.py:256-262 | Faixas 10000/5000/1000 e percentuais soltos no código |
| 12 | LOW | Imports não usados / `print` como log | database.py:2, models.py:2, controllers.py:8-11 | `os` e `sqlite3` sem uso; logs com `print` |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

| # | Severidade | Problema | Local | Justificativa |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais e chave de gateway hardcoded | src/utils.js:1-7 | `dbPass` e `paymentGatewayKey: "pk_live_..."` no código |
| 2 | CRITICAL | Número do cartão e chave logados | src/AppManager.js:45 | `console.log` com cartão completo e chave (PCI) |
| 3 | CRITICAL | Hash de senha caseiro + senha padrão | src/utils.js:17-23, src/AppManager.js:68, src/AppManager.js:18 | `badCrypto` só repete 2 caracteres do base64; sem `pwd` a senha vira "123456"; seed em claro |
| 4 | CRITICAL | God Class | src/AppManager.js:4-139 | Uma classe abre o banco, cria schema, faz seed, registra rotas e tem toda a regra |
| 5 | HIGH | Escrita multi-etapa sem transação e órfãos | src/AppManager.js:50-62, src/AppManager.js:131-137 | Matrícula/pagamento/auditoria sem `BEGIN/COMMIT`; DELETE deixa matrículas e pagamentos (a própria resposta admite) |
| 6 | HIGH | Estado global mutável | src/utils.js:9-10 | `globalCache` cresce sem limite; `totalRevenue` exportado |
| 7 | MEDIUM | Callback hell + N+1 no relatório | src/AppManager.js:80-129 | Contadores manuais `coursesPending--`; 1 + cursos + 2×matrículas queries; ordem dos alunos não determinística |
| 8 | MEDIUM | Request malformado derruba o processo | src/AppManager.js:46 | `card` numérico → `cc.startsWith` lança dentro do callback do sqlite, sem captura |
| 9 | MEDIUM | Erros ignorados | src/AppManager.js:57, src/AppManager.js:92, src/AppManager.js:133-135 | `err` não checado; DELETE responde sucesso mesmo com erro |
| 10 | LOW | Nomes ruins | src/AppManager.js:29-33, src/utils.js:17 | `u, e, p, cid, cc`, `badCrypto` |
| 11 | LOW | Código morto e mágicos | src/AppManager.js:2, src/utils.js:19, src/AppManager.js:46 | `totalRevenue` importado e não usado; `10000`, prefixo `"4"` |

### Projeto 3 — task-manager-api (Python/Flask + SQLAlchemy, gerenciador de tarefas)

| # | Severidade | Problema | Local | Justificativa |
|---|---|---|---|---|
| 1 | CRITICAL | Senha com MD5 sem salt | models/user.py:27-32 | Reversível por rainbow table |
| 2 | CRITICAL | Hash da senha nas respostas | models/user.py:21 (usado em routes/user_routes.py:33, 85, 129, 209) | `to_dict()` devolve `password` em GET/POST/PUT `/users` e no `/login` |
| 3 | CRITICAL | Segredos hardcoded | app.py:13, services/notification_service.py:7-10 | `SECRET_KEY` e senha SMTP literais |
| 4 | HIGH | Debug em 0.0.0.0 | app.py:34 | Debugger exposto |
| 5 | HIGH | Regra de negócio e queries nas rotas | routes/report_routes.py:12-101, routes/task_routes.py:85-154 | `services/` existe mas não é usado; relatório com 13 queries dentro da rota |
| 6 | HIGH | DELETE de categoria deixa tasks órfãs | routes/report_routes.py:211-223 | `category_id` fica apontando para registro inexistente |
| 7 | MEDIUM | N+1 | routes/task_routes.py:41-57, routes/user_routes.py:22, routes/report_routes.py:55-56, routes/report_routes.py:163 | Query por task/usuário/categoria dentro de laço |
| 8 | MEDIUM | APIs deprecated | models/task.py:15-16, routes/task_routes.py:42, 67 (e outras) | `datetime.utcnow()` (Python 3.12) e `Query.get()` (SQLAlchemy 2.x) |
| 9 | MEDIUM | Regra de "atrasada" duplicada 6× | routes/task_routes.py:30-39, 71-80, 283-287; routes/user_routes.py:171-180; routes/report_routes.py:33-37, 132-135 | `Task.is_overdue()` (models/task.py:50-60) existe e ninguém usa |
| 10 | MEDIUM | `except:` sem tipo | routes/task_routes.py:62, 137, 204, 236 | Engole a causa e não loga |
| 11 | LOW | Imports e código morto | app.py:7, routes/task_routes.py:7, utils/helpers.py:57-116 | `os, sys, json, time` sem uso; `process_task_data` e constantes nunca usados |
| 12 | LOW | Números mágicos | routes/report_routes.py:24-28, routes/report_routes.py:45 | `p1..p5` por prioridade, `7` dias |

---

## B) Construção da skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                              # prompt: 3 fases, formatos de saída, pausa obrigatória
└── references/
    ├── project-analysis.md               # heurísticas de linguagem, framework, banco, arquitetura, endpoints
    ├── anti-patterns-catalog.md          # 23 anti-patterns com sinais de detecção e severidade
    ├── audit-report-template.md          # formato do relatório
    ├── mvc-guidelines.md                 # camadas, direção de dependências, árvore-alvo por stack
    └── refactoring-playbook.md           # 15 transformações com antes/depois em Python e JS
```

### Decisões de design

- **SKILL.md curto e procedural, conhecimento nas referências.** O SKILL.md diz o que fazer em cada fase e qual referência ler naquele momento (progressive disclosure): a Fase 1 só carrega `project-analysis.md`, a Fase 2 carrega catálogo + template, a Fase 3 carrega guidelines + playbook.
- **Description como gatilho.** Diz o que a skill faz, quando usar (`/refactor-arch`, "refatorar para MVC", auditoria, code smells) e quando não usar (bug isolado, feature nova).
- **Saídas com formato fixo.** Os blocos `PHASE 1`, relatório e `PHASE 3` têm layout definido, para o resultado ser comparável entre projetos e fácil de checar.
- **Pausa explícita.** A Fase 2 termina com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e a instrução "PARE AQUI". O único arquivo que pode ser escrito antes da resposta é o relatório. Em execução não interativa a skill encerra após o relatório (a menos que receba `--yes`).
- **Linhas exatas.** A skill manda ler os arquivos com numeração e reler o trecho antes de escrever o número; cada finding traz uma evidência (trecho citado) para facilitar a conferência.
- **Contrato HTTP como critério de sucesso.** A Fase 3 começa com uma baseline (sobe a app original e chama todos os endpoints) e termina repetindo as mesmas chamadas. Diferenças só são aceitas se forem correções de segurança/integridade listadas no resumo.
- **Projetos já organizados.** As guidelines dizem para preservar o que está correto e mover só o que viola as camadas (caso do projeto 3, que manteve `models/`, `routes/` e `services/` na raiz e ganhou `config/`, `controllers/`, `middlewares/` e app factory).

### Catálogo de anti-patterns (23)

| Severidade | Itens | Por que entraram |
|---|---|---|
| CRITICAL (6) | AP01 segredos hardcoded, AP02 SQL injection, AP03 God Class, AP04 admin sem auth, AP05 senha sem hash/fraca, AP06 exposição de dados sensíveis | São os problemas que expõem dados ou impedem qualquer evolução; os três projetos têm vários deles |
| HIGH (5) | AP07 fat controller, AP08 estado global, AP09 sem DI, AP10 sem transação/órfãos, AP11 debug/CORS inseguro | Violações de MVC/SOLID que travam teste e manutenção |
| MEDIUM (7) | AP12 callback hell, AP13 N+1, AP14 duplicação, AP15 validação, AP16 erro espalhado, **AP17 APIs deprecated**, AP18 efeito colateral inline | Performance, consistência e manutenção |
| LOW (5) | AP19 mágicos, AP20 nomes, AP21 código morto, AP22 print/console.log, AP23 condicionais aninhadas | Legibilidade |

O AP17 traz uma tabela de APIs deprecated com o equivalente moderno (Python 3.12 `datetime.utcnow`, SQLAlchemy 2 `Query.get`, Flask 2.x/3.x, Node `new Buffer`/`url.parse`/`fs.exists`, Express 4→5) e comandos `grep` para encontrar cada uma.

### Agnosticismo de tecnologia

- Sinais de detecção descritos pelo conceito ("query montada com dado do request", "query dentro de laço") e só depois exemplificados por stack.
- `project-analysis.md` mapeia manifestos e frameworks de Python, Node, Java, Go, PHP, Ruby e C#, e traz padrões de rota de Flask, FastAPI, Django, Express, NestJS, Spring, Laravel, Gin e Rails.
- `mvc-guidelines.md` define as responsabilidades de cada camada de forma neutra e dá a árvore-alvo para Flask, Express e, resumidamente, Spring/Laravel/Go.
- O playbook mostra cada transformação em Python **e** JavaScript.
- A prova prática foi rodar a mesma skill, sem alteração, em Flask com SQL cru, Express com callbacks e Flask com SQLAlchemy.

### Desafios encontrados

- **Escrita do relatório fora do diretório do projeto.** Na primeira execução não interativa, a escrita em `../reports/` foi bloqueada pelas permissões. Adicionei o argumento `--report <caminho>` e a regra "se a escrita for negada, imprima o relatório e siga para a pergunta, sem tentar outro caminho".
- **Findings LOW resumidos.** Na primeira rodada do projeto 3 os LOW vieram agrupados num bloco só, sem arquivo:linha por item. Acrescentei ao SKILL.md que todo finding tem bloco completo, e na segunda rodada todos vieram no formato.
- **Bloco da Fase 1 no relatório.** No modo `-p` só a última mensagem aparece; passei a exigir que o arquivo salvo comece com o bloco da Fase 1.
- **Preservar contrato com correções de segurança.** Ex.: remover a senha da resposta muda o JSON. A regra ficou: diferença só por segurança/integridade e sempre listada.
- **Ordem não determinística no Node.** O relatório financeiro original monta a lista de alunos na ordem em que os callbacks terminam (rodando duas vezes saiu em ordens diferentes). Na refatoração a ordem passou a ser explícita (`ORDER BY c.id, e.id`).

### Como a skill foi executada

Usei o Claude Code. As fases 1 e 2 rodaram em cada projeto com a skill copiada para dentro dele:

```bash
cd code-smells-project && claude -p "/refactor-arch --report ../reports/audit-project-1.md"
cd ecommerce-api-legacy && claude -p "/refactor-arch --report ../reports/audit-project-2.md"
cd task-manager-api   && claude -p "/refactor-arch --report ../reports/audit-project-3.md"
```

Em modo não interativo a skill para na pergunta `Proceed with refactoring (Phase 3)? [y/n]`, como previsto (os três relatórios terminam nessa linha). A Fase 3 foi feita na sessão interativa, seguindo o SKILL.md: baseline dos endpoints, refatoração camada por camada pelo playbook, validação com o mesmo smoke test e nova varredura do catálogo.

---

## C) Resultados

### Findings por severidade (Fase 2)

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Deprecated |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | 6 | 6 | 5 | 5 | **22** | nenhuma (verificado) |
| 2 — ecommerce-api-legacy | 5 | 4 | 6 | 4 | **19** | nenhuma (verificado) |
| 3 — task-manager-api | 4 | 4 | 5 | 5 | **18** | `datetime.utcnow` e `Query.get` |

No projeto 1, os 12 itens da análise manual aparecem no relatório da skill (AP02, AP04, AP01/AP06, AP05, AP11, AP08, AP10, AP13/AP14, AP18, AP15, AP19, AP21/AP22).

### Antes / depois da estrutura

**Projeto 1**
```
ANTES                         DEPOIS
app.py  (rotas + SQL admin)   app.py                      # entry point
controllers.py                src/app.py                  # create_app (composition root)
models.py  (SQL + regra)      src/config/settings.py
database.py (global + seed)   src/database.py             # conexão por request, schema, seed
                              src/errors.py
                              src/models/      produto_model, usuario_model, pedido_model, domain
                              src/services/    produto, usuario, pedido, admin, notification
                              src/controllers/ produto, usuario, pedido, admin
                              src/views/routes.py
                              src/middlewares/ error_handler.py, auth.py
```

**Projeto 2**
```
ANTES                         DEPOIS
src/app.js                    src/server.js               # entry point
src/AppManager.js (tudo)      src/app.js                  # createApp (composition root)
src/utils.js (config+cache)   src/config/index.js
                              src/database/    connection.js (promises + transação), schema.js
                              src/models/      user, course, enrollment, payment, auditLog, domain
                              src/services/    checkout, report, user, paymentGateway, memoryCache
                              src/controllers/ checkout, report, user
                              src/routes/index.js
                              src/middlewares/ errorHandler, asyncHandler, requireAdmin
                              src/lib/passwordHasher.js, src/logger.js, src/errors.js
```

**Projeto 3**
```
ANTES                                   DEPOIS
app.py (config fixa + create_all)       app.py                 # create_app (entry + composition root)
models/ (MD5, utcnow, to_dict c/ senha) config/settings.py
routes/ (regra + queries)               errors.py
services/notification (não usado)       models/ (+ constants.py)
utils/helpers.py (quase todo morto)     services/   task, user, category, report, notification, base
                                        controllers/ task, user, category, report
                                        routes/     só blueprints -> controller (categories separado)
                                        middlewares/error_handler.py
                                        utils/helpers.py (utcnow, e-mail, cor, percentual)
```

### Checklist de validação

| Item | P1 code-smells | P2 ecommerce | P3 task-manager |
|---|---|---|---|
| **Fase 1** — linguagem | ✅ Python 3.12 | ✅ JavaScript / Node 22 | ✅ Python 3.12 |
| framework | ✅ Flask 3.1.1 | ✅ Express 4.22.1 (^4.18.2) | ✅ Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 |
| domínio | ✅ e-commerce | ✅ LMS com checkout | ✅ gerenciador de tarefas |
| nº de arquivos | ✅ 4 (~780 linhas) | ✅ 3 (~180 linhas) | ✅ 15 (~1158 linhas) |
| **Fase 2** — segue o template | ✅ | ✅ | ✅ |
| arquivo + linhas exatos | ✅ (conferidos por amostragem) | ✅ | ✅ |
| ordenado CRITICAL → LOW | ✅ | ✅ | ✅ |
| ≥ 5 findings | ✅ 22 | ✅ 19 | ✅ 18 |
| APIs deprecated | ✅ verificado, nenhuma | ✅ verificado, nenhuma | ✅ 2 APIs, todas as ocorrências |
| pausa pedindo confirmação | ✅ | ✅ | ✅ |
| **Fase 3** — estrutura MVC | ✅ | ✅ | ✅ |
| config extraída (sem hardcoded) | ✅ `src/config/settings.py` | ✅ `src/config/index.js` | ✅ `config/settings.py` |
| models | ✅ | ✅ | ✅ |
| views/routes | ✅ `src/views/routes.py` | ✅ `src/routes/index.js` | ✅ `routes/` |
| controllers | ✅ | ✅ | ✅ |
| error handling centralizado | ✅ | ✅ | ✅ |
| entry point claro | ✅ `app.py` | ✅ `src/server.js` (`npm start`) | ✅ `app.py` |
| inicia sem erros | ✅ (com `-W error::DeprecationWarning`) | ✅ | ✅ (com `-W error::DeprecationWarning`) |
| endpoints originais respondem | ✅ 41/41 sem 5xx | ✅ 8/8 sem 5xx | ✅ 44/44 sem 5xx |

### Validação de endpoints (antes × depois)

`scripts/smoke_test.py` chama todos os endpoints originais com casos de sucesso e de erro, normaliza timestamps e compara as respostas (status + corpo). Arquivos completos em `reports/validation/`.

| Projeto | Chamadas | Idênticas | Diferentes (todas intencionais) |
|---|---|---|---|
| 1 | 41 | 35 | 6 |
| 2 | 8 | 5 | 3 |
| 3 | 44 | 39 | 5 |

Mudanças de comportamento intencionais:

| Projeto | Endpoint | Antes → depois | Motivo |
|---|---|---|---|
| 1 | `GET /health` | devolvia `secret_key`; `debug: true` → sem `secret_key`; `debug` reflete a config (padrão `false`) | AP01/AP06/AP11 |
| 1 | `GET /usuarios`, `GET /usuarios/<id>` | traziam `senha` → sem `senha` | AP06 |
| 1 | `POST /login` com `admin@loja.com' --` | 200 (logado como admin) → 401 | AP02 |
| 1 | `GET /produtos/busca?q=' OR '1'='1` | devolvia todos os produtos → lista vazia (termo tratado como texto) | AP02 |
| 1 | `POST /admin/query`, `POST /admin/reset-db` | abertos → exigem `X-Admin-Token` = `ADMIN_TOKEN` (403 sem token; com token, resposta igual) | AP04 |
| 1 | erros 500 | `{"erro": str(e)}` → `{"erro": "Erro interno do servidor"}` (detalhe só no log) | AP06/AP16 |
| 1 | entradas inválidas (`preco: "abc"`, item sem quantidade, quantidade ≤ 0, login sem body) | 500 ou estoque aumentando → 400 com mensagem | AP15 |
| 2 | `GET /api/admin/financial-report`, `DELETE /api/users/:id` | abertos → exigem `X-Admin-Token` | AP04 |
| 2 | `DELETE /api/users/:id` | `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` → `"Usuário deletado."`, apagando matrículas e pagamentos na mesma transação | AP10 |
| 2 | relatório após o DELETE | alunos "Unknown" e receita de pagamentos órfãos → sem órfãos | AP10 |
| 2 | relatório | ordem dos alunos dependia dos callbacks → ordem por matrícula | AP12 |
| 2 | checkout sem `pwd` | senha "123456" → senha aleatória; `card` numérico derrubava o processo → aceito | AP05/AP15 |
| 3 | `/users*`, `/login` | traziam `password` (hash MD5) → sem `password`; hash novo com scrypt e migração automática de MD5 no login | AP05/AP06 |
| 3 | `DELETE /categories/<id>` | tasks ficavam com `category_id` inválido → `category_id = null` | AP10 |
| 3 | entradas inválidas (`priority: "alta"`, `?priority=x`, PUT categoria sem body, cor inválida) | 500 → 400 | AP15 |

### Logs da aplicação rodando após a refatoração

Projeto 1 (`ADMIN_TOKEN=... PORT=5101 python app.py`):
```
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5101
INFO werkzeug: 127.0.0.1 - - "GET / HTTP/1.1" 200 -
INFO werkzeug: 127.0.0.1 - - "GET /health HTTP/1.1" 200 -
INFO werkzeug: 127.0.0.1 - - "GET /produtos HTTP/1.1" 200 -
WARNING src.services.admin_service: query administrativa executada
WARNING src.services.admin_service: banco de dados resetado via /admin/reset-db
$ python scripts/smoke_test.py run code-smells http://127.0.0.1:5101
-- 41/41 respostas sem erro 5xx
$ python scripts/smoke_test.py diff reports/validation/code-smells-antes.json reports/validation/code-smells-depois.json
-- 35/41 respostas idênticas
$ curl -X POST localhost:5101/admin/reset-db        # sem token
403
```

Projeto 2 (`ADMIN_TOKEN=... PORT=5102 npm start`):
```
> node src/server.js
[INFO] LMS API rodando na porta 5102
[INFO] Processando cartão final 4444 no valor de 497
[INFO] Processando cartão final 4444 no valor de 997
[INFO] Processando cartão final 3333 no valor de 497
[INFO] usuário 1 removido
$ python scripts/smoke_test.py run ecommerce http://127.0.0.1:5102
-- 8/8 respostas sem erro 5xx
-- 5/8 respostas idênticas
$ curl localhost:5102/api/admin/financial-report    # sem token
Acesso negado 403
```

Projeto 3 (`python seed.py && PORT=5103 python app.py`):
```
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5103
INFO werkzeug: 127.0.0.1 - - "GET / HTTP/1.1" 200 -
INFO werkzeug: 127.0.0.1 - - "GET /tasks HTTP/1.1" 200 -
$ python scripts/smoke_test.py run task-manager http://127.0.0.1:5103
-- 44/44 respostas sem erro 5xx
-- 39/44 respostas idênticas
```

### Observações por stack

- **Flask + SQL cru (P1):** a maior parte do ganho veio de parametrizar as queries e tirar a conexão global (agora uma por request em `flask.g`). `with conn:` do sqlite3 deu transação com rollback de graça para o pedido. As listagens de pedidos caíram de 1 + N + N×M queries para 2.
- **Express + sqlite3 com callbacks (P2):** o passo mais importante foi promisificar o driver; com `async/await` a transação (`BEGIN/COMMIT/ROLLBACK`) ficou simples. Como é uma conexão só, as transações entram numa fila para não se misturarem. O relatório virou uma query com `LEFT JOIN`.
- **Flask + SQLAlchemy parcialmente organizado (P3):** a estrutura de pastas foi mantida; o trabalho foi esvaziar as rotas (regra → services, request/response → controllers), trocar APIs deprecated e corrigir N+1 com `joinedload` e `GROUP BY`. `-W error::DeprecationWarning` no boot garante que não sobrou `utcnow`.

### Pendências e limites conhecidos

- **Autenticação de verdade (P3, AP04 do relatório):** qualquer cliente ainda cria usuário `admin` e o token do login continua `fake-jwt-token-<id>`. Corrigir exige um sistema de auth (JWT) e muda o contrato de todos os endpoints; ficou fora do escopo e está marcado com TODO em `services/user_service.py`.
- **`/relatorios/vendas` (P1)** continua público: protegi só as rotas sob `/admin`. Proteger o relatório depende de existir autenticação de usuários.
- **`/admin/query` (P1)** continua aceitando escrita quando o token é válido (mantido por compatibilidade); o ideal seria removê-lo ou limitar a SELECT.
- **Senhas de exemplo do seed** (`admin123` etc.) continuam iguais para manter o login dos exemplos; agora são gravadas com hash.
- Não há testes automatizados nos projetos; a validação foi feita pelo smoke test de ponta a ponta.

---

## D) Como executar

### Pré-requisitos
- Python 3.12+ e Node.js 18+ (testado com Python 3.12.10 e Node 22.12)
- Claude Code (para invocar a skill)

### Invocar a skill
```bash
cd code-smells-project      # ou ecommerce-api-legacy / task-manager-api
claude "/refactor-arch"     # interativo: para na Fase 2 e pergunta antes de alterar arquivos
# relatório em outro caminho:
claude "/refactor-arch --report ../reports/audit-project-1.md"
```

### Rodar cada projeto
```bash
# Projeto 1
cd code-smells-project
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
PORT=5101 ADMIN_TOKEN=troque python app.py

# Projeto 2
cd ecommerce-api-legacy
npm install
PORT=5102 ADMIN_TOKEN=troque npm start

# Projeto 3
cd task-manager-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py
PORT=5103 python app.py
```
Variáveis de cada projeto: ver `.env.example` dentro dele.

### Validar
Com a API no ar (banco recém-criado: apague `loja.db` / rode `seed.py` antes):
```bash
ADMIN_TOKEN=troque python scripts/smoke_test.py run code-smells  http://127.0.0.1:5101 --out /tmp/p1.json
ADMIN_TOKEN=troque python scripts/smoke_test.py run ecommerce    http://127.0.0.1:5102 --out /tmp/p2.json
python scripts/smoke_test.py run task-manager http://127.0.0.1:5103 --out /tmp/p3.json

# comparar com as respostas da versão original
python scripts/smoke_test.py diff reports/validation/code-smells-antes.json /tmp/p1.json
python scripts/smoke_test.py diff reports/validation/ecommerce-antes.json   /tmp/p2.json
python scripts/smoke_test.py diff reports/validation/task-manager-antes.json /tmp/p3.json
```
As únicas diferenças esperadas são as da tabela "Mudanças de comportamento intencionais".
