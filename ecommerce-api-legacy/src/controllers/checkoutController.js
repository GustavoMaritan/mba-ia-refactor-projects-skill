const { AppError } = require('../errors');

// Os nomes dos campos (usr, eml, pwd, c_id, card) fazem parte do contrato da API.
function parseCheckout(body) {
  const { usr, eml, pwd, c_id: courseId, card } = body || {};
  if (!usr || !eml || !courseId || !card) throw new AppError('Bad Request', 400);
  if (typeof card !== 'string' && typeof card !== 'number') throw new AppError('Bad Request', 400);
  return { name: usr, email: eml, password: pwd, courseId, card: String(card) };
}

function checkoutController(checkoutService) {
  return {
    async create(req, res) {
      const enrollmentId = await checkoutService.checkout(parseCheckout(req.body));
      res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    },
  };
}

module.exports = checkoutController;
