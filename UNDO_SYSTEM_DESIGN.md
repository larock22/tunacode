# TunaCode Enhanced Undo System - Three-Layer Protection

## Overview
The enhanced undo system provides **three independent layers** of protection to ensure file operations can always be reversed.

```
┌─────────────────────────────────────────────────────────────┐
│                     UNDO SYSTEM LAYERS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 3: Git Commits (Primary)                            │
│  ├─ Full project snapshots                                 │
│  ├─ Efficient storage (only diffs)                         │
│  └─ Complete history with messages                         │
│                                                             │
│  Layer 2: Operation Log (Fallback)                         │
│  ├─ JSONL file with all operations                         │
│  ├─ Stores file content (up to 100KB)                      │
│  └─ Timestamp and operation metadata                       │
│                                                             │
│  Layer 1: File Backups (Last Resort)                       │
│  ├─ Physical copies of files                               │
│  ├─ Timestamped: file.txt.20250527_143022_123456.bak      │
│  └─ Auto-cleanup keeps last 50 backups                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. **Before Any File Operation**
```python
# Automatic backup creation
original.txt → original.txt.20250527_143022_123456.bak
```

### 2. **During File Operation**
```python
# Operation logging
{
  "type": "file_operation",
  "operation": "write",
  "file": "/path/to/file.txt",
  "old_content": "previous content...",
  "new_content": "new content...",
  "timestamp": "2025-05-27T14:30:22"
}
```

### 3. **After File Operation**
```bash
# Git commit (if available)
git add .
git commit -m "Modified file.txt"
```

## Undo Process (Automatic Failover)

When user types `/undo`:

```
┌─────────────┐     Failed?    ┌──────────────┐     Failed?    ┌─────────────┐
│   Try Git   │ ─────────────► │ Try Op Log   │ ─────────────► │ Use Backups │
│  (Layer 3)  │                │  (Layer 2)   │                │  (Layer 1)  │
└─────────────┘                └──────────────┘                └─────────────┘
      │                               │                               │
      ▼                               ▼                               ▼
  "Restored via                "Restored from              "Manual restore from:
   Git history"                operation log"               - file.20250527.bak
                                                            - file.20250526.bak"
```

## Storage Structure

```
your-project/                # Project root
├── src/                     # Your code
├── tests/                   # Your tests
├── .git/                    # Layer 3: Git (if exists)
└── .tunacode/               # Local undo directory
    ├── .gitignore           # Excludes from version control
    ├── README.md            # Explains the directory
    ├── operations.jsonl     # Layer 2: Operation log
    └── backups/             # Layer 1: File backups
        └── [mirrors project structure]
            └── file.txt.20250527_143022.bak
```

**Key Change**: Undo data is stored **locally in each project** rather than globally. This is better for a pip-installed tool because:
- No global state management
- Each project has isolated undo history  
- Easy to see and clean up
- Works immediately in any directory

## Key Benefits

### 1. **Always Recoverable**
- Even if Git fails, operation log has content
- Even if log is corrupted, physical backups exist
- Multiple recovery paths ensure data safety

### 2. **Automatic & Transparent**
- No user action required for protection
- Undo command tries all methods automatically
- Clear feedback on which method succeeded

### 3. **Storage Efficient**
- Git stores only diffs (most efficient)
- Operation log has 100KB content limit
- Old backups auto-cleaned (keep last 50)

### 4. **Performance Optimized**
- Backup creation is async
- Git operations have 5-second timeout
- Log writes are non-blocking

## Implementation Usage

### For Tool Developers
```python
# Use the safe wrappers
safe_ops = SafeFileOperations(enhanced_undo)
success, msg = await safe_ops.safe_write(filepath, content)
```

### For Users
```bash
/undo              # Automatic failover through all layers
/undo --status     # Show undo system status
/undo --list       # List recent operations
```

## Failure Scenarios Handled

1. **Git not installed** → Falls back to operation log
2. **Git timeout** → Falls back to operation log  
3. **Large file (>100KB)** → No content in log, use backups
4. **Corrupted log** → Use physical backups
5. **Disk full** → At least tries to log the operation

## Future Enhancements

1. **Cloud Backup** - Optional S3/GCS backup for critical files
2. **Compression** - Compress old backups to save space
3. **Selective Undo** - Undo specific files, not just last operation
4. **Undo Preview** - Show what will be changed before undoing
5. **Multi-Level Undo** - Undo multiple operations in sequence

This three-layer system ensures that **no file operation is ever truly irreversible** in TunaCode!