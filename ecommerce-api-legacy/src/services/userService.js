class UserService {
  constructor({ db, users, enrollments, payments, logger }) {
    Object.assign(this, { db, users, enrollments, payments, logger });
  }

  // remove o usuário junto com matrículas e pagamentos (antes ficavam órfãos)
  async delete(userId) {
    await this.db.transaction(async () => {
      await this.payments.deleteByUser(userId);
      await this.enrollments.deleteByUser(userId);
      await this.users.delete(userId);
    });
    this.logger.info(`usuário ${userId} removido`);
  }
}

module.exports = UserService;
