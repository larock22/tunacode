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
    tool_instance = RunCommandTool(_get_ui())
    try:
        # Always run in a separate thread to avoid deadlocks
        result = _run_async_in_thread(tool_instance.execute(command, timeout))
        return result
    except ToolExecutionError as e:
        raise Exception(str(e))
