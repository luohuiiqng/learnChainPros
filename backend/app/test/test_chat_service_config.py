import importlib
import os
import sys
import types

import pytest

from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.persistent_session_store import PersistentSessionStore
from app.runtime.persistent_transcript_store import PersistentTranscriptStore


@pytest.fixture(scope="module")
def fake_openai_installed():
    os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
    fake_openai_module = types.ModuleType("openai")

    class FakeOpenAI:
        def __init__(self, *args, **kwargs) -> None:
            pass

    fake_openai_module.OpenAI = FakeOpenAI
    sys.modules.setdefault("openai", fake_openai_module)
    yield


def test_chat_service_module_uses_memory_store_when_env_memory(
    fake_openai_installed, monkeypatch
) -> None:
    monkeypatch.setenv("STORE_BACKEND", "memory")
    mod = importlib.import_module("app.services.chat_service")
    mod = importlib.reload(mod)
    assert isinstance(mod.chat_service._session_store, InMemorySessionStore)
    assert isinstance(mod.chat_service._transcript_store, InMemoryTranscriptStore)


def test_chat_service_module_uses_sqlite_when_env_sqlite(
    fake_openai_installed, monkeypatch, tmp_path
) -> None:
    db_path = str(tmp_path / "runtime.db")
    monkeypatch.setenv("STORE_BACKEND", "sqlite")
    monkeypatch.setenv("RUNTIME_DB_PATH", db_path)
    mod = importlib.import_module("app.services.chat_service")
    mod = importlib.reload(mod)
    assert isinstance(mod.chat_service._session_store, PersistentSessionStore)
    assert isinstance(mod.chat_service._transcript_store, PersistentTranscriptStore)
    monkeypatch.setenv("STORE_BACKEND", "memory")
    monkeypatch.delenv("RUNTIME_DB_PATH", raising=False)
    importlib.reload(mod)
