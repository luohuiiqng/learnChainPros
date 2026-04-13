from app.config.settings import Settings


def test_settings_from_env_full(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("OPENAI_ORGANIZATION", "test-org")
    monkeypatch.setenv("STORE_BACKEND", "sqlite")
    monkeypatch.setenv("RUNTIME_DB_PATH", "/tmp/runtime.db")
    settings = Settings.from_env()
    assert settings.openai_api_key == "test-key"
    assert settings.openai_model == "test-model"
    assert settings.openai_base_url == "https://example.com/v1"
    assert settings.openai_organization == "test-org"
    assert settings.store_backend == "sqlite"
    assert settings.runtime_db_path == "/tmp/runtime.db"


def test_settings_defaults_for_missing_optional_env(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("STORE_BACKEND", raising=False)
    monkeypatch.delenv("RUNTIME_DB_PATH", raising=False)
    default_settings = Settings.from_env()
    assert default_settings.openai_model == "gpt-5.4"
    assert default_settings.store_backend == "memory"
    assert default_settings.runtime_db_path is None


def test_settings_for_tests() -> None:
    ft = Settings.for_tests()
    assert ft.openai_api_key == "test-api-key"
    assert ft.openai_model == "test-model"
    assert ft.store_backend == "memory"
    assert ft.runtime_db_path is None
