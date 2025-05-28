"""Lazy imports for heavy modules to improve startup time."""

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # For type checking only
    import rich
    import prompt_toolkit
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer

def lazy_import(module_name: str):
    """Lazy import a module."""
    if module_name not in sys.modules:
        __import__(module_name)
    return sys.modules[module_name]


# Lazy accessors
def get_rich():
    """Get rich module lazily."""
    return lazy_import('rich')


def get_rich_console():
    """Get rich console lazily."""
    rich = lazy_import('rich.console')
    return rich.Console


def get_rich_table():
    """Get rich table lazily."""
    return lazy_import('rich.table').Table


def get_rich_panel():
    """Get rich panel lazily."""
    return lazy_import('rich.panel').Panel


def get_rich_markdown():
    """Get rich markdown lazily."""
    return lazy_import('rich.markdown').Markdown


def get_prompt_toolkit():
    """Get prompt_toolkit lazily."""
    return lazy_import('prompt_toolkit')


def get_prompt_session():
    """Get PromptSession lazily."""
    return lazy_import('prompt_toolkit').PromptSession