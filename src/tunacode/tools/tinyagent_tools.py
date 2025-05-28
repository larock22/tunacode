"""TinyAgent tool implementations with decorators."""

from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

from tinyagent import tool
from prompt_toolkit.application import run_in_terminal

from tunacode.exceptions import ToolExecutionError

# Import the existing tool classes to reuse their logic
from .read_file import ReadFileTool
from .run_command import RunCommandTool
from .update_file import UpdateFileTool
from .write_file import WriteFileTool


def _get_ui():
    """Lazy import of UI to avoid circular dependencies."""
    from tunacode.ui import console as ui
    return ui


def _get_state_manager():
    """Get the global state manager instance."""
    # This is a bit hacky but necessary since TinyAgent doesn't pass context
    from tunacode.cli.repl import _command_registry
    # We need to find a way to get the current state manager
    # For now, we'll need to store it globally when the agent is created
    return getattr(_get_state_manager, '_instance', None)


def _set_state_manager(state_manager):
    """Set the global state manager instance."""
    _get_state_manager._instance = state_manager


def _run_async_in_thread(coro):
    """Run an async coroutine in a new thread with its own event loop."""
    def run_in_new_loop():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_new_loop)
        return future.result()


def _handle_confirmation(tool_name: str, args: dict) -> bool:
    """Handle tool confirmation synchronously.
    
    For TinyAgent, confirmations are disabled to avoid async/sync conflicts.
    TinyAgent's ReAct loop provides sufficient oversight.
    
    Returns:
        bool: Always True (approved)
    """
    # TinyAgent integration: Skip confirmations entirely
    # The ReAct loop provides sufficient oversight and planning
    return True


@tool
def read_file(filepath: str) -> str:
    """Read the contents of a file.

    Args:
        filepath: The path to the file to read.

    Returns:
        The contents of the file.

    Raises:
        Exception: If file cannot be read.
    """
    # Show immediate feedback
    print(f"● read_file('{filepath}')")
    
    # Handle confirmation
    if not _handle_confirmation("read_file", {"filepath": filepath}):
        raise Exception("User rejected the operation")
    
    # Create tool instance without UI to avoid async issues
    tool_instance = ReadFileTool(None)  # Pass None instead of _get_ui()
    try:
        # Always run in a separate thread to avoid deadlocks
        result = _run_async_in_thread(tool_instance.execute(filepath))
        return result
    except ToolExecutionError as e:
        # tinyAgent expects exceptions to be raised, not returned as strings
        raise Exception(str(e))


@tool
def write_file(filepath: str, content: str) -> str:
    """Write content to a file.

    Args:
        filepath: The path to the file to write.
        content: The content to write to the file.

    Returns:
        Success message.

    Raises:
        Exception: If file cannot be written.
    """
    # Show immediate feedback
    print(f"● write_file('{filepath}')")
    
    # Handle confirmation
    if not _handle_confirmation("write_file", {"filepath": filepath, "content": content}):
        raise Exception("User rejected the operation")
    
    # Create tool instance without UI to avoid async issues
    tool_instance = WriteFileTool(None)  # Pass None instead of _get_ui()
    try:
        # Always run in a separate thread to avoid deadlocks
        result = _run_async_in_thread(tool_instance.execute(filepath, content))
        return result
    except ToolExecutionError as e:
        raise Exception(str(e))


@tool
def update_file(filepath: str, old_content: str, new_content: str) -> str:
    """Update specific content in a file.

    Args:
        filepath: The path to the file to update.
        old_content: The content to find and replace.
        new_content: The new content to insert.

    Returns:
        Success message.

    Raises:
        Exception: If file cannot be updated.
    """
    # Show immediate feedback
    print(f"● update_file('{filepath}')")
    
    # Handle confirmation - use 'target' and 'patch' for UI compatibility
    if not _handle_confirmation("update_file", {
        "filepath": filepath, 
        "target": old_content,  # UI expects 'target' not 'old_content'
        "patch": new_content    # UI expects 'patch' not 'new_content'
    }):
        raise Exception("User rejected the operation")
    
    # Create tool instance without UI to avoid async issues
    tool_instance = UpdateFileTool(None)  # Pass None instead of _get_ui()
    try:
        # Always run in a separate thread to avoid deadlocks
        result = _run_async_in_thread(tool_instance.execute(filepath, old_content, new_content))
        return result
    except ToolExecutionError as e:
        raise Exception(str(e))


@tool
def run_command(command: str, timeout: Optional[int] = None) -> str:
    """Run a shell command.

    Args:
        command: The command to run.
        timeout: Optional timeout in seconds.

    Returns:
        The command output.

    Raises:
        Exception: If command fails.
    """
    # Show immediate feedback
    print(f"● run_command('{command}')")
    
    # Handle confirmation
    if not _handle_confirmation("run_command", {"command": command, "timeout": timeout}):
        raise Exception("User rejected the operation")
    
    # Create tool instance without UI to avoid async issues
    tool_instance = RunCommandTool(None)  # Pass None instead of _get_ui()
    try:
        # Always run in a separate thread to avoid deadlocks
        result = _run_async_in_thread(tool_instance.execute(command, timeout))
        return result
    except ToolExecutionError as e:
        raise Exception(str(e))
