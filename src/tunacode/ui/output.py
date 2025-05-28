"""Output and display functions for Sidekick UI."""

from prompt_toolkit.application import run_in_terminal
from rich.console import Console
from rich.padding import Padding

from tunacode.configuration.settings import ApplicationSettings
from tunacode.constants import (MSG_UPDATE_AVAILABLE, MSG_UPDATE_INSTRUCTION, MSG_VERSION_DISPLAY,
                                UI_COLORS, UI_THINKING_MESSAGE)
from tunacode.core.state import StateManager
from tunacode.utils.file_utils import DotDict

from .constants import SPINNER_TYPE
from .decorators import create_sync_wrapper

console = Console()
colors = DotDict(UI_COLORS)

BANNER = (
    "[bold #00d7ff]┌─────────────────────────────────────────────────────────────────┐"
    "[/bold #00d7ff]\n"
    "[bold #00d7ff]│[/bold #00d7ff] [bold white]T U N A C O D E[/bold white] "
    "[dim #64748b]• Agentic AI Development Environment[/dim #64748b] "
    "[bold #00d7ff]│[/bold #00d7ff]\n"
    "[bold #00d7ff]└─────────────────────────────────────────────────────────────────┘"
    "[/bold #00d7ff]"
)


@create_sync_wrapper
async def print(message, **kwargs) -> None:
    """Print a message to the console."""
    await run_in_terminal(lambda: console.print(message, **kwargs))


async def line() -> None:
    """Print a line to the console."""
    await run_in_terminal(lambda: console.line())


async def info(text: str) -> None:
    """Print an informational message."""
    await print(f"[{colors.primary}]●[/{colors.primary}] {text}", style=colors.muted)


async def success(message: str) -> None:
    """Print a success message."""
    await print(f"[{colors.success}]✓[/{colors.success}] {message}")


async def warning(text: str) -> None:
    """Print a warning message."""
    await print(f"[{colors.warning}]⚠[/{colors.warning}] {text}")


async def muted(text: str, spaces: int = 0) -> None:
    """Print a muted message."""
    await print(f"{' ' * spaces}[{colors.muted}]•[/{colors.muted}] [dim]{text}[/dim]")


async def usage(usage: str) -> None:
    """Print usage information."""
    await print(Padding(usage, (0, 0, 1, 2)), style=colors.muted)


async def version() -> None:
    """Print version information."""
    app_settings = ApplicationSettings()
    await info(MSG_VERSION_DISPLAY.format(version=app_settings.version))


async def banner() -> None:
    """Display the application banner."""
    console.clear()
    banner_padding = Padding(BANNER, (2, 0, 1, 0))
    await print(banner_padding)


async def clear() -> None:
    """Clear the console and display the banner."""
    console.clear()
    await banner()


async def update_available(latest_version: str) -> None:
    """Display update available notification."""
    await warning(MSG_UPDATE_AVAILABLE.format(latest_version=latest_version))
    await muted(MSG_UPDATE_INSTRUCTION)


async def spinner(show: bool = True, spinner_obj=None, state_manager: StateManager = None):
    """Manage a spinner display."""
    icon = SPINNER_TYPE
    message = UI_THINKING_MESSAGE

    # Get spinner from state manager if available
    if spinner_obj is None and state_manager:
        spinner_obj = state_manager.session.spinner

    if not spinner_obj:
        spinner_obj = await run_in_terminal(lambda: console.status(message, spinner=icon))
        # Store it back in state manager if available
        if state_manager:
            state_manager.session.spinner = spinner_obj

    if show:
        spinner_obj.start()
    else:
        spinner_obj.stop()

    return spinner_obj


# Auto-generated sync version
sync_print = print.sync  # type: ignore
