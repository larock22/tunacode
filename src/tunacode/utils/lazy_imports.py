"""Lazy imports for heavy modules to improve startup time."""

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # For type checking only
    import prompt_toolkit  # noqa: F401
    import rich  # noqa: F401
    from prompt_toolkit import PromptSession  # noqa: F401
    from prompt_toolkit.completion import Completer  # noqa: F401
    from rich.console import Console  # noqa: F401
    from rich.markdown import Markdown  # noqa: F401
    from rich.panel import Panel  # noqa: F401
    from rich.table import Table  # noqa: F401


def lazy_import(module_name: str):
    """Lazy import a module."""
    if module_name not in sys.modules:
        __import__(module_name)
    return sys.modules[module_name]


# Lazy accessors
def get_rich():
    """Get rich module lazily."""
    return lazy_import("rich")


def get_rich_console():
    """Get rich console lazily."""
    rich_console = lazy_import("rich.console")
    return rich_console.Console


def get_rich_table():
    """Get rich table lazily."""
    return lazy_import("rich.table").Table


def get_rich_panel():
    """Get rich panel lazily."""
    return lazy_import("rich.panel").Panel


def get_rich_markdown():
    """Get rich markdown lazily."""
    return lazy_import("rich.markdown").Markdown


def get_prompt_toolkit():
    """Get prompt_toolkit lazily."""
    return lazy_import("prompt_toolkit")


def get_prompt_session():
    """Get PromptSession lazily."""
    return lazy_import("prompt_toolkit").PromptSession
