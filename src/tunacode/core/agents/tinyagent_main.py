"""TinyAgent-based agent implementation."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from tinyagent import ReactAgent

from tunacode.core.state import StateManager
from tunacode.tools.tinyagent_tools import read_file, run_command, update_file, write_file
from tunacode.types import ModelName, ToolCallback


def get_or_create_react_agent(model: ModelName, state_manager: StateManager) -> ReactAgent:
    """
    Get or create a ReactAgent for the specified model.

    Args:
        model: The model name (e.g., "openai:gpt-4o", "openrouter:openai/gpt-4.1")
        state_manager: The state manager instance

    Returns:
        ReactAgent instance configured for the model
    """
    agents = state_manager.session.agents

    if model not in agents:
        # Parse model string to determine provider and actual model name
        # Format: "provider:model" or "openrouter:provider/model"
        if model.startswith("openrouter:"):
            # OpenRouter model - extract the actual model name
            actual_model = model.replace("openrouter:", "")
            # Set environment to use OpenRouter base URL
            import os

            os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
            # Use OpenRouter API key if available
            if state_manager.session.user_config["env"].get("OPENROUTER_API_KEY"):
                os.environ["OPENAI_API_KEY"] = state_manager.session.user_config["env"][
                    "OPENROUTER_API_KEY"
                ]
        else:
            # Direct provider (openai, anthropic, google-gla)
            provider, actual_model = model.split(":", 1)
            # Reset to default base URL for direct providers
            import os

            if provider == "openai":
                os.environ["OPENAI_BASE_URL"] = "https://api.openai.com/v1"
            # Set appropriate API key
            provider_key_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "google-gla": "GEMINI_API_KEY",
            }
            if provider in provider_key_map:
                key_name = provider_key_map[provider]
                if state_manager.session.user_config["env"].get(key_name):
                    os.environ[key_name] = state_manager.session.user_config["env"][key_name]

        # Create new ReactAgent with tools
        # Note: tinyAgent gets model from environment variables, not constructor
        agent = ReactAgent(tools=[read_file, write_file, update_file, run_command])

        # Add MCP compatibility method
        @asynccontextmanager
        async def run_mcp_servers():
            # TinyAgent doesn't have built-in MCP support yet
            # This is a placeholder for compatibility
            yield

        agent.run_mcp_servers = run_mcp_servers

        # Cache the agent
        agents[model] = agent

    return agents[model]


async def process_request_with_tinyagent(
    model: ModelName,
    message: str,
    state_manager: StateManager,
    tool_callback: Optional[ToolCallback] = None,
) -> Dict[str, Any]:
    """
    Process a request using TinyAgent's ReactAgent.

    Args:
        model: The model to use
        message: The user message
        state_manager: State manager instance
        tool_callback: Optional callback for tool execution (for UI updates)

    Returns:
        Dict containing the result and any metadata
    """
    agent = get_or_create_react_agent(model, state_manager)

    # Convert message history to format expected by tinyAgent
    # Note: tinyAgent handles message history differently than pydantic-ai
    # We'll need to adapt based on tinyAgent's actual API

    try:
        # Run the agent with the message
        # The new API's run() method might be synchronous based on the examples
        import asyncio
        if asyncio.iscoroutinefunction(agent.run):
            result = await agent.run(message)
        else:
            result = agent.run(message)

        # Update message history in state_manager
        # This will need to be adapted based on how tinyAgent returns messages
        state_manager.session.messages.append(
            {
                "role": "user",
                "content": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        state_manager.session.messages.append(
            {
                "role": "assistant",
                "content": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        return {"result": result, "success": True, "model": model}

    except Exception as e:
        # Handle errors
        error_result = {
            "result": f"Error: {str(e)}",
            "success": False,
            "model": model,
            "error": str(e),
        }

        # Still update message history with the error
        state_manager.session.messages.append(
            {
                "role": "user",
                "content": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        state_manager.session.messages.append(
            {
                "role": "assistant",
                "content": f"Error occurred: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": True,
            }
        )

        return error_result


def patch_tool_messages(
    error_message: str = "Tool operation failed",
    state_manager: StateManager = None,
):
    """
    Compatibility function for patching tool messages.
    With tinyAgent, this may not be needed as it handles tool errors differently.
    """
    # TinyAgent handles tool retries and errors internally
    # This function is kept for compatibility but may be simplified
    pass
