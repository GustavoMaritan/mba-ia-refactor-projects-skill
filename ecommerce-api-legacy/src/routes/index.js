const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

// Mapa de rotas -> controllers. Rotas administrativas passam pelo requireAdmin.
function buildRoutes({ checkout, reports, users, requireAdmin }) {
  const router = express.Router();
  router.post('/api/checkout', asyncHandler(checkout.create));
  router.get('/api/admin/financial-report', requireAdmin, asyncHandler(reports.financial));
  router.delete('/api/users/:id', requireAdmin, asyncHandler(users.remove));
  return router;
}

module.exports = buildRoutes;
