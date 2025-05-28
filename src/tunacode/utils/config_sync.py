"""
Config synchronization utilities.

This module handles bidirectional sync between TunaCode and TinyAgent configs
without circular import dependencies.
"""

import os
import json
import yaml
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tunacode.core.state import StateManager


def _find_tinyagent_config() -> Optional[Path]:
    """Find the TinyAgent config file location."""
    # Same logic as in tinyagent_main.py
    package_dir = Path(__file__).parent.parent.parent  # Navigate to tunacode root
    config_candidates = [
        package_dir / "tunacode_config.yml",  # In package root
        Path.home() / ".config" / "tunacode_config.yml",  # In user config dir
        Path.cwd() / "tunacode_config.yml",  # In current directory
    ]
    
    # Find the first existing config file
    for config_path in config_candidates:
        if config_path.exists():
            return config_path
    
    return None


def sync_model_configs(tunacode_model: str, state_manager: "StateManager"):
    """
    Bidirectional sync between TunaCode and TinyAgent configs.
    Compares modification times and syncs the older config to match the newer one.
    
    Args:
        tunacode_model: The model name in TunaCode format (e.g., "openrouter:mistralai/devstral-small")
        state_manager: State manager instance for accessing TunaCode config
    """
    try:
        # Get config file paths
        tinyagent_config_path = _find_tinyagent_config()
        tunacode_config_path = Path.home() / ".config" / "tunacode.json"
        
        if not tinyagent_config_path or not tinyagent_config_path.exists():
            return
            
        if not tunacode_config_path.exists():
            return
            
        # Get modification times
        tinyagent_mtime = tinyagent_config_path.stat().st_mtime
        tunacode_mtime = tunacode_config_path.stat().st_mtime
        
        # Read both configs
        with open(tinyagent_config_path, 'r') as f:
            tinyagent_config = yaml.safe_load(f)
            
        with open(tunacode_config_path, 'r') as f:
            tunacode_config = json.load(f)
            
        # Extract models from both configs
        tinyagent_model = tinyagent_config.get('model', {}).get('default', '')
        tunacode_default_model = tunacode_config.get('default_model', '')
        
        # Convert TunaCode model to TinyAgent format for comparison
        if tunacode_default_model.startswith("openrouter:"):
            tunacode_model_for_tinyagent = tunacode_default_model.replace("openrouter:", "")
        else:
            # For direct providers, extract just the model name
            if ":" in tunacode_default_model:
                tunacode_model_for_tinyagent = tunacode_default_model.split(":", 1)[1]
            else:
                tunacode_model_for_tinyagent = tunacode_default_model
        
        # Determine which config is newer and needs to be the source of truth
        if tinyagent_mtime > tunacode_mtime:
            # TinyAgent config is newer - sync TunaCode to match
            if tinyagent_model and tinyagent_model != tunacode_model_for_tinyagent:
                # Convert TinyAgent model back to TunaCode format
                if "/" in tinyagent_model:  # OpenRouter format
                    new_tunacode_model = f"openrouter:{tinyagent_model}"
                else:  # Direct provider - need to determine provider
                    # Default to OpenAI for simple model names
                    new_tunacode_model = f"openai:{tinyagent_model}"
                
                # Update TunaCode config
                tunacode_config['default_model'] = new_tunacode_model
                state_manager.session.user_config['default_model'] = new_tunacode_model
                
                with open(tunacode_config_path, 'w') as f:
                    json.dump(tunacode_config, f, indent=2)
                    
        elif tunacode_mtime > tinyagent_mtime:
            # TunaCode config is newer - sync TinyAgent to match
            if tunacode_model_for_tinyagent != tinyagent_model:
                # Update TinyAgent config
                if 'model' not in tinyagent_config:
                    tinyagent_config['model'] = {}
                tinyagent_config['model']['default'] = tunacode_model_for_tinyagent
                
                # Update base URL to match current environment
                current_base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
                tinyagent_config['base_url'] = current_base_url
                
                with open(tinyagent_config_path, 'w') as f:
                    yaml.safe_dump(tinyagent_config, f, default_flow_style=False, sort_keys=False)
        
        # If models already match, no sync needed
        
    except Exception:
        # Silent fail - don't break the agent if config sync fails
        pass


def force_sync_to_model(model_name: str, state_manager: "StateManager"):
    """
    Force both configs to sync to a specific model (used when user switches models).
    
    Args:
        model_name: The model name in TunaCode format to sync both configs to
        state_manager: State manager instance
    """
    try:
        # Get config file paths
        tinyagent_config_path = _find_tinyagent_config()
        tunacode_config_path = Path.home() / ".config" / "tunacode.json"
        
        if not tinyagent_config_path or not tinyagent_config_path.exists():
            print(f"DEBUG: TinyAgent config not found")  # Debug output
            return
            
        if not tunacode_config_path.exists():
            print(f"DEBUG: TunaCode config not found")  # Debug output
            return
        
        # Convert TunaCode model to TinyAgent format
        if model_name.startswith("openrouter:"):
            tinyagent_model = model_name.replace("openrouter:", "")
            # Set OpenRouter base URL
            os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        else:
            # For direct providers, extract just the model name
            if ":" in model_name:
                provider, tinyagent_model = model_name.split(":", 1)
                # Set appropriate base URL
                if provider == "openai":
                    os.environ["OPENAI_BASE_URL"] = "https://api.openai.com/v1"
            else:
                tinyagent_model = model_name
        
        # Update TunaCode config
        with open(tunacode_config_path, 'r') as f:
            tunacode_config = json.load(f)
        
        tunacode_config['default_model'] = model_name
        state_manager.session.user_config['default_model'] = model_name
        
        with open(tunacode_config_path, 'w') as f:
            json.dump(tunacode_config, f, indent=4)
        
        # Update TinyAgent config
        with open(tinyagent_config_path, 'r') as f:
            tinyagent_config = yaml.safe_load(f)
        
        if 'model' not in tinyagent_config:
            tinyagent_config['model'] = {}
        tinyagent_config['model']['default'] = tinyagent_model
        
        # Update base URL in config
        tinyagent_config['base_url'] = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        
        with open(tinyagent_config_path, 'w') as f:
            yaml.safe_dump(tinyagent_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"DEBUG: Synced to model {model_name} -> {tinyagent_model}")  # Debug output
            
    except Exception as e:
        print(f"DEBUG: Sync failed with error: {e}")  # Debug output
        import traceback
        traceback.print_exc() 