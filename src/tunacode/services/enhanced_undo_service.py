"""
Enhanced undo service with multiple failsafe mechanisms.
Provides three layers of protection for file operations.
"""

import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tunacode.core.state import StateManager
from tunacode.utils.system import get_session_dir


class EnhancedUndoService:
    """Multi-layer undo system with failsafes."""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.session_dir = get_session_dir(state_manager)
        
        # Layer 1: File backups directory
        self.backup_dir = self.session_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Layer 2: Operation log
        self.op_log_file = self.session_dir / "operations.jsonl"
        
        # Layer 3: Git (existing system)
        self.git_dir = self.session_dir / ".git"
        
        self._init_systems()
    
    def _init_systems(self):
        """Initialize all undo systems."""
        # Ensure operation log exists
        if not self.op_log_file.exists():
            self.op_log_file.touch()
    
    # ===== LAYER 1: File Backups =====
    
    def backup_file(self, filepath: Path) -> Optional[Path]:
        """
        Create a timestamped backup of a file before modification.
        
        Returns:
            Path to backup file, or None if backup failed
        """
        # Note: We'll create empty backup even if file doesn't exist yet
        # This helps track file creation operations
            
        try:
            # Create unique backup name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_name = f"{filepath.name}.{timestamp}.bak"
            backup_path = self.backup_dir / backup_name
            
            # Copy the file
            shutil.copy2(filepath, backup_path)
            
            # Log the backup
            self._log_operation({
                "type": "backup",
                "original": str(filepath),
                "backup": str(backup_path),
                "timestamp": timestamp
            })
            
            return backup_path
        except Exception as e:
            print(f"⚠️  Failed to create backup: {e}")
            return None
    
    def restore_from_backup(self, original_path: Path) -> Tuple[bool, str]:
        """
        Restore a file from its most recent backup.
        
        Returns:
            (success, message) tuple
        """
        try:
            # Find most recent backup for this file
            backups = sorted([
                f for f in self.backup_dir.glob(f"{original_path.name}.*.bak")
            ], reverse=True)
            
            if not backups:
                return False, f"No backups found for {original_path.name}"
            
            latest_backup = backups[0]
            
            # Restore the file
            shutil.copy2(latest_backup, original_path)
            
            # Log the restore
            self._log_operation({
                "type": "restore",
                "file": str(original_path),
                "from_backup": str(latest_backup),
                "timestamp": datetime.now().isoformat()
            })
            
            return True, f"Restored {original_path.name} from backup"
            
        except Exception as e:
            return False, f"Failed to restore from backup: {e}"
    
    # ===== LAYER 2: Operation Log =====
    
    def _log_operation(self, operation: Dict):
        """Log an operation to the operations file."""
        try:
            with open(self.op_log_file, 'a') as f:
                json.dump(operation, f)
                f.write('\n')
        except Exception:
            pass  # Silent fail for logging
    
    def log_file_operation(self, op_type: str, filepath: Path, 
                          old_content: Optional[str] = None,
                          new_content: Optional[str] = None):
        """
        Log a file operation with content for potential recovery.
        """
        operation = {
            "type": "file_operation",
            "operation": op_type,
            "file": str(filepath),
            "timestamp": datetime.now().isoformat()
        }
        
        # For safety, only log content for smaller files
        if old_content and len(old_content) < 100_000:  # 100KB limit
            operation["old_content"] = old_content
        if new_content and len(new_content) < 100_000:
            operation["new_content"] = new_content
            
        self._log_operation(operation)
    
    def get_recent_operations(self, limit: int = 10) -> List[Dict]:
        """Get recent operations from the log."""
        operations = []
        try:
            with open(self.op_log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        operations.append(json.loads(line))
        except Exception:
            pass
        
        return operations[-limit:]
    
    def undo_from_log(self) -> Tuple[bool, str]:
        """
        Attempt to undo the last operation using the operation log.
        """
        operations = self.get_recent_operations(20)
        
        # Find the last file operation
        for op in reversed(operations):
            if op.get("type") == "file_operation" and "old_content" in op:
                filepath = Path(op["file"])
                
                try:
                    # Restore old content
                    with open(filepath, 'w') as f:
                        f.write(op["old_content"])
                    
                    self._log_operation({
                        "type": "undo_from_log",
                        "restored_file": str(filepath),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    return True, f"Restored {filepath.name} from operation log"
                except Exception as e:
                    return False, f"Failed to restore from log: {e}"
        
        return False, "No recoverable operations found in log"
    
    # ===== LAYER 3: Git Integration =====
    
    def git_commit(self, message: str = "Auto-save") -> bool:
        """Create a git commit if available."""
        if not self.git_dir.exists():
            return False
            
        try:
            git_dir_arg = f"--git-dir={self.git_dir}"
            subprocess.run(["git", git_dir_arg, "add", "."], 
                         capture_output=True, timeout=5)
            
            subprocess.run(
                ["git", git_dir_arg, "commit", "-m", message],
                capture_output=True, timeout=5
            )
            return True
        except Exception:
            return False
    
    # ===== Unified Undo Interface =====
    
    def perform_undo(self) -> Tuple[bool, str]:
        """
        Perform undo with automatic failover:
        1. Try Git first (if available)
        2. Fall back to operation log
        3. Fall back to file backups
        """
        # Layer 3: Try Git first
        if self.git_dir.exists():
            try:
                from tunacode.services.undo_service import perform_undo
                success, message = perform_undo(self.state_manager)
                if success:
                    return success, f"[Git] {message}"
            except Exception:
                pass
        
        # Layer 2: Try operation log
        success, message = self.undo_from_log()
        if success:
            return success, f"[OpLog] {message}"
        
        # Layer 1: Show available backups
        backups = list(self.backup_dir.glob("*.bak"))
        if backups:
            recent_backups = sorted(backups, reverse=True)[:5]
            backup_list = "\n".join([f"  - {b.name}" for b in recent_backups])
            return False, f"Manual restore available from backups:\n{backup_list}"
        
        return False, "No undo information available"
    
    def cleanup_old_backups(self, keep_recent: int = 50):
        """Clean up old backup files, keeping the most recent ones."""
        backups = sorted(self.backup_dir.glob("*.bak"))
        
        if len(backups) > keep_recent:
            for backup in backups[:-keep_recent]:
                try:
                    backup.unlink()
                except Exception:
                    pass


# ===== Safe File Operations Wrapper =====

class SafeFileOperations:
    """Wrapper for file operations with automatic backup."""
    
    def __init__(self, undo_service: EnhancedUndoService):
        self.undo = undo_service
    
    async def safe_write(self, filepath: Path, content: str) -> Tuple[bool, str]:
        """Write file with automatic backup."""
        filepath = Path(filepath)
        
        # Get old content if file exists
        old_content = None
        if filepath.exists():
            try:
                old_content = filepath.read_text()
            except Exception:
                pass
        
        # Always create backup before write (even for new files)
        self.undo.backup_file(filepath)
        
        # Write new content
        try:
            filepath.write_text(content)
            
            # Log the operation
            self.undo.log_file_operation(
                "write", filepath, old_content, content
            )
            
            # Commit to git if available
            self.undo.git_commit(f"Modified {filepath.name}")
            
            return True, "File written successfully"
            
        except Exception as e:
            return False, f"Failed to write file: {e}"
    
    async def safe_delete(self, filepath: Path) -> Tuple[bool, str]:
        """Delete file with automatic backup."""
        filepath = Path(filepath)
        
        if not filepath.exists():
            return False, "File does not exist"
        
        try:
            # Create backup first
            backup_path = self.undo.backup_file(filepath)
            
            # Get content for operation log
            content = filepath.read_text()
            
            # Delete the file
            filepath.unlink()
            
            # Log the operation
            self.undo.log_file_operation(
                "delete", filepath, old_content=content
            )
            
            # Commit to git
            self.undo.git_commit(f"Deleted {filepath.name}")
            
            return True, f"File deleted (backup at {backup_path.name})"
            
        except Exception as e:
            return False, f"Failed to delete file: {e}"