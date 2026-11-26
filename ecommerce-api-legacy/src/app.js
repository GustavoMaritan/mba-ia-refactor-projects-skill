// Composition root: cria as dependências e injeta nas camadas.
const express = require('express');

const AuditLogModel = require('./models/auditLogModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const UserModel = require('./models/userModel');
const CheckoutService = require('./services/checkoutService');
const FakePaymentGateway = require('./services/paymentGateway');
const MemoryCache = require('./services/memoryCache');
const ReportService = require('./services/reportService');
const UserService = require('./services/userService');
const checkoutController = require('./controllers/checkoutController');
const reportController = require('./controllers/reportController');
const userController = require('./controllers/userController');
const buildRoutes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');
const requireAdmin = require('./middlewares/requireAdmin');

function createApp({ db, config, logger }) {
  const models = {
    users: new UserModel(db),
    courses: new CourseModel(db),
    enrollments: new EnrollmentModel(db),
    payments: new PaymentModel(db),
    auditLogs: new AuditLogModel(db),
  };

  const checkoutService = new CheckoutService({
    db,
    ...models,
    paymentGateway: new FakePaymentGateway({ apiKey: config.paymentGatewayKey, logger }),
    cache: new MemoryCache(),
    logger,
  });
  const reportService = new ReportService(models);
  const userService = new UserService({ db, ...models, logger });

  const app = express();
  app.use(express.json());
  app.use(buildRoutes({
    checkout: checkoutController(checkoutService),
    reports: reportController(reportService),
    users: userController(userService),
    requireAdmin: requireAdmin(config.adminToken),
  }));
  app.use(errorHandler(logger));
  return app;
}

module.exports = { createApp };
