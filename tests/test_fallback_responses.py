import pytest
from unittest.mock import patch, MagicMock

from tunacode.core.state import StateManager
from tunacode.core.agents import main as agent_main
from tunacode.core.agents.orchestrator import OrchestratorAgent

class DummyNode:
    pass

class FakeAgentRun:
    def __init__(self, nodes):
        self._nodes = nodes
        self.result = None
    def __aiter__(self):
        async def gen():
            for n in self._nodes:
                yield n
        return gen()
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass

class FakeAgent:
    def __init__(self, nodes):
        self._nodes = nodes
    def iter(self, message, message_history=None):
        return FakeAgentRun(self._nodes)

@pytest.mark.asyncio
async def test_process_request_generates_fallback():
    state = StateManager()
    state.session.user_config = {
        "settings": {"max_iterations": 3, "fallback_response": True}
    }
    nodes = [DummyNode() for _ in range(5)]
    with patch("tunacode.core.agents.main.get_or_create_agent", return_value=FakeAgent(nodes)):
        res = await agent_main.process_request("model", "test", state)
        assert hasattr(res, "result")
        assert "maximum iterations" in res.result.output.lower()

@pytest.mark.asyncio
async def test_orchestrator_synthesizes_summary():
    state = StateManager()
    orch = OrchestratorAgent(state)
    tasks = [MagicMock(id=1, description="task", mutate=True)]
    fake_run = MagicMock()
    fake_run.result = None
    with patch.object(orch, "plan", return_value=tasks):
        with patch.object(orch, "_run_sub_task", return_value=fake_run):
            results = await orch.run("req")
            assert len(results) == 2
            # Check that fallback response was generated
            assert "orchestrator completed all tasks" in results[-1].result.output.lower()
            assert "executed 1/1 tasks" in results[-1].result.output.lower()
