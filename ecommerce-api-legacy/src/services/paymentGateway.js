const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../models/domain');

// Gateway simulado. A chave vem da config e nunca vai para o log.
class FakePaymentGateway {
  constructor({ apiKey, logger }) {
    this.apiKey = apiKey;
    this.logger = logger;
  }

  charge(card, amount) {
    this.logger.info(`Processando cartão final ${card.slice(-4)} no valor de ${amount}`);
    return card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
  }
}

module.exports = FakePaymentGateway;
