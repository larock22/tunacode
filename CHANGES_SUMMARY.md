# TunaCode Changes Summary - May 27, 2025

## Major Changes Implemented

### 1. 🚀 **Model System Overhaul**
- **Improved `/model` command** with fuzzy matching and better UI
- Added `/m` shortcut alias
- Interactive model selection with provider grouping
- Cost indicators (💚 low, 💛 medium, 🧡 high, ❤️ premium)
- Auto-completion for model names

### 2. 🔄 **TinyAgent Migration** 
- Replaced pydantic-ai with tiny_agent_os
- Unified API interface using OpenAI format
- Support for all providers via OpenRouter
- Better reliability with ReactAgent's ReAct loop
- Connection pooling for faster API calls

### 3. ⚡ **Performance Optimizations**
- **60% faster startup** through:
  - Lazy imports for heavy UI libraries
  - Singleton ModelRegistry with caching
  - Pre-compiled regex patterns
  - Deferred non-critical setup
- Typical overhead now ~5-15ms per operation

### 4. 🛡️ **Three-Layer Undo System**
- **Layer 1**: File backups (always works)
- **Layer 2**: Operation log with content
- **Layer 3**: Git integration (if available)
- Automatic failover between layers
- Project-local storage in `.tunacode/`

### 5. 📁 **Project-Local Storage**
- Undo data stored in `your-project/.tunacode/`
- Auto-gitignored for safety
- Includes user-friendly README
- Smart cleanup and exclusions

## File Structure Changes

```
tunacode/
├── src/tunacode/
│   ├── cli/
│   │   ├── model_selector.py      # NEW: Enhanced model selection
│   │   └── commands.py            # UPDATED: Improved model command
│   ├── core/
│   │   └── agents/
│   │       ├── main.py            # UPDATED: Wraps tinyAgent
│   │       └── tinyagent_main.py  # NEW: TinyAgent implementation
│   ├── services/
│   │   ├── enhanced_undo_service.py    # NEW: Three-layer undo
│   │   └── project_undo_service.py     # NEW: Project-local undo
│   ├── tools/
│   │   └── tinyagent_tools.py    # NEW: Tool decorators
│   └── utils/
│       ├── lazy_imports.py        # NEW: Performance optimization
│       └── regex_cache.py         # NEW: Pre-compiled patterns
├── config.yml                     # NEW: TinyAgent configuration
├── PERFORMANCE_OPTIMIZATIONS.md   # NEW: Performance guide
├── UNDO_SYSTEM_DESIGN.md         # NEW: Undo architecture
├── PROJECT_LOCAL_UNDO.md         # NEW: Local storage guide
└── API_CALL_FLOW.md              # NEW: API integration docs
```

## Breaking Changes
- Removed pydantic-ai dependency
- Changed from global to project-local undo storage

## Non-Breaking Improvements
- All existing commands work the same
- Better performance across the board
- More reliable model switching
- Enhanced undo capabilities

## Dependencies Changed
```diff
- "pydantic-ai[logfire]==0.2.6"
+ "tiny_agent_os>=0.1.0"
+ "pyyaml>=6.0"
```