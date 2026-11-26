```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js — engines não declarado; runtime local v22.12.0)
Framework:     Express ^4.18.2 (resolvido 4.22.1 no package-lock.json)
Dependencies:  express 4.22.1, sqlite3 5.1.7
Domain:        LMS com checkout (users, courses, enrollments, payments, audit_logs)
Architecture:  God Class — src/AppManager.js abre conexão, cria schema, faz seed, registra rotas e contém toda a regra de negócio
Entry point:   src/app.js (npm start → node src/app.js, porta 3000 fixa em src/utils.js:6)
Source files:  3 files analyzed | ~180 lines of code
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite :memory:, seed no boot)
Endpoints:     3 (POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1
Files:   3 analyzed | ~180 lines of code
Date:    2026-11-26

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 6 | LOW: 4

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP01 | Credenciais e segredos hardcoded | src/utils.js:1-7 |
| 2 | CRITICAL | AP03 | God Class `AppManager` | src/AppManager.js:4-139 |
| 3 | CRITICAL | AP04 | Endpoints administrativos sem autenticação | src/AppManager.js:80, src/AppManager.js:131 |
| 4 | CRITICAL | AP05 | Senha com hash caseiro fraco / em texto puro / padrão fixo | src/utils.js:17-23, src/AppManager.js:68, src/AppManager.js:18 |
| 5 | CRITICAL | AP06 | Número de cartão e chave do gateway no log | src/AppManager.js:45 |
| 6 | HIGH | AP07 | Regra de negócio e SQL dentro das rotas | src/AppManager.js:28-78, src/AppManager.js:80-129, src/AppManager.js:131-137 |
| 7 | HIGH | AP08 | Estado global mutável e conexão única | src/utils.js:9-15, src/AppManager.js:7 |
| 8 | HIGH | AP09 | Acoplamento forte, sem injeção de dependência | src/AppManager.js:1-2, src/AppManager.js:7, src/app.js:8-10 |
| 9 | HIGH | AP10 | Escritas em várias etapas sem transação / órfãos no DELETE | src/AppManager.js:50-61, src/AppManager.js:69-71, src/AppManager.js:133-135 |
| 10 | MEDIUM | AP12 | Callback hell com contadores manuais | src/AppManager.js:37-77, src/AppManager.js:83-128 |
| 11 | MEDIUM | AP13 | Consultas N+1 no relatório financeiro | src/AppManager.js:89-106 |
| 12 | MEDIUM | AP14 | Código duplicado (fechamento do relatório, mensagens de erro) | src/AppManager.js:95-99, src/AppManager.js:117-122, src/AppManager.js:41, src/AppManager.js:84 |
| 13 | MEDIUM | AP15 | Validação de entrada ausente | src/AppManager.js:35, src/AppManager.js:46, src/AppManager.js:132 |
| 14 | MEDIUM | AP16 | Erros ignorados e respostas de erro inconsistentes | src/AppManager.js:38, src/AppManager.js:57, src/AppManager.js:92-93, src/AppManager.js:104-106, src/AppManager.js:133-135 |
| 15 | MEDIUM | AP18 | Pagamento e cache acoplados ao fluxo HTTP | src/AppManager.js:45-46, src/AppManager.js:59 |
| 16 | LOW | AP19 | Números e strings mágicos | src/AppManager.js:46, src/AppManager.js:68, src/utils.js:6, src/utils.js:19-22 |
| 17 | LOW | AP20 | Nomes ruins / abreviações obscuras | src/AppManager.js:4, src/AppManager.js:29-33, src/utils.js:17 |
| 18 | LOW | AP21 | Código morto e exports não usados | src/utils.js:2-5, src/utils.js:10, src/utils.js:25, src/AppManager.js:2 |
| 19 | LOW | AP22 | `console.log` como sistema de log | src/AppManager.js:45, src/utils.js:13, src/app.js:13 |

## Findings

### 1. [CRITICAL] AP01 — Credenciais e segredos hardcoded
File: src/utils.js:1-7
Evidence: `dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef"`
Description: O objeto `config` guarda usuário/senha de banco, chave live do gateway de pagamento e usuário SMTP como literais no código-fonte.
Impact: Segredos de produção versionados no git, idênticos em todos os ambientes e impossíveis de rotacionar sem deploy; qualquer pessoa com acesso ao repositório pode cobrar cartões com a chave do gateway.
Recommendation: Ler toda configuração de variáveis de ambiente num módulo `config/` sem valor padrão para segredos; remover os campos não usados (playbook T1).

### 2. [CRITICAL] AP03 — God Class `AppManager`
File: src/AppManager.js:4-139
Evidence: `class AppManager { constructor() { this.db = new sqlite3.Database(':memory:') } initDb() {...} setupRoutes(app) {...} }`
Description: Uma única classe abre a conexão (l.7), cria o schema (l.12-16), faz seed (l.18-21), registra as três rotas (l.28, 80, 131) e implementa checkout, relatório financeiro e exclusão de usuário.
Impact: Nenhuma parte pode ser testada ou alterada isoladamente; qualquer mudança toca o arquivo inteiro, violando SRP.
Recommendation: Separar em `config/database` (conexão, schema, seed), models/repositories, services, controllers e routes (playbook T3 + T4 + T5).

### 3. [CRITICAL] AP04 — Endpoints administrativos sem autenticação
File: src/AppManager.js:80, src/AppManager.js:131
Evidence: `app.get('/api/admin/financial-report', (req, res) => {` e `app.delete('/api/users/:id', (req, res) => {`
Description: O relatório financeiro (receita por curso e nomes de alunos) e a exclusão de usuários estão abertos, sem nenhuma checagem de identidade ou papel.
Impact: Qualquer cliente na rede lê dados financeiros e pessoais e apaga usuários arbitrários.
Recommendation: Middleware de autorização admin com token vindo de config (`ADMIN_TOKEN`), negando acesso quando o token não está configurado (playbook T6b).

### 4. [CRITICAL] AP05 — Senha com hash caseiro fraco, em texto puro e com padrão fixo
File: src/utils.js:17-23, src/AppManager.js:68, src/AppManager.js:18
Evidence: `hash += Buffer.from(pwd).toString('base64').substring(0, 2);` / `badCrypto(p || "123456")` / `VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')`
Description: `badCrypto` repete os 2 primeiros caracteres do base64 da senha e trunca em 10 — é reversível e colide para senhas com o mesmo prefixo; sem senha, o usuário recebe `"123456"`; o seed grava a senha `'123'` em claro.
Impact: Vazamento do banco expõe senhas (ou prefixos) reais; contas criadas sem senha ficam com senha conhecida.
Recommendation: Hash adaptativo com salt (`crypto.scrypt` + `timingSafeEqual`), sem senha padrão (exigir `pwd` ou gerar valor aleatório), seed também com hash (playbook T9).

### 5. [CRITICAL] AP06 — Número de cartão e chave do gateway no log
File: src/AppManager.js:45
Evidence: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`);`
Description: Cada checkout escreve no stdout o PAN completo do cartão e a chave live do gateway.
Impact: Violação de PCI-DSS; logs passam a conter dados de cartão e credenciais, acessíveis a quem lê logs/agregadores.
Recommendation: Nunca logar segredo; mascarar o cartão (só os 4 últimos dígitos) e usar logger estruturado (playbook T14 + T6).

### 6. [HIGH] AP07 — Regra de negócio e SQL dentro das rotas (Fat Controller)
File: src/AppManager.js:28-78, src/AppManager.js:80-129, src/AppManager.js:131-137
Evidence: `let status = cc.startsWith("4") ? "PAID" : "DENIED";` dentro do handler de `/api/checkout`; `courseData.revenue += payment.amount;` dentro do handler do relatório
Description: Os handlers HTTP fazem tudo: buscam curso, criam usuário, decidem aprovação do pagamento, gravam matrícula/pagamento/auditoria e calculam receita, com SQL inline.
Impact: Regras de checkout e de receita ficam presas ao HTTP, sem reaproveitamento nem teste unitário.
Recommendation: Extrair `CheckoutService`, `ReportService` e `UserService`; controllers só leem request, chamam o service e respondem (playbook T4 + T5).

### 7. [HIGH] AP08 — Estado global mutável e conexão única
File: src/utils.js:9-15, src/AppManager.js:7
Evidence: `let globalCache = {}; let totalRevenue = 0;` e `this.db = new sqlite3.Database(':memory:');`
Description: Cache e acumulador de receita são variáveis de módulo exportadas e mutáveis; a conexão é um singleton criado no construtor e compartilhado por todas as requisições.
Impact: Estado vaza entre requisições e testes; cache cresce sem limite (memory leak); impossível trocar a implementação.
Recommendation: Conexão criada no composition root e injetada; cache como objeto injetado (ou removido, pois ninguém lê) (playbook T7).

### 8. [HIGH] AP09 — Acoplamento forte, sem injeção de dependência
File: src/AppManager.js:1-2, src/AppManager.js:7, src/app.js:8-10
Evidence: `const sqlite3 = require('sqlite3').verbose();` + `new sqlite3.Database(':memory:')` dentro da classe; `manager.setupRoutes(app)`
Description: A classe instancia o driver de banco por conta própria e importa config/utilitários diretamente; as rotas chamam `this.db` sem abstração.
Impact: Não dá para substituir o banco por fake em teste, nem mudar de SQLite sem reescrever as rotas.
Recommendation: App factory `createApp({ db, config })` montando repositories → services → controllers (playbook T7).

### 9. [HIGH] AP10 — Escritas em várias etapas sem transação / órfãos no DELETE
File: src/AppManager.js:50-61, src/AppManager.js:69-71, src/AppManager.js:133-135
Evidence: `INSERT INTO enrollments` → `INSERT INTO payments` → `INSERT INTO audit_logs` em callbacks encadeados; `res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.")`
Description: Criação de usuário, matrícula, pagamento e auditoria são comandos independentes sem `BEGIN/COMMIT/ROLLBACK`; o DELETE remove o usuário e deixa matrículas e pagamentos órfãos (o próprio código admite).
Impact: Falha no meio gera matrícula sem pagamento ou usuário criado sem matrícula; o relatório passa a listar alunos "Unknown".
Recommendation: Transação no service de checkout; exclusão em cascata explícita (payments → enrollments → user) dentro de transação (playbook T10).

### 10. [MEDIUM] AP12 — Callback hell com contadores manuais
File: src/AppManager.js:37-77, src/AppManager.js:83-128
Evidence: 6 níveis de callbacks aninhados no checkout; `let coursesPending = courses.length; ... enrPending--; if (enrPending === 0) {...}` no relatório
Description: Fluxo controlado por callbacks aninhados e contadores decrementados manualmente para saber quando responder.
Impact: Ordem imprevisível (a ordem dos cursos/alunos no relatório depende de qual callback termina antes), erro em qualquer nível perdido, risco de resposta nunca enviada.
Recommendation: Promisificar o driver e usar `async/await` (playbook T12).

### 11. [MEDIUM] AP13 — Consultas N+1 no relatório financeiro
File: src/AppManager.js:89-106
Evidence: `courses.forEach(...) → db.all("SELECT * FROM enrollments WHERE course_id = ?") → enrollments.forEach(...) → db.get(users) + db.get(payments)`
Description: Para cada curso uma query de matrículas, e para cada matrícula duas queries (usuário e pagamento): 1 + C + 2E idas ao banco.
Impact: Custo cresce linearmente com o volume de matrículas.
Recommendation: Uma query com `LEFT JOIN` courses/enrollments/users/payments e agregação no service (playbook T8).

### 12. [MEDIUM] AP14 — Código duplicado
File: src/AppManager.js:95-99, src/AppManager.js:117-122, src/AppManager.js:41, src/AppManager.js:84
Evidence: `report.push(courseData); coursesPending--; if (coursesPending === 0) res.json(report);` repetido; `res.status(500).send("Erro DB")` repetido
Description: O bloco que fecha o curso e responde o relatório aparece duas vezes; a resposta de erro de banco é copiada em vários handlers.
Impact: Correções precisam ser feitas em vários pontos e tendem a divergir.
Recommendation: Montagem do relatório num único método do service; erro de banco tratado no error handler central (playbook T4 + T6).

### 13. [MEDIUM] AP15 — Validação de entrada ausente
File: src/AppManager.js:35, src/AppManager.js:46, src/AppManager.js:132
Evidence: `if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");` e `cc.startsWith("4")`
Description: Só checa presença; `card` numérico (`4111...` sem aspas) quebra em `cc.startsWith` e derruba a requisição com 500/HTML; e-mail sem formato, `c_id` sem tipo, `:id` do DELETE não validado.
Impact: Entradas inválidas viram erros 500 imprevisíveis em vez de 400.
Recommendation: Validador na borda (controller) com tipos e formatos, mantendo a resposta `400 Bad Request` (playbook T15).

### 14. [MEDIUM] AP16 — Erros ignorados e respostas de erro inconsistentes
File: src/AppManager.js:38, src/AppManager.js:57, src/AppManager.js:92-93, src/AppManager.js:104-106, src/AppManager.js:133-135
Evidence: `(err, enrollments) => { let enrPending = enrollments.length;` sem checar `err`; `this.db.run("DELETE ...", [id], (err) => { res.send("Usuário deletado...") })`
Description: Vários callbacks ignoram `err` (um erro em l.92 gera `TypeError` em `enrollments.length` e derruba o processo); erro de banco em l.38 vira 404; o DELETE responde sucesso mesmo com erro ou id inexistente.
Impact: Falhas silenciosas, crash do processo dentro de callback assíncrono, status codes enganosos.
Recommendation: Error handler central do Express + erros de domínio (`NotFoundError`, `ValidationError`) propagados pelos services (playbook T6).

### 15. [MEDIUM] AP18 — Pagamento e cache acoplados ao fluxo HTTP
File: src/AppManager.js:45-46, src/AppManager.js:59
Evidence: `let status = cc.startsWith("4") ? "PAID" : "DENIED";` e `logAndCache(\`last_checkout_${userId}\`, course.title);`
Description: A "integração" com o gateway de pagamento e a escrita em cache estão inline no handler.
Impact: Impossível trocar o gateway por um real ou por um fake em teste; efeitos colaterais misturados com a persistência.
Recommendation: `PaymentGateway` injetado no `CheckoutService`; remover o cache global sem leitor (playbook T4).

### 16. [LOW] AP19 — Números e strings mágicos
File: src/AppManager.js:46, src/AppManager.js:68, src/utils.js:6, src/utils.js:19-22
Evidence: `cc.startsWith("4")`, `"PAID"/"DENIED"` literais, `p || "123456"`, `port: 3000`, `i < 10000`, `substring(0, 2)`, `substring(0, 10)`
Description: Regras e configurações expressas como literais sem nome; a porta é fixa no código.
Impact: Significado implícito e valores repetidos que divergem ao mudar.
Recommendation: Constantes nomeadas (`PaymentStatus.PAID`, `APPROVED_CARD_PREFIX`) e porta via `PORT` (playbook T13 + T1).

### 17. [LOW] AP20 — Nomes ruins / abreviações obscuras
File: src/AppManager.js:4, src/AppManager.js:29-33, src/utils.js:17
Evidence: `let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd; let cid = req.body.c_id; let cc = req.body.card;`, `badCrypto`, `AppManager`
Description: Variáveis de uma letra e nomes genéricos que não dizem o que fazem.
Impact: Leitura e manutenção mais difíceis.
Recommendation: Renomear internamente (`name`, `email`, `password`, `courseId`, `cardNumber`, `hashPassword`) mantendo os campos `usr/eml/pwd/c_id/card` do contrato HTTP.

### 18. [LOW] AP21 — Código morto e exports não usados
File: src/utils.js:2-5, src/utils.js:10, src/utils.js:25, src/AppManager.js:2
Evidence: `let totalRevenue = 0;` exportado e importado em AppManager.js:2 sem uso; `globalCache` exportado sem leitor; `dbUser`, `dbPass`, `smtpUser` nunca usados
Description: Variáveis, exports e campos de config sem nenhum consumidor.
Impact: Ruído e falsa impressão de funcionalidade (ex.: credenciais de banco que o SQLite em memória não usa).
Recommendation: Remover.

### 19. [LOW] AP22 — `console.log` como sistema de log
File: src/AppManager.js:45, src/utils.js:13, src/app.js:13
Evidence: `console.log(\`[LOG] Salvando no cache: ${key}\`);`, `console.log(\`Frankenstein LMS rodando na porta ${config.port}...\`);`
Description: Logs ad hoc via `console.log`, sem nível nem formato.
Impact: Sem controle de verbosidade por ambiente; facilitou o vazamento do finding 5.
Recommendation: Logger mínimo com níveis configurado no composition root.

## Deprecated APIs
Nenhuma encontrada para Node.js 22 / Express 4.22.1 / sqlite3 5.1.7 (`Buffer.from` já é a forma moderna; sem `new Buffer`, `url.parse`, `req.param`, `bodyParser`, `res.send(status)`). Observação: o estilo callback (sem `async/await`) é legado, coberto em AP12.

Outros itens do catálogo verificados e não encontrados: AP02 (todas as queries usam placeholders `?`), AP11 (sem debug/CORS; porta fixa tratada em AP19), AP23.

## Endpoint inventory (contrato a preservar)
| Method | Route | Handler |
|---|---|---|
| POST | /api/checkout | src/AppManager.js:28 |
| GET | /api/admin/financial-report | src/AppManager.js:80 |
| DELETE | /api/users/:id | src/AppManager.js:131 |

Total: 19 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
