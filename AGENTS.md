# AGENTS.md

Instruções para agentes de IA (Claude Code, Codex, Copilot, Cursor etc.) que trabalham neste repositório.
Leia este arquivo inteiro antes de sugerir ou alterar código. Para a visão de produto, veja o `README.md`.

## Projeto

Data Warehouse local que simula um ambiente produtivo:

```
data/ (csv, txt, json) ─► Python (src/ingestion) ─► Postgres schema raw
                                                     │
                       dbt: staging ─► intermediate ─► marts (star schema) + snapshots (SCD2)
                                                     │
                         Airflow 3 (airflow/dags) orquestra ingestão + dbt build
                                                     │
                                Metabase lê apenas o schema marts
```

Este é um **projeto de mentoria**: o objetivo é o mentorado aprender. Explique as decisões
(o porquê, não só o como), prefira mudanças pequenas e revisáveis e não entregue o desafio
inteiro de uma vez.

## Stack e versões

| Componente | Versão | Onde está fixada |
|------------|--------|------------------|
| Python | 3.12 | `.python-version`, `pyproject.toml` |
| Gerenciador de pacotes | uv 0.13 | `uv.lock` (nunca editar à mão) |
| Postgres (DW) | 18 | `docker-compose.yml` |
| dbt-core / dbt-postgres | 1.11 | grupo `dbt` do `pyproject.toml` |
| Airflow | 3.3.2 (LocalExecutor) | `airflow/Dockerfile` |
| Metabase | v0.63 | `docker-compose.yml` |
| Lint/format/tipos | ruff, mypy (strict), sqlfluff | `pyproject.toml`, `.sqlfluff` |

## Comandos

Rode da raiz do repositório. Todo PR precisa passar em todos eles (são os mesmos do CI).

```bash
uv sync --group dbt                     # cria/atualiza o .venv com dev + dbt
uv run ruff check .                     # lint + regras de segurança (bandit)
uv run ruff format --check .            # formatação (use sem --check para corrigir)
uv run mypy                             # tipagem estrita em src/
uv run sqlfluff lint dbt/               # lint dos modelos SQL
uv run pytest                           # testes + cobertura (falha abaixo de 90%)
DW_PASSWORD=x uv run dbt parse --project-dir dbt --profiles-dir dbt

# Com a stack no ar (docker compose up -d):
docker compose exec airflow-scheduler python -m pytest /opt/airflow/tests -p no:cacheprovider
docker compose exec dbt dbt build       # roda modelos + testes do dbt no Postgres
```

Arquivo único: `uv run pytest tests/test_metadata.py -q` e `uv run ruff check src/ingestion/loader.py`.

## Estrutura

| Caminho | Conteúdo |
|---------|----------|
| `data/` | Arquivos brutos. **Somente leitura**: a sujeira (datas mistas, preços inválidos, nulos) é proposital e deve ser tratada no código |
| `src/ingestion/` | Pacote Python de ingestão. Uma pipeline por fonte, registrada em `main.PIPELINES` |
| `tests/` | Testes unitários do pacote `ingestion` (espelham os módulos de `src/`) |
| `dbt/models/staging/` | `stg_<fonte>`: 1:1 com `raw`, só renomeia, tipa e padroniza. Único lugar que usa `source()` |
| `dbt/models/intermediate/` | `int_<conceito>`: joins e regras de negócio reutilizáveis |
| `dbt/models/marts/` | `dim_<entidade>` e `fct_<processo>`, consumidos pelo Metabase |
| `dbt/snapshots/` | Histórico SCD tipo 2 |
| `airflow/dags/` | DAGs finas: só orquestram e chamam código de `src/` e o dbt |
| `airflow/tests/` | Testes de integridade das DAGs (rodam com Airflow instalado) |
| `postgres/init/` | SQL executado na criação do volume (schemas, roles) |
| `docker/`, `airflow/Dockerfile` | Imagens. `docker-compose.yml` sobe a stack inteira |
| `scripts/` | Utilitários do mentor (ex.: proteção da branch) |

## Convenções de código

**Python**
- Tipagem completa em `src/` (mypy strict). Use `X | None`, nunca `Optional[X]`.
- Funções pequenas e puras para transformação. I/O (arquivo, banco) fica nas bordas para facilitar teste.
- Logging com `logging.getLogger(__name__)` e placeholders (`logger.info("x=%s", x)`), nunca `print`.
- Toda carga adiciona metadados com `ingestion.metadata.add_ingestion_metadata`.
- Configuração só via variáveis de ambiente (`ingestion.config.DatabaseSettings.from_env`).

**SQL / dbt**
- Palavras-chave em minúsculas, CTEs nomeadas (`source`, `renamed`, `final`), colunas explícitas nos marts (sem `select *` no select final de um mart).
- Nomes em snake_case e português, seguindo os dados (`cliente_id`, `data_venda`).
- Todo modelo tem entrada em um `.yml` com descrição e testes: `unique` + `not_null` na chave, `relationships` nas FKs, `accepted_values` em domínios fechados.
- Crie uma dimensão de tempo (`dim_tempo`) e ao menos uma dimensão SCD2 via snapshot.

**Airflow**
- Imports do Airflow 3: `from airflow.sdk import DAG`, operadores de `airflow.providers.standard`.
- `catchup=False`, `tags` obrigatórias, `start_date` fixo, tarefas idempotentes.
- Nada pesado no topo do arquivo da DAG (conexão a banco, `Variable.get`, leitura de arquivo).

## Testes

- Testes são escritos **junto** com a funcionalidade, nunca depois.
- Padrão Arrange / Act / Assert, um comportamento por teste, nome descritivo (`test_<o_que>_<quando>`).
- Arquivos temporários com `tmp_path`; banco com mocks ou Postgres descartável. Teste unitário não depende da stack Docker.
- Cobertura mínima de 90% (`--cov-fail-under=90`). **Nunca** baixe o limite, use `# pragma: no cover` ou `pytest -k` para esconder falhas: corrija o código ou o teste.

## Segurança

- Zero credenciais em código, YAML, DAG, Dockerfile ou SQL. Use `.env` (ignorado pelo git) e mantenha o `.env.example` atualizado com valores fictícios.
- Nunca leia, imprima ou commite o `.env`.
- SQL parametrizado sempre (bind params do SQLAlchemy / `psycopg.sql.Identifier`); nada de f-string com valor externo.
- Menor privilégio: Metabase lê apenas `marts`; aplicações não usam o superusuário em produção.
- Actions do GitHub fixadas por SHA; imagens Docker com tag de versão (nunca `latest`).

## Git e Pull Requests

- **Nunca faça commit ou push na `master`.** Ela é protegida: merge só via PR aprovado pelo mentor com CI verde.
- Branches: `feature/<descricao>`, `fix/<descricao>`, `chore/<descricao>`.
- Commits no padrão Conventional Commits: `feat:`, `fix:`, `test:`, `refactor:`, `docs:`, `build:`, `ci:`.
- Um PR por assunto (ex.: "ingestão de clientes", "dim_produtos SCD2"), com testes no mesmo PR.
- Preencha o template de PR (`.github/pull_request_template.md`) e rode todos os comandos da seção **Comandos** antes de abrir.

## Limites

| Sempre | Pergunte antes | Nunca |
|--------|----------------|-------|
| Rodar lint, mypy e testes antes de concluir | Adicionar/atualizar dependências | Commitar segredos ou o `.env` |
| Escrever testes para código novo | Alterar `docker-compose.yml`, Dockerfiles ou o CI | Editar arquivos em `data/` |
| Seguir os padrões dos arquivos vizinhos | Mudar colunas/grão de um mart já usado no Metabase | Push na `master` ou force-push |
| Atualizar docs quando o comportamento muda | Rodar `DROP`/`TRUNCATE`/`--full-refresh` | Baixar o limite de cobertura ou pular testes |
