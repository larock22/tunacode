"""Completers for file references and commands."""

import os
from typing import Iterable, Optional

from prompt_toolkit.completion import CompleteEvent, Completer, Completion, merge_completers
from prompt_toolkit.document import Document

from ..cli.commands import CommandRegistry


class CommandCompleter(Completer):
    """Completer for slash commands and their arguments."""
    
    def __init__(self, command_registry: Optional[CommandRegistry] = None):
        self.command_registry = command_registry
        self._model_selector = None
    
    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Get completions for slash commands and model names."""
        # Get the text before cursor
        text = document.text_before_cursor
        
        # Check if we're completing model names after /model or /m command
        if self._should_complete_model_names(text):
            yield from self._get_model_completions(document, text)
            return
        
        # Check if we're at the start of a line or after whitespace
        if text and not text.isspace() and text[-1] != '\n':
            # Only complete commands at the start of input or after a newline
            last_newline = text.rfind('\n')
            line_start = text[last_newline + 1:] if last_newline >= 0 else text
            
            # Skip if not at the beginning of a line
            if line_start and not line_start.startswith('/'):
                return
        
        # Get the word before cursor
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        
        # Only complete if word starts with /
        if not word_before_cursor.startswith('/'):
            return
            
        # Get command names from registry
        if self.command_registry:
            command_names = self.command_registry.get_command_names()
        else:
            # Fallback list of commands
            command_names = ['/help', '/clear', '/dump', '/yolo', '/undo', 
                           '/branch', '/compact', '/model', '/m', '/init']
        
        # Get the partial command (without /)
        partial = word_before_cursor[1:].lower()
        
        # Yield completions for matching commands
        for cmd in command_names:
            if cmd.startswith('/') and cmd[1:].lower().startswith(partial):
                yield Completion(
                    text=cmd,
                    start_position=-len(word_before_cursor),
                    display=cmd,
                    display_meta='command'
                )
    
    def _should_complete_model_names(self, text: str) -> bool:
        """Check if we should complete model names."""
        # Look for /model or /m command followed by space
        import re
        pattern = r'(?:^|\n)\s*(?:/model|/m)\s+\S*$'
        return bool(re.search(pattern, text))
    
    def _get_model_completions(self, document: Document, text: str) -> Iterable[Completion]:
        """Get completions for model names."""
        # Lazy import and cache
        if self._model_selector is None:
            try:
                from ..cli.model_selector import ModelSelector
                self._model_selector = ModelSelector()
            except ImportError:
                return
        
        # Get the partial model name
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        partial = word_before_cursor.lower()
        
        # Yield model short names and indices
        seen = set()
        for i, model in enumerate(self._model_selector.models):
            # Complete by index
            index_str = str(i)
            if index_str.startswith(partial) and index_str not in seen:
                seen.add(index_str)
                yield Completion(
                    text=index_str,
                    start_position=-len(word_before_cursor),
                    display=f"{index_str} - {model.display_name}",
                    display_meta=model.provider.value[2]
                )
            
            # Complete by short name
            if model.short_name.lower().startswith(partial) and model.short_name not in seen:
                seen.add(model.short_name)
                yield Completion(
                    text=model.short_name,
                    start_position=-len(word_before_cursor),
                    display=f"{model.short_name} - {model.display_name}",
                    display_meta=model.provider.value[2]
                )


class FileReferenceCompleter(Completer):
    """Completer for @file references that provides file path suggestions."""

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Get completions for @file references."""
        # Get the word before cursor
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        
        # Check if we're in an @file reference
        if not word_before_cursor.startswith("@"):
            return
            
        # Get the path part after @
        path_part = word_before_cursor[1:]  # Remove @
        
        # Determine directory and prefix
        if "/" in path_part:
            # Path includes directory
            dir_path = os.path.dirname(path_part)
            prefix = os.path.basename(path_part)
        else:
            # Just filename, search in current directory
            dir_path = "."
            prefix = path_part
            
        # Get matching files
        try:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                for item in sorted(os.listdir(dir_path)):
                    if item.startswith(prefix):
                        full_path = os.path.join(dir_path, item) if dir_path != "." else item
                        
                        # Skip hidden files unless explicitly requested
                        if item.startswith(".") and not prefix.startswith("."):
                            continue
                            
                        # Add / for directories
                        if os.path.isdir(full_path):
                            display = item + "/"
                            completion = full_path + "/"
                        else:
                            display = item
                            completion = full_path
                            
                        # Calculate how much to replace
                        start_position = -len(path_part)
                        
                        yield Completion(
                            text=completion,
                            start_position=start_position,
                            display=display,
                            display_meta="dir" if os.path.isdir(full_path) else "file"
                        )
        except (OSError, PermissionError):
            # Silently ignore inaccessible directories
            pass


def create_completer(command_registry: Optional[CommandRegistry] = None) -> Completer:
    """Create a merged completer for both commands and file references."""
    return merge_completers([
        CommandCompleter(command_registry),
        FileReferenceCompleter(),
    ])