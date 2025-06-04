"""
Module: tunacode.cli.main

Enhanced CLI entry point with better styling while staying CLI-based.
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
app = typer.Typer(help="🐟 TunaCode - Your AI-powered development assistant")
state_manager = StateManager()


@app.command()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
    run_setup: bool = typer.Option(False, "--setup", help="Run setup process."),
    baseurl: str = typer.Option(
        None, "--baseurl", help="API base URL (e.g., https://openrouter.ai/api/v1)"
    ),
    model: str = typer.Option(None, "--model", help="Default model to use (e.g., openai/gpt-4)"),
    key: str = typer.Option(None, "--key", help="API key for the provider"),
):
    """🚀 Start TunaCode - Your AI-powered development assistant"""

    async def async_main():
        if version:
            await ui.version()
            return

        await ui.banner()

        # Start update check in background
        update_task = asyncio.to_thread(check_for_updates)

        cli_config = {}
        if baseurl or model or key:
            cli_config = {"baseurl": baseurl, "model": model, "key": key}

        try:
            await setup(run_setup, state_manager, cli_config)
            await repl(state_manager)
        except Exception as e:
            import traceback

            await ui.error(f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}")

        has_update, latest_version = await update_task
        if has_update:
            await ui.update_available(latest_version)

    asyncio.run(async_main())


if __name__ == "__main__":
    app()
