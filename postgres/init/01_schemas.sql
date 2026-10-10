-- Executado apenas na PRIMEIRA subida do volume (docker-entrypoint-initdb.d).
-- Para reaplicar: docker compose down -v && docker compose up -d

CREATE SCHEMA IF NOT EXISTS raw;           -- dados brutos carregados pelo Python
CREATE SCHEMA IF NOT EXISTS staging;       -- dbt: limpeza/padronização (1:1 com as fontes)
CREATE SCHEMA IF NOT EXISTS intermediate;  -- dbt: regras de negócio intermediárias
CREATE SCHEMA IF NOT EXISTS marts;         -- dbt: fatos e dimensões consumidos pelo Metabase
CREATE SCHEMA IF NOT EXISTS snapshots;     -- dbt: histórico SCD2

-- TODO (mentorado): criar roles de menor privilégio
--   ingestion_role -> escreve apenas em raw
--   dbt_role       -> lê raw, escreve em staging/intermediate/marts/snapshots
--   metabase_role  -> SELECT apenas em marts
-- Senhas NÃO podem ficar neste arquivo.
