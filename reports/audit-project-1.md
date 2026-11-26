```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.12 (versão do interpretador local; o projeto não declara versão)
Framework:     Flask 3.1.1 (requirements.txt)
Dependencies:  flask==3.1.1, flask-cors==5.0.1, sqlite3 (stdlib)
Domain:        E-commerce / loja virtual (produtos, usuários, pedidos, itens de pedido, relatório de vendas)
Architecture:  Pseudo-camadas — existem models.py/controllers.py, mas models.py monta SQL cru + regra de desconto + montagem de pedidos, app.py executa SQL direto nas rotas admin e database.py junta conexão global + schema + seed
Entry point:   app.py (python app.py, porta 5000 fixa no código, host 0.0.0.0, debug=True)
Source files:  4 files analyzed | ~780 lines of code
DB tables:     produtos, usuarios, pedidos, itens_pedido (SQLite, loja.db, criado e populado no primeiro get_db())
Endpoints:     19 (produtos x6, usuarios x3, login, pedidos x4, relatorios/vendas, health, /, admin/reset-db, admin/query)
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.12 + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-11-26
```

## Summary
CRITICAL: 6 | HIGH: 6 | MEDIUM: 5 | LOW: 5

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP01 | Credenciais e segredos hardcoded | app.py:7, controllers.py:289, database.py:76-78 |
| 2 | CRITICAL | AP02 | SQL Injection | models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299 |
| 3 | CRITICAL | AP03 | God File (models.py / database.py) | models.py:1-314, database.py:7-86 |
| 4 | CRITICAL | AP04 | Endpoints administrativos sem autenticação | app.py:47-57, app.py:59-78 |
| 5 | CRITICAL | AP05 | Senha em texto puro | models.py:126-129, models.py:109-111, database.py:75-83 |
| 6 | CRITICAL | AP06 | Exposição de segredo e senha nas respostas | controllers.py:285-289, models.py:83, models.py:99 |
| 7 | HIGH | AP06 | Exposição de dados pessoais/internos em log e erro | controllers.py:161, 179, 182; controllers.py:12, 22, 62, 96, 109, 126, 134, 144, 165, 186, 220, 227, 235, 255, 262, 292; app.py:78 |
| 8 | HIGH | AP07 | Regra de negócio e SQL na camada HTTP | controllers.py:24-62, 64-96, 237-255, 264-292; app.py:47-78 |
| 9 | HIGH | AP08 | Conexão singleton global mutável | database.py:4-12 |
| 10 | HIGH | AP09 | Acoplamento forte sem injeção de dependência | app.py:3-4, controllers.py:2-3, models.py:1 (+ `get_db()` em cada função) |
| 11 | HIGH | AP10 | Escrita em várias etapas sem transação / integridade | models.py:133-169, models.py:65-70, app.py:51-55 |
| 12 | HIGH | AP11 | Configuração insegura de execução | app.py:8, app.py:9, app.py:88 |
| 13 | MEDIUM | AP13 | Consultas N+1 | models.py:177-200, 209-232, 139-146, 154-161, 239-254 |
| 14 | MEDIUM | AP14 | Código duplicado | models.py:12-21/31-40/304-313, 79-86/95-102, 171-201/203-233; controllers.py:28-50/72-90 |
| 15 | MEDIUM | AP15 | Validação de entrada ausente ou inconsistente | controllers.py:43-50, 81-90, 118-121, 153-158, 169-171, 195-201, 239-245 |
| 16 | MEDIUM | AP16 | Tratamento de erro espalhado | controllers.py (16 blocos `except Exception`), app.py:77-78 |
| 17 | MEDIUM | AP18 | Efeitos colaterais acoplados ao fluxo | controllers.py:208-210, controllers.py:247-250 |
| 18 | LOW | AP19 | Números e strings mágicos | models.py:256-262, controllers.py:52, 242, 285-288, app.py:88, database.py:5 |
| 19 | LOW | AP20 | Nomes ruins | models.py:187, 191, 193; controllers.py:14, 56, 64, 98, 136, 160 |
| 20 | LOW | AP21 | Imports não usados e código morto | models.py:2, database.py:2, controllers.py:268 |
| 21 | LOW | AP22 | `print` como sistema de log | controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86 |
| 22 | LOW | AP23 | Condicionais redundantes | controllers.py:17-20, 139-142, 177-183, 200 |

## Findings

### 1. [CRITICAL] AP01 — Credenciais e segredos hardcoded
File: app.py:7, controllers.py:289, database.py:76-78
Evidence: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` e `"secret_key": "minha-chave-super-secreta-123"`
Description: A chave secreta do Flask está fixa no código e duplicada como literal no health check. O seed cria um usuário admin com senha fixa conhecida (`"admin@loja.com", "admin123"`).
Impact: A chave vai para o git e vale em todos os ambientes; quem lê o repositório pode forjar sessões assinadas. A conta admin padrão tem senha pública.
Recommendation: Ler `SECRET_KEY` de variável de ambiente (sem valor padrão sensível; em dev gerar aleatório), remover o literal do health check e não semear senha conhecida fora de dev (playbook T1).

### 2. [CRITICAL] AP02 — SQL Injection
File: models.py:28, models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140, models.py:148-151, models.py:155, models.py:157-161, models.py:163-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-299
Evidence: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (models.py:110)
Description: Praticamente todas as queries são montadas por concatenação de strings com dados vindos do request (nome, descrição, email, senha, termo de busca, categoria, status, quantidade).
Impact: Bypass de login com `' OR '1'='1' --` no email, leitura de qualquer tabela via `/produtos/busca?q=`, alteração/destruição de dados via criação de produto/usuário.
Recommendation: Usar placeholders `?` com parâmetros em todas as queries; montar filtros dinâmicos da busca com lista de cláusulas fixas + lista de parâmetros (playbook T2).

### 3. [CRITICAL] AP03 — God File (models.py / database.py)
File: models.py:1-314, database.py:7-86
Evidence: `models.py` contém SQL cru, serialização manual de linhas, cálculo de desconto (`if faturamento > 10000: desconto = faturamento * 0.1`, models.py:256-262) e orquestração de pedido com baixa de estoque (models.py:133-169); `get_db()` abre conexão, cria schema e faz seed na mesma função.
Description: Uma única camada mistura acesso a dados, regra de negócio e formatação de resposta; a função de conexão também é responsável por DDL e dados de exemplo.
Impact: Não dá para testar a regra de desconto ou de pedido sem banco; qualquer mudança de schema, regra ou formato de resposta toca o mesmo arquivo.
Recommendation: Separar em `database` (conexão), `schema/seed`, models/repositórios por entidade, services (pedido, relatório) e serializers (playbook T3 + T4 + T5).

### 4. [CRITICAL] AP04 — Endpoints administrativos sem autenticação
File: app.py:47-57, app.py:59-78
Evidence: `cursor.execute(query)` com `query = dados.get("sql", "")` em `POST /admin/query`; `DELETE FROM usuarios` em `POST /admin/reset-db`
Description: `/admin/query` executa qualquer SQL recebido no body e devolve o resultado; `/admin/reset-db` apaga todas as tabelas. Nenhum dos dois verifica autenticação ou papel. `/relatorios/vendas` (dados financeiros) também é aberto.
Impact: Qualquer cliente na rede lê senhas (`SELECT * FROM usuarios`), altera preços ou apaga o banco inteiro com uma requisição.
Recommendation: Proteger rotas administrativas com middleware de autorização baseado em token de admin vindo de config, desabilitadas quando o token não estiver configurado; restringir `/admin/query` a SELECT somente leitura ou removê-lo (playbook T6b).

### 5. [CRITICAL] AP05 — Senha em texto puro
File: models.py:126-129, models.py:109-111, database.py:75-83
Evidence: `"INSERT INTO usuarios (nome, email, senha, tipo) VALUES ('" + nome + "', '" + email + "', '" + senha + "', ..."` e `WHERE email = ... AND senha = '...'`
Description: A senha é gravada exatamente como recebida, o login compara a senha em claro dentro da query e o seed grava senhas reais em texto puro.
Impact: Qualquer vazamento do banco (inclusive via `/admin/query` ou `/usuarios`) expõe as senhas reais dos clientes.
Recommendation: Gravar hash adaptativo (`werkzeug.security.generate_password_hash`) e validar com `check_password_hash` após buscar o usuário só pelo email; migrar o seed (playbook T9).

### 6. [CRITICAL] AP06 — Exposição de segredo e senha nas respostas
File: controllers.py:285-289, models.py:83, models.py:99
Evidence: `"db_path": "loja.db", "debug": True, "secret_key": "minha-chave-super-secreta-123"` no `/health`; `"senha": row["senha"]` em `get_todos_usuarios` e `get_usuario_por_id`
Description: O health check público devolve a chave secreta, o caminho do banco e o modo debug. `GET /usuarios` e `GET /usuarios/<id>` devolvem a senha de cada usuário.
Impact: Qualquer cliente obtém a SECRET_KEY e as senhas de todos os usuários (inclusive o admin) sem autenticação.
Recommendation: Serialização explícita sem `senha`; health check só com status e contagens (playbook T14).

### 7. [HIGH] AP06 — Exposição de dados pessoais/internos em log e erro
File: controllers.py:161, controllers.py:179, controllers.py:182; controllers.py:12, 22, 62, 96, 109, 126, 134, 144, 165, 186, 220, 227, 235, 255, 262, 292; app.py:78
Evidence: `print("Login falhou: " + email)` e `return jsonify({"erro": str(e)}), 500`
Description: E-mails de usuários são escritos em claro no stdout em cadastro e login; todo erro inesperado devolve `str(e)` ao cliente, incluindo mensagens do SQLite.
Impact: Dados pessoais no log; mensagens de exceção revelam estrutura de tabelas e facilitam explorar a injeção SQL.
Recommendation: Erro genérico ao cliente no handler central e detalhe só no log; não registrar e-mail em claro (playbook T6 + T14).

### 8. [HIGH] AP07 — Regra de negócio e SQL na camada HTTP
File: controllers.py:24-62, controllers.py:64-96, controllers.py:237-255, controllers.py:264-292, app.py:47-78
Evidence: `categorias_validas = ["informatica", "moveis", ...]` dentro de `criar_produto`; `cursor.execute("SELECT COUNT(*) FROM produtos")` em `health_check`; `DELETE FROM ...` direto em `reset_database`
Description: Controllers fazem validação de domínio (categorias, limites de preço/estoque, status válidos, transições de pedido) e alguns acessam o banco diretamente; rotas admin em app.py executam SQL.
Impact: Regras não reutilizáveis nem testáveis fora do HTTP; já divergem entre criar e atualizar produto.
Recommendation: Mover regras para services (produto, pedido, admin) e deixar controllers só lendo request, chamando service e devolvendo resposta (playbook T4 + T5).

### 9. [HIGH] AP08 — Conexão singleton global mutável
File: database.py:4-12
Evidence: `global db_connection` ... `sqlite3.connect(db_path, check_same_thread=False)`
Description: Uma única conexão SQLite em variável global é compartilhada por todas as requisições e threads, com a checagem de thread desligada.
Impact: Transações de requisições concorrentes se misturam (um `commit` de uma requisição grava escrita pendente de outra); testes não conseguem isolar o banco.
Recommendation: Conexão por requisição em `flask.g`, fechada em `teardown_appcontext`, com caminho do banco vindo de config (playbook T7).

### 10. [HIGH] AP09 — Acoplamento forte sem injeção de dependência
File: app.py:3-4, controllers.py:2-3, models.py:1 (e `db = get_db()` em todas as funções de models.py, controllers.py:266, app.py:49, app.py:66)
Evidence: `from database import get_db` + `db = get_db()` no início de cada função
Description: Todos os módulos importam o singleton de banco e o próprio app importa módulos inteiros por efeito colateral; não há app factory nem ponto de composição.
Impact: Impossível trocar o banco por um de teste ou substituir dependências (ex.: notificação) sem editar o código.
Recommendation: App factory `create_app(config)` que registra blueprints e fornece a conexão; models recebem a conexão (playbook T7).

### 11. [HIGH] AP10 — Escrita em várias etapas sem transação / integridade
File: models.py:133-169, models.py:65-70, app.py:51-55
Evidence: `INSERT INTO pedidos` → loop `INSERT INTO itens_pedido` + `UPDATE produtos SET estoque = estoque - ...` → `db.commit()` só no fim, sem rollback
Description: A criação do pedido grava pedido, itens e baixa de estoque sem transação explícita nem rollback; uma exceção no meio deixa escritas pendentes na conexão global, que serão confirmadas pelo próximo `commit` de qualquer requisição. A checagem de estoque e a baixa não são atômicas. `deletar_produto` apaga o produto deixando `itens_pedido` apontando para ele.
Impact: Estoque baixado sem pedido, pedido sem itens, venda acima do estoque com requisições concorrentes, itens órfãos.
Recommendation: Transação no service (`with conn:` / BEGIN-COMMIT-ROLLBACK), baixa condicional `WHERE estoque >= ?` e política explícita para itens ao deletar produto (playbook T10).

### 12. [HIGH] AP11 — Configuração insegura de execução
File: app.py:8, app.py:9, app.py:88
Evidence: `app.run(host="0.0.0.0", port=5000, debug=True)` e `CORS(app)`
Description: Debug ligado com bind em todas as interfaces e CORS liberado para qualquer origem; porta fixa no código.
Impact: O debugger do Werkzeug exposto na rede permite execução remota de código; qualquer site pode chamar a API pelo navegador do usuário.
Recommendation: `DEBUG`, `HOST`, `PORT` e origens CORS por variável de ambiente, padrão seguro (debug off) (playbook T1).

### 13. [MEDIUM] AP13 — Consultas N+1
File: models.py:177-200, models.py:209-232, models.py:139-146, models.py:154-161, models.py:239-254
Evidence: `for item in itens: cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))` dentro do laço de pedidos
Description: Listar pedidos faz 1 query por pedido para os itens e mais 1 por item para o nome do produto; criar pedido busca cada produto duas vezes; o relatório faz 5 queries onde uma agregação bastaria.
Impact: Número de idas ao banco cresce com pedidos × itens; `/pedidos` degrada linearmente.
Recommendation: JOIN `itens_pedido`+`produtos` com `IN (...)` dos pedidos, reaproveitar os produtos já lidos na criação e `GROUP BY status` no relatório (playbook T8).

### 14. [MEDIUM] AP14 — Código duplicado
File: models.py:12-21, models.py:31-40, models.py:304-313, models.py:79-86, models.py:95-102, models.py:171-201, models.py:203-233, controllers.py:28-50, controllers.py:72-90
Evidence: o dicionário `{"id": row["id"], "nome": row["nome"], ..., "criado_em": row["criado_em"]}` repetido três vezes para produto
Description: Serialização de produto (3x) e usuário (2x) copiada; `get_pedidos_usuario` e `get_todos_pedidos` são idênticas salvo o WHERE; validação de produto duplicada entre criar e atualizar.
Impact: Mudanças de campo ou regra precisam ser feitas em vários lugares e já divergem (atualizar não valida nome nem categoria).
Recommendation: Um serializer por entidade, uma função de listagem de pedidos com filtro opcional e um validador compartilhado de produto (playbook T4/T14 + T13).

### 15. [MEDIUM] AP15 — Validação de entrada ausente ou inconsistente
File: controllers.py:43-50, controllers.py:81-90, controllers.py:118-121, controllers.py:153-158, controllers.py:169-171, controllers.py:195-201, controllers.py:239-245
Evidence: `if preco < 0:` sem checar tipo; `dados = request.get_json()` seguido de `dados.get(...)` sem checar `None` em `login` e `atualizar_status_pedido`
Description: Tipos não são validados (`preco: "abc"` gera TypeError → 500); body ausente em login/status gera AttributeError → 500; `float(preco_min)` inválido → 500; atualizar produto não valida nome nem categoria; itens do pedido não validam `produto_id`/`quantidade` (KeyError, quantidade negativa aumenta estoque); e-mail sem formato nem unicidade; status atualizado sem verificar se o pedido existe (200 para id inexistente).
Impact: Erros de cliente viram 500, dados inválidos entram no banco e regras divergem entre rotas.
Recommendation: Validação na borda com mensagens previsíveis e 400 (playbook T15).

### 16. [MEDIUM] AP16 — Tratamento de erro espalhado
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78
Evidence: `except Exception as e: return jsonify({"erro": str(e)}), 500` em cada handler
Description: O mesmo `try/except Exception` é copiado em todos os handlers; formatos de erro variam (`{"erro"}`, `{"erro", "sucesso": False}`, `{"status": "erro", "detalhes"}`).
Impact: Ruído em todo handler, formato inconsistente para o cliente e vazamento de detalhes internos.
Recommendation: Error handler centralizado com exceções de domínio (`NotFound`, `ValidationError`) mapeadas para status (playbook T6).

### 17. [MEDIUM] AP18 — Efeitos colaterais acoplados ao fluxo
File: controllers.py:208-210, controllers.py:247-250
Evidence: `print("ENVIANDO EMAIL: Pedido " + ...)`, `print("ENVIANDO SMS: ...")`, `print("NOTIFICAÇÃO: Pedido ... cancelado. Devolver estoque.")`
Description: Notificações (email, SMS, push) são "enviadas" inline no controller após gravar. Ao cancelar, a mensagem diz "Devolver estoque", mas nenhum estoque é devolvido.
Impact: Trocar o canal de notificação exige editar controllers; falha no envio real derrubaria a requisição após o pedido já gravado.
Recommendation: Serviço de notificação injetado, chamado pelo service de pedido (playbook T4).

### 18. [LOW] AP19 — Números e strings mágicos
File: models.py:256-262, controllers.py:52, controllers.py:242, controllers.py:285-288, app.py:88, database.py:5
Evidence: `if faturamento > 10000: desconto = faturamento * 0.1` / `elif faturamento > 5000: ... 0.05`
Description: Faixas de desconto, lista de categorias, lista de status, versão/ambiente, porta e caminho do banco estão como literais espalhados.
Impact: Regras de negócio escondidas no código e listas que precisam ser mantidas em vários pontos.
Recommendation: Constantes nomeadas em módulo de domínio e config (playbook T13).

### 19. [LOW] AP20 — Nomes ruins
File: models.py:187, models.py:191, models.py:193; controllers.py:14, controllers.py:56, controllers.py:64, controllers.py:98, controllers.py:136, controllers.py:160
Evidence: `cursor2 = db.cursor()`, `cursor3 = db.cursor()`, `prod = cursor3.fetchone()`; parâmetro/variável `id` sombreando o builtin
Description: Nomes numerados e abreviados, e `id` usado como nome de variável em vários handlers.
Impact: Legibilidade; sombra do builtin `id` dificulta depuração.
Recommendation: Renomear internamente (`produto_id`, `itens_cursor`), mantendo nomes de campos e parâmetros de rota do contrato HTTP.

### 20. [LOW] AP21 — Imports não usados e código morto
File: models.py:2, database.py:2, controllers.py:268
Evidence: `import sqlite3` (models.py), `import os` (database.py), `cursor.execute("SELECT 1")` cujo resultado nunca é lido
Description: Imports sem uso e query redundante no health check.
Impact: Ruído e leitura enganosa.
Recommendation: Remover.

### 21. [LOW] AP22 — `print` como sistema de log
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, app.py:83-86
Evidence: `print("ERRO: " + str(e))`, banner `print("SERVIDOR INICIADO")`
Description: Logs e erros são escritos com `print`, sem nível nem formato.
Impact: Impossível filtrar por nível ou desligar em produção.
Recommendation: `logging` configurado no composition root, nível por ambiente.

### 22. [LOW] AP23 — Condicionais redundantes
File: controllers.py:17-20, controllers.py:139-142, controllers.py:177-183, controllers.py:200
Evidence: `if not itens or len(itens) == 0:`; `if produto: return ... else: return ... 404`
Description: Checagem dupla equivalente e `if/else` com `return` em ambos os ramos em vez de guard clause.
Impact: Legibilidade.
Recommendation: Guard clauses (`if not produto: raise NotFound`) e expressão única (`if not itens`).

## Deprecated APIs
Nenhuma encontrada para Python 3.12 + Flask 3.1.1 + sqlite3. Verificados: `datetime.utcnow()`, `before_first_request`, `json_encoder`, `attachment_filename`, `imp`/`distutils`, adaptadores padrão de datetime do sqlite3 (o código não passa objetos `datetime`; `criado_em` usa `CURRENT_TIMESTAMP` no próprio SQLite).

## Endpoint inventory (contrato a preservar)
| Method | Route | Handler |
|---|---|---|
| GET | / | app.py:33 (`index`) |
| GET | /produtos | controllers.py:5 (`listar_produtos`) |
| GET | /produtos/busca | controllers.py:111 (`buscar_produtos`) |
| GET | /produtos/<int:id> | controllers.py:14 (`buscar_produto`) |
| POST | /produtos | controllers.py:24 (`criar_produto`) |
| PUT | /produtos/<int:id> | controllers.py:64 (`atualizar_produto`) |
| DELETE | /produtos/<int:id> | controllers.py:98 (`deletar_produto`) |
| GET | /usuarios | controllers.py:128 (`listar_usuarios`) |
| GET | /usuarios/<int:id> | controllers.py:136 (`buscar_usuario`) |
| POST | /usuarios | controllers.py:146 (`criar_usuario`) |
| POST | /login | controllers.py:167 (`login`) |
| POST | /pedidos | controllers.py:188 (`criar_pedido`) |
| GET | /pedidos | controllers.py:229 (`listar_todos_pedidos`) |
| GET | /pedidos/usuario/<int:usuario_id> | controllers.py:222 (`listar_pedidos_usuario`) |
| PUT | /pedidos/<int:pedido_id>/status | controllers.py:237 (`atualizar_status_pedido`) |
| GET | /relatorios/vendas | controllers.py:257 (`relatorio_vendas`) |
| GET | /health | controllers.py:264 (`health_check`) |
| POST | /admin/reset-db | app.py:48 (`reset_database`) |
| POST | /admin/query | app.py:60 (`executar_query`) |

Total: 22 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
