const { Router } = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function userRoutes({ userController }, { requireAdmin }) {
    const router = Router();

    router.delete('/api/users/:id', requireAdmin, asyncHandler(async (req, res) => {
        await userController.delete(req.params.id);
        res.send('Usuário deletado');
    }));

    return router;
}

module.exports = { userRoutes };
