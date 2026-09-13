const PaymentStatus = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

// Nome exibido no relatório quando a matrícula aponta para um usuário inexistente.
const UNKNOWN_STUDENT = 'Unknown';

module.exports = { PaymentStatus, UNKNOWN_STUDENT };
