// Constantes de domínio do LMS
const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// gateway fake: cartões que começam com 4 são aprovados
const APPROVED_CARD_PREFIX = '4';

const UNKNOWN_STUDENT = 'Unknown';

module.exports = { PAYMENT_STATUS, APPROVED_CARD_PREFIX, UNKNOWN_STUDENT };
