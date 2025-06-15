"""
Constrained LLM planner for architect mode.

Provides a minimal, strictly-validated LLM planning interface for requests
that can't be handled by the deterministic analyzer.
"""

import json
from dataclasses import dataclass
from typing import List, Optional

from ...types import ModelName
from ..state import StateManager


@dataclass
class Task:
    """Simple task representation."""

    id: int
    description: str
    mutate: bool
    tool: Optional[str] = None
    args: Optional[dict] = None


def _load_planner_prompt() -> str:
    """Load the planner prompt from file."""
    from pathlib import Path

    # Get the prompt file path
    current_dir = Path(__file__).parent.parent.parent
    prompt_path = current_dir / "prompts" / "architect_planner.md"

    if prompt_path.exists():
        with open(prompt_path, "r") as f:
            return f.read()
    else:
        # Fallback prompt if file not found
        return """You are a task planner. Convert requests into JSON arrays.
Each task needs: id (int), description (str), mutate (bool).
Return ONLY valid JSON array."""


# Load the prompt
PLANNER_PROMPT = _load_planner_prompt()


class ConstrainedPlanner:
    """Minimal LLM planner with strict validation."""

    def __init__(self, state_manager: StateManager):
        self.state = state_manager
        self.max_retries = 3

    async def plan(
        self, request: str, model: ModelName, context: Optional[str] = None
    ) -> List[Task]:
        """Generate a task plan using the LLM with strict validation."""
        from rich.console import Console

        from ..agents.main import get_agent_tool

        console = Console()
        Agent, _ = get_agent_tool()

        # Build the full prompt
        full_prompt = request
        if context:
            full_prompt = f"Context: {context}\n\nRequest: {request}"

        # Log what we're sending to LLM
        console.print("\n[blue]━━━ ARCHITECT MODE: SENDING TO LLM ━━━[/blue]")
        console.print(f"[cyan]User Prompt:[/cyan] {full_prompt}")
        console.print("[blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/blue]")

        # Try to get a valid plan with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                console.print(
                    f"[dim][Constrained Planning] Attempt {attempt + 1}/{self.max_retries}[/dim]"
                )

                # Create planner with strict prompt
                planner = Agent(
                    model=model,
                    system_prompt=PLANNER_PROMPT,
                    result_type=str,  # Get raw string to parse ourselves
                    retries=1,  # Handle retries ourselves
                )

                # Get the response
                result = await planner.run(full_prompt)
                response_text = result.data.strip()

                # Log what we got back
                console.print("\n[green]━━━ ARCHITECT MODE: LLM RESPONSE ━━━[/green]")
                console.print(response_text)
                console.print("[green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/green]")

                # Remove any markdown code blocks if present
                if response_text.startswith("```"):
                    lines = response_text.split("\n")
                    response_text = "\n".join(lines[1:-1])

                # Try to parse the JSON
                tasks_data = json.loads(response_text)

                # Validate and convert to Task objects
                tasks = self._validate_and_convert(tasks_data)

                console.print(
                    f"[dim][Constrained Planning] Successfully generated {len(tasks)} tasks[/dim]"
                )
                return tasks

            except json.JSONDecodeError as e:
                last_error = f"Invalid JSON: {str(e)}"
                console.print(
                    f"[yellow][Constrained Planning] JSON parse error: {last_error}[/yellow]"
                )

            except ValueError as e:
                last_error = f"Validation error: {str(e)}"
                console.print(f"[yellow][Constrained Planning] {last_error}[/yellow]")

            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                console.print(f"[red][Constrained Planning] {last_error}[/red]")

            # Exponential backoff between retries
            if attempt < self.max_retries - 1:
                import asyncio

                wait_time = 2**attempt
                console.print(f"[dim]Waiting {wait_time}s before retry...[/dim]")
                await asyncio.sleep(wait_time)

        # All retries failed
        console.print(f"[red][Constrained Planning] Failed after {self.max_retries} attempts[/red]")
        raise ValueError(f"Failed to generate valid plan: {last_error}")

    def _validate_and_convert(self, tasks_data: list) -> List[Task]:
        """Validate task data and convert to Task objects."""
        if not isinstance(tasks_data, list):
            raise ValueError("Response must be a JSON array")

        if not tasks_data:
            raise ValueError("Task list cannot be empty")

        tasks = []
        seen_ids = set()

        for i, task_data in enumerate(tasks_data):
            if not isinstance(task_data, dict):
                raise ValueError(f"Task {i + 1} must be a JSON object")

            # Required fields
            if "id" not in task_data:
                raise ValueError(f"Task {i + 1} missing required field: id")
            if "description" not in task_data:
                raise ValueError(f"Task {i + 1} missing required field: description")
            if "mutate" not in task_data:
                raise ValueError(f"Task {i + 1} missing required field: mutate")

            # Validate types
            task_id = task_data["id"]
            if not isinstance(task_id, int):
                raise ValueError(f"Task {i + 1} id must be an integer")
            if task_id in seen_ids:
                raise ValueError(f"Duplicate task id: {task_id}")
            seen_ids.add(task_id)

            if not isinstance(task_data["description"], str):
                raise ValueError(f"Task {task_id} description must be a string")
            if not isinstance(task_data["mutate"], bool):
                raise ValueError(f"Task {task_id} mutate must be a boolean")

            # Optional fields
            tool = task_data.get("tool")
            args = task_data.get("args")

            if tool is not None and not isinstance(tool, str):
                raise ValueError(f"Task {task_id} tool must be a string")
            if args is not None and not isinstance(args, dict):
                raise ValueError(f"Task {task_id} args must be a dictionary")

            # Create Task object
            tasks.append(
                Task(
                    id=task_id,
                    description=task_data["description"],
                    mutate=task_data["mutate"],
                    tool=tool,
                    args=args,
                )
            )

        # Validate task ordering (reads before writes when possible)
        # This is a soft validation - we'll just warn
        last_read_id = -1
        first_write_id = float("inf")
        for task in tasks:
            if not task.mutate:
                last_read_id = max(last_read_id, task.id)
            else:
                first_write_id = min(first_write_id, task.id)

        if last_read_id > first_write_id:
            from rich.console import Console

            Console().print("[yellow]Warning: Some read operations come after writes[/yellow]")

        return tasks
