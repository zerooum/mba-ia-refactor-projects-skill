# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

Requer Node.js >= 20.12.

```bash
npm install
cp .env.example .env   # preencha PAYMENT_GATEWAY_KEY e ADMIN_TOKEN
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.
Sem `PAYMENT_GATEWAY_KEY` ou `ADMIN_TOKEN` o boot falha com mensagem indicando a variável ausente.

Exemplos de requisições estão em `api.http`.

## Rotas

| Método | Path | Auth |
|---|---|---|
| `POST` | `/api/checkout` | — (rate limit por IP: `CHECKOUT_RATE_LIMIT_MAX` / `CHECKOUT_RATE_LIMIT_WINDOW_MS`) |
| `GET` | `/api/admin/financial-report` | `Authorization: Bearer <ADMIN_TOKEN>` |
| `DELETE` | `/api/users/:id` | `Authorization: Bearer <ADMIN_TOKEN>` |

Regras do checkout: `usr`, `eml`, `pwd`, `card` (strings) e `c_id` são obrigatórios. Email já cadastrado exige a
senha do dono. Recompra do mesmo curso responde `409`. Usuário com matrícula não pode ser excluído (`409`).

## Estrutura

```
src/
├── config/        # variáveis de ambiente
├── infra/         # conexão/transação, schema, seed, cache, logger, hash de senha, gateway simulado
├── models/        # acesso a dados, constantes e erros de domínio
├── controllers/   # casos de uso (checkout, relatório financeiro, usuários)
├── routes/        # rotas HTTP e serialização das respostas
├── middlewares/   # auth, validação, rate limit, tratamento de erros
└── app.js         # composition root
```
