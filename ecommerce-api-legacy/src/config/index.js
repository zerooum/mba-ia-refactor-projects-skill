const path = require('path');

const ENV_FILE = path.resolve(__dirname, '..', '..', '.env');

function loadEnvFile(file) {
    try {
        process.loadEnvFile(file);
    } catch (err) {
        if (err.code !== 'ENOENT') throw err;
    }
}

function required(env, name) {
    const value = env[name];
    if (!value) {
        throw new Error(`Variável de ambiente obrigatória ausente: ${name} (veja .env.example)`);
    }
    return value;
}

function loadConfig(env = process.env) {
    if (env === process.env) loadEnvFile(ENV_FILE);

    return {
        port: Number(env.PORT || 3000),
        debug: env.DEBUG === 'true',
        databaseUrl: env.DATABASE_URL || ':memory:',
        paymentGatewayKey: required(env, 'PAYMENT_GATEWAY_KEY'),
        adminToken: required(env, 'ADMIN_TOKEN'),
        checkoutRateLimit: {
            windowMs: Number(env.CHECKOUT_RATE_LIMIT_WINDOW_MS || 60_000),
            limit: Number(env.CHECKOUT_RATE_LIMIT_MAX || 10),
        },
    };
}

module.exports = { loadConfig };
