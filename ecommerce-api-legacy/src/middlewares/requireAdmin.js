const crypto = require('crypto');

function safeEqual(a, b) {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  return bufA.length === bufB.length && crypto.timingSafeEqual(bufA, bufB);
}

// Exige X-Admin-Token igual ao ADMIN_TOKEN; sem token configurado, nega sempre.
function requireAdmin(adminToken) {
  return (req, res, next) => {
    const sent = req.get('X-Admin-Token') || '';
    if (!adminToken || !safeEqual(sent, adminToken)) return res.status(403).send('Acesso negado');
    next();
  };
}

module.exports = requireAdmin;
