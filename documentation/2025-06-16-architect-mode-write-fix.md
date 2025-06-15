# Architect Mode Write Operations Fix

Date: 2025-06-16

## Overview

Fixed a critical bug where architect mode was incorrectly using ReadOnlyAgent for write operations, making it impossible to create or modify files. The issue was that the `mutate` field was missing from task definitions, causing all operations to be treated as read-only.

## Problem

When users tried write operations in architect mode like "just put hello world", the system would respond:
```
I am a read-only assistant and cannot create files.
```

This occurred because:
1. The `TaskSchema` in `schemas.py` didn't have a `mutate` field
2. The `HybridRequestAnalyzer` wasn't setting the `mutate` field on generated tasks
3. The `AdaptiveOrchestrator` checks `task.get("mutate", False)` to decide which agent to use

## Solution

### 1. Added `mutate` field to TaskSchema

```python
# In schemas.py
class TaskSchema(BaseModel):
    """Schema for a single task."""
    id: int = Field(..., description="Task ID")
    description: str = Field(..., description="Task description")
    tool: str = Field(..., description="Tool to use")
    args: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    mutate: bool = Field(default=False, description="True if task modifies files/system")
```

### 2. Updated HybridRequestAnalyzer

- Added `mutating_tools` set to identify which tools modify the system
- Added write operation patterns to detect create/write requests
- Set `mutate=True` for write_file, update_file, run_command, and bash tools
- Set `mutate=False` for read_file, grep, list_dir, and analyze tools

### 3. Added Write Pattern Detection

Added new regex patterns to catch common write operations:
```python
# Pattern for simple write operations
self.write_pattern = re.compile(
    r"^(?:create|write|put|make)\s+(?:a\s+)?(?:new\s+)?(?:file\s+)?@?([\w\-./]+\.[\w]+)?\s*(?:with\s+)?(?:content\s+)?[\"']?(.+?)[\"']?$",
    re.IGNORECASE | re.DOTALL
)

# Pattern for "just put X" style commands
self.simple_put_pattern = re.compile(
    r"^(?:just\s+)?(?:put|write|create)\s+(.+)$",
    re.IGNORECASE | re.DOTALL
)
```

## Testing

Created test cases that verify:
- "create test.txt with content hello" → generates write_file task with `mutate=True`
- "write output.py with print('hello')" → generates write_file task with `mutate=True`
- "just put hello world" → detected as write operation with medium confidence

## Impact

Architect mode now properly handles write operations by:
1. Using the main agent (with confirmation prompts) for mutating operations
2. Using the ReadOnlyAgent only for non-mutating operations
3. Respecting user permissions and /yolo mode for write confirmations

This restores full CRUD functionality to architect mode while maintaining safety through confirmation prompts.