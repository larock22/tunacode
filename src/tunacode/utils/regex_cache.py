"""Pre-compiled regex patterns for better performance."""

import re

# Command patterns
MODEL_COMMAND_PATTERN = re.compile(r"(?:^|\n)\s*(?:/model|/m)\s+\S*$")
COMMAND_START_PATTERN = re.compile(r"^/\w+")

# File reference patterns
FILE_REF_PATTERN = re.compile(r"@([^\s]+)")
FILE_PATH_PATTERN = re.compile(r"^[a-zA-Z0-9_\-./]+$")

# Code patterns
IMPORT_PATTERN = re.compile(r"^\s*(?:from|import)\s+\S+")
FUNCTION_DEF_PATTERN = re.compile(r"^\s*def\s+(\w+)\s*\(")
CLASS_DEF_PATTERN = re.compile(r"^\s*class\s+(\w+)")

# Environment variable patterns
ENV_VAR_PATTERN = re.compile(r"\$\{(\w+)(?::([^}]*))?\}")
API_KEY_PATTERN = re.compile(r"_API_KEY$")

# Common text patterns
WHITESPACE_PATTERN = re.compile(r"\s+")
WORD_BOUNDARY_PATTERN = re.compile(r"\b\w+\b")
LINE_SPLIT_PATTERN = re.compile(r"\r?\n")

# Tool output patterns
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
ERROR_PATTERN = re.compile(r"(?i)(error|exception|failed|failure):\s*(.+)")

# Model name patterns
MODEL_PROVIDER_PATTERN = re.compile(r"^(\w+):(.+)$")
OPENROUTER_MODEL_PATTERN = re.compile(r"^openrouter:(.+)$")
