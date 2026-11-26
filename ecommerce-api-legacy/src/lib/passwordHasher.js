const crypto = require('crypto');

const KEY_LENGTH = 64;

// scrypt com salt aleatório; formato salvo: "<salt>:<hash>"
function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
  return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
  const [salt, hash] = String(stored).split(':');
  if (!salt || !hash) return false;
  const candidate = crypto.scryptSync(password, salt, KEY_LENGTH);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}

function randomPassword() {
  return crypto.randomBytes(12).toString('base64url');
}

module.exports = { hashPassword, verifyPassword, randomPassword };
