"""TinyAgent tool implementations with decorators."""

from typing import Optional

from tinyagent import tool

from tunacode.exceptions import ToolExecutionError
from tunacode.ui import console as ui

# Import the existing tool classes to reuse their logic
from .read_file import ReadFileTool
from .run_command import RunCommandTool
from .update_file import UpdateFileTool
from .write_file import WriteFileTool


@tool
async def read_file(filepath: str) -> str:
    """Read the contents of a file.

    Args:
        filepath: The path to the file to read.

    Returns:
        The contents of the file.

    Raises:
        Exception: If file cannot be read.
    """
    tool_instance = ReadFileTool(ui)
    try:
        result = await tool_instance.execute(filepath)
        return result
    except ToolExecutionError as e:
        # tinyAgent expects exceptions to be raised, not returned as strings
        raise Exception(str(e))


@tool
async def write_file(filepath: str, content: str) -> str:
    """Write content to a file.

    Args:
        filepath: The path to the file to write.
        content: The content to write to the file.

    Returns:
        Success message.

    Raises:
        Exception: If file cannot be written.
    """
    tool_instance = WriteFileTool(ui)
    try:
        result = await tool_instance.execute(filepath, content)
        return result
    except ToolExecutionError as e:
        raise Exception(str(e))


@tool
async def update_file(filepath: str, old_content: str, new_content: str) -> str:
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
    tool_instance = UpdateFileTool(ui)
    try:
        result = await tool_instance.execute(filepath, old_content, new_content)
        return result
    except ToolExecutionError as e:
        raise Exception(str(e))


@tool
async def run_command(command: str, timeout: Optional[int] = None) -> str:
    """Run a shell command.

    Args:
        command: The command to run.
        timeout: Optional timeout in seconds.

    Returns:
        The command output.

    Raises:
        Exception: If command fails.
    """
    tool_instance = RunCommandTool(ui)
    try:
        result = await tool_instance.execute(command, timeout)
        return result
    except ToolExecutionError as e:
        raise Exception(str(e))
