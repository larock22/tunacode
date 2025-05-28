"""
Project-local undo service that stores backups in the working directory.
Designed for pip-installed CLI tool usage.
"""

import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from tunacode.core.state import StateManager


class ProjectUndoService:
    """Undo system that stores backups in .tunacode/ within the project."""

    # Directory name for local undo data
    UNDO_DIR_NAME = ".tunacode"
    BACKUP_SUBDIR = "backups"
    GITIGNORE_CONTENT = """# TunaCode undo system files
*
!.gitignore
"""

    def __init__(self, state_manager: StateManager, project_dir: Optional[Path] = None):
        self.state_manager = state_manager
        self.project_dir = Path(project_dir or Path.cwd())

        # Local undo directory in the project
        self.undo_dir = self.project_dir / self.UNDO_DIR_NAME
        self.backup_dir = self.undo_dir / self.BACKUP_SUBDIR
        self.op_log_file = self.undo_dir / "operations.jsonl"

        # Git directory (if project uses git)
        self.git_dir = self.project_dir / ".git"

        self._init_undo_directory()

    def _init_undo_directory(self):
        """Initialize the .tunacode directory in the project."""
        try:
            # Create directories
            self.undo_dir.mkdir(exist_ok=True)
            self.backup_dir.mkdir(exist_ok=True)

            # Create .gitignore to exclude undo files from version control
            gitignore_path = self.undo_dir / ".gitignore"
            if not gitignore_path.exists():
                gitignore_path.write_text(self.GITIGNORE_CONTENT)

            # Create operation log
            if not self.op_log_file.exists():
                self.op_log_file.touch()

            # Add informational README
            readme_path = self.undo_dir / "README.md"
            if not readme_path.exists():
                readme_path.write_text(
                    """# TunaCode Undo System

This directory contains local backup files created by TunaCode to enable undo functionality.

## Contents:
- `backups/` - Timestamped file backups
- `operations.jsonl` - Operation history log
- `.gitignore` - Excludes these files from git

## Notes:
- These files are local to your machine
- Safe to delete if you don't need undo history
- Automatically cleaned up (keeps last 50 backups)
- Not committed to version control

Created by TunaCode (https://github.com/larock22/tunacode)
"""
                )

        except PermissionError:
            print(f"⚠️  Cannot create {self.UNDO_DIR_NAME}/ directory - undo will be limited")
        except Exception as e:
            print(f"⚠️  Error initializing undo directory: {e}")

    def should_track_file(self, filepath: Path) -> bool:
        """Check if a file should be tracked by undo system."""
        # Don't track files in our own undo directory
        try:
            if self.undo_dir in filepath.parents:
                return False
        except ValueError:
            pass

        # Don't track hidden files/directories (except .gitignore, .env, etc)
        parts = filepath.parts
        for part in parts:
            if part.startswith(".") and part not in {".gitignore", ".env", ".envrc"}:
                return False

        # Don't track common build/cache directories
        exclude_dirs = {
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            "dist",
            "build",
            ".next",
            ".nuxt",
            "target",
        }
        if any(excluded in parts for excluded in exclude_dirs):
            return False

        return True

    def backup_file(self, filepath: Path) -> Optional[Path]:
        """Create a timestamped backup of a file."""
        # Check if we should track this file
        if not self.should_track_file(filepath):
            return None

        try:
            # Use relative path for organizing backups
            rel_path = filepath.relative_to(self.project_dir)

            # Create subdirectories in backup dir to mirror project structure
            backup_subdir = self.backup_dir / rel_path.parent
            backup_subdir.mkdir(parents=True, exist_ok=True)

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filepath.name}.{timestamp}.bak"
            backup_path = backup_subdir / backup_name

            # Copy the file if it exists
            if filepath.exists():
                shutil.copy2(filepath, backup_path)
            else:
                # Create empty backup for new files
                backup_path.touch()

            # Log the backup
            self._log_operation(
                {
                    "type": "backup",
                    "file": str(rel_path),
                    "backup": str(backup_path.relative_to(self.undo_dir)),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Clean up old backups for this file
            self._cleanup_file_backups(backup_subdir, filepath.name, keep=10)

            return backup_path

        except Exception:
            # Silent fail - don't interrupt user's work
            return None

    def _cleanup_file_backups(self, backup_dir: Path, filename: str, keep: int = 10):
        """Keep only the most recent backups for a specific file."""
        try:
            # Find all backups for this file
            pattern = f"{filename}.*.bak"
            backups = sorted(backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime)

            # Remove old backups
            if len(backups) > keep:
                for old_backup in backups[:-keep]:
                    old_backup.unlink()

        except Exception:
            pass  # Silent cleanup failure

    def _log_operation(self, operation: Dict):
        """Log an operation to the operations file."""
        try:
            with open(self.op_log_file, "a") as f:
                json.dump(operation, f)
                f.write("\n")

            # Keep log file size reasonable (last 1000 operations)
            self._trim_log_file(1000)

        except Exception:
            pass

    def _trim_log_file(self, max_lines: int):
        """Keep only the last N operations in the log."""
        try:
            with open(self.op_log_file, "r") as f:
                lines = f.readlines()

            if len(lines) > max_lines:
                with open(self.op_log_file, "w") as f:
                    f.writelines(lines[-max_lines:])

        except Exception:
            pass

    def get_undo_status(self) -> Dict[str, any]:
        """Get current status of undo system."""
        try:
            backup_count = sum(1 for _ in self.backup_dir.rglob("*.bak"))
            backup_size = sum(f.stat().st_size for f in self.backup_dir.rglob("*.bak"))
            log_size = self.op_log_file.stat().st_size if self.op_log_file.exists() else 0

            return {
                "enabled": True,
                "location": str(self.undo_dir),
                "backup_count": backup_count,
                "backup_size_mb": backup_size / (1024 * 1024),
                "log_size_kb": log_size / 1024,
                "git_available": self.git_dir.exists(),
            }
        except Exception:
            return {"enabled": False, "error": "Cannot access undo directory"}

    def cleanup_old_backups(self, days: int = 7):
        """Remove backups older than specified days."""
        try:
            cutoff_time = time.time() - (days * 24 * 60 * 60)

            for backup in self.backup_dir.rglob("*.bak"):
                if backup.stat().st_mtime < cutoff_time:
                    backup.unlink()

        except Exception:
            pass


class ProjectSafeFileOperations:
    """File operations with project-local backup."""

    def __init__(self, undo_service: ProjectUndoService):
        self.undo = undo_service

    async def safe_write(self, filepath: Path, content: str) -> Tuple[bool, str]:
        """Write file with automatic local backup."""
        filepath = Path(filepath).resolve()

        # Create backup before write
        backup_path = self.undo.backup_file(filepath)

        # Check if file exists for logging
        if filepath.exists() and filepath.stat().st_size < 100_000:
            try:
                filepath.read_text()  # Just check it's readable
            except Exception:
                pass

        # Write the file
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content)

            # Log the operation
            self.undo._log_operation(
                {
                    "type": "write",
                    "file": str(filepath.relative_to(self.undo.project_dir)),
                    "size": len(content),
                    "backup": (
                        str(backup_path.relative_to(self.undo.undo_dir)) if backup_path else None
                    ),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return True, "File written successfully"

        except Exception as e:
            return False, f"Failed to write file: {e}"

    async def safe_delete(self, filepath: Path) -> Tuple[bool, str]:
        """Delete file with automatic local backup."""
        filepath = Path(filepath).resolve()

        if not filepath.exists():
            return False, "File does not exist"

        # Create backup before delete
        backup_path = self.undo.backup_file(filepath)

        try:
            filepath.unlink()

            # Log the operation
            self.undo._log_operation(
                {
                    "type": "delete",
                    "file": str(filepath.relative_to(self.undo.project_dir)),
                    "backup": (
                        str(backup_path.relative_to(self.undo.undo_dir)) if backup_path else None
                    ),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return True, f"File deleted (backup available in {self.undo.UNDO_DIR_NAME}/)"

        except Exception as e:
            return False, f"Failed to delete file: {e}"


def get_project_undo_service(state_manager: StateManager) -> ProjectUndoService:
    """Get or create project-local undo service."""
    if not hasattr(state_manager.session, "project_undo"):
        state_manager.session.project_undo = ProjectUndoService(state_manager)
    return state_manager.session.project_undo
