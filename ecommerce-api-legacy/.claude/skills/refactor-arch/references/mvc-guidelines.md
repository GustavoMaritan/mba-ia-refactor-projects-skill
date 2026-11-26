# Guidelines de arquitetura MVC (APIs backend)

Em uma API não há template HTML: a **View** é a camada de apresentação HTTP — definição das rotas e a serialização da resposta (JSON). Para não engordar o controller, a regra de negócio fica em **services**.

## Camadas e responsabilidades

| Camada | Faz | Não faz |
|---|---|---|
| `config/` | lê variáveis de ambiente, define padrões seguros, constantes de ambiente | lógica, acesso a banco |
| `database` / `db` | cria conexão/pool/sessão, schema, migrations, seed | regra de negócio, HTTP |
| `models/` | entidades, mapeamento de tabelas, queries parametrizadas (repository), regras intrínsecas da entidade (ex.: `is_overdue`) | ler `request`, montar resposta HTTP, enviar e-mail |
| `services/` | casos de uso: regras de negócio, orquestração de models, transações, efeitos colaterais (notificação) via dependência injetada | conhecer `request`/`response`, status HTTP |
| `controllers/` | extrai e valida dados do request, chama o service, escolhe status code e devolve a view | SQL, regra de negócio, `try/except` genérico |
| `views/` ou `routes/` | mapeia método + URL → controller; serializers/presenters que definem o formato do JSON | lógica |
| `middlewares/` | error handler central, autenticação/autorização, logging de request | regra de negócio |
| entry point / composition root | cria a app (`create_app()` / `createApp()`), carrega config, instancia dependências e injeta, registra rotas e middlewares, sobe o servidor | qualquer lógica de domínio |

## Direção das dependências

```
routes/views → controllers → services → models → database
                     ↑            ↑
              middlewares     config (injetada pelo composition root)
```

- Camada de baixo nunca importa a de cima (model não importa controller).
- Dependências de infraestrutura (conexão, notificador, gateway de pagamento, cache) são **criadas no composition root** e passadas por parâmetro/construtor.
- Erros de domínio são exceções próprias (`NotFoundError`, `ValidationError`, `BusinessRuleError`) levantadas no service e traduzidas para HTTP no error handler.

## Estrutura-alvo por stack

### Python / Flask
```
<projeto>/
├── app.py                      # entry point: from src.app import create_app; app.run(...)
├── src/
│   ├── app.py                  # create_app(): composition root
│   ├── config/settings.py      # Settings lido de os.environ
│   ├── database.py             # conexão por request (g) ou SQLAlchemy(); schema + seed
│   ├── models/                 # um módulo por agregado
│   ├── services/               # um módulo por caso de uso/agregado
│   ├── controllers/            # funções/classes finas
│   ├── views/routes.py         # Blueprint(s) com add_url_rule → controller
│   └── middlewares/
│       ├── error_handler.py    # @app.errorhandler para exceções de domínio e 500
│       └── auth.py             # decorators de autorização
└── requirements.txt
```
Projetos que já têm `models/`, `routes/`, `services/` na raiz podem manter a raiz como pacote (sem `src/`) desde que adicionem `config/`, `controllers/`, `middlewares/` e um `create_app()`.

### Node.js / Express
```
<projeto>/
├── package.json                # "start": "node src/server.js"
└── src/
    ├── server.js               # entry point: createApp() + listen(config.port)
    ├── app.js                  # createApp(deps): composition root
    ├── config/index.js         # process.env com padrões
    ├── database/connection.js  # abre o banco, helpers promisificados, transação
    ├── database/schema.js      # schema + seed
    ├── models/                 # repositories com SQL parametrizado
    ├── services/               # regras de negócio, async/await
    ├── controllers/            # (req, res) finos
    ├── routes/index.js         # express.Router() → controllers
    └── middlewares/            # errorHandler(err, req, res, next), asyncHandler, auth
```

### Outras stacks (mesmo princípio)
- **Java/Spring:** `config`, `entity`/`model`, `repository`, `service`, `controller` (`@RestController`), `dto`, `exception` (`@ControllerAdvice`).
- **PHP/Laravel:** `config/`, `app/Models`, `app/Services`, `app/Http/Controllers`, `routes/api.php`, `app/Exceptions/Handler.php`.
- **Go:** `internal/config`, `internal/model`, `internal/repository`, `internal/service`, `internal/handler`, `cmd/api/main.go` como composition root.

## Regras para preservar o contrato HTTP
1. Mesma URL, método, status code, chaves do JSON e tipo de corpo (JSON vs texto).
2. Mensagens de erro iguais às originais (o cliente pode depender delas).
3. Ordem de listas: mantenha a ordenação implícita original (normalmente por `id`); deixe-a explícita com `ORDER BY`.
4. Mudanças de comportamento só por segurança/integridade e sempre documentadas no resumo da Fase 3.

## Checklist de conclusão
- [ ] Nenhum segredo literal no código; tudo vem de `config`.
- [ ] Models sem `request`/HTTP; queries parametrizadas.
- [ ] Controllers com poucas linhas por handler e sem SQL.
- [ ] Services com as regras e as transações.
- [ ] Rotas declaradas em um lugar só.
- [ ] Um único error handler define o formato de erro e loga o detalhe.
- [ ] Entry point claro; app sobe com um comando; porta via env.
