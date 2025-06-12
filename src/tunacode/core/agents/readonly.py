"""Read-only agent implementation for non-mutating operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...tools.grep import grep
from ...tools.read_file import read_file
from ...types import AgentRun, ModelName, ResponseState
from ..state import StateManager

if TYPE_CHECKING:
    from ...types import PydanticAgent


class ReadOnlyAgent:
    """Agent configured with read-only tools for analysis tasks."""

    def __init__(self, model: ModelName, state_manager: StateManager):
        self.model = model
        self.state_manager = state_manager
        self._agent: PydanticAgent | None = None

    def _get_agent(self) -> PydanticAgent:
        """Lazily create the agent with read-only tools."""
        if self._agent is None:
            from .main import get_agent_tool

            Agent, Tool = get_agent_tool()

            # Create agent with only read-only tools
            self._agent = Agent(
                model=self.model,
                system_prompt="You are a read-only assistant. You can analyze and read files but cannot modify them.",
                tools=[
                    Tool(read_file),
                    Tool(grep),
                ],
            )
        return self._agent

    async def process_request(self, request: str) -> AgentRun:
        """Process a request using only read-only tools."""
        agent = self._get_agent()
        response_state = ResponseState()

        # Use iter() like main.py does to get the full run context
        async with agent.iter(request) as agent_run:
            async for node in agent_run:
                # Check if this node produced user-visible output
                if hasattr(node, "result") and node.result and hasattr(node.result, "output"):
                    if node.result.output:
                        response_state.has_user_response = True

        # Wrap the agent run to include response_state
        class AgentRunWithState:
            def __init__(self, wrapped_run):
                self._wrapped = wrapped_run
                self.response_state = response_state

            def __getattr__(self, name):
                # Delegate all other attributes to the wrapped object
                return getattr(self._wrapped, name)

        return AgentRunWithState(agent_run)
