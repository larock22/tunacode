"""High level workflow agent orchestrating planning and execution."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from tunacode.core.state import StateManager
from tunacode.types import ModelName, ToolCallback

from .tinyagent_main import get_or_create_react_agent


class WorkflowAgent:
    """Agent implementing Planner → Executor → Reflector pipeline."""

    def __init__(self, model: ModelName, state_manager: StateManager):
        self.model = model
        self.state_manager = state_manager
        self._agent = get_or_create_react_agent(model, state_manager)

    async def plan(self, goal: str) -> List[str]:
        """Generate a list of tasks for the given goal."""
        prompt = (
            "You are the Planner. Break the following user request into a JSON list of"
            " short tasks.\nUser request:\n" + goal + '\nReturn JSON: {"tasks": [..]}'
        )
        result = await self._agent.run_react(prompt)
        try:
            data = json.loads(result)
            tasks = data.get("tasks") or []
        except Exception:
            tasks = []
        if not tasks:
            tasks = [goal]
        return [str(t) for t in tasks]

    async def execute(self, task: str, tool_callback: ToolCallback | None = None) -> str:
        """Execute a single task using the ReactAgent."""
        exec_prompt = (
            "You are the Executor. Perform the following task using available tools and"
            " respond with the result only.\nTask:\n" + task
        )
        if tool_callback:
            return await self._agent.run_react(exec_prompt, tool_callback=tool_callback)
        return await self._agent.run_react(exec_prompt)

    async def reflect(self, goal: str, history: List[Dict[str, str]]) -> str:
        """Reflect on results and produce final answer or new tasks."""
        prompt = (
            "You are the Reflector. Given the original goal and the task history,"
            " determine if the goal is met. If so, summarise the result. If not,"
            " suggest new tasks in JSON under 'tasks'.\nGoal:\n"
            + goal
            + "\nHistory:\n"
            + json.dumps(history)
        )
        return await self._agent.run_react(prompt)

    async def run(self, message: str, tool_callback: ToolCallback | None = None) -> Dict[str, Any]:
        """Run the full Planner → Executor → Reflector workflow."""
        tasks = await self.plan(message)
        history: List[Dict[str, str]] = []
        for task in tasks:
            result = await self.execute(task, tool_callback=tool_callback)
            history.append({"task": task, "result": result})
        final = await self.reflect(message, history)
        return {"result": final, "success": True, "model": self.model}


def get_workflow_agent(model: ModelName, state_manager: StateManager) -> WorkflowAgent:
    """Convenience factory for a workflow agent."""
    return WorkflowAgent(model, state_manager)
