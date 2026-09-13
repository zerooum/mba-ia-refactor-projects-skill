const { NotFoundError, persistenceFailure } = require('../models/errors');

class UserController {
    constructor({ users }) {
        this.users = users;
    }

    async delete(id) {
        const user = await this.users.findById(id).catch(persistenceFailure('Erro DB'));
        if (!user) throw new NotFoundError('Usuário não encontrado');

        await this.users.deleteById(user.id).catch(persistenceFailure('Erro DB'));
    }
}

module.exports = { UserController };
