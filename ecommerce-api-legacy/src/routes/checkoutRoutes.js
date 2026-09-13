const { Router } = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');
const { validateCheckout } = require('../middlewares/validate');
const { checkoutResponse } = require('./serializers');

function checkoutRoutes({ checkoutController }, { checkoutRateLimit }) {
    const router = Router();

    router.post('/api/checkout', checkoutRateLimit, validateCheckout, asyncHandler(async (req, res) => {
        const result = await checkoutController.execute(req.checkoutInput);
        res.status(200).json(checkoutResponse(result));
    }));

    return router;
}

module.exports = { checkoutRoutes };
