import importlib
import os
import sys
import tempfile
import types

from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.persistent_session_store import PersistentSessionStore
from app.runtime.persistent_transcript_store import PersistentTranscriptStore


os.environ.setdefault("OPENAI_API_KEY", "test-api-key")

fake_openai_module = types.ModuleType("openai")


class FakeOpenAI:
    def __init__(self, *args, **kwargs) -> None:
        pass


fake_openai_module.OpenAI = FakeOpenAI
sys.modules.setdefault("openai", fake_openai_module)


chat_service_module_name = "app.services.chat_service"


os.environ["STORE_BACKEND"] = "memory"
memory_module = importlib.import_module(chat_service_module_name)
memory_module = importlib.reload(memory_module)

assert isinstance(memory_module.chat_service._session_store, InMemorySessionStore)
assert isinstance(memory_module.chat_service._transcript_store, InMemoryTranscriptStore)


with tempfile.TemporaryDirectory() as tmp_dir:
    db_path = os.path.join(tmp_dir, "runtime.db")
    os.environ["STORE_BACKEND"] = "sqlite"
    os.environ["RUNTIME_DB_PATH"] = db_path

    sqlite_module = importlib.reload(memory_module)

    assert isinstance(sqlite_module.chat_service._session_store, PersistentSessionStore)
    assert isinstance(
        sqlite_module.chat_service._transcript_store, PersistentTranscriptStore
    )


os.environ["STORE_BACKEND"] = "memory"

print("chat service config tests passed")
