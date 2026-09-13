# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # preencha SECRET_KEY (obrigatória), ADMIN_TOKEN e as senhas SEED_SENHA_*
python app.py
```

A aplicação sobe em `http://localhost:5000` (configurável por `HOST`/`PORT`). O banco SQLite (`loja.db`, ou
`DB_PATH`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo. As senhas dos
usuários de exemplo vêm de `SEED_SENHA_*`; sem elas, o usuário é criado com senha aleatória.

As rotas `/admin/*` exigem o header `X-Admin-Token` com o valor de `ADMIN_TOKEN`; sem `ADMIN_TOKEN`
configurado elas ficam desabilitadas.

## Estrutura

```
app.py                  # entrypoint: python app.py
src/
├── app.py              # composition root (create_app)
├── config/             # configuração lida do ambiente
├── infra/              # conexão SQLite por request, schema/seed, notificador
├── models/             # entidades, invariantes, erros de domínio, repositórios
├── controllers/        # casos de uso
├── views/              # blueprints e serializers
└── middlewares/        # error handler central, autenticação admin
```
