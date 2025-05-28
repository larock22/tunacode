"""Module: sidekick.core.agents.main

Main agent functionality and coordination for the Sidekick CLI.
Provides agent creation, message processing, and tool call management.
Now using tinyAgent instead of pydantic-ai.
"""

from typing import Optional

from tunacode.core.state import StateManager
from tunacode.types import AgentRun, ErrorMessage, ModelName, ToolCallback

# Import tinyAgent implementation
from .tinyagent_main import get_or_create_react_agent
from .tinyagent_main import patch_tool_messages as tinyagent_patch_tool_messages
from .tinyagent_main import process_request_with_tinyagent

# Wrapper functions for backward compatibility with pydantic-ai interface


def get_or_create_agent(model: ModelName, state_manager: StateManager):
    """
    Wrapper for backward compatibility.
    Returns the ReactAgent instance from tinyAgent.
    """
    return get_or_create_react_agent(model, state_manager)


def patch_tool_messages(
    error_message: ErrorMessage = "Tool operation failed",
    state_manager: StateManager = None,
):
    """
    Wrapper for backward compatibility.
    TinyAgent handles tool errors internally, so this is mostly a no-op.
    """
    tinyagent_patch_tool_messages(error_message, state_manager)


async def process_request(
    model: ModelName,
    message: str,
    state_manager: StateManager,
    tool_callback: Optional[ToolCallback] = None,
) -> AgentRun:
    """
    Process a request using tinyAgent.
    Returns a result that mimics the pydantic-ai AgentRun structure.
    """
    result = await process_request_with_tinyagent(model, message, state_manager, tool_callback)

    # Create a mock AgentRun object for compatibility
    class MockAgentRun:
        def __init__(self, result_dict):
            self._result = result_dict

        @property
        def result(self):
            class MockResult:
                def __init__(self, content):
                    self._content = content

                @property
                def output(self):
                    return self._content

            return MockResult(self._result.get("result", ""))

        @property
        def messages(self):
            return state_manager.session.messages

        @property
        def model(self):
            return self._result.get("model", model)

    return MockAgentRun(result)
