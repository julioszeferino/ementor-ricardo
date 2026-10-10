"""Ponto de entrada da ingestão: `python -m ingestion.main`.

Cada fonte de `data/` vira uma função registrada em `PIPELINES`. Uma pipeline
recebe a pasta de dados e o engine e devolve quantas linhas carregou.

TODO (mentorado): implementar uma pipeline por fonte, cada uma com seus testes.
    - data/clientes/clientes.csv   -> raw.clientes
    - data/produtos/produtos.txt   -> raw.produtos   (separador `|`)
    - data/vendas/vendas2023.json  -> raw.vendas
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import Engine

from ingestion.loader import get_engine

logger = logging.getLogger(__name__)

Pipeline = Callable[[Path, Engine], int]

PIPELINES: dict[str, Pipeline] = {
    # "clientes": ingest_clientes,
}


def run(data_dir: Path, engine: Engine, pipelines: dict[str, Pipeline] | None = None) -> int:
    """Executa todas as pipelines e retorna o total de linhas carregadas."""
    pipelines = PIPELINES if pipelines is None else pipelines
    if not pipelines:
        logger.warning("Nenhuma pipeline registrada em PIPELINES")
    total = 0
    for name, pipeline in pipelines.items():
        logger.info("Iniciando pipeline %s", name)
        total += pipeline(data_dir, engine)
    return total


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    total = run(data_dir, get_engine())
    logger.info("Ingestão concluída: %d linhas", total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
