const { AppError, NotFoundError } = require('../errors');
const { PAYMENT_STATUS } = require('../models/domain');
const { hashPassword, randomPassword } = require('../lib/passwordHasher');

class CheckoutService {
  constructor({ db, users, courses, enrollments, payments, auditLogs, paymentGateway, cache, logger }) {
    Object.assign(this, { db, users, courses, enrollments, payments, auditLogs, paymentGateway, cache, logger });
  }

  async checkout({ name, email, password, courseId, card }) {
    const course = await this.courses.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    const status = this.paymentGateway.charge(card, course.price);
    if (status !== PAYMENT_STATUS.PAID) throw new AppError('Pagamento recusado', 400);

    const result = await this.db.transaction(async () => {
      let user = await this.users.findByEmail(email);
      let userId = user && user.id;
      if (!userId) {
        // sem senha informada, gera uma aleatória (antes era "123456" fixo)
        const passwordHash = hashPassword(password || randomPassword());
        userId = await this.users.create({ name, email, passwordHash });
      }
      const enrollmentId = await this.enrollments.create(userId, courseId);
      await this.payments.create(enrollmentId, course.price, status);
      await this.auditLogs.create(`Checkout curso ${courseId} por ${userId}`);
      return { userId, enrollmentId };
    });

    this.cache.set(`last_checkout_${result.userId}`, course.title);
    this.logger.debug(`checkout ok: matrícula ${result.enrollmentId}`);
    return result.enrollmentId;
  }
}

module.exports = CheckoutService;
