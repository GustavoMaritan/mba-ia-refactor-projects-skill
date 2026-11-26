# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`, já refatorada para MVC.

## Como rodar

```bash
npm install
npm start                          # ou: PORT=5102 ADMIN_TOKEN=xyz npm start
```

A aplicação sobe em `http://localhost:3000` (porta via `PORT`). O banco SQLite é em memória por padrão (`DATABASE_FILE`) e carrega os seeds no boot.

Variáveis de ambiente: ver `.env.example`. `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem o header `X-Admin-Token` igual a `ADMIN_TOKEN` (sem `ADMIN_TOKEN` definido, respondem 403).

Exemplos de requisições estão em `api.http`.

## Estrutura

```
src/
  server.js                 # entry point: banco + schema/seed + listen
  app.js                    # createApp(): composition root (injeção de dependências)
  config/index.js           # configuração via ambiente
  database/                 # conexão promisificada com transação, schema e seed
  models/                   # repositories com SQL parametrizado + constantes de domínio
  services/                 # checkout, relatório, usuários, gateway fake, cache
  controllers/              # leitura do request e resposta
  routes/index.js           # mapa URL -> controller
  middlewares/              # errorHandler, asyncHandler, requireAdmin
  lib/passwordHasher.js     # hash scrypt com salt
```
