# Metabase

O Metabase sobe pelo `docker-compose.yml` em http://localhost:3000 e guarda sua
configuração no banco `metabase` do serviço `app-db` (persistida no volume `app-db-data`).

## Conectando ao Data Warehouse

No primeiro acesso, crie o usuário admin e adicione o banco:

| Campo    | Valor                                      |
|----------|--------------------------------------------|
| Tipo     | PostgreSQL                                 |
| Host     | `postgres` (nome do serviço, não localhost) |
| Porta    | `5432`                                     |
| Banco    | `warehouse`                                |
| Usuário  | idealmente um role somente leitura em `marts` |

## TODO (mentorado)

- Criar o `metabase_role` com `SELECT` apenas no schema `marts` (veja `postgres/init/01_schemas.sql`).
- Montar ao menos um dashboard de vendas usando a fato e as dimensões (incluindo a dimensão de tempo).
- Documentar aqui as perguntas/dashboards criados.
