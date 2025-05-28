"""
Module: sidekick.cli.main

CLI entry point and main command handling for the Sidekick application.
Manages application startup, version checking, and REPL initialization.
"""

import asyncio
import os
from pathlib import Path

import typer

from tunacode.cli.repl import repl
from tunacode.configuration.settings import ApplicationSettings
from tunacode.core.state import StateManager
from tunacode.setup import setup
from tunacode.ui import console as ui
from tunacode.utils.system import check_for_updates

app_settings = ApplicationSettings()
state_manager = StateManager()


def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
    run_setup: bool = typer.Option(False, "--setup", help="Run setup process."),
    update: bool = typer.Option(False, "--update", "--upgrade", help="Update TunaCode to the latest version."),
    model: str = typer.Option(None, "--model", "-m", help="Set the model to use (e.g., 'openai:gpt-4o', 'openrouter:anthropic/claude-3.5-sonnet')."),
    base_url: str = typer.Option(None, "--base-url", help="Override the API base URL for OpenAI-compatible endpoints (e.g., 'https://openrouter.ai/api/v1')."),
):
    """TunaCode - Your agentic CLI developer."""
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            # dotenv not installed, skip loading
            pass
    if version:
        asyncio.run(ui.version())
        return
    
    if update:
        from tunacode.utils.system import update_tunacode
        asyncio.run(update_tunacode())
        return

    # Apply CLI overrides to state manager before setup
    if model:
        state_manager.session.model = model
        state_manager.session.user_config["default_model"] = model
    
    if base_url:
        import os
        os.environ["OPENAI_BASE_URL"] = base_url

    asyncio.run(ui.banner())

    has_update, latest_version = check_for_updates()
    if has_update:
        asyncio.run(ui.show_update_message(latest_version))

    try:
        asyncio.run(setup(run_setup, state_manager))
        asyncio.run(repl(state_manager))
    except Exception as e:
        asyncio.run(ui.error(str(e)))


app = typer.Typer(
    name="tunacode",
    help="TunaCode - Your agentic CLI developer",
    add_completion=False,
)

app.command()(main)

if __name__ == "__main__":
    app()
