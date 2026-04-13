import dataclasses
import importlib
import json
import logging
import os
import sys
import tempfile
import types

import pytest

from app.agent.chat_agent import ChatAgent
from app.config.settings import Settings
from app.hooks.logging_hook import LoggingLifecycleHook
from app.planners.rule_planner import RulePlanner
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.persistent_session_store import PersistentSessionStore
from app.runtime.persistent_transcript_store import PersistentTranscriptStore
from app.runtime.runtime_manager import RuntimeManager


@pytest.fixture(scope="module")
def AgentFactory_cls():
    """在隔离的 OpenAI stub 下加载 AgentFactory，避免测试进程依赖真实 openai 包行为。"""
    os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
    fake_openai_module = types.ModuleType("openai")

    class FakeOpenAI:
        def __init__(self, *args, **kwargs) -> None:
            pass

    fake_openai_module.OpenAI = FakeOpenAI
    sys.modules.setdefault("openai", fake_openai_module)
    mod = importlib.import_module("app.services.agent_factory")
    mod = importlib.reload(mod)
    return mod.AgentFactory


@pytest.fixture
def memory_settings() -> Settings:
    return Settings(
        openai_api_key="test-api-key",
        openai_model="test-model",
        openai_base_url="https://example.com/v1",
        openai_organization=None,
        store_backend="memory",
        runtime_db_path=None,
    )


def test_agent_factory_logs_planner_rules_path(
    AgentFactory_cls, memory_settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="app.agent.factory")
    data = {"version": 1, "workflow_triggers": []}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f)
        path = f.name
    try:
        settings = dataclasses.replace(memory_settings, planner_rules_path=path)
        factory = AgentFactory_cls()
        factory.create_chat_agent(settings=settings)
    finally:
        os.unlink(path)
    assert any(
        "loading planner workflow triggers" in r.message and path in r.message
        for r in caplog.records
    )


def test_agent_factory_create_chat_agent(
    AgentFactory_cls, memory_settings: Settings
) -> None:
    factory = AgentFactory_cls()
    agent = factory.create_chat_agent(settings=memory_settings)
    assert isinstance(agent, ChatAgent)
    assert agent._hooks == ()
    assert agent._runtime_manager is not None
    assert isinstance(agent._runtime_manager, RuntimeManager)
    assert agent._planner is not None
    assert isinstance(agent._planner, RulePlanner)
    assert agent._tool_registry is not None
    assert agent._memory is not None


def test_agent_factory_attaches_logging_hook_when_enabled(
    AgentFactory_cls, memory_settings: Settings
) -> None:
    factory = AgentFactory_cls()
    settings = dataclasses.replace(
        memory_settings, agent_lifecycle_logging=True
    )
    agent = factory.create_chat_agent(settings=settings)
    assert len(agent._hooks) == 1
    assert isinstance(agent._hooks[0], LoggingLifecycleHook)


def test_agent_factory_memory_backend_stores(AgentFactory_cls) -> None:
    memory_factory = AgentFactory_cls(store_backend="memory")
    assert isinstance(memory_factory.get_session_store(), InMemorySessionStore)
    assert isinstance(memory_factory.get_transcript_store(), InMemoryTranscriptStore)


def test_agent_factory_sqlite_backend_stores(AgentFactory_cls) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "runtime.db")
        sqlite_factory = AgentFactory_cls(store_backend="sqlite", db_path=db_path)
        assert isinstance(sqlite_factory.get_session_store(), PersistentSessionStore)
        assert isinstance(
            sqlite_factory.get_transcript_store(), PersistentTranscriptStore
        )


def test_agent_factory_sqlite_requires_db_path(AgentFactory_cls) -> None:
    with pytest.raises(ValueError):
        AgentFactory_cls(store_backend="sqlite")


def test_agent_factory_unknown_backend_raises(AgentFactory_cls) -> None:
    with pytest.raises(ValueError):
        AgentFactory_cls(store_backend="unknown")
