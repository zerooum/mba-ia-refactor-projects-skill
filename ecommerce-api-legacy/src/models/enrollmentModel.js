const { isConstraintViolation } = require('../infra/db');
const { ConflictError } = require('./errors');

const ALREADY_ENROLLED = 'Usuário já matriculado neste curso';

// Agregado matrícula + pagamento.
class EnrollmentModel {
    constructor(db) {
        this.db = db;
    }

    async assertNotEnrolled({ userId, courseId }, db = this.db) {
        const row = await db.get('SELECT 1 FROM enrollments WHERE user_id = ? AND course_id = ?', [userId, courseId]);
        if (row) throw new ConflictError(ALREADY_ENROLLED);
    }

    async create({ userId, courseId }, db = this.db) {
        try {
            const { lastID } = await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
            return lastID;
        } catch (err) {
            if (isConstraintViolation(err, 'UNIQUE')) throw new ConflictError(ALREADY_ENROLLED);
            throw err;
        }
    }

    async recordPayment({ enrollmentId, amount, status }, db = this.db) {
        const { lastID } = await db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status],
        );
        return lastID;
    }
}

module.exports = { EnrollmentModel };
