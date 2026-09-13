const { Router } = require('express');
const { checkoutRoutes } = require('./checkoutRoutes');
const { adminRoutes } = require('./adminRoutes');
const { userRoutes } = require('./userRoutes');

function routes(controllers, middlewares) {
    const router = Router();
    router.use(checkoutRoutes(controllers, middlewares));
    router.use(adminRoutes(controllers, middlewares));
    router.use(userRoutes(controllers, middlewares));
    return router;
}

module.exports = { routes };
