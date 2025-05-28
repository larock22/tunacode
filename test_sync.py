#!/usr/bin/env python3
"""Debug script to test config sync functionality."""

import os
import sys
sys.path.insert(0, 'src')

from pathlib import Path
from tunacode.utils.config_sync import force_sync_to_model, _find_tinyagent_config
from tunacode.configuration.defaults import DEFAULT_USER_CONFIG

# Mock state manager for testing
class MockSession:
    def __init__(self):
        self.user_config = DEFAULT_USER_CONFIG.copy()

class MockStateManager:
    def __init__(self):
        self.session = MockSession()

print("=== CONFIG SYNC DEBUG ===")
print(f"1. TINYAGENT_CONFIG env var: {os.environ.get('TINYAGENT_CONFIG', 'NOT SET')}")

# Check if config files exist
tunacode_config = Path.home() / ".config" / "tunacode.json"
print(f"2. TunaCode config exists: {tunacode_config.exists()} at {tunacode_config}")

# Find TinyAgent config using our function
tinyagent_path = _find_tinyagent_config()
print(f"3. TinyAgent config found at: {tinyagent_path}")
if tinyagent_path:
    print(f"   Config exists: {tinyagent_path.exists()}")
    print(f"   Absolute path: {tinyagent_path.absolute()}")

# Show current working directory
print(f"4. Current working directory: {Path.cwd()}")

# Try to run the sync
print("\n5. Testing force_sync_to_model...")
try:
    state_manager = MockStateManager()
    model_to_sync = "openai:gpt-4o-mini"
    
    print(f"   Syncing to model: {model_to_sync}")
    force_sync_to_model(model_to_sync, state_manager)
    print("   ✅ Sync function completed (no exception)")
    
    # Check if files were updated
    import json
    import yaml
    
    with open(tunacode_config, 'r') as f:
        tc_data = json.load(f)
    print(f"   TunaCode config model: {tc_data.get('default_model')}")
    
    if tinyagent_path and tinyagent_path.exists():
        with open(tinyagent_path, 'r') as f:
            ta_data = yaml.safe_load(f)
        print(f"   TinyAgent config model: {ta_data.get('model', {}).get('default')}")
        print(f"   TinyAgent base_url: {ta_data.get('base_url')}")
    
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n6. Checking if sync is modifying the actual function...")
# Let's add some debug prints to the actual sync function
print("   Adding debug output to sync function...") 