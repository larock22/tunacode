# TinyAgent Migration Plan: Pure Sync Architecture

## Overview

Migrate TunaCode from the complex async tool system to a pure TinyAgent-based sync architecture. This eliminates the async/sync boundary issues and simplifies the entire codebase.

## Current Problems

1. **Complex async tool classes** with threading bridges
2. **Event loop conflicts** in confirmation system  
3. **Over-engineered architecture** with unnecessary abstractions
4. **Two agent systems** (legacy + TinyAgent) causing confusion
5. **Performance overhead** from threading and async/sync boundaries

## Target Architecture

```
User Input → TinyAgent → Simple Sync Tools → Direct File/Command Operations
```

**Key principles:**
- All tools are simple sync functions decorated with `@tool`
- No async/await anywhere in the tool system
- Direct file operations without abstraction layers
- Simple sync confirmation using `input()` and `run_in_terminal()`

## Migration Steps

### Phase 1: Create Pure Sync Tools
- [ ] Create new simple sync tool implementations
- [ ] Replace complex async tool classes with direct operations
- [ ] Fix confirmation system with sync `input()` approach
- [ ] Test all basic tool operations work

### Phase 2: Remove Async Tool System  
- [ ] Delete async tool classes (`/tools/read_file.py`, `/tools/write_file.py`, etc.)
- [ ] Delete base tool classes (`/tools/base.py`)
- [ ] Remove threading bridge code (`_run_async_in_thread`)
- [ ] Clean up imports and dependencies

### Phase 3: Remove Legacy Agent System
- [ ] Delete legacy agent implementation (`/core/agents/main.py`)
- [ ] Remove Pydantic-AI dependencies
- [ ] Update all references to use TinyAgent directly
- [ ] Simplify agent creation and management

### Phase 4: Simplify Architecture
- [ ] Remove tool handler complexity (`/core/tool_handler.py`)
- [ ] Simplify state management (remove async tool tracking)
- [ ] Clean up UI tool confirmation system
- [ ] Remove async-related utility functions

### Phase 5: Testing & Cleanup
- [ ] Test all core functionality works
- [ ] Update documentation to reflect new architecture
- [ ] Remove unused imports and dependencies
- [ ] Performance testing to confirm improvements

## New Tool Implementation Example

**Before (Complex):**
```python
# Async tool class with UI logging, error handling, git commits
class ReadFileTool(FileBasedTool):
    async def _execute(self, filepath: str) -> str:
        # Complex async implementation
        
# TinyAgent wrapper with threading
@tool
def read_file(filepath: str) -> str:
    tool_instance = ReadFileTool(None)
    return _run_async_in_thread(tool_instance.execute(filepath))
```

**After (Simple):**
```python
@tool
def read_file(filepath: str) -> str:
    """Read file contents."""
    if not _confirm_operation("read_file", {"filepath": filepath}):
        raise Exception("Operation cancelled")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✓ Read {len(content)} characters from {filepath}")
        return content
    except Exception as e:
        raise Exception(f"Failed to read {filepath}: {e}")
```

## Benefits of This Approach

### Performance
- ✅ No threading overhead
- ✅ No async/sync boundary crossings
- ✅ Direct file operations
- ✅ Faster startup and execution

### Simplicity  
- ✅ Easy to understand and debug
- ✅ No complex inheritance hierarchies
- ✅ No async/await mental overhead
- ✅ Straightforward error handling

### Reliability
- ✅ No event loop conflicts
- ✅ No threading race conditions
- ✅ Simple confirmation system that works
- ✅ Fewer moving parts to break

### Maintainability
- ✅ Much less code to maintain
- ✅ Clear separation of concerns
- ✅ Easy to add new tools
- ✅ No complex abstractions

## Files to Modify/Delete

### Delete (Async Tool System)
- `src/tunacode/tools/base.py`
- `src/tunacode/tools/read_file.py`
- `src/tunacode/tools/write_file.py` 
- `src/tunacode/tools/update_file.py`
- `src/tunacode/tools/run_command.py`
- `src/tunacode/core/agents/main.py`
- `src/tunacode/core/tool_handler.py`

### Modify (Simplify)
- `src/tunacode/tools/tinyagent_tools.py` - Replace with simple sync tools
- `src/tunacode/core/state.py` - Remove async tool tracking
- `src/tunacode/ui/tool_ui.py` - Simplify confirmation system
- `src/tunacode/core/agents/tinyagent_main.py` - Remove legacy compatibility

### Keep (Core functionality)
- Agent management and message handling
- UI and terminal management
- Configuration and setup
- Undo service (git-based)

## Migration Strategy

1. **Big Bang Approach**: Implement all changes at once
   - Pros: Clean break, no half-working states
   - Cons: Higher risk, harder to test incrementally

2. **Incremental Approach**: Migrate tool by tool
   - Pros: Lower risk, easier testing
   - Cons: Temporary complexity, mixed systems

**Recommendation**: Big Bang - the current system is already broken, so a clean rewrite is safer.

## Testing Plan

1. **Unit Tests**: Test each tool function independently
2. **Integration Tests**: Test agent → tool → file system flow
3. **UI Tests**: Test confirmation system works in terminal
4. **Regression Tests**: Ensure all existing functionality works
5. **Performance Tests**: Measure speed improvements

## Success Criteria

- ✅ All tool operations work reliably
- ✅ Confirmation system works without event loop conflicts
- ✅ No threading or async/sync boundary issues
- ✅ Performance improvements measurable
- ✅ Codebase is significantly simpler
- ✅ Easy to add new tools in the future

## Risk Mitigation

1. **Backup current working state** before starting
2. **Test each phase** before moving to next
3. **Keep git history** for easy rollback if needed
4. **Test on multiple platforms** (Linux, macOS, Windows)
5. **Verify all existing functionality** still works