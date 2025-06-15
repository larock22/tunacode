# Architect Mode State Manager Fix

Date: 2025-06-16

## Overview

Fixed a critical bug in architect mode where the `AdaptiveOrchestrator` was trying to access `state_manager.model` which doesn't exist. The `StateManager` class doesn't have a `model` attribute - instead, the model is stored in `state_manager.session.current_model`.

## Problem

When using architect mode with commands like `@CAPABILITIES.md summarize this file`, the system would crash with:
```
'StateManager' object has no attribute 'model'
```

This occurred in `adaptive_orchestrator.py` line 37 during initialization of the `HybridRequestAnalyzer`.

## Solution

Changed the initialization in `AdaptiveOrchestrator.__init__()`:

```python
# Before (incorrect):
self.analyzer = HybridRequestAnalyzer(model=state_manager.model)

# After (correct):
self.analyzer = HybridRequestAnalyzer(model=state_manager.session.current_model)
```

## Technical Details

- The `StateManager` class only has a `session` property that returns a `SessionState` object
- The `SessionState` dataclass contains the `current_model` field with default value `"openai:gpt-4o"`
- The `HybridRequestAnalyzer` accepts an optional model parameter for LLM fallback operations

## Testing

All 42 tests in `test_hybrid_analyzer.py` pass successfully after the fix. The analyzer now correctly interprets requests like "@CAPABILITIES.md summarize this file" as:
- Request type: EXPLAIN_CODE
- File paths: ['CAPABILITIES.md']
- Operations: ['summarize']
- Generates appropriate tasks for reading and analyzing the file

## Impact

This fix restores functionality to architect mode, allowing it to properly analyze user requests and generate execution plans without crashing on initialization.