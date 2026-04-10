import os

from app.config.settings import Settings


os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["OPENAI_MODEL"] = "test-model"
os.environ["OPENAI_BASE_URL"] = "https://example.com/v1"
os.environ["OPENAI_ORGANIZATION"] = "test-org"
os.environ["STORE_BACKEND"] = "sqlite"
os.environ["RUNTIME_DB_PATH"] = "/tmp/runtime.db"

settings = Settings.from_env()

assert settings.openai_api_key == "test-key"
assert settings.openai_model == "test-model"
assert settings.openai_base_url == "https://example.com/v1"
assert settings.openai_organization == "test-org"
assert settings.store_backend == "sqlite"
assert settings.runtime_db_path == "/tmp/runtime.db"

os.environ.pop("OPENAI_MODEL", None)
os.environ.pop("STORE_BACKEND", None)
os.environ.pop("RUNTIME_DB_PATH", None)

default_settings = Settings.from_env()

assert default_settings.openai_model == "gpt-5.4"
assert default_settings.store_backend == "memory"
assert default_settings.runtime_db_path is None

print("settings tests passed")
