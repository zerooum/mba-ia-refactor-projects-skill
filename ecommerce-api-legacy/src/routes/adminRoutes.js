const { Router } = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');
const { financialReportResponse } = require('./serializers');

function adminRoutes({ financialReportController }, { requireAdmin }) {
    const router = Router();

    router.get('/api/admin/financial-report', requireAdmin, asyncHandler(async (req, res) => {
        res.json(financialReportResponse(await financialReportController.generate()));
    }));

    return router;
}

module.exports = { adminRoutes };
