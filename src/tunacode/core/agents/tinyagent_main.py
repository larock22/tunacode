"""TinyAgent-based agent implementation."""

import os
import yaml
import json
import sys
import io
from contextlib import asynccontextmanager, redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from tinyagent import ReactAgent

from tunacode.core.state import StateManager
from tunacode.tools.tinyagent_tools import read_file, run_command, update_file, write_file
from tunacode.tools.tinyagent_tools import _set_state_manager  # Import the setter
from tunacode.types import ModelName, ToolCallback

# Set up tinyagent configuration
# First check if config exists in the package directory
_package_dir = Path(__file__).parent.parent.parent.parent  # Navigate to tunacode root
_config_candidates = [
    _package_dir / "tunacode_config.yml",  # In package root
    Path.home() / ".config" / "tunacode_config.yml",  # In user config dir
    Path.cwd() / "tunacode_config.yml",  # In current directory
]

# Find the first existing config file
for config_path in _config_candidates:
    if config_path.exists():
        os.environ["TINYAGENT_CONFIG"] = str(config_path)
        break
else:
    # If no config found, we'll rely on tinyagent to handle it
    # This prevents the immediate error on import
    pass


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
    
    # Set the state manager globally so tools can access it
    _set_state_manager(state_manager)

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

        # Sync both configs to ensure they match
        _sync_model_configs(model, state_manager)
        
        # Create new ReactAgent with tools
        # ReactAgent constructor: (tools, llm_callable=None, max_steps=10, add_base_tools=True)
        agent = ReactAgent(tools=[read_file, write_file, update_file, run_command], max_steps=10)

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
        # Run the agent with the message, suppressing debug output if not verbose
        if state_manager.session.verbose:
            # Run normally with full output
            result = agent.run(message)
        else:
            # Capture and suppress the debug output
            # The spinner is already running from the REPL, no need for duplicate thinking message
            captured_output = io.StringIO()
            with redirect_stdout(captured_output), redirect_stderr(captured_output):
                result = agent.run(message)
            
            # Optionally log the captured output for debugging
            # debug_output = captured_output.getvalue()

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


def _sync_model_configs(tunacode_model: str, state_manager: StateManager):
    """
    Bidirectional sync between TunaCode and TinyAgent configs.
    Compares modification times and syncs the older config to match the newer one.
    
    Args:
        tunacode_model: The model name in TunaCode format (e.g., "openrouter:mistralai/devstral-small")
        state_manager: State manager instance for accessing TunaCode config
    """
    try:
        # Get config file paths
        tinyagent_config_path = os.environ.get("TINYAGENT_CONFIG")
        tunacode_config_path = Path.home() / ".config" / "tunacode.json"
        
        if not tinyagent_config_path or not Path(tinyagent_config_path).exists():
            return
            
        tinyagent_config_path = Path(tinyagent_config_path)
        
        if not tunacode_config_path.exists():
            return
            
        # Get modification times
        tinyagent_mtime = tinyagent_config_path.stat().st_mtime
        tunacode_mtime = tunacode_config_path.stat().st_mtime
        
        # Read both configs
        with open(tinyagent_config_path, 'r') as f:
            tinyagent_config = yaml.safe_load(f)
            
        with open(tunacode_config_path, 'r') as f:
            tunacode_config = json.load(f)
            
        # Extract models from both configs
        tinyagent_model = tinyagent_config.get('model', {}).get('default', '')
        tunacode_default_model = tunacode_config.get('default_model', '')
        
        # Convert TunaCode model to TinyAgent format for comparison
        if tunacode_default_model.startswith("openrouter:"):
            tunacode_model_for_tinyagent = tunacode_default_model.replace("openrouter:", "")
        else:
            # For direct providers, extract just the model name
            if ":" in tunacode_default_model:
                tunacode_model_for_tinyagent = tunacode_default_model.split(":", 1)[1]
            else:
                tunacode_model_for_tinyagent = tunacode_default_model
        
        # Determine which config is newer and needs to be the source of truth
        if tinyagent_mtime > tunacode_mtime:
            # TinyAgent config is newer - sync TunaCode to match
            if tinyagent_model and tinyagent_model != tunacode_model_for_tinyagent:
                # Convert TinyAgent model back to TunaCode format
                if "/" in tinyagent_model:  # OpenRouter format
                    new_tunacode_model = f"openrouter:{tinyagent_model}"
                else:  # Direct provider - need to determine provider
                    # Default to OpenAI for simple model names
                    new_tunacode_model = f"openai:{tinyagent_model}"
                
                # Update TunaCode config
                tunacode_config['default_model'] = new_tunacode_model
                state_manager.session.user_config['default_model'] = new_tunacode_model
                
                with open(tunacode_config_path, 'w') as f:
                    json.dump(tunacode_config, f, indent=2)
                    
        elif tunacode_mtime > tinyagent_mtime:
            # TunaCode config is newer - sync TinyAgent to match
            if tunacode_model_for_tinyagent != tinyagent_model:
                # Update TinyAgent config
                if 'model' not in tinyagent_config:
                    tinyagent_config['model'] = {}
                tinyagent_config['model']['default'] = tunacode_model_for_tinyagent
                
                # Update base URL to match current environment
                current_base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
                tinyagent_config['base_url'] = current_base_url
                
                with open(tinyagent_config_path, 'w') as f:
                    yaml.safe_dump(tinyagent_config, f, default_flow_style=False, sort_keys=False)
        
        # If models already match, no sync needed
        
    except Exception:
        # Silent fail - don't break the agent if config sync fails
        pass


def _update_tinyagent_config_model(model: str):
    """
    Legacy function - replaced by _sync_model_configs for bidirectional sync.
    Kept for backward compatibility.
    """
    # This function is now deprecated in favor of _sync_model_configs
    pass


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
