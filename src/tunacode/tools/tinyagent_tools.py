"""TinyAgent tool implementations with decorators."""

from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

from tinyagent import tool

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
    
    Returns:
        bool: True if approved, False if rejected
    """
    state_manager = _get_state_manager()
    if not state_manager:
        # If no state manager, assume approval (backward compatibility)
        return True
    
    # Import here to avoid circular imports
    from tunacode.core.tool_handler import ToolHandler
    from tunacode.ui.tool_ui import ToolUI
    
    tool_handler = ToolHandler(state_manager)
    
    # Check if confirmation is needed
    if not tool_handler.should_confirm(tool_name):
        # No confirmation needed - tool already logged its execution
        return True
    
    # STOP THE SPINNER BEFORE SHOWING CONFIRMATION
    # This is critical - spinner must be stopped so user can type
    spinner = state_manager.session.spinner
    spinner_was_running = False
    if spinner and hasattr(spinner, 'stop'):
        try:
            spinner.stop()
            spinner_was_running = True
        except:
            pass  # Spinner might not be running
    
    # Create confirmation request
    request = tool_handler.create_confirmation_request(tool_name, args)
    
    # Show confirmation UI synchronously
    tool_ui = ToolUI()
    try:
        response = tool_ui.show_sync_confirmation(request)
        
        # Process the response
        result = tool_handler.process_confirmation(response, tool_name)
    finally:
        # RESTART THE SPINNER AFTER CONFIRMATION
        # Only restart if it was running before
        if spinner_was_running and spinner and hasattr(spinner, 'start'):
            try:
                spinner.start()
            except:
                pass  # Might fail if already started
    
    return result


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
    
    tool_instance = ReadFileTool(_get_ui())
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
    
    tool_instance = WriteFileTool(_get_ui())
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
    
    tool_instance = UpdateFileTool(_get_ui())
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
    
    tool_instance = RunCommandTool(_get_ui())
    try:
        # Always run in a separate thread to avoid deadlocks
        result = _run_async_in_thread(tool_instance.execute(command, timeout))
        return result
    except ToolExecutionError as e:
        raise Exception(str(e))
