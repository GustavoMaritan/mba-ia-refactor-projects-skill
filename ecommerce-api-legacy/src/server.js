// Entry point: abre o banco, prepara schema/seed e sobe o HTTP.
const config = require('./config');
const Database = require('./database/connection');
const { createSchema, seed } = require('./database/schema');
const { createApp } = require('./app');
const { createLogger } = require('./logger');

async function main() {
  const logger = createLogger(config.logLevel);
  const db = new Database(config.databaseFile);
  await createSchema(db);
  await seed(db);

  const app = createApp({ db, config, logger });
  app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}`));
}

main().catch((err) => {
  console.error('falha ao iniciar', err);
  process.exit(1);
});
