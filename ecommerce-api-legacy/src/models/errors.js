// Exceções de domínio. O status é o único ponto de contato com HTTP e só o
// errorHandler o lê; controllers e models apenas lançam.
class DomainError extends Error {
    constructor(message, status, options) {
        super(message, options);
        this.name = new.target.name;
        this.status = status;
    }
}

class ValidationError extends DomainError {
    constructor(message = 'Bad Request') {
        super(message, 400);
    }
}

class PaymentDeniedError extends DomainError {
    constructor(message = 'Pagamento recusado') {
        super(message, 400);
    }
}

class UnauthorizedError extends DomainError {
    constructor(message = 'Não autorizado') {
        super(message, 401);
    }
}

class NotFoundError extends DomainError {
    constructor(message, cause) {
        super(message, 404, { cause });
    }
}

class ConflictError extends DomainError {
    constructor(message) {
        super(message, 409);
    }
}

// Falha de I/O com mensagem pública fixa; o erro original fica em `cause` (só vai para o log).
class PersistenceError extends DomainError {
    constructor(message, cause) {
        super(message, 500, { cause });
    }
}

// Para usar em .catch(): erro de domínio passa direto, erro de I/O vira PersistenceError.
const persistenceFailure = (message) => (cause) => {
    if (cause instanceof DomainError) throw cause;
    throw new PersistenceError(message, cause);
};

module.exports = {
    DomainError,
    ValidationError,
    PaymentDeniedError,
    UnauthorizedError,
    NotFoundError,
    ConflictError,
    PersistenceError,
    persistenceFailure,
};
