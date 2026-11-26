# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`, já refatorada para MVC (controllers + services + app factory).

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py                    # ou: PORT=5103 python app.py  /  flask --app app run
```

A aplicação sobe em `http://127.0.0.1:5000` (porta/host via `PORT`/`HOST`). O `seed.py` recria o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — rode antes do primeiro boot. Configuração: ver `.env.example` (lido também de um `.env` local).

## Estrutura

```
app.py                  # create_app(): entry point e composition root
config/settings.py      # configuração via ambiente
database.py             # instância do SQLAlchemy
errors.py               # exceções de domínio
models/                 # entidades ORM + constants.py
services/               # regras de negócio (tasks, users, categories, reports, notificações)
controllers/            # leitura do request e resposta
routes/                 # blueprints: só mapeiam URL -> controller
middlewares/            # error handler central
utils/helpers.py        # utilitários (datas UTC, e-mail, cor, percentual)
seed.py
```
