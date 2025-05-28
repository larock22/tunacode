"""Module: sidekick.core.setup.config_setup

Configuration system initialization for the Sidekick CLI.
Handles user configuration loading, validation, and first-time setup onboarding.
"""

import json
from pathlib import Path

from tunacode.configuration.defaults import DEFAULT_USER_CONFIG
from tunacode.configuration.models import ModelRegistry
from tunacode.constants import APP_NAME, CONFIG_FILE_NAME, UI_COLORS
from tunacode.core.setup.base import BaseSetup
from tunacode.core.state import StateManager
from tunacode.exceptions import ConfigurationError
from tunacode.types import ConfigFile, ConfigPath, UserConfig
from tunacode.ui import console as ui
from tunacode.utils import system, user_configuration
from tunacode.utils.text_utils import key_to_title


class ConfigSetup(BaseSetup):
    """Setup step for configuration and onboarding."""

    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)
        self.config_dir: ConfigPath = Path.home() / ".config"
        self.config_file: ConfigFile = self.config_dir / CONFIG_FILE_NAME
        self.model_registry = ModelRegistry()

    @property
    def name(self) -> str:
        return "Configuration"

    async def should_run(self, force_setup: bool = False) -> bool:
        """Config setup should always run to load and merge configuration."""
        return True

    async def execute(self, force_setup: bool = False) -> None:
        """Setup configuration and run onboarding if needed."""
        self.state_manager.session.device_id = system.get_device_id()
        loaded_config = user_configuration.load_config()

        if loaded_config and not force_setup:
            # Silent loading
            # Merge loaded config with defaults to ensure all required keys exist
            self.state_manager.session.user_config = self._merge_with_defaults(loaded_config)
        else:
            if force_setup:
                await ui.muted("Running setup process, resetting config")
            else:
                await ui.muted("No user configuration found, running setup")
            self.state_manager.session.user_config = DEFAULT_USER_CONFIG.copy()
            user_configuration.save_config(self.state_manager)  # Save the default config initially
            await self._onboarding()

        if not self.state_manager.session.user_config.get("default_model"):
            raise ConfigurationError(
                (
                    f"No default model found in config at [bold]{self.config_file}[/bold]\n\n"
                    "Run [code]sidekick --setup[/code] to rerun the setup process."
                )
            )

        # Check if the configured model still exists
        default_model = self.state_manager.session.user_config["default_model"]
        if not self.model_registry.get_model(default_model):
            # If model not found, run the onboarding again
            await ui.panel(
                "Model Not Found",
                f"The configured model '[bold]{default_model}[/bold]' is no longer available.\n"
                "Let's reconfigure your setup.",
                border_style=UI_COLORS["warning"],
            )
            await self._onboarding()

        self.state_manager.session.current_model = self.state_manager.session.user_config[
            "default_model"
        ]

    async def validate(self) -> bool:
        """Validate that configuration is properly set up."""
        # Check that we have a user config
        if not self.state_manager.session.user_config:
            return False

        # Check that we have a default model
        if not self.state_manager.session.user_config.get("default_model"):
            return False

        # Check that the default model is valid
        default_model = self.state_manager.session.user_config["default_model"]
        if not self.model_registry.get_model(default_model):
            return False

        return True

    def _merge_with_defaults(self, loaded_config: UserConfig) -> UserConfig:
        """Merge loaded config with defaults to ensure all required keys exist."""
        # Start with loaded config if available, otherwise use defaults
        if loaded_config:
            merged = loaded_config.copy()

            # Add missing top-level keys from defaults
            for key, default_value in DEFAULT_USER_CONFIG.items():
                if key not in merged:
                    merged[key] = default_value

            return merged
        else:
            return DEFAULT_USER_CONFIG.copy()

    async def _onboarding(self):
        """Run the onboarding process for new users."""
        initial_config = json.dumps(self.state_manager.session.user_config, sort_keys=True)

        # Welcome message
        message = (
            f"Welcome to {APP_NAME}!\n\n"
            "Let's configure your AI provider. TunaCode supports:\n"
            "• OpenAI (api.openai.com)\n"
            "• OpenRouter (openrouter.ai) - Access 100+ models\n"
            "• Any OpenAI-compatible API\n"
        )
        await ui.panel("Setup", message, border_style=UI_COLORS["primary"])

        # Step 1: Ask for base URL
        base_url = await ui.input(
            "step1",
            pretext="  API Base URL (press Enter for OpenAI): ",
            default="https://api.openai.com/v1",
            state_manager=self.state_manager,
        )
        base_url = base_url.strip()
        if not base_url:
            base_url = "https://api.openai.com/v1"

        # Step 2: Ask for API key
        if "openrouter.ai" in base_url.lower():
            key_prompt = "  OpenRouter API Key: "
            key_name = "OPENROUTER_API_KEY"
            default_model = "openrouter:openai/gpt-4o-mini"
        else:
            key_prompt = "  API Key: "
            key_name = "OPENAI_API_KEY"
            default_model = "openai:gpt-4o"

        api_key = await ui.input(
            "step2",
            pretext=key_prompt,
            is_password=True,
            state_manager=self.state_manager,
        )
        api_key = api_key.strip()

        if api_key:
            # Set the environment variable
            self.state_manager.session.user_config["env"][key_name] = api_key
            
            # Set base URL in environment for OpenRouter
            if "openrouter.ai" in base_url.lower():
                import os
                os.environ["OPENAI_BASE_URL"] = base_url
            
            # Set default model
            self.state_manager.session.user_config["default_model"] = default_model

            # Save configuration
            current_config = json.dumps(self.state_manager.session.user_config, sort_keys=True)
            if initial_config != current_config:
                if user_configuration.save_config(self.state_manager):
                    message = (
                        f"✅ Configuration saved!\n\n"
                        f"Default model: {default_model}\n"
                        f"Config file: {self.config_file}\n\n"
                        f"You can change models anytime with /model"
                    )
                    await ui.panel("Setup Complete", message, top=0, border_style=UI_COLORS["success"])
                else:
                    await ui.error("Failed to save configuration.")
        else:
            await ui.panel(
                "Setup canceled",
                "An API key is required to use TunaCode.",
                border_style=UI_COLORS["warning"],
            )

