# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Refatorada para MVC em
camadas — auditoria em `reports/audit-task-manager-api.md`.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # defina SECRET_KEY (obrigatória: a app não sobe sem ela)
python src/seed.py
python src/app.py
```

A aplicação sobe em `http://localhost:5000` (host, porta e debug vêm do `.env`). O `seed.py` recria o banco
SQLite (`instance/tasks.db`, na raiz do projeto) com usuários, categorias e tasks de exemplo — **rode-o antes
do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Autenticação

`POST /login` devolve um `token` assinado. Envie-o nas demais rotas:

```
Authorization: Bearer <token>
```

Rotas públicas: `GET /`, `GET /health`, `POST /login` e `POST /users` (cadastro com role `user`; outras roles
só por admin autenticado). Alterar ou apagar um usuário exige ser o próprio usuário ou admin; mudar `role`
exige admin.

## Estrutura

```
src/
├── app.py          composition root (create_app)
├── seed.py         popula o banco
├── config/         Settings lidas do ambiente
├── infra/          extensão SQLAlchemy + transação
├── models/         entidades, invariantes, constantes, erros de domínio e repositórios
├── services/       casos de uso (camada Controller)
├── routes/         Blueprints finos, serializers e parsing de entrada (camada View)
├── middlewares/    error handler central e guards de autenticação
└── utils/          funções utilitárias sem estado
```

Na raiz ficam só manifesto (`requirements.txt`), `.env.example`, documentação e `reports/`.
