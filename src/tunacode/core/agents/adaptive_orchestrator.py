"""
Adaptive orchestrator for architect mode.

Implements the hybrid approach with deterministic analysis, constrained planning,
parallel execution, and feedback loops.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...types import AgentRun, ModelName, ResponseState
from ..analysis import ConstrainedPlanner, FeedbackDecision, FeedbackLoop
from ..analysis.hybrid_request_analyzer import HybridRequestAnalyzer
from ..state import StateManager
from . import main as agent_main
from .readonly import ReadOnlyAgent


@dataclass
class ExecutionResult:
    """Result of executing a task."""

    task: Dict[str, Any]
    result: Any
    duration: float
    error: Optional[Exception] = None


class AdaptiveOrchestrator:
    """Orchestrates task execution with adaptive planning and parallel execution."""

    def __init__(self, state_manager: StateManager):
        self.state = state_manager
        self.analyzer = HybridRequestAnalyzer(model=state_manager.session.current_model)
        self.planner = ConstrainedPlanner(state_manager)
        self.feedback_loop = FeedbackLoop(state_manager)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Timeouts
        self.task_timeout = 30  # 30s per task
        self.total_timeout = 120  # 2min total

    async def run(self, request: str, model: ModelName | None = None) -> List[AgentRun]:
        """Execute a request with adaptive planning and feedback loops.

        Implements the Frame → Think → Act → Loop pattern:
        1. Frame: Establish context (who, where, what)
        2. Think: Analyze request and plan tasks
        3. Act: Execute tasks
        4. Loop: Analyze results and adapt
        """
        from rich.console import Console

        console = Console()

        model = model or self.state.session.current_model
        start_time = time.time()

        console.print("\n[cyan]Adaptive Orchestrator: Framing context...[/cyan]")

        try:
            # Step 1: FRAME - Establish context
            project_context = self.analyzer.project_context.detect_context()
            sources = (
                ", ".join(project_context.source_dirs[:2])
                if project_context.source_dirs
                else "unknown"
            )
            framework = f"({project_context.framework})" if project_context.framework else ""
            console.print(
                f"[dim]Project: {project_context.project_type.value} {framework} | Sources: {sources}[/dim]"
            )

            # Step 2: THINK - Get tasks from LLM planner
            tasks = await self._get_initial_tasks(request, None, model)
            if not tasks:
                console.print("[yellow]No tasks generated. Falling back to regular mode.[/yellow]")
                return []

            console.print(f"\n[cyan]Executing plan with {len(tasks)} initial tasks...[/cyan]")

            # Step 3 & 4: ACT & LOOP - Execute with feedback loop
            return await self._execute_with_feedback(request, tasks, model, start_time)

        except asyncio.TimeoutError:
            console.print("[red]Orchestrator timeout. Falling back to regular mode.[/red]")
            return []
        except Exception as e:
            console.print(f"[red]Orchestrator error: {str(e)}. Falling back to regular mode.[/red]")
            return []

    async def _get_initial_tasks(
        self, request: str, intent: Any, model: ModelName
    ) -> Optional[List[Dict[str, Any]]]:
        """Get tasks from LLM planner."""
        from rich.console import Console

        console = Console()

        # Just use LLM planning for everything
        console.print("[dim]Using LLM planner[/dim]")
        try:
            # Build context from session state
            context_parts = []

            # Add files in context
            if self.state.session.files_in_context:
                files_list = list(self.state.session.files_in_context)
                context_parts.append(f"Files currently in context: {', '.join(files_list)}")

            # Add recent tool calls if any
            if self.state.session.tool_calls:
                recent_tools = [tc["tool"] for tc in self.state.session.tool_calls[-3:]]
                context_parts.append(f"Recent operations: {', '.join(recent_tools)}")

            context = "\n".join(context_parts) if context_parts else None

            task_objects = await self.planner.plan(request, model, context=context)
            # Convert Task objects to dicts
            return [
                {
                    "id": t.id,
                    "description": t.description,
                    "mutate": t.mutate,
                    "tool": t.tool,
                    "args": t.args,
                }
                for t in task_objects
            ]
        except Exception as e:
            console.print(f"[yellow]Planning failed: {str(e)}[/yellow]")
            return None

    async def _execute_with_feedback(
        self, request: str, initial_tasks: List[Dict[str, Any]], model: ModelName, start_time: float
    ) -> List[AgentRun]:
        """Execute tasks with feedback loop - the ACT and LOOP phases."""
        from rich.console import Console

        console = Console()

        # all_results = []  # Not used after refactoring
        completed_tasks = []
        remaining_tasks = initial_tasks
        iteration = 0

        # Track aggregated output from all tasks
        aggregated_outputs = []
        has_any_output = False

        # Track findings for adaptive task generation
        findings = {
            "interesting_files": [],
            "directories_found": [],
            "patterns_detected": [],
        }

        response_state = ResponseState()

        while remaining_tasks and iteration < self.feedback_loop.max_iterations:
            # Check total timeout
            if time.time() - start_time > self.total_timeout:
                console.print("[yellow]Total execution timeout reached[/yellow]")
                break

            console.print(
                f"\n[dim]Iteration {iteration + 1}: Executing {len(remaining_tasks)} tasks[/dim]"
            )

            # Execute current batch
            batch_results = await self._execute_task_batch(remaining_tasks, model)

            # Convert ExecutionResults to AgentRuns and collect
            for exec_result in batch_results:
                if exec_result.error:
                    console.print(f"[red]Task failed: {exec_result.task['description']}[/red]")
                    console.print(f"[red]Error: {str(exec_result.error)}[/red]")

                # Collect outputs instead of adding results directly
                if (
                    exec_result.result
                    and hasattr(exec_result.result, "result")
                    and exec_result.result.result
                ):
                    if (
                        hasattr(exec_result.result.result, "output")
                        and exec_result.result.result.output
                    ):
                        aggregated_outputs.append(exec_result.result.result.output)
                        has_any_output = True
                        response_state.has_user_response = True

                completed_tasks.append(exec_result.task)

                # Extract findings from successful tasks
                if exec_result.result and not exec_result.error:
                    self._extract_findings(exec_result, findings)

                    # Track files created/modified for context
                    tool = exec_result.task.get("tool")
                    if tool in ["write_file", "update_file"]:
                        file_path = exec_result.task.get("args", {}).get("file_path")
                        if file_path:
                            self.state.session.files_in_context.add(file_path)

            # THINK phase of the loop - analyze and adapt
            # Get project context for smarter decisions
            project_context = self.analyzer.project_context.detect_context()

            # Generate adaptive follow-up tasks based on findings
            if iteration < self.feedback_loop.max_iterations - 1:  # Not last iteration
                followup_tasks = self.analyzer.task_generator.generate_followup_tasks(
                    findings, project_context
                )

                if followup_tasks:
                    # Task generator already returns dicts, just limit them
                    new_tasks = followup_tasks[:3]  # Limit follow-ups per iteration

                    if new_tasks:
                        console.print(
                            f"[dim]Generated {len(new_tasks)} adaptive follow-up tasks[/dim]"
                        )
                        remaining_tasks = new_tasks
                    else:
                        # Use original feedback mechanism
                        feedback = await self.feedback_loop.analyze_results(
                            request, completed_tasks, batch_results, iteration + 1, model
                        )

                        console.print(
                            f"[dim]Feedback: {feedback.decision.value} - {feedback.summary}[/dim]"
                        )

                        if feedback.decision == FeedbackDecision.COMPLETE:
                            break
                        elif feedback.decision == FeedbackDecision.ERROR:
                            console.print(
                                f"[red]Stopping due to error: {feedback.error_message}[/red]"
                            )
                            break
                        elif feedback.new_tasks:
                            remaining_tasks = feedback.new_tasks
                        else:
                            break
                else:
                    break
            else:
                break

            iteration += 1

        console.print(
            f"\n[green]Adaptive execution completed after {iteration + 1} iterations[/green]"
        )

        # Create a single consolidated response
        if has_any_output:
            # Combine all outputs into one response
            combined_output = "\n\n".join(aggregated_outputs)

            class ConsolidatedResult:
                def __init__(self, output: str):
                    self.output = output

            class ConsolidatedRun:
                def __init__(self, output: str):
                    self.result = ConsolidatedResult(output)
                    self.response_state = response_state

            return [ConsolidatedRun(combined_output)]
        elif completed_tasks:
            # No output from tasks, create a summary
            summary_parts = [f"Completed {len(completed_tasks)} tasks:"]
            for task in completed_tasks[:5]:  # Show first 5
                summary_parts.append(f"• {task['description']}")
            if len(completed_tasks) > 5:
                summary_parts.append(f"• ... and {len(completed_tasks) - 5} more")

            class SummaryResult:
                def __init__(self, output: str):
                    self.output = output

            class SummaryRun:
                def __init__(self, output: str):
                    self.result = SummaryResult(output)
                    self.response_state = response_state

            return [SummaryRun("\n".join(summary_parts))]

        return []

    async def _execute_task_batch(
        self, tasks: List[Dict[str, Any]], model: ModelName
    ) -> List[ExecutionResult]:
        """Execute a batch of tasks with parallelization."""
        from rich.console import Console

        console = Console()

        # Separate read and write tasks
        read_tasks = [t for t in tasks if not t.get("mutate", False)]
        write_tasks = [t for t in tasks if t.get("mutate", False)]

        results = []

        # Execute read tasks in parallel
        if read_tasks:
            if len(read_tasks) > 1:
                console.print(f"[dim]Executing {len(read_tasks)} read tasks in parallel...[/dim]")

            read_coros = [self._execute_single_task(task, model) for task in read_tasks]
            read_results = await asyncio.gather(*read_coros, return_exceptions=True)

            for task, result in zip(read_tasks, read_results):
                if isinstance(result, Exception):
                    results.append(
                        ExecutionResult(task=task, result=None, duration=0, error=result)
                    )
                else:
                    results.append(result)

        # Execute write tasks sequentially
        for task in write_tasks:
            console.print(f"[dim]Executing write task: {task['description']}[/dim]")
            try:
                result = await self._execute_single_task(task, model)
                results.append(result)
            except Exception as e:
                results.append(ExecutionResult(task=task, result=None, duration=0, error=e))

        return results

    async def _execute_single_task(self, task: Dict[str, Any], model: ModelName) -> ExecutionResult:
        """Execute a single task."""
        start_time = time.time()

        try:
            # Execute with timeout
            result = await asyncio.wait_for(self._run_task(task, model), timeout=self.task_timeout)

            duration = time.time() - start_time
            return ExecutionResult(task=task, result=result, duration=duration)

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return ExecutionResult(
                task=task,
                result=None,
                duration=duration,
                error=Exception(f"Task timed out after {self.task_timeout}s"),
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(task=task, result=None, duration=duration, error=e)

    async def _run_task(self, task: Dict[str, Any], model: ModelName) -> AgentRun:
        """Run a task using the appropriate agent."""
        from rich.console import Console

        console = Console()

        # Show task execution
        task_type = "WRITE" if task.get("mutate", False) else "READ"
        console.print(f"\n[dim][Task {task['id']}] {task_type}[/dim]")
        console.print(f"[dim]  → {task['description']}[/dim]")

        # If task has specific tool and args, format the request
        if task.get("tool") and task.get("args"):
            # This is a specific tool call
            tool_request = self._format_tool_request(task)
        else:
            # This is a general request
            # Add context about recent operations
            context_info = ""
            if self.state.session.files_in_context:
                files_list = list(self.state.session.files_in_context)
                context_info = f" (context: working with {', '.join(files_list)})"
            tool_request = task["description"] + context_info

        # Execute using appropriate agent
        if task.get("mutate", False):
            agent_main.get_or_create_agent(model, self.state)
            result = await agent_main.process_request(model, tool_request, self.state)
        else:
            agent = ReadOnlyAgent(model, self.state)
            result = await agent.process_request(tool_request)

        console.print(f"[dim][Task {task['id']}] Complete[/dim]")
        return result

    def _format_tool_request(self, task: Dict[str, Any]) -> str:
        """Format a specific tool request."""
        tool = task.get("tool")
        args = task.get("args", {})

        # Format based on tool type
        if tool == "read_file":
            return f"Read the file {args.get('file_path', '')}"
        elif tool == "grep":
            pattern = args.get("pattern", "")
            directory = args.get("directory", ".")
            include_files = args.get("include_files", "")
            use_regex = args.get("use_regex", False)

            # Build a more detailed request
            request_parts = [f"Search for '{pattern}' in {directory}"]
            if include_files:
                request_parts.append(f"in files matching {include_files}")
            if use_regex:
                request_parts.append("using regex")

            return " ".join(request_parts)
        elif tool == "list_dir":
            directory = args.get("directory", ".")
            return f"List the contents of directory {directory}"
        elif tool == "write_file":
            file_path = args.get("file_path", "")
            content = args.get("content", "")
            if content:
                # Include the actual content in the request
                return f"Create file {file_path} with the following content:\n{content}"
            else:
                return f"Create file {file_path} with appropriate content"
        elif tool == "update_file":
            file_path = args.get("file_path", "")
            target = args.get("target", "")
            patch = args.get("patch", "")
            if target and patch:
                return f"Update {file_path} by replacing '{target}' with '{patch}'"
            else:
                return f"Update {file_path} as described: {task['description']}"
        elif tool == "run_command":
            return f"Run command: {args.get('command', '')}"
        elif tool == "bash":
            command = args.get("command", "")
            # Handle special cases for better commands
            if "ls -R" in command:
                # Replace recursive ls with list_dir tool
                return "Use list_dir tool to list directory contents"
            elif command.strip() in ["ls", "ls -la", "ls -l"]:
                # Simple ls commands should use list_dir
                return "Use list_dir tool to list current directory"
            return f"Execute bash command: {command}"
        elif tool == "analyze":
            # For analyze tasks, pass through the original request
            original_request = args.get("request", task["description"])
            return original_request
        else:
            return task["description"]

    def _extract_findings(self, exec_result: ExecutionResult, findings: Dict[str, List]) -> None:
        """Extract interesting findings from task execution results."""
        task = exec_result.task
        tool = task.get("tool")

        # Extract output text if available
        output_text = ""
        if exec_result.result and hasattr(exec_result.result, "result"):
            result = exec_result.result.result
            if hasattr(result, "output"):
                output_text = str(result.output)

        if not output_text:
            return

        # Extract findings based on tool type
        if tool == "list_dir":
            # Look for interesting files and directories
            lines = output_text.split("\n")
            for line in lines:
                line = line.strip()
                if "[DIR]" in line:
                    # Extract directory name
                    dir_name = line.split("[DIR]")[0].strip()
                    if dir_name and not dir_name.startswith("."):
                        findings["directories_found"].append(dir_name)
                elif "[FILE]" in line:
                    # Extract file name
                    file_name = line.split("[FILE]")[0].strip()
                    # Look for interesting files
                    if any(
                        pattern in file_name.lower()
                        for pattern in [
                            "config",
                            "settings",
                            "main",
                            "index",
                            "app",
                            "server",
                            "api",
                        ]
                    ):
                        findings["interesting_files"].append(file_name)

        elif tool == "grep":
            # Track that we found matches for this pattern
            pattern = task.get("args", {}).get("pattern", "")
            if "matches" in output_text.lower() or "found" in output_text.lower():
                findings["patterns_detected"].append(pattern)

        elif tool == "read_file":
            # Look for imports, dependencies, or other interesting patterns
            # file_path = task.get("args", {}).get("file_path", "")  # Not used yet

            # For package.json, pyproject.toml, etc., we could extract dependencies
            # but keeping it simple for now
            if "import" in output_text or "require" in output_text:
                # This file has imports, might be worth exploring imports
                findings["interesting_files"].extend(
                    [
                        f
                        for f in output_text.split()
                        if f.endswith((".py", ".js", ".ts", ".jsx", ".tsx"))
                    ]
                )

        # Limit findings to avoid explosion
        for key in findings:
            findings[key] = list(set(findings[key]))[:10]
