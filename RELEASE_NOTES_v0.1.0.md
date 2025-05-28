# TunaCode v0.1.0 Release Notes

## 🎉 Major Release: Performance, Reliability, and Safety

This release brings significant improvements to TunaCode's core architecture, making it faster, more reliable, and safer to use.

### 🚀 Performance Improvements (60% Faster)
- **Lazy loading** for heavy UI libraries (Rich, Prompt Toolkit)
- **Singleton pattern** for ModelRegistry with caching
- **Pre-compiled regex** patterns for common operations
- **Deferred initialization** for non-critical components
- Result: Startup time reduced from ~2s to ~0.8s

### 🤖 TinyAgent Integration
- Replaced pydantic-ai with tiny_agent_os for better reliability
- Unified API interface using OpenAI format
- Support for ALL providers through OpenRouter
- Connection pooling for faster API calls
- More robust error handling with ReAct loop

### 🛡️ Three-Layer Undo System
- **Layer 1**: Physical file backups (always works)
- **Layer 2**: Operation log with content tracking
- **Layer 3**: Git integration (when available)
- Automatic failover between layers
- Project-local storage in `.tunacode/` directory
- Smart exclusions (node_modules, __pycache__, etc.)

### 📊 Enhanced Model Management
- New `/m` shortcut for model command
- Fuzzy matching: `/m opus`, `/m gpt-4`
- Cost indicators: 💚 low, 💛 medium, 🧡 high, ❤️ premium
- Provider grouping in model list
- Auto-completion for model names

### 🔧 Developer Experience
- Project-local undo storage (no global state)
- Auto-gitignored `.tunacode/` directory
- Better error messages with suggestions
- Improved command auto-completion
- Support for any OpenRouter model without config

## Breaking Changes
- Undo files now stored in `.tunacode/` instead of `~/.tunacode/sessions/`
- Removed pydantic-ai dependency (replaced with tiny_agent_os)

## Migration Guide
1. Run `pip install --upgrade tunacode-cli`
2. Your config at `~/.config/tunacode.json` remains unchanged
3. New undo directory `.tunacode/` will be created automatically

## Technical Details
- Added 10+ new modules for better organization
- Comprehensive test suite for undo system
- Performance benchmarks showing <5ms overhead
- Detailed documentation for all new features

## What's Next
- Streaming responses for long outputs
- Multi-level undo (undo multiple operations)
- Enhanced MCP integration
- Project templates and scaffolding

## Contributors
Thank you to everyone who provided feedback and tested the beta releases!

---

**Full Changelog**: [v0.0.5...v0.1.0](https://github.com/larock22/tunacode/compare/v0.0.5...v0.1.0)