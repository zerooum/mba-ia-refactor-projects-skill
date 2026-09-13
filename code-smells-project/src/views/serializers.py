"""O que sai na resposta HTTP. Allowlist explícita de campos por entidade."""


def produto_publico(p):
    return {
        "id": p.id,
        "nome": p.nome,
        "descricao": p.descricao,
        "preco": p.preco,
        "estoque": p.estoque,
        "categoria": p.categoria,
        "ativo": p.ativo,
        "criado_em": p.criado_em,
    }


def usuario_publico(u):
    return {
        "id": u.id,
        "nome": u.nome,
        "email": u.email,
        "tipo": u.tipo,
        "criado_em": u.criado_em,
    }


def usuario_login(u):
    return {"id": u.id, "nome": u.nome, "email": u.email, "tipo": u.tipo}


def pedido_publico(p):
    return {
        "id": p.id,
        "usuario_id": p.usuario_id,
        "status": p.status,
        "total": p.total,
        "criado_em": p.criado_em,
        "itens": [
            {
                "produto_id": i.produto_id,
                "produto_nome": i.produto_nome,
                "quantidade": i.quantidade,
                "preco_unitario": i.preco_unitario,
            }
            for i in p.itens
        ],
    }
