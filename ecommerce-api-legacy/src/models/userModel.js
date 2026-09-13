const { isConstraintViolation } = require('../infra/db');
const { ConflictError } = require('./errors');

const USER_HAS_ENROLLMENTS = 'Usuário possui matrículas e pagamentos; exclusão bloqueada para preservar o histórico financeiro';

function toUser(row) {
    return row && { id: row.id, name: row.name, email: row.email, passwordHash: row.pass };
}

class UserModel {
    constructor(db) {
        this.db = db;
    }

    async findById(id, db = this.db) {
        return toUser(await db.get('SELECT id, name, email, pass FROM users WHERE id = ?', [id]));
    }

    async findByEmail(email, db = this.db) {
        return toUser(await db.get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]));
    }

    async create({ name, email, passwordHash }, db = this.db) {
        const { lastID } = await db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash],
        );
        return lastID;
    }

    // FK RESTRICT: usuário com matrícula não sai, para preservar o histórico financeiro.
    async deleteById(id, db = this.db) {
        try {
            const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
            return changes;
        } catch (err) {
            if (isConstraintViolation(err, 'FOREIGN KEY')) throw new ConflictError(USER_HAS_ENROLLMENTS);
            throw err;
        }
    }
}

module.exports = { UserModel };
