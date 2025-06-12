"""Agent orchestration scaffolding.

This module defines an ``OrchestratorAgent`` class that demonstrates how
higher level planning and delegation could be layered on top of the existing
``process_request`` workflow.  The goal is to keep orchestration logic isolated
from the core agent implementation while reusing all current tooling and state
handling provided by ``main.process_request``.
"""

from __future__ import annotations

import asyncio
import itertools
from typing import List

from ...types import AgentRun, FallbackResponse, ModelName, ResponseState
from ..llm.planner import make_plan
from ..state import StateManager
from . import main as agent_main
from .planner_schema import Task
from .readonly import ReadOnlyAgent


class OrchestratorAgent:
    """Plan and run a sequence of sub-agent tasks."""

    def __init__(self, state_manager: StateManager):
        self.state = state_manager

    async def plan(self, request: str, model: ModelName) -> List[Task]:
        """Plan tasks for a user request using the planner LLM."""

        return await make_plan(request, model, self.state)

    async def _run_sub_task(self, task: Task, model: ModelName) -> AgentRun:
        """Execute a single task using an appropriate sub-agent."""
        from rich.console import Console

        console = Console()

        # Show which task is being executed
        task_type = "WRITE" if task.mutate else "READ"
        console.print(f"\n[dim][Task {task.id}] {task_type}[/dim]")
        console.print(f"[dim]  → {task.description}[/dim]")

        if task.mutate:
            agent_main.get_or_create_agent(model, self.state)
            result = await agent_main.process_request(model, task.description, self.state)
        else:
            agent = ReadOnlyAgent(model, self.state)
            result = await agent.process_request(task.description)

        console.print(f"[dim][Task {task.id}] Complete[/dim]")
        return result

    async def run(self, request: str, model: ModelName | None = None) -> List[AgentRun]:
        """Plan and execute a user request.

        Parameters
        ----------
        request:
            The high level user request to process.
        model:
            Optional model name to use for sub agents.  Defaults to the current
            session model.
        """
        from rich.console import Console

        console = Console()
        model = model or self.state.session.current_model

        # Track response state across all sub-tasks
        response_state = ResponseState()

        # Show orchestrator is starting
        console.print(
            "\n[cyan]Orchestrator Mode: Analyzing request and creating execution plan...[/cyan]"
        )

        tasks = await self.plan(request, model)

        # Show execution is starting
        console.print(f"\n[cyan]Executing plan with {len(tasks)} tasks...[/cyan]")

        results: List[AgentRun] = []
        task_progress = []

        for mutate_flag, group in itertools.groupby(tasks, key=lambda t: t.mutate):
            if mutate_flag:
                for t in group:
                    result = await self._run_sub_task(t, model)
                    results.append(result)

                    # Track task progress
                    task_progress.append(
                        {
                            "task": t,
                            "completed": True,
                            "had_output": hasattr(result, "result")
                            and result.result
                            and getattr(result.result, "output", None),
                        }
                    )

                    # Check if this task produced user-visible output
                    if hasattr(result, "response_state"):
                        response_state.has_user_response |= result.response_state.has_user_response
            else:
                # Show parallel execution
                task_list = list(group)
                if len(task_list) > 1:
                    console.print(
                        f"\n[dim][Parallel Execution] Running {len(task_list)} read-only tasks concurrently...[/dim]"
                    )
                coros = [self._run_sub_task(t, model) for t in task_list]
                parallel_results = await asyncio.gather(*coros)
                results.extend(parallel_results)

                # Track parallel task progress
                for t, result in zip(task_list, parallel_results):
                    task_progress.append(
                        {
                            "task": t,
                            "completed": True,
                            "had_output": hasattr(result, "result")
                            and result.result
                            and getattr(result.result, "output", None),
                        }
                    )

                    # Check if this task produced user-visible output
                    if hasattr(result, "response_state"):
                        response_state.has_user_response |= result.response_state.has_user_response

        console.print("\n[green]Orchestrator completed all tasks successfully![/green]")

        # Check if we need a fallback response
        has_any_output = any(
            hasattr(r, "result") and r.result and getattr(r.result, "output", None) for r in results
        )

        fallback_enabled = self.state.session.user_config.get("settings", {}).get(
            "fallback_response", True
        )

        # Use has_any_output as the primary check since response_state might not be set for all agents
        if not has_any_output and fallback_enabled:
            # Generate a detailed fallback response
            completed_count = sum(1 for tp in task_progress if tp["completed"])
            output_count = sum(1 for tp in task_progress if tp["had_output"])

            fallback = FallbackResponse(
                summary="Orchestrator completed all tasks but no final response was generated.",
                progress=f"Executed {completed_count}/{len(tasks)} tasks successfully",
            )

            # Add task details based on verbosity
            verbosity = self.state.session.user_config.get("settings", {}).get(
                "fallback_verbosity", "normal"
            )

            if verbosity in ["normal", "detailed"]:
                # List what was done
                if task_progress:
                    fallback.issues.append(f"Tasks executed: {completed_count}")
                    if output_count == 0:
                        fallback.issues.append("No tasks produced visible output")

                    if verbosity == "detailed":
                        # Add task descriptions
                        for i, tp in enumerate(task_progress, 1):
                            task_type = "WRITE" if tp["task"].mutate else "READ"
                            status = "✓" if tp["completed"] else "✗"
                            fallback.issues.append(
                                f"{status} Task {i} [{task_type}]: {tp['task'].description}"
                            )

            # Suggest next steps
            fallback.next_steps.append("Review the task execution above for any errors")
            fallback.next_steps.append(
                "Try running individual tasks separately for more detailed output"
            )

            # Create synthesized response
            synthesis_parts = [fallback.summary, ""]

            if fallback.progress:
                synthesis_parts.append(f"Progress: {fallback.progress}")

            if fallback.issues:
                synthesis_parts.append("\nDetails:")
                synthesis_parts.extend(f"  • {issue}" for issue in fallback.issues)

            if fallback.next_steps:
                synthesis_parts.append("\nNext steps:")
                synthesis_parts.extend(f"  • {step}" for step in fallback.next_steps)

            synthesis = "\n".join(synthesis_parts)

            class FallbackResult:
                def __init__(self, output: str, response_state: ResponseState):
                    self.output = output
                    self.response_state = response_state

            class FallbackRun:
                def __init__(self, synthesis: str, response_state: ResponseState):
                    self.result = FallbackResult(synthesis, response_state)
                    self.response_state = response_state

            response_state.has_final_synthesis = True
            results.append(FallbackRun(synthesis, response_state))

        return results
