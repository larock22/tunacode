"""
Module: sidekick.tools.run_command

Command execution tool for agent operations in the Sidekick application.
Provides controlled shell command execution with output capture and truncation.
"""

import subprocess
from typing import Optional

from tunacode.constants import (CMD_OUTPUT_FORMAT, CMD_OUTPUT_NO_ERRORS, CMD_OUTPUT_NO_OUTPUT,
                                CMD_OUTPUT_TRUNCATED, COMMAND_OUTPUT_END_SIZE,
                                COMMAND_OUTPUT_START_INDEX, COMMAND_OUTPUT_THRESHOLD,
                                ERROR_COMMAND_EXECUTION, MAX_COMMAND_OUTPUT)
from tunacode.exceptions import ToolExecutionError
from tunacode.tools.base import BaseTool
from tunacode.types import ToolResult
from tunacode.ui import console as default_ui


class RunCommandTool(BaseTool):
    """Tool for running shell commands."""

    @property
    def tool_name(self) -> str:
        return "Shell"

    async def _execute(self, command: str, timeout: Optional[int] = None) -> ToolResult:
        """Run a shell command and return the output.

        Args:
            command: The command to run.
            timeout: Optional timeout in seconds.

        Returns:
            ToolResult: The output of the command (stdout and stderr).

        Raises:
            FileNotFoundError: If command not found
            subprocess.TimeoutExpired: If timeout is exceeded
            Exception: Any command execution errors
        """
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate(timeout=timeout)
            output = stdout.strip() or CMD_OUTPUT_NO_OUTPUT
            error = stderr.strip() or CMD_OUTPUT_NO_ERRORS
            resp = CMD_OUTPUT_FORMAT.format(output=output, error=error).strip()

            # Truncate if the output is too long to prevent issues
            if len(resp) > MAX_COMMAND_OUTPUT:
                # Include both the beginning and end of the output
                start_part = resp[:COMMAND_OUTPUT_START_INDEX]
                end_part = (
                    resp[-COMMAND_OUTPUT_END_SIZE:]
                    if len(resp) > COMMAND_OUTPUT_THRESHOLD
                    else resp[COMMAND_OUTPUT_START_INDEX:]
                )
                truncated_resp = start_part + CMD_OUTPUT_TRUNCATED + end_part
                return truncated_resp

            return resp
        except subprocess.TimeoutExpired:
            if self.ui:
                await self.ui.error(f"Command timed out after {timeout} seconds")
            raise ToolExecutionError(
                tool_name=self.tool_name,
                message=f"Command timed out after {timeout} seconds",
                original_error=None
            )

    async def _handle_error(self, error: Exception, *args, **kwargs) -> ToolResult:
        """Handle errors with specific messages for common cases.

        Raises:
            ToolExecutionError: Always raised with structured error information
        """
        command = args[0] if args else kwargs.get('command', 'unknown')
        
        if isinstance(error, FileNotFoundError):
            err_msg = ERROR_COMMAND_EXECUTION.format(command=command, error=error)
        else:
            # Use parent class handling for other errors
            await super()._handle_error(error, *args, **kwargs)
            return  # super() will raise, this is unreachable

        if self.ui:
            await self.ui.error(err_msg)

        raise ToolExecutionError(tool_name=self.tool_name, message=err_msg, original_error=error)

    def _get_error_context(self, command: str = None, *args, **kwargs) -> str:
        """Get error context for command execution."""
        if command:
            return f"running command '{command}'"
        return super()._get_error_context(*args, **kwargs)


# Create the function that maintains the existing interface
async def run_command(command: str, timeout: Optional[int] = None) -> ToolResult:
    """
    Run a shell command and return the output. User must confirm risky commands.

    Args:
        command (str): The command to run.
        timeout (Optional[int]): Optional timeout in seconds.

    Returns:
        ToolResult: The output of the command (stdout and stderr) or an error message.
    """
    tool = RunCommandTool(default_ui)
    try:
        return await tool.execute(command, timeout)
    except ToolExecutionError as e:
        # Return error message for pydantic-ai compatibility
        return str(e)
