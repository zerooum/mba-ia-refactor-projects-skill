const { ValidationError } = require('../models/errors');

const isFilledString = (value) => typeof value === 'string' && value.length > 0;
const isId = (value) => (typeof value === 'number' || typeof value === 'string') && Boolean(value);

// Validação de formato do body do checkout; entrega a entrada já traduzida em req.checkoutInput.
// Tipo errado responde 400 em vez de estourar dentro do fluxo de pagamento.
function validateCheckout(req, res, next) {
    const { usr, eml, pwd, c_id, card } = req.body || {};
    const valid = isFilledString(usr) && isFilledString(eml) && isFilledString(pwd)
        && isId(c_id) && isFilledString(card);
    if (!valid) return next(new ValidationError());

    req.checkoutInput = { name: usr, email: eml, password: pwd, courseId: c_id, card };
    next();
}

module.exports = { validateCheckout };
