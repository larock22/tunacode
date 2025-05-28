"""Optimized setup coordinator with deferred loading."""

import asyncio
from typing import List, Set

from tunacode.core.setup.base import BaseSetup
from tunacode.core.state import StateManager
from tunacode.ui import console as ui


class OptimizedSetupCoordinator:
    """Optimized coordinator that defers non-critical setup steps."""

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.critical_steps: List[BaseSetup] = []
        self.deferred_steps: List[BaseSetup] = []
        self._deferred_task = None

        # Define critical steps that must run at startup
        self.critical_step_names: Set[str] = {
            "Configuration",  # Need config to know which model to use
            "Environment Variables",  # Need API keys
        }

    def register_step(self, step: BaseSetup) -> None:
        """Register a setup step, separating critical from deferred."""
        if step.name in self.critical_step_names:
            self.critical_steps.append(step)
        else:
            self.deferred_steps.append(step)

    async def run_setup(self, force_setup: bool = False) -> None:
        """Run critical setup immediately, defer the rest."""
        # Run critical steps synchronously
        for step in self.critical_steps:
            try:
                if await step.should_run(force_setup):
                    await step.execute(force_setup)
                    if not await step.validate():
                        await ui.error(f"Setup validation failed: {step.name}")
                        raise RuntimeError(f"Setup step '{step.name}' failed validation")
            except Exception as e:
                await ui.error(f"Setup failed at step '{step.name}': {str(e)}")
                raise

        # Schedule deferred steps to run in background
        if self.deferred_steps and not self._deferred_task:
            self._deferred_task = asyncio.create_task(self._run_deferred_steps(force_setup))

    async def _run_deferred_steps(self, force_setup: bool) -> None:
        """Run deferred steps in the background."""
        # Wait a moment to let the main UI start
        await asyncio.sleep(0.1)

        for step in self.deferred_steps:
            try:
                if await step.should_run(force_setup):
                    await step.execute(force_setup)
                    # Don't validate deferred steps - they're non-critical
            except Exception:
                # Log but don't fail on deferred steps
                pass

    async def ensure_deferred_complete(self) -> None:
        """Ensure deferred steps are complete before certain operations."""
        if self._deferred_task and not self._deferred_task.done():
            await self._deferred_task

    def clear_steps(self) -> None:
        """Clear all registered setup steps."""
        self.critical_steps.clear()
        self.deferred_steps.clear()
