const http = require('http');
const { DomainError } = require('../models/errors');

// Registrado depois de todas as rotas. Respostas em texto puro, como no contrato original;
// detalhe do erro só vai para o log.
function errorHandler(logger) {
    // 4 parâmetros: é assim que o Express reconhece um middleware de erro
    return (err, req, res, next) => {
        if (err instanceof DomainError) {
            if (err.cause) logger.error(`${req.method} ${req.path}: ${err.message}`, err.cause);
            return res.status(err.status).send(err.message);
        }
        // erros do body parser (JSON malformado, body grande demais) já trazem status 4xx
        if (err.expose && err.status >= 400 && err.status < 500) {
            return res.status(err.status).send(http.STATUS_CODES[err.status]);
        }
        logger.error(`${req.method} ${req.path}: erro não tratado`, err);
        res.status(500).send('Erro interno');
    };
}

module.exports = { errorHandler };
