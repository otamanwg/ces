import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.app.core.config import Settings


def _production_env(**overrides: str) -> dict[str, str]:
    env = {
        "CITY_ENV": "production",
        "CITY_DATABASE_URL": "postgresql+psycopg2://city:secret@postgres:5432/city_game",
        "REDIS_URL": "redis://:secret@redis:6379/0",
        "CITY_CORS_ORIGINS": "https://game.example.test",
        "CITY_DEBUG": "false",
        "CITY_RELEASE_SHA": "test-release-sha",
        "CITY_RELEASE_IMAGE": "registry.example.test/ces-backend:test-release-sha",
        "CITY_RELEASE_VERSION": "0.3.0-test",
    }
    env.update(overrides)
    return env


def test_production_rejects_debug() -> None:
    with (
        patch.dict(os.environ, _production_env(CITY_DEBUG="true"), clear=True),
        pytest.raises(ValueError, match="CITY_DEBUG"),
    ):
        Settings().validate()


def test_production_rejects_wildcard_cors() -> None:
    with (
        patch.dict(os.environ, _production_env(CITY_CORS_ORIGINS="*"), clear=True),
        pytest.raises(ValueError, match="Wildcard"),
    ):
        Settings().validate()


def test_production_rejects_non_https_cors_origin() -> None:
    with (
        patch.dict(os.environ, _production_env(CITY_CORS_ORIGINS="http://game.example.test"), clear=True),
        pytest.raises(ValueError, match="https"),
    ):
        Settings().validate()


def test_production_rejects_database_url_without_password() -> None:
    with (
        patch.dict(
            os.environ,
            _production_env(CITY_DATABASE_URL="postgresql+psycopg2://city@postgres:5432/city_game"),
            clear=True,
        ),
        pytest.raises(ValueError, match="CITY_DATABASE_URL"),
    ):
        Settings().validate()


def test_production_rejects_redis_url_without_password() -> None:
    with (
        patch.dict(os.environ, _production_env(REDIS_URL="redis://redis:6379/0"), clear=True),
        pytest.raises(ValueError, match="REDIS_URL"),
    ):
        Settings().validate()


def test_production_rejects_development_credentials() -> None:
    with (
        patch.dict(
            os.environ,
            _production_env(
                CITY_DATABASE_URL="postgresql+psycopg2://city:city_dev_password@postgres:5432/city_game",
            ),
            clear=True,
        ),
        pytest.raises(ValueError, match="development credential"),
    ):
        Settings().validate()


def test_scheduler_lock_rejects_renew_interval_not_below_ttl() -> None:
    with (
        patch.dict(
            os.environ,
            _production_env(
                CITY_SCHEDULER_LOCK_TTL_SECONDS="15",
                CITY_SCHEDULER_LOCK_RENEW_SECONDS="15",
            ),
            clear=True,
        ),
        pytest.raises(ValueError, match="CITY_SCHEDULER_LOCK_RENEW_SECONDS"),
    ):
        Settings().validate()


def test_scheduler_lock_rejects_nonpositive_retry_interval() -> None:
    with (
        patch.dict(
            os.environ,
            _production_env(CITY_SCHEDULER_LOCK_RETRY_SECONDS="0"),
            clear=True,
        ),
        pytest.raises(ValueError, match="CITY_SCHEDULER_LOCK_RETRY_SECONDS"),
    ):
        Settings().validate()


def test_log_format_rejects_unknown_value() -> None:
    with (
        patch.dict(
            os.environ,
            _production_env(CITY_LOG_FORMAT="xml"),
            clear=True,
        ),
        pytest.raises(ValueError, match="CITY_LOG_FORMAT"),
    ):
        Settings().validate()


@pytest.mark.parametrize("missing_name", ["CITY_RELEASE_SHA", "CITY_RELEASE_IMAGE", "CITY_RELEASE_VERSION"])
def test_production_requires_release_metadata(missing_name: str) -> None:
    env = _production_env()
    del env[missing_name]
    with (
        patch.dict(os.environ, env, clear=True),
        pytest.raises(ValueError, match=missing_name),
    ):
        Settings().validate()


def test_migrations_on_startup_default_to_false_in_production() -> None:
    with patch.dict(os.environ, _production_env(), clear=True):
        assert Settings().run_migrations_on_startup is False


def test_migrations_on_startup_default_to_true_in_development() -> None:
    with patch.dict(os.environ, {"CITY_ENV": "development"}, clear=True):
        assert Settings().run_migrations_on_startup is True


@pytest.mark.parametrize("missing_name", ["CITY_DATABASE_URL", "REDIS_URL"])
def test_production_requires_dependency_urls(missing_name: str) -> None:
    env = _production_env()
    del env[missing_name]
    with (
        patch.dict(os.environ, env, clear=True),
        pytest.raises(ValueError, match=missing_name),
    ):
        Settings().validate()


def test_production_accepts_dependency_urls_from_files(tmp_path: Path) -> None:
    database_url_file = tmp_path / "database_url"
    redis_url_file = tmp_path / "redis_url"
    database_url_file.write_text("postgresql+psycopg2://city:file-secret@postgres:5432/city_game", encoding="utf-8")
    redis_url_file.write_text("redis://:file-secret@redis:6379/0", encoding="utf-8")

    env = _production_env()
    del env["CITY_DATABASE_URL"]
    del env["REDIS_URL"]
    env["CITY_DATABASE_URL_FILE"] = str(database_url_file)
    env["REDIS_URL_FILE"] = str(redis_url_file)

    with patch.dict(os.environ, env, clear=True):
        settings = Settings()
        settings.validate()

    assert settings.database_url == "postgresql+psycopg2://city:file-secret@postgres:5432/city_game"
    assert settings.redis_url == "redis://:file-secret@redis:6379/0"


def test_file_dependency_urls_override_plain_env_values(tmp_path: Path) -> None:
    database_url_file = tmp_path / "database_url"
    redis_url_file = tmp_path / "redis_url"
    database_url_file.write_text("postgresql+psycopg2://city:file-secret@postgres:5432/city_game", encoding="utf-8")
    redis_url_file.write_text("redis://:file-secret@redis:6379/0", encoding="utf-8")

    env = _production_env(
        CITY_DATABASE_URL="postgresql+psycopg2://city:city_dev_password@postgres:5432/city_game",
        REDIS_URL="redis://:city_dev_password@redis:6379/0",
        CITY_DATABASE_URL_FILE=str(database_url_file),
        REDIS_URL_FILE=str(redis_url_file),
    )

    with patch.dict(os.environ, env, clear=True):
        settings = Settings()
        settings.validate()

    assert "city_dev_password" not in settings.database_url
    assert "city_dev_password" not in settings.redis_url


def test_file_dependency_url_missing_file_has_clear_error(tmp_path: Path) -> None:
    missing_database_url_file = tmp_path / "missing_database_url"
    redis_url_file = tmp_path / "redis_url"
    redis_url_file.write_text("redis://:file-secret@redis:6379/0", encoding="utf-8")

    env = _production_env()
    del env["CITY_DATABASE_URL"]
    del env["REDIS_URL"]
    env["CITY_DATABASE_URL_FILE"] = str(missing_database_url_file)
    env["REDIS_URL_FILE"] = str(redis_url_file)

    with (
        patch.dict(os.environ, env, clear=True),
        pytest.raises(ValueError, match="CITY_DATABASE_URL_FILE could not be read"),
    ):
        Settings()


def test_file_dependency_url_empty_file_has_clear_error(tmp_path: Path) -> None:
    database_url_file = tmp_path / "database_url"
    redis_url_file = tmp_path / "redis_url"
    database_url_file.write_text("", encoding="utf-8")
    redis_url_file.write_text("redis://:file-secret@redis:6379/0", encoding="utf-8")

    env = _production_env()
    del env["CITY_DATABASE_URL"]
    del env["REDIS_URL"]
    env["CITY_DATABASE_URL_FILE"] = str(database_url_file)
    env["REDIS_URL_FILE"] = str(redis_url_file)

    with (
        patch.dict(os.environ, env, clear=True),
        pytest.raises(ValueError, match="CITY_DATABASE_URL_FILE must not be empty"),
    ):
        Settings()


def test_production_rejects_unsafe_credentials_inside_file(tmp_path: Path) -> None:
    database_url_file = tmp_path / "database_url"
    redis_url_file = tmp_path / "redis_url"
    database_url_file.write_text(
        "postgresql+psycopg2://city:city_dev_password@postgres:5432/city_game",
        encoding="utf-8",
    )
    redis_url_file.write_text("redis://:file-secret@redis:6379/0", encoding="utf-8")

    env = _production_env()
    del env["CITY_DATABASE_URL"]
    del env["REDIS_URL"]
    env["CITY_DATABASE_URL_FILE"] = str(database_url_file)
    env["REDIS_URL_FILE"] = str(redis_url_file)

    with (
        patch.dict(os.environ, env, clear=True),
        pytest.raises(ValueError, match="development credential"),
    ):
        Settings().validate()


def test_production_disables_frozen_routes_and_docs() -> None:
    env = {**os.environ, **_production_env(), "PYTHONPATH": os.getcwd()}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from backend.main import app; "
                "paths={route.path for route in app.routes}; "
                "assert not any(path.startswith('/api/frozen') for path in paths); "
                "assert app.docs_url is None; "
                "assert app.openapi_url is None"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr


def test_production_compose_uses_one_shot_migration_service() -> None:
    compose = Path("docker-compose.prod.yml").read_text(encoding="utf-8")

    assert "  migrate:" in compose
    assert 'command: ["python", "-m", "alembic", "upgrade", "head"]' in compose
    assert "condition: service_completed_successfully" in compose
    assert 'CITY_RUN_MIGRATIONS_ON_STARTUP: "false"' in compose
    assert "CITY_DATABASE_URL_FILE: /run/secrets/city_database_url" in compose
    assert "REDIS_URL_FILE: /run/secrets/redis_url" in compose
    assert "POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password" in compose
    assert "GF_SECURITY_ADMIN_PASSWORD__FILE: /run/secrets/grafana_admin_password" in compose
    assert compose.count("image: ${CITY_RELEASE_IMAGE:?CITY_RELEASE_IMAGE is required}") == 2
    assert compose.count("CITY_RELEASE_SHA: ${CITY_RELEASE_SHA:?CITY_RELEASE_SHA is required}") >= 2
    assert compose.count("CITY_RELEASE_IMAGE: ${CITY_RELEASE_IMAGE:?CITY_RELEASE_IMAGE is required}") >= 2
    assert compose.count("CITY_RELEASE_VERSION: ${CITY_RELEASE_VERSION:?CITY_RELEASE_VERSION is required}") >= 2
    assert "CITY_DATABASE_URL: postgresql+psycopg2://" not in compose
    assert "REDIS_URL: redis://:" not in compose
    assert "secrets:" in compose


def test_production_dockerfile_has_oci_release_labels() -> None:
    dockerfile = Path("backend/Dockerfile").read_text(encoding="utf-8")

    assert "ARG CITY_RELEASE_SHA=unknown" in dockerfile
    assert "ARG CITY_RELEASE_IMAGE=local" in dockerfile
    assert "ARG CITY_RELEASE_VERSION=0.3.0" in dockerfile
    assert 'org.opencontainers.image.revision="${CITY_RELEASE_SHA}"' in dockerfile
    assert 'org.opencontainers.image.version="${CITY_RELEASE_VERSION}"' in dockerfile
    assert 'org.opencontainers.image.ref.name="${CITY_RELEASE_IMAGE}"' in dockerfile


def test_production_compose_binds_monitoring_to_localhost() -> None:
    compose = Path("docker-compose.prod.yml").read_text(encoding="utf-8")

    assert "127.0.0.1:${PROMETHEUS_PORT:-9090}:9090" in compose
    assert "127.0.0.1:${GRAFANA_PORT:-3001}:3000" in compose
    assert "--web.enable-lifecycle" not in compose
