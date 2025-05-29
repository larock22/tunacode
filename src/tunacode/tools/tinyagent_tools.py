"""Simple synchronous tool implementations for TinyAgent."""

from __future__ import annotations

import os
import subprocess
from typing import Optional

from tinyagent import tool
from prompt_toolkit.application import run_in_terminal


def _confirm_operation(tool_name: str, args: dict) -> bool:
    """Ask the user to confirm a tool operation."""

    def _ask() -> bool:
        print(f"\n{tool_name} called with: {args}")
        answer = input("Proceed? [y/N]: ").strip().lower()
        return answer in {"y", "yes"}

    return run_in_terminal(_ask)


@tool
def read_file(filepath: str) -> str:
    """Read file contents."""
    if not _confirm_operation("read_file", {"filepath": filepath}):
        raise Exception("Operation cancelled")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"✓ Read {len(content)} characters from {filepath}")
    return content


@tool
def write_file(filepath: str, content: str) -> str:
    """Write content to a file, creating directories if needed."""
    if not _confirm_operation("write_file", {"filepath": filepath}):
        raise Exception("Operation cancelled")

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✓ Wrote {len(content)} characters to {filepath}")
    return f"Wrote to {filepath}"


@tool
def update_file(filepath: str, old_content: str, new_content: str) -> str:
    """Replace the first occurrence of ``old_content`` with ``new_content``."""
    if not _confirm_operation(
        "update_file", {"filepath": filepath, "target": old_content, "patch": new_content}
    ):
        raise Exception("Operation cancelled")

    with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()

    if old_content not in data:
        raise Exception("Target text not found in file")

    updated = data.replace(old_content, new_content, 1)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"✓ Updated {filepath}")
    return f"Updated {filepath}"


@tool
def run_command(command: str, timeout: Optional[int] = None) -> str:
    """Run a shell command and return its output."""
    if not _confirm_operation("run_command", {"command": command, "timeout": timeout}):
        raise Exception("Operation cancelled")

    completed = subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    output = completed.stdout.strip() or "No output."
    error = completed.stderr.strip() or "No errors."

    result = f"STDOUT:\n{output}\n\nSTDERR:\n{error}"
    print(f"✓ Command exited with {completed.returncode}")
    return result
