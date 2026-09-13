const sqlite3 = require('sqlite3');
const { promisify } = require('util');

// Executor sem lock: usado direto pela transação, que já detém o lock.
function createExecutor(conn) {
    return {
        run(sql, params = []) {
            return new Promise((resolve, reject) => {
                // function (não arrow): o sqlite3 expõe lastID/changes em this
                conn.run(sql, params, function onRun(err) {
                    if (err) return reject(err);
                    resolve({ lastID: this.lastID, changes: this.changes });
                });
            });
        },
        get: promisify(conn.get.bind(conn)),
        all: promisify(conn.all.bind(conn)),
    };
}

// Uma conexão só (o banco é :memory:), então todo acesso passa por uma fila:
// sem isso, statements de outra requisição cairiam dentro de um BEGIN aberto.
class Database {
    constructor(conn) {
        this.conn = conn;
        this.executor = createExecutor(conn);
        this.queue = Promise.resolve();
    }

    exclusive(task) {
        const result = this.queue.then(task);
        // a fila não pode travar numa rejeição; quem chamou recebe o erro via `result`
        this.queue = result.catch(() => {});
        return result;
    }

    run(sql, params) {
        return this.exclusive(() => this.executor.run(sql, params));
    }

    get(sql, params) {
        return this.exclusive(() => this.executor.get(sql, params));
    }

    all(sql, params) {
        return this.exclusive(() => this.executor.all(sql, params));
    }

    transaction(work) {
        return this.exclusive(async () => {
            const tx = this.executor;
            await tx.run('BEGIN IMMEDIATE');
            try {
                const result = await work(tx);
                await tx.run('COMMIT');
                return result;
            } catch (err) {
                await tx.run('ROLLBACK');
                throw err;
            }
        });
    }

    close() {
        return this.exclusive(() => promisify(this.conn.close.bind(this.conn))());
    }
}

// kind: 'UNIQUE' | 'FOREIGN KEY'
function isConstraintViolation(err, kind) {
    return err.code === 'SQLITE_CONSTRAINT' && err.message.includes(`${kind} constraint failed`);
}

function createDb(filename, { verbose = false } = {}) {
    const driver = verbose ? sqlite3.verbose() : sqlite3;
    return new Database(new driver.Database(filename));
}

module.exports = { createDb, isConstraintViolation };
