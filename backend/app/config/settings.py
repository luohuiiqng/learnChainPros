from dataclasses import dataclass
import os


@dataclass
class Settings:
    openai_api_key: str | None
    openai_model: str
    openai_base_url: str | None
    openai_organization: str | None
    store_backend: str
    runtime_db_path: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
            openai_base_url=os.getenv("OPENAI_BASE_URL"),
            openai_organization=os.getenv("OPENAI_ORGANIZATION"),
            store_backend=os.getenv("STORE_BACKEND", "memory"),
            runtime_db_path=os.getenv("RUNTIME_DB_PATH"),
        )
