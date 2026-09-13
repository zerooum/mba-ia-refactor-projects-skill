const express = require('express');
const helmet = require('helmet');
const { loadConfig } = require('./config');
const { createDb } = require('./infra/db');
const { createSchema } = require('./infra/schema');
const { seed } = require('./infra/seed');
const { Cache } = require('./infra/cache');
const { createLogger } = require('./infra/logger');
const { FakePaymentGateway } = require('./infra/paymentGateway');
const passwords = require('./infra/password');
const { UserModel } = require('./models/userModel');
const { CourseModel } = require('./models/courseModel');
const { EnrollmentModel } = require('./models/enrollmentModel');
const { AuditLogModel } = require('./models/auditLogModel');
const { FinancialReportModel } = require('./models/financialReportModel');
const { CheckoutController } = require('./controllers/checkoutController');
const { FinancialReportController } = require('./controllers/financialReportController');
const { UserController } = require('./controllers/userController');
const { routes } = require('./routes');
const { requireAdmin } = require('./middlewares/auth');
const { checkoutRateLimit } = require('./middlewares/rateLimit');
const { errorHandler } = require('./middlewares/errorHandler');

// Composition root: monta o grafo de dependências e não faz mais nada.
async function createApp(config = loadConfig(), logger = createLogger()) {
    const db = createDb(config.databaseUrl, { verbose: config.debug });
    await createSchema(db);
    await seed(db, { hashPassword: passwords.hash });

    const users = new UserModel(db);
    const controllers = {
        checkoutController: new CheckoutController({
            db,
            users,
            courses: new CourseModel(db),
            enrollments: new EnrollmentModel(db),
            auditLogs: new AuditLogModel(db),
            paymentGateway: new FakePaymentGateway({ apiKey: config.paymentGatewayKey, logger }),
            cache: new Cache({ logger }),
            passwords,
        }),
        financialReportController: new FinancialReportController({
            financialReports: new FinancialReportModel(db),
        }),
        userController: new UserController({ users }),
    };
    const middlewares = {
        requireAdmin: requireAdmin(config.adminToken),
        checkoutRateLimit: checkoutRateLimit(config.checkoutRateLimit),
    };

    const app = express();
    app.use(helmet());
    app.use(express.json());
    app.use(routes(controllers, middlewares));
    app.use(errorHandler(logger));
    return { app, db };
}

async function start() {
    const config = loadConfig();
    const logger = createLogger();
    const { app } = await createApp(config, logger);
    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

if (require.main === module) {
    start().catch((err) => {
        createLogger().error('Falha no boot:', err.message);
        process.exit(1);
    });
}

module.exports = { createApp };
