Circular Import Analysis

The Problem

The circular import happens when modules try to import each other in a way that creates a dependency loop.
Here's the specific chain:

tinyagent_main.py
→ imports tinyagent_tools.py
→ imports ReadFileTool from read_file.py
→ imports UI console
→ imports completers.py
→ imports CLI commands
→ imports repl.py
→ imports agents/main.py
→ imports tinyagent_main.py ❌ LOOP!

Root Cause

The issue is architectural - the tool layer is trying to import UI components, but the UI layer depends on
CLI components, which depend on the agent layer. This creates a circular dependency.

Why It Happens

1. TinyAgent tools need UI feedback - They want to show progress/errors to users
2. UI components need CLI knowledge - For command completion and input handling
3. CLI needs agent access - To process user requests
4. Agents need tools - To perform file operations

Current Workaround

I attempted to fix it with lazy imports in tinyagent_tools.py:
def \_get_ui():
"""Lazy import of UI to avoid circular dependencies."""
from tunacode.ui import console as ui
return ui

But the issue persists because the base tool classes (ReadFileTool, etc.) also import UI directly.

Impact

- ✅ Runtime functionality works - TunaCode runs successfully when launched normally
- ❌ Direct module imports fail - Can't import tinyagent components directly for testing
- ⚠️ Development/testing complexity - Makes unit testing harder

Proper Solutions (for later):

1. Dependency Injection - Pass UI instance to tools instead of importing
2. Event System - Tools emit events, UI listens (decoupled)
3. Interface Segregation - Create minimal UI interfaces for tools
4. Layer Restructuring - Move UI dependencies to a higher layer

Current Status

The circular import is a code quality issue, not a functionality blocker. All core features work correctly
when TunaCode is run normally. The system is ready for user testing.

Config Sync Issue (FIXED)

The circular import caused a secondary issue with bidirectional config sync:

**Problem**: The `/model` command couldn't sync configs because:

1. `commands.py` tried to import `_sync_model_configs` from `tinyagent_main.py`
2. But `tinyagent_main.py` was part of the circular import chain
3. The `TINYAGENT_CONFIG` env var wasn't set when commands executed
4. Sync function would exit early without the env var

**Solution**: Created `src/tunacode/utils/config_sync.py`:

- Independent utility module with no circular dependencies
- `_find_tinyagent_config()` function that locates the config file itself
- `force_sync_to_model()` updates both TunaCode and TinyAgent configs
- Proper format conversion between providers

**Result**: ✅ Bidirectional sync now works perfectly

- `/model` command updates both configs automatically
- Manual config edits are detected and synced
- Correct config files in `~/.config/` are used
  okayu
