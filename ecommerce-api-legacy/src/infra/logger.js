// Logger mínimo: um ponto só para trocar por pino/winston depois.
function createLogger(sink = console) {
    return {
        info: (message) => sink.log(message),
        error: (message, err) => sink.error(message, err),
    };
}

module.exports = { createLogger };
