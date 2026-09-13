const crypto = require('crypto');
const { UnauthorizedError } = require('../models/errors');

const digest = (value) => crypto.createHash('sha256').update(value).digest();

// Exige "Authorization: Bearer <ADMIN_TOKEN>". Compara digests para ter tempo constante
// independente do tamanho do token enviado.
function requireAdmin(adminToken) {
    const expected = digest(adminToken);

    return (req, res, next) => {
        const [scheme, token] = (req.get('authorization') || '').split(' ');
        if (scheme === 'Bearer' && token && crypto.timingSafeEqual(digest(token), expected)) {
            return next();
        }
        res.set('WWW-Authenticate', 'Bearer');
        next(new UnauthorizedError());
    };
}

module.exports = { requireAdmin };
