-- EXEMPLO de modelo staging: 1:1 com a fonte, só renomeia, tipa e padroniza.
-- Use-o como referência para stg_produtos e stg_vendas.
with

source as (
    select * from {{ source('raw', 'clientes') }}
),

renamed as (
    select
        cast(id_cliente as integer) as cliente_id,
        trim(nome) as nome,
        lower(trim(email)) as email,
        trim(cidade) as cidade,
        upper(trim(estado)) as uf,
        _ingested_at
    from source
)

select * from renamed
