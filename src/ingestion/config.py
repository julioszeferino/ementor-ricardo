"""Configuração lida de variáveis de ambiente (nunca coloque credenciais no código)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy.engine import URL


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> DatabaseSettings:
        """Monta as configurações a partir de `DW_*`. Falha cedo se a senha não existir."""
        env = os.environ if env is None else env
        password = env.get("DW_PASSWORD")
        if not password:
            raise ValueError("Variável de ambiente DW_PASSWORD não definida")
        return cls(
            host=env.get("DW_HOST", "localhost"),
            port=int(env.get("DW_PORT", "5432")),
            database=env.get("DW_DATABASE", "warehouse"),
            user=env.get("DW_USER", "postgres"),
            password=password,
        )

    @property
    def url(self) -> URL:
        # URL.create escapa caracteres especiais da senha e não a expõe no repr.
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )
