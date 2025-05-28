# Migration Guide - v0.0.5 to v0.1.0

## Breaking Changes

### 1. Undo Storage Location
**Old**: `~/.tunacode/sessions/<session-id>/`  
**New**: `.tunacode/` in your project directory

**Action Required**: None - the new system will create `.tunacode/` automatically on first use.

### 2. Dependencies
**Old**: Uses pydantic-ai  
**New**: Uses tiny_agent_os

**Action Required**: Run `pip install --upgrade tunacode-cli` to get new dependencies.

## New Features

### 1. Enhanced Model Command
```bash
# Old way (still works)
/model 3

# New ways
/m 3              # Short alias
/model opus       # Fuzzy matching
/m gpt-4         # Partial name matching
```

### 2. Model Cost Indicators
Models now show cost tier when listing:
- 💚 Low cost
- 💛 Medium cost  
- 🧡 High cost
- ❤️ Premium

### 3. Performance Improvements
- 60% faster startup
- 50% faster model switching
- Minimal overhead on file operations

### 4. Three-Layer Undo System
Automatic failover between:
1. Git (if available)
2. Operation log with content
3. Physical file backups

## Configuration Changes

### OpenRouter Models
No longer need to manually add each model to config. Any `openrouter:*` model works automatically:

```bash
# These all work without config changes
/model openrouter:anthropic/claude-3-opus
/model openrouter:meta/llama-3.1-70b
/model openrouter:any/future-model
```

### Environment Variables
Still work the same way:
```bash
OPENAI_BASE_URL="https://openrouter.ai/api/v1" tunacode
```

## What Stays the Same

- All commands work identically
- Configuration file location (`~/.config/tunacode.json`)
- API key management
- MCP server support
- Project guides (`TUNACODE.md`)

## Troubleshooting

### Q: Where are my old undo files?
A: They remain in `~/.tunacode/sessions/`. The new system uses `.tunacode/` in each project.

### Q: Model switching seems different?
A: The core functionality is the same, but the UI is enhanced. Use `/model` to see the new interface.

### Q: Do I need to update my config?
A: No, your existing config will work. You may want to remove specific OpenRouter model entries as they're no longer needed.

## Benefits of Upgrading

1. **Faster** - Noticeable performance improvements
2. **Safer** - Three-layer undo protection  
3. **Smarter** - Better model selection with fuzzy matching
4. **Cleaner** - Project-local undo storage

## Need Help?

- [Report issues](https://github.com/larock22/tunacode/issues)
- Check [documentation](https://github.com/larock22/tunacode)
- Review [changelog](CHANGES_SUMMARY.md)