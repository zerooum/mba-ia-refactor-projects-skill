const { PaymentStatus } = require('../models/constants');

// Gateway simulado: cartão começando com "4" é aprovado.
const APPROVED_CARD_PREFIX = '4';
const VISIBLE_CARD_DIGITS = 4;

// Nunca logar PAN completo (PCI-DSS) nem a chave do gateway.
const maskCard = (card) => `****${card.slice(-VISIBLE_CARD_DIGITS)}`;

class FakePaymentGateway {
    constructor({ apiKey, logger }) {
        this.apiKey = apiKey;
        this.logger = logger;
    }

    charge({ card }) {
        this.logger.info(`Processando cartão ${maskCard(card)}`);
        return card.startsWith(APPROVED_CARD_PREFIX) ? PaymentStatus.PAID : PaymentStatus.DENIED;
    }
}

module.exports = { FakePaymentGateway };
