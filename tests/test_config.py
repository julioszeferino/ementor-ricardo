import pytest

from ingestion.config import DatabaseSettings


def test_from_env_uses_defaults_when_only_password_is_set() -> None:
    settings = DatabaseSettings.from_env({"DW_PASSWORD": "secret"})

    assert settings.host == "localhost"
    assert settings.port == 5432
    assert settings.database == "warehouse"
    assert settings.user == "postgres"


def test_from_env_reads_all_variables() -> None:
    env = {
        "DW_HOST": "postgres",
        "DW_PORT": "6543",
        "DW_DATABASE": "dw",
        "DW_USER": "ingestion",
        "DW_PASSWORD": "secret",
    }

    settings = DatabaseSettings.from_env(env)

    assert settings == DatabaseSettings("postgres", 6543, "dw", "ingestion", "secret")


def test_from_env_fails_without_password() -> None:
    with pytest.raises(ValueError, match="DW_PASSWORD"):
        DatabaseSettings.from_env({})


def test_url_hides_password_in_repr() -> None:
    url = DatabaseSettings("h", 5432, "db", "u", "p@ss").url

    assert url.password == "p@ss"
    assert "p@ss" not in repr(url)
