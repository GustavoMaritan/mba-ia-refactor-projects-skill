// Erros de domínio; o errorHandler traduz para HTTP (corpo em texto, como na API original)
class AppError extends Error {
  constructor(message, status = 400) {
    super(message);
    this.status = status;
  }
}

class NotFoundError extends AppError {
  constructor(message) {
    super(message, 404);
  }
}

module.exports = { AppError, NotFoundError };
