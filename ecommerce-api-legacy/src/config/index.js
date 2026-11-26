// Configuração vinda do ambiente. Segredos não têm valor padrão.
module.exports = {
  port: Number(process.env.PORT) || 3000,
  databaseFile: process.env.DATABASE_FILE || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  // rotas administrativas ficam fechadas enquanto ADMIN_TOKEN não for definido
  adminToken: process.env.ADMIN_TOKEN || '',
  logLevel: process.env.LOG_LEVEL || 'info',
};
