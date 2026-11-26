# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, já refatorada para MVC.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                    # ou: PORT=5101 python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (porta/host via `PORT`/`HOST`). O banco SQLite (`loja.db`) é criado no primeiro boot, com produtos e usuários de exemplo (senhas gravadas com hash).

Variáveis de ambiente: ver `.env.example`. As rotas `/admin/*` só respondem com o header `X-Admin-Token` igual a `ADMIN_TOKEN`; sem `ADMIN_TOKEN` definido elas devolvem 403.

## Estrutura

```
app.py                      # entry point
src/
  app.py                    # create_app(): composition root
  config/settings.py        # configuração via ambiente
  database.py               # conexão por request, schema e seed
  errors.py                 # exceções de domínio
  models/                   # acesso a dados (SQL parametrizado) + constantes de domínio
  services/                 # regras de negócio, transações, notificações
  controllers/              # leitura do request e montagem da resposta
  views/routes.py           # mapa URL -> controller
  middlewares/              # error handler central e auth das rotas admin
```
