const { AppError } = require('../errors');

function errorHandler(logger) {
  // eslint-disable-next-line no-unused-vars
  return (err, req, res, next) => {
    if (err instanceof AppError) return res.status(err.status).send(err.message);
    if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');
    logger.error(err);
    res.status(500).send('Erro interno');
  };
}

module.exports = errorHandler;
