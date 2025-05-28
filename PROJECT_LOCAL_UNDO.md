# Project-Local Undo System

## Overview

TunaCode stores undo/backup files **directly in your project** rather than in a global location. This is better for a pip-installed CLI tool.

## Storage Location

```
your-project/
├── src/
├── tests/
├── README.md
└── .tunacode/              # Local undo directory (auto-created)
    ├── .gitignore          # Excludes undo files from git
    ├── README.md           # Explains this directory
    ├── operations.jsonl    # Operation history
    └── backups/            # File backups
        ├── src/
        │   └── main.py.20250527_143022.bak
        └── tests/
            └── test_main.py.20250527_143155.bak
```

## Key Benefits

### 1. **Project Isolation**
- Each project has its own undo history
- No cross-project contamination
- Easy to clean up per project

### 2. **Portability**
- Undo data travels with the project
- Works immediately after cloning
- No global state to manage

### 3. **Transparency**
- See exactly what TunaCode is tracking
- Easy to inspect backups
- Simple to delete if needed

### 4. **Git-Friendly**
- `.tunacode/` is gitignored by default
- Backups are local to each developer
- No accidental commits of backup files

## How It Works

### File Structure
```
.tunacode/
├── backups/
│   └── [mirrors your project structure]
│       └── file.txt.20250527_143022.bak
├── operations.jsonl    # Log of all operations
├── .gitignore         # Auto-generated
└── README.md          # User-friendly explanation
```

### Automatic Cleanup
- Keeps last 10 backups per file
- Removes backups older than 7 days
- Log file trimmed to last 1000 operations

### Smart Exclusions
Won't backup files in:
- `node_modules/`
- `__pycache__/`
- `.git/`
- `dist/`, `build/`
- Hidden directories (except `.env`, `.gitignore`)

## Usage Examples

### Check Undo Status
```bash
# See undo system status
ls -la .tunacode/

# Check backup count
find .tunacode/backups -name "*.bak" | wc -l

# See recent operations
tail .tunacode/operations.jsonl
```

### Manual Recovery
```bash
# Find backups for a specific file
ls .tunacode/backups/src/main.py.*.bak

# Restore from backup
cp .tunacode/backups/src/main.py.20250527_143022.bak src/main.py
```

### Clean Up
```bash
# Remove all undo data for this project
rm -rf .tunacode/

# Remove old backups only
find .tunacode/backups -name "*.bak" -mtime +7 -delete
```

## FAQ

**Q: Will .tunacode/ be committed to git?**
A: No, it contains a .gitignore that excludes all contents.

**Q: How much space does it use?**
A: Typically 5-20MB, auto-cleaned to stay small.

**Q: Can I disable it?**
A: Yes, just delete .tunacode/ or set TUNACODE_NO_UNDO=1

**Q: What if I work on multiple machines?**
A: Each machine maintains its own local undo history.

**Q: Is sensitive data backed up?**
A: Yes, so don't commit .tunacode/ to public repos.

## Implementation Details

### For Maintainers

The project-local approach:
1. Creates `.tunacode/` on first file operation
2. Mirrors project structure in `backups/`
3. Uses relative paths in logs
4. Auto-cleans old backups
5. Respects file exclusion rules

### For Users

Just works! TunaCode will:
- ✅ Create `.tunacode/` automatically
- ✅ Add it to your .gitignore
- ✅ Clean up old backups
- ✅ Keep your undo data local

No configuration needed!