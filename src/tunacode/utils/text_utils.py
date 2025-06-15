"""
Module: sidekick.utils.text_utils

Provides text processing utilities.
Includes file extension to language mapping and key formatting functions.
"""

import os
from typing import List, Set, Tuple


def key_to_title(key: str, uppercase_words: Set[str] = None) -> str:
    """Convert key to title, replacing underscores with spaces and capitalizing words."""
    if uppercase_words is None:
        uppercase_words = {"api", "id", "url"}

    words = key.split("_")
    result_words = []
    for word in words:
        lower_word = word.lower()
        if lower_word in uppercase_words:
            result_words.append(lower_word.upper())
        elif word:
            result_words.append(word[0].upper() + word[1:].lower())
        else:
            result_words.append("")

    return " ".join(result_words)


def ext_to_lang(path: str) -> str:
    """Get the language from the file extension. Default to `text` if not found."""
    MAP = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "java": "java",
        "c": "c",
        "cpp": "cpp",
        "cs": "csharp",
        "html": "html",
        "css": "css",
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
    }
    ext = os.path.splitext(path)[1][1:]
    if ext in MAP:
        return MAP[ext]
    return "text"


def expand_file_refs(text: str) -> Tuple[str, List[str]]:
    """Expand @file references with file contents wrapped in code fences.

    Args:
        text: The input text potentially containing @file references.

    Returns:
        Tuple[str, List[str]]: A tuple containing:
            - Text with any @file references replaced by the file's contents
            - List of absolute paths of files that were successfully expanded

    Raises:
        ValueError: If a referenced file does not exist or is too large.
    """
    import os
    import re

    from tunacode.constants import (ERROR_FILE_NOT_FOUND, ERROR_FILE_TOO_LARGE, MAX_FILE_SIZE,
                                    MSG_FILE_SIZE_LIMIT)

    pattern = re.compile(r"@([\w./_-]+)")
    expanded_files = []

    def replacer(match: re.Match) -> str:
        path = match.group(1)
        if not os.path.exists(path):
            raise ValueError(ERROR_FILE_NOT_FOUND.format(filepath=path))

        if os.path.getsize(path) > MAX_FILE_SIZE:
            raise ValueError(ERROR_FILE_TOO_LARGE.format(filepath=path) + MSG_FILE_SIZE_LIMIT)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Track the relative path of the file (not absolute)
        expanded_files.append(path)

        lang = ext_to_lang(path)
        # Add clear headers to indicate this is a file reference, not code to write
        return f"\n=== FILE REFERENCE: {path} ===\n```{lang}\n{content}\n```\n=== END FILE REFERENCE: {path} ===\n"

    expanded_text = pattern.sub(replacer, text)
    return expanded_text, expanded_files
