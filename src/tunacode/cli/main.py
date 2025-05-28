"""
Module: sidekick.cli.main

CLI entry point and main command handling for the Sidekick application.
Manages application startup, version checking, and REPL initialization.
"""

import asyncio

import typer

from tunacode.cli.repl import repl
from tunacode.configuration.settings import ApplicationSettings
from tunacode.core.state import StateManager
from tunacode.setup import setup
from tunacode.ui import console as ui
from tunacode.utils.system import check_for_updates

app_settings = ApplicationSettings()
app = typer.Typer(help=app_settings.name)
state_manager = StateManager()


@app.command()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
    run_setup: bool = typer.Option(False, "--setup", help="Run setup process."),
    update: bool = typer.Option(False, "--update", "--upgrade", help="Update TunaCode to the latest version."),
):
    if version:
        asyncio.run(ui.version())
        return
    
    if update:
        from tunacode.utils.system import update_tunacode
        asyncio.run(update_tunacode())
        return

    asyncio.run(ui.banner())

    has_update, latest_version = check_for_updates()
    if has_update:
        asyncio.run(ui.show_update_message(latest_version))

    try:
        asyncio.run(setup(run_setup, state_manager))
        asyncio.run(repl(state_manager))
    except Exception as e:
        asyncio.run(ui.error(str(e)))


if __name__ == "__main__":
    app()
