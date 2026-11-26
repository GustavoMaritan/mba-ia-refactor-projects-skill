================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.12 (.venv/pyvenv.cfg: version = 3.12.10; não declarada no projeto)
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.1.9 resolvido no .venv)
Dependencies:  flask-cors 4.0.0, marshmallow 3.20.1 (não usado), requests 2.31.0 (não usado), python-dotenv 1.0.0 (não usado)
Domain:        Gerenciador de tarefas (tasks, users, categories, relatórios de produtividade)
Architecture:  Parcialmente em camadas — existem models/, routes/, services/, utils/, mas as rotas (routes/task_routes.py, routes/report_routes.py) concentram queries, regra de negócio e serialização; services/ só tem um NotificationService nunca usado; config hardcoded em app.py
Entry point:   app.py (python seed.py && python app.py, porta 5000 fixa no código)
Source files:  15 files analyzed | ~1158 lines of code
DB tables:     users, tasks, categories (SQLite via SQLAlchemy, sqlite:///tasks.db em instance/)
Endpoints:     22 (7 tasks, 7 users/login, 2 reports, 4 categories, /health, /) — ver inventário
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.12 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.1.9)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-11-26

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 5 | LOW: 5

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP01 | Credenciais e segredos hardcoded | app.py:13, services/notification_service.py:7-10 |
| 2 | CRITICAL | AP04 | Operações administrativas sem autenticação (escalada de privilégio, token falso) | routes/user_routes.py:52, routes/user_routes.py:71-72, routes/user_routes.py:119-122, routes/user_routes.py:134-151, routes/user_routes.py:210 |
| 3 | CRITICAL | AP05 | Senha com hash fraco (MD5 sem salt) | models/user.py:29, models/user.py:32 |
| 4 | CRITICAL | AP06 | Hash de senha exposto nas respostas | models/user.py:21, routes/user_routes.py:33, routes/user_routes.py:85, routes/user_routes.py:129, routes/user_routes.py:209 |
| 5 | HIGH | AP07 | Regra de negócio e queries nas rotas (Fat Controller) | routes/task_routes.py:11-63, routes/task_routes.py:85-154, routes/task_routes.py:156-223, routes/task_routes.py:273-299, routes/report_routes.py:12-101, routes/report_routes.py:103-155, routes/user_routes.py:42-90, routes/user_routes.py:92-132 |
| 6 | HIGH | AP09 | Acoplamento forte, sem injeção de dependência / sem app factory | app.py:9-31, seed.py:2, routes/task_routes.py:2-5, routes/user_routes.py:2-4, routes/report_routes.py:2-5, services/notification_service.py:15 |
| 7 | HIGH | AP10 | Exclusão de categoria deixa tasks órfãs | routes/report_routes.py:211-223, models/task.py:14, models/task.py:21 |
| 8 | HIGH | AP11 | Configuração insegura de execução (debug + 0.0.0.0, CORS aberto) | app.py:15, app.py:34 |
| 9 | MEDIUM | AP13 | Consultas N+1 e contagens repetidas | routes/task_routes.py:41-57, routes/user_routes.py:22, routes/report_routes.py:55-56, routes/report_routes.py:161-163, routes/report_routes.py:15-28, routes/task_routes.py:275-279 |
| 10 | MEDIUM | AP14 | Código duplicado (overdue, serialização, validação, listas) | routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:33-37, routes/report_routes.py:132-135, routes/task_routes.py:17-28, routes/user_routes.py:162-169, routes/task_routes.py:110, routes/task_routes.py:177, routes/user_routes.py:61, routes/user_routes.py:106 |
| 11 | MEDIUM | AP15 | Validação de entrada ausente ou inconsistente (500 em vez de 400) | routes/task_routes.py:113, routes/task_routes.py:167-169, routes/task_routes.py:182, routes/task_routes.py:261, routes/task_routes.py:264, routes/report_routes.py:196-202, routes/report_routes.py:180, routes/user_routes.py:102-103, routes/user_routes.py:124-125 |
| 12 | MEDIUM | AP16 | Exceções engolidas com `except:` e sem error handler central | routes/task_routes.py:62, routes/task_routes.py:137, routes/task_routes.py:204, routes/task_routes.py:236, routes/report_routes.py:186, routes/report_routes.py:207, routes/report_routes.py:221, routes/user_routes.py:130, routes/user_routes.py:149, utils/helpers.py:46, utils/helpers.py:48, utils/helpers.py:88 |
| 13 | MEDIUM | AP17 | Uso de APIs deprecated (`datetime.utcnow`, `Query.get`) | ver seção Deprecated APIs |
| 14 | LOW | AP19 | Números e strings mágicos | routes/task_routes.py:113, routes/task_routes.py:182, routes/report_routes.py:24-28, routes/report_routes.py:129, routes/report_routes.py:45, routes/user_routes.py:64, routes/user_routes.py:115, app.py:34 |
| 15 | LOW | AP20 | Nomes ruins / blueprint com responsabilidade trocada | routes/report_routes.py:24-28, routes/report_routes.py:157-223, models/category.py:14, models/user.py:27, routes/task_routes.py:268 |
| 16 | LOW | AP21 | Imports não usados e código morto | app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, models/task.py:38-60, models/user.py:34-38, utils/helpers.py:1-116, services/notification_service.py:1-48 |
| 17 | LOW | AP22 | `print` como sistema de log | routes/task_routes.py:149, routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39-41 |
| 18 | LOW | AP23 | Condicionais aninhadas no lugar de expressão simples | models/task.py:39-43, models/task.py:46-48, models/task.py:51-60, models/user.py:35-38, routes/task_routes.py:41-57 |

## Findings

### 1. [CRITICAL] AP01 — Credenciais e segredos hardcoded
File: app.py:13, services/notification_service.py:7-10
Evidence: `app.config['SECRET_KEY'] = 'super-secret-key-123'`; `self.email_user = 'taskmanager@gmail.com'` / `self.email_password = 'senha123'`
Description: A chave de assinatura do Flask e as credenciais SMTP estão como literais no código, junto com host/porta do servidor de e-mail. A URI do banco (app.py:11) também é fixa.
Impact: Segredos vão para o git e valem para todos os ambientes; com a SECRET_KEY conhecida é possível forjar cookies de sessão; a senha do e-mail fica exposta a qualquer leitor do repositório e não dá para rotacionar sem deploy.
Recommendation: Extrair para `config/settings.py` lendo variáveis de ambiente (`SECRET_KEY`, `DATABASE_URL`, `SMTP_*`), sem valor padrão para segredo (em dev, gerar aleatório) (playbook T1).

### 2. [CRITICAL] AP04 — Operações administrativas sem autenticação
File: routes/user_routes.py:52, routes/user_routes.py:71-72, routes/user_routes.py:119-122, routes/user_routes.py:134-151, routes/user_routes.py:210
Evidence: `role = data.get('role', 'user')` em `POST /users`; `user.role = data['role']` em `PUT /users/<id>`; `'token': 'fake-jwt-token-' + str(user.id)`
Description: Qualquer cliente anônimo cria um usuário com `role: "admin"`, promove qualquer conta a admin via `PUT`, e apaga usuários (com todas as suas tasks) via `DELETE /users/<id>`. Nenhuma rota verifica autenticação; o "token" do login é previsível (`fake-jwt-token-<id>`) e nunca é validado.
Impact: Escalada de privilégio trivial e destruição de dados por qualquer pessoa na rede; o token falso dá falsa sensação de segurança.
Recommendation: Middleware de autorização (decorator `require_admin`) com token de admin vindo de config, desabilitado por padrão quando não configurado, aplicado a `DELETE /users/<id>` e às mudanças de `role`; atribuição de `role` diferente de `user` só por admin (playbook T6b).

### 3. [CRITICAL] AP05 — Senha com hash fraco (MD5 sem salt)
File: models/user.py:29, models/user.py:32
Evidence: `self.password = hashlib.md5(pwd.encode()).hexdigest()`
Description: As senhas são armazenadas como MD5 puro, sem salt, e comparadas com `==` (não constante no tempo). O seed (seed.py:19, 26, 33) ainda cria senhas de 4 caracteres.
Impact: Um vazamento do banco revela as senhas em segundos (rainbow tables); senhas iguais geram hashes iguais.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (scrypt/pbkdf2 com salt) e aceitar o hash MD5 legado apenas para migração no login (playbook T9).

### 4. [CRITICAL] AP06 — Hash de senha exposto nas respostas
File: models/user.py:21, routes/user_routes.py:33, routes/user_routes.py:85, routes/user_routes.py:129, routes/user_routes.py:209
Evidence: `'password': self.password,` dentro de `User.to_dict()`
Description: `to_dict()` inclui o hash da senha, e é usado em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e na resposta do `POST /login`.
Impact: Qualquer cliente obtém o hash MD5 de qualquer usuário (combinado com AP05, equivale a vazar a senha).
Recommendation: Serialização explícita sem campos sensíveis (`password` removido do `to_dict`) (playbook T14).

### 5. [HIGH] AP07 — Regra de negócio e queries nas rotas (Fat Controller)
File: routes/task_routes.py:11-63, routes/task_routes.py:85-154, routes/task_routes.py:156-223, routes/task_routes.py:273-299, routes/report_routes.py:12-101, routes/report_routes.py:103-155, routes/user_routes.py:42-90, routes/user_routes.py:92-132
Evidence: `summary_report()` com 13 queries, laços de cálculo de atraso e produtividade por usuário em 90 linhas; `create_task()` valida, busca usuário/categoria, converte datas e grava
Description: Os handlers fazem validação, consultas ORM, cálculo de atraso, estatísticas, regras de unicidade de e-mail e commit, tudo dentro da função da rota; a camada `services/` não é usada.
Impact: Nenhuma regra pode ser testada sem HTTP, e as regras se repetem entre rotas (ver AP14).
Recommendation: Criar `TaskService`, `UserService`, `CategoryService` e `ReportService` com a regra; rotas viram controllers finos (playbook T4 + T5).

### 6. [HIGH] AP09 — Acoplamento forte, sem injeção de dependência
File: app.py:9-31, seed.py:2, routes/task_routes.py:2-5, routes/user_routes.py:2-4, routes/report_routes.py:2-5, services/notification_service.py:15
Evidence: `app = Flask(__name__)` no nível do módulo + `with app.app_context(): db.create_all()`; `from app import app, db` no seed; `server = smtplib.SMTP(self.email_host, self.email_port)`
Description: A app é criada e o schema é gerado como efeito colateral do import de `app.py`, o seed importa a instância global, as rotas usam `db.session` e os models diretamente, e o serviço de notificação instancia SMTP internamente.
Impact: Impossível criar a app com outra config (teste, banco em memória) ou substituir infraestrutura por fakes.
Recommendation: App factory `create_app(config)` como composition root, services recebendo dependências, seed usando a factory (playbook T7).

### 7. [HIGH] AP10 — Exclusão de categoria deixa tasks órfãs
File: routes/report_routes.py:211-223, models/task.py:14, models/task.py:21
Evidence: `db.session.delete(cat)` sem tratar `Task.category_id`; relacionamento `db.relationship('Category', backref='tasks')` sem cascade
Description: Ao apagar uma categoria, as tasks continuam com `category_id` apontando para um registro inexistente (o SQLite não aplica FK por padrão). `delete_user` (routes/user_routes.py:140-146) resolve isso manualmente, mas a categoria não.
Impact: Dados inconsistentes: tasks com `category_id` inválido aparecem com `category_name: null` e quebram relatórios.
Recommendation: No service, dentro da mesma transação, desassociar (`category_id = NULL`) as tasks antes de apagar a categoria; cascata explícita no model (playbook T10).

### 8. [HIGH] AP11 — Configuração insegura de execução
File: app.py:15, app.py:34
Evidence: `app.run(debug=True, host='0.0.0.0', port=5000)`; `CORS(app)`
Description: O debugger do Werkzeug fica ativo e acessível de qualquer interface; CORS libera qualquer origem; a porta é fixa.
Impact: O debugger permite execução remota de código; qualquer site pode chamar a API a partir do navegador da vítima.
Recommendation: `DEBUG`, `HOST`, `PORT` e `CORS_ORIGINS` via env com padrão seguro (debug desligado, 127.0.0.1) (playbook T1).

### 9. [MEDIUM] AP13 — Consultas N+1 e contagens repetidas
File: routes/task_routes.py:41-57, routes/user_routes.py:22, routes/report_routes.py:55-56, routes/report_routes.py:161-163, routes/report_routes.py:15-28, routes/task_routes.py:275-279
Evidence: `user = User.query.get(t.user_id)` e `cat = Category.query.get(t.category_id)` dentro do laço de tasks; `'task_count': len(u.tasks)`; `Task.query.filter_by(category_id=c.id).count()` por categoria
Description: `GET /tasks` faz até 2 queries por task; `GET /users`, `/reports/summary` e `GET /categories` fazem 1 query por usuário/categoria; o resumo e o `/tasks/stats` fazem uma contagem separada para cada status e prioridade.
Impact: 1 + N idas ao banco; latência cresce linearmente com o volume.
Recommendation: Eager loading (`joinedload`) e agregações `GROUP BY` (`func.count`) em repositórios/models (playbook T8).

### 10. [MEDIUM] AP14 — Código duplicado
File: routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:33-37, routes/report_routes.py:132-135, routes/task_routes.py:17-28, routes/user_routes.py:162-169, routes/task_routes.py:110, routes/task_routes.py:177, routes/user_routes.py:61, routes/user_routes.py:106
Evidence: escada `if t.due_date: if t.due_date < datetime.utcnow(): if t.status != 'done' and t.status != 'cancelled':` repetida em 6 lugares, enquanto `Task.is_overdue()` (models/task.py:50) existe e não é usado
Description: O cálculo de "atrasada" está copiado em 6 rotas; a serialização de task é refeita à mão em vez de `to_dict()`; a lista de status e a regex de e-mail se repetem em várias rotas e em `utils/helpers.py`; validações de criar e atualizar são duplicadas com mensagens diferentes ("Formato de data inválido. Use YYYY-MM-DD" vs "Formato de data inválido").
Impact: Mudar uma regra exige editar vários pontos; versões já divergem.
Recommendation: Um ponto de verdade: `Task.is_overdue()`, serializers no model, validadores compartilhados e constantes de domínio (playbook T4/T14 + T13).

### 11. [MEDIUM] AP15 — Validação de entrada ausente ou inconsistente
File: routes/task_routes.py:113, routes/task_routes.py:167-169, routes/task_routes.py:182, routes/task_routes.py:261, routes/task_routes.py:264, routes/report_routes.py:196-202, routes/report_routes.py:180, routes/user_routes.py:102-103, routes/user_routes.py:124-125
Evidence: `if priority < 1 or priority > 5:` com `priority` vindo do JSON sem checar tipo; `tasks.filter(Task.priority == int(priority))` com query string; `data = request.get_json()` seguido de `if 'name' in data:` sem checar `None`
Description: `priority: "alta"` ou `title: null` geram `TypeError`; `?priority=x` gera `ValueError`; `PUT /categories/<id>` sem corpo JSON quebra; `PUT /users` aceita nome vazio e `active` de qualquer tipo; cor da categoria não é validada.
Impact: Entradas inválidas resultam em 500 com página de erro do Flask, não em 400 com mensagem previsível.
Recommendation: Validação na borda/serviço com mensagens previsíveis e 400 (playbook T15).

### 12. [MEDIUM] AP16 — Exceções engolidas e sem error handler central
File: routes/task_routes.py:62, routes/task_routes.py:137, routes/task_routes.py:204, routes/task_routes.py:236, routes/report_routes.py:186, routes/report_routes.py:207, routes/report_routes.py:221, routes/user_routes.py:130, routes/user_routes.py:149, utils/helpers.py:46, utils/helpers.py:48, utils/helpers.py:88
Evidence: `except:` / `return jsonify({'error': 'Erro interno'}), 500`
Description: `try/except` sem tipo copiado em quase todo handler, sem log da causa; não há `errorhandler` registrado, então erros fora dos `try` (AP15) devolvem HTML.
Impact: Falhas reais ficam invisíveis; formato de erro inconsistente (JSON às vezes, HTML outras).
Recommendation: Exceções de domínio (`NotFoundError`, `ValidationError`, `ConflictError`) + error handler centralizado que loga e devolve `{"error": ...}` (playbook T6).

### 13. [MEDIUM] AP17 — Uso de APIs deprecated
File: ver tabela "Deprecated APIs" (32 chamadas + 4 defaults de coluna)
Evidence: `datetime.utcnow()` (deprecated no Python 3.12); `Task.query.get(task_id)` (Legacy Query API no SQLAlchemy 2.x, emite `LegacyAPIWarning`)
Description: O projeto roda em Python 3.12.10 e SQLAlchemy 2.1.9, onde ambas as APIs emitem avisos de depreciação.
Impact: Warnings em runtime e quebra futura ao atualizar versões; `utcnow` devolve datetime naive.
Recommendation: `datetime.now(timezone.utc)` (gravando naive UTC para manter o formato) e `db.session.get(Model, id)` / `db.select(...)` (playbook T11).

### 14. [LOW] AP19 — Números e strings mágicos
File: routes/task_routes.py:113, routes/task_routes.py:182, routes/report_routes.py:24-28, routes/report_routes.py:129, routes/report_routes.py:45, routes/user_routes.py:64, routes/user_routes.py:115, app.py:34
Evidence: `if t.priority <= 2:`; `filter_by(priority=1)` … `priority=5`; `timedelta(days=7)`; `len(password) < 4`
Description: Limites de prioridade, janela de "atividade recente", tamanho mínimo de senha e porta estão como literais, enquanto `utils/helpers.py:110-116` define constantes (`VALID_STATUSES`, `MIN_PASSWORD_LENGTH`...) que ninguém usa.
Impact: Regras implícitas e fáceis de divergir.
Recommendation: Módulo de constantes de domínio usado por models/services (playbook T13).

### 15. [LOW] AP20 — Nomes ruins / blueprint com responsabilidade trocada
File: routes/report_routes.py:24-28, routes/report_routes.py:157-223, models/category.py:14, models/user.py:27, routes/task_routes.py:268
Evidence: `p1 = Task.query.filter_by(priority=1).count()`; `d = {...}`; `def set_password(self, pwd)`; `for t in results:`; CRUD de `/categories` dentro de `report_bp`
Description: Variáveis de uma letra/abreviadas e o CRUD de categorias morando no blueprint de relatórios.
Impact: Dificulta leitura e localização do código.
Recommendation: Renomear internamente e mover categorias para módulo próprio, mantendo rotas e campos do contrato.

### 16. [LOW] AP21 — Imports não usados e código morto
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, models/task.py:38-60, models/user.py:34-38, utils/helpers.py:1-116, services/notification_service.py:1-48
Evidence: `import os, sys, json, datetime` (só `datetime` usado); `import json, os, sys, time`; `import hashlib, json, re` (só `re` usado); `from utils.helpers import format_date, calculate_percentage` (nenhum usado)
Description: Imports sem uso; `Task.validate_status/validate_priority/is_overdue` e `User.is_admin` nunca chamados; `utils/helpers.py` inteiro não é usado; `NotificationService` nunca é instanciado; `marshmallow`, `requests` e `python-dotenv` no requirements sem uso.
Impact: Ruído e falsa impressão de que existe validação/notificação.
Recommendation: Remover; reaproveitar o que for útil (ex.: `is_overdue`) no lugar da duplicação.

### 17. [LOW] AP22 — `print` como sistema de log
File: routes/task_routes.py:149, routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39-41
Evidence: `print(f"Erro ao criar task: {str(e)}")`
Description: Eventos e erros são escritos com `print`, sem nível nem formato.
Impact: Sem controle de nível por ambiente; logs se perdem em produção.
Recommendation: `logging` configurado no composition root.

### 18. [LOW] AP23 — Condicionais aninhadas no lugar de expressão simples
File: models/task.py:39-43, models/task.py:46-48, models/task.py:51-60, models/user.py:35-38, routes/task_routes.py:41-57
Evidence: `if self.role == 'admin': return True else: return False`; escada de 3 `if` em `is_overdue`
Description: Booleanos calculados com escadas de `if/else` em vez de expressão direta.
Impact: Mais linhas e mais chance de erro para lógica trivial.
Recommendation: Guard clauses / `return a and b and not c`.

## Deprecated APIs
| API | Location | Modern replacement |
|---|---|---|
| `datetime.utcnow()` (Python 3.12) | models/task.py:52, routes/report_routes.py:35, routes/report_routes.py:42, routes/report_routes.py:45, routes/report_routes.py:71, routes/report_routes.py:133, routes/task_routes.py:31, routes/task_routes.py:72, routes/task_routes.py:215, routes/task_routes.py:285, routes/user_routes.py:172, seed.py:66, seed.py:67, seed.py:69, seed.py:70, seed.py:74, services/notification_service.py:35, utils/helpers.py:38 | `datetime.now(timezone.utc)` |
| `default=datetime.utcnow` / `onupdate=datetime.utcnow` | models/category.py:11, models/task.py:15, models/task.py:16, models/user.py:14 | função `utcnow()` própria baseada em `datetime.now(timezone.utc)` |
| `Model.query.get(id)` (SQLAlchemy 2.x Legacy Query API) | routes/report_routes.py:105, routes/report_routes.py:192, routes/report_routes.py:213, routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188, routes/task_routes.py:195, routes/task_routes.py:227, routes/user_routes.py:29, routes/user_routes.py:94, routes/user_routes.py:136, routes/user_routes.py:155 | `db.session.get(Model, id)` |

## Endpoint inventory (contrato a preservar)
| Method | Route | Handler |
|---|---|---|
| GET | /health | app.py:22 |
| GET | / | app.py:26 |
| GET | /tasks | routes/task_routes.py:11 |
| GET | /tasks/<int:task_id> | routes/task_routes.py:65 |
| POST | /tasks | routes/task_routes.py:85 |
| PUT | /tasks/<int:task_id> | routes/task_routes.py:156 |
| DELETE | /tasks/<int:task_id> | routes/task_routes.py:225 |
| GET | /tasks/search | routes/task_routes.py:240 |
| GET | /tasks/stats | routes/task_routes.py:273 |
| GET | /users | routes/user_routes.py:10 |
| GET | /users/<int:user_id> | routes/user_routes.py:27 |
| POST | /users | routes/user_routes.py:42 |
| PUT | /users/<int:user_id> | routes/user_routes.py:92 |
| DELETE | /users/<int:user_id> | routes/user_routes.py:134 |
| GET | /users/<int:user_id>/tasks | routes/user_routes.py:153 |
| POST | /login | routes/user_routes.py:185 |
| GET | /reports/summary | routes/report_routes.py:12 |
| GET | /reports/user/<int:user_id> | routes/report_routes.py:103 |
| GET | /categories | routes/report_routes.py:157 |
| POST | /categories | routes/report_routes.py:167 |
| PUT | /categories/<int:cat_id> | routes/report_routes.py:190 |
| DELETE | /categories/<int:cat_id> | routes/report_routes.py:211 |

Total: 18 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
