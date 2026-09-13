// Cache em memória com limite de entradas (FIFO). Substitui o globalCache sem limite.
class Cache {
    constructor({ maxSize = 500, logger }) {
        this.maxSize = maxSize;
        this.logger = logger;
        this.store = new Map();
    }

    get(key) {
        return this.store.get(key);
    }

    set(key, value) {
        this.logger.info(`[LOG] Salvando no cache: ${key}`);
        this.store.delete(key);
        if (this.store.size >= this.maxSize) {
            this.store.delete(this.store.keys().next().value);
        }
        this.store.set(key, value);
    }
}

module.exports = { Cache };
