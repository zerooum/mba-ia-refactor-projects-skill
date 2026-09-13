const { rateLimit } = require('express-rate-limit');

// Limita tentativas de checkout por IP (mitiga card testing).
function checkoutRateLimit({ windowMs, limit }) {
    return rateLimit({
        windowMs,
        limit,
        message: 'Muitas requisições, tente novamente mais tarde',
        standardHeaders: 'draft-8',
        legacyHeaders: false,
    });
}

module.exports = { checkoutRateLimit };
