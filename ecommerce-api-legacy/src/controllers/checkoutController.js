const { PaymentStatus } = require('../models/constants');
const {
    NotFoundError,
    PaymentDeniedError,
    UnauthorizedError,
    persistenceFailure,
} = require('../models/errors');

class CheckoutController {
    constructor({ db, users, courses, enrollments, auditLogs, paymentGateway, cache, passwords }) {
        this.db = db;
        this.users = users;
        this.courses = courses;
        this.enrollments = enrollments;
        this.auditLogs = auditLogs;
        this.paymentGateway = paymentGateway;
        this.cache = cache;
        this.passwords = passwords;
    }

    async execute({ name, email, password, courseId, card }) {
        // erro de banco aqui responde 404, como no contrato original (a causa vai para o log)
        const course = await this.courses.findActiveById(courseId).catch((cause) => {
            throw new NotFoundError('Curso não encontrado', cause);
        });
        if (!course) throw new NotFoundError('Curso não encontrado');

        const userId = await this.resolveUser({ name, email, password });
        await this.enrollments.assertNotEnrolled({ userId, courseId }).catch(persistenceFailure('Erro DB'));

        const status = this.paymentGateway.charge({ card, amount: course.price });
        if (status === PaymentStatus.DENIED) throw new PaymentDeniedError();

        const enrollmentId = await this.db.transaction(async (tx) => {
            const id = await this.enrollments.create({ userId, courseId }, tx)
                .catch(persistenceFailure('Erro Matrícula'));
            await this.enrollments.recordPayment({ enrollmentId: id, amount: course.price, status }, tx)
                .catch(persistenceFailure('Erro Pagamento'));
            await this.auditLogs.record(`Checkout curso ${courseId} por ${userId}`, tx)
                .catch(persistenceFailure('Erro interno'));
            return id;
        });

        this.cache.set(`last_checkout_${userId}`, course.title);
        return { enrollmentId };
    }

    // Email já cadastrado exige a senha do dono. Usuário novo é criado antes da decisão de
    // pagamento: continua existindo se o pagamento for recusado (regra original).
    async resolveUser({ name, email, password }) {
        const user = await this.users.findByEmail(email).catch(persistenceFailure('Erro DB'));
        if (user) {
            const matches = await this.passwords.verify(password, user.passwordHash);
            if (!matches) throw new UnauthorizedError('Credenciais inválidas');
            return user.id;
        }

        const passwordHash = await this.passwords.hash(password);
        return this.users.create({ name, email, passwordHash })
            .catch(persistenceFailure('Erro ao criar usuário'));
    }
}

module.exports = { CheckoutController };
