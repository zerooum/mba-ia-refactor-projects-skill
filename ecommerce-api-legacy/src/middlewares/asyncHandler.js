// Express 4 não encaminha rejeição de handler async ao errorHandler sozinho.
const asyncHandler = (handler) => (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
};

module.exports = { asyncHandler };
