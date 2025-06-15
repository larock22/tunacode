"""
Request analyzer for architect mode.

Provides pattern-based analysis of user requests to generate tasks deterministically
when possible, falling back to LLM planning for complex cases.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from ..code_index import CodeIndex
from .project_context import ProjectContext
from .task_generator import AdaptiveTaskGenerator


class RequestType(Enum):
    """Types of requests we can recognize."""

    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    UPDATE_FILE = "update_file"
    SEARCH_CODE = "search_code"
    EXPLAIN_CODE = "explain_code"
    ANALYZE_CODEBASE = "analyze_codebase"
    RUN_COMMAND = "run_command"
    COMPLEX = "complex"  # Needs LLM planning


class Confidence(Enum):
    """Confidence levels for pattern matching."""

    HIGH = 0.9
    MEDIUM = 0.7
    LOW = 0.5
    NONE = 0.0


@dataclass
class ParsedIntent:
    """Result of analyzing a user request."""

    request_type: RequestType
    confidence: Confidence
    file_paths: List[str]
    search_terms: List[str]
    operations: List[str]
    raw_request: str


class RequestAnalyzer:
    """Analyzes user requests to extract intent and generate tasks."""

    def __init__(self):
        # Initialize code index for file lookups
        self.code_index = CodeIndex()
        # Initialize project context detector
        self.project_context = ProjectContext(self.code_index)
        # Initialize task generator
        self.task_generator = AdaptiveTaskGenerator(self.project_context)

        # Patterns for different request types
        self.patterns = {
            RequestType.READ_FILE: [
                (r"(?:read|show|display|view|cat|print)\s+(@?\S+\.[\w]+)", Confidence.HIGH),
                (r"(?:what's in|what is in|look at)\s+(@?\S+\.[\w]+)", Confidence.HIGH),
                (r"(@\S+\.[\w]+)", Confidence.MEDIUM),  # Just a file reference
            ],
            RequestType.WRITE_FILE: [
                (
                    r"(?:create|write|make)\s+(?:a\s+)?(?:new\s+)?(?:file\s+)?(@?\S+\.[\w]+)",
                    Confidence.HIGH,
                ),
                (r"(?:write|create)\s+(.+?)\s+to\s+(@?\S+\.[\w]+)", Confidence.HIGH),
            ],
            RequestType.UPDATE_FILE: [
                (r"(?:update|modify|change|edit|fix)\s+(@?\S+\.[\w]+)", Confidence.HIGH),
                (r"(?:add|insert|append).+?(?:to|in)\s+(@?\S+\.[\w]+)", Confidence.HIGH),
                (r"(?:replace|rename).+?in\s+(@?\S+\.[\w]+)", Confidence.HIGH),
            ],
            RequestType.SEARCH_CODE: [
                (
                    r"(?:search|find|grep|look\s+for)\s+(?:for\s+)?[\"']([^\"']+)[\"']",
                    Confidence.HIGH,
                ),
                (
                    r"(?:search|find|grep|look\s+for)\s+(?:for\s+)?(\S+)(?:\s+in\s+(.+))?",
                    Confidence.HIGH,
                ),
                (
                    r"(?:where|which\s+files?).+?(?:contain|have|use)\s+[\"']([^\"']+)[\"']",
                    Confidence.HIGH,
                ),
                (
                    r"(?:where|which\s+files?).+?(?:contain|have|use)\s+(\S+)",
                    Confidence.MEDIUM,
                ),
            ],
            RequestType.EXPLAIN_CODE: [
                (
                    r"(?:explain|describe|tell me about|how does).+?(?:work|function)",
                    Confidence.HIGH,
                ),
                (r"(?:what does|what is)\s+(.+?)\s+(?:do|for)", Confidence.HIGH),
                # Pattern for summarize with file reference
                (r"(@?\S+\.\w+)\s+(?:summarize|summary)", Confidence.HIGH),
                (r"(?:summarize|summary)\s+(?:the\s+)?(?:file\s+)?(@?\S+\.\w+)", Confidence.HIGH),
                # General summarize pattern
                (r"summarize\s+(?:this|the)\s+file", Confidence.MEDIUM),
            ],
            RequestType.ANALYZE_CODEBASE: [
                (
                    r"(?:analyze|review|audit)\s+(?:the\s+)?(?:code|codebase|project)",
                    Confidence.HIGH,
                ),
                (
                    r"(?:how does|how is)\s+(?:this|the)\s+(?:code|project|codebase).+?(?:organized|structured|work)",
                    Confidence.HIGH,
                ),
                (
                    r"(?:tell\s+me\s+about|describe|what\s+is)\s+(?:this\s+)?(?:code|codebase|project)",
                    Confidence.HIGH,
                ),
            ],
            RequestType.RUN_COMMAND: [
                (r"(?:run|execute|exec)\s+(.+)", Confidence.HIGH),
                (r"(?:npm|pip|make|python|node|cargo)\s+(.+)", Confidence.HIGH),
            ],
        }

        # Keywords that suggest complex multi-step operations
        self.complex_keywords = {
            "and then",
            "after that",
            "next",
            "finally",
            "first",
            "second",
            "third",
            "step 1",
            "step 2",
            "refactor",
            "migrate",
            "convert",
            "implement",
            "build",
            "design",
        }

    def analyze(self, request: str) -> ParsedIntent:
        """Analyze a user request and extract intent."""
        request_lower = request.lower().strip()

        # Check for complex multi-step operations first
        if self._is_complex(request_lower):
            return ParsedIntent(
                request_type=RequestType.COMPLEX,
                confidence=Confidence.HIGH,
                file_paths=self._extract_file_paths(request),
                search_terms=[],
                operations=self._extract_operations(request_lower),
                raw_request=request,
            )

        # Try to match against known patterns
        best_match = None
        best_confidence = Confidence.NONE
        matches_by_type = {}  # Track all matches by type

        for request_type, patterns in self.patterns.items():
            for pattern, confidence in patterns:
                match = re.search(pattern, request_lower, re.IGNORECASE)
                if match:
                    if request_type not in matches_by_type:
                        matches_by_type[request_type] = []
                    matches_by_type[request_type].append((match, confidence))

                    if confidence.value > best_confidence.value:
                        best_match = (request_type, match, confidence)
                        best_confidence = confidence

        # Special handling: if we have both READ_FILE and EXPLAIN_CODE matches,
        # and the request contains "summarize", prefer EXPLAIN_CODE
        if (
            RequestType.READ_FILE in matches_by_type
            and RequestType.EXPLAIN_CODE in matches_by_type
            and "summariz" in request_lower  # catches summarize, summarizing, summary
        ):
            # Use the best EXPLAIN_CODE match
            for match, conf in matches_by_type[RequestType.EXPLAIN_CODE]:
                best_match = (RequestType.EXPLAIN_CODE, match, conf)
                best_confidence = conf
                break

        if best_match:
            request_type, match, confidence = best_match
            return self._create_parsed_intent(request, request_type, match, confidence)

        # Default to complex if we can't parse it
        return ParsedIntent(
            request_type=RequestType.COMPLEX,
            confidence=Confidence.LOW,
            file_paths=self._extract_file_paths(request),
            search_terms=self._extract_quoted_strings(request),
            operations=self._extract_operations(request_lower),
            raw_request=request,
        )

    def _is_complex(self, request_lower: str) -> bool:
        """Check if request contains complex multi-step indicators."""
        return any(keyword in request_lower for keyword in self.complex_keywords)

    def _extract_file_paths(self, request: str) -> List[str]:
        """Extract file paths from request."""
        # Pattern for @file references or explicit file paths
        pattern = r'@([\w\-./]+\.[\w]+)|(?:["\'`])([\w\-./]+\.[\w]+)(?:["\'`])'
        matches = re.findall(pattern, request)
        # Flatten the tuple results and filter out empty strings
        paths = []
        for match in matches:
            for path in match:
                if path:
                    paths.append(path)
        return paths

    def _extract_quoted_strings(self, request: str) -> List[str]:
        """Extract quoted strings that might be search terms."""
        pattern = r'["\'`]([^"\'`]+)["\'`]'
        return re.findall(pattern, request)

    def _extract_operations(self, request_lower: str) -> List[str]:
        """Extract operation keywords from request."""
        operation_keywords = [
            "read",
            "write",
            "create",
            "update",
            "modify",
            "delete",
            "search",
            "find",
            "grep",
            "explain",
            "analyze",
            "run",
            "test",
            "build",
            "compile",
            "lint",
            "format",
            "summarize",
            "summary",
        ]
        found = []
        for keyword in operation_keywords:
            if keyword in request_lower:
                found.append(keyword)
        return found

    def _create_parsed_intent(
        self, request: str, request_type: RequestType, match: re.Match, confidence: Confidence
    ) -> ParsedIntent:
        """Create a ParsedIntent from a pattern match."""
        file_paths = self._extract_file_paths(request)
        search_terms = []

        # Extract search terms for search operations
        if request_type == RequestType.SEARCH_CODE and match.groups():
            # Get all non-None groups
            groups = [g for g in match.groups() if g]
            if groups:
                # First group is typically the search term
                search_term = groups[0].strip()
                if search_term:
                    search_terms.append(search_term)
                # If there's a directory specified, add it to file_paths
                if len(groups) > 1 and groups[1]:
                    directory = groups[1].strip()
                    if directory and directory not in file_paths:
                        file_paths.append(directory)

        return ParsedIntent(
            request_type=request_type,
            confidence=confidence,
            file_paths=file_paths,
            search_terms=search_terms,
            operations=self._extract_operations(request.lower()),
            raw_request=request,
        )

    def generate_simple_tasks(self, intent: ParsedIntent) -> Optional[List[dict]]:
        """Generate simple task list for high-confidence, simple operations."""
        if intent.confidence.value < Confidence.MEDIUM.value:
            return None

        tasks = []
        task_id = 1

        if intent.request_type == RequestType.READ_FILE:
            # If no file paths extracted from the pattern, try to extract from raw request
            file_paths = intent.file_paths
            if not file_paths and intent.request_type == RequestType.READ_FILE:
                # Try to extract file paths that might not have been caught
                import re

                file_pattern = r"(?:read|show|view)\s+(?:the\s+)?(\S+\.[\w]+)"
                match = re.search(file_pattern, intent.raw_request, re.IGNORECASE)
                if match:
                    file_paths = [match.group(1)]

            for file_path in file_paths:
                tasks.append(
                    {
                        "id": task_id,
                        "description": f"Read file {file_path}",
                        "mutate": False,
                        "tool": "read_file",
                        "args": {"file_path": file_path},
                    }
                )
                task_id += 1

        elif intent.request_type == RequestType.SEARCH_CODE:
            search_term = intent.search_terms[0] if intent.search_terms else ""
            directory = intent.file_paths[0] if intent.file_paths else "."

            # Use CodeIndex to build a more precise pattern
            pattern = self._build_precise_grep_pattern(search_term)

            if pattern:
                tasks.append(
                    {
                        "id": task_id,
                        "description": f"Search for '{search_term}' in {directory}",
                        "mutate": False,
                        "tool": "grep",
                        "args": {
                            "pattern": pattern,
                            "directory": directory,
                            "search_type": "smart",
                        },
                    }
                )
            else:
                # If no pattern can be built, return None to trigger LLM planning
                return None

        elif intent.request_type == RequestType.EXPLAIN_CODE:
            # First read relevant files
            for file_path in intent.file_paths:
                tasks.append(
                    {
                        "id": task_id,
                        "description": f"Read {file_path} to understand the code",
                        "mutate": False,
                        "tool": "read_file",
                        "args": {"file_path": file_path},
                    }
                )
                task_id += 1

            # Then analyze based on the request
            if "summariz" in intent.raw_request.lower():
                analyze_desc = f"Summarize the contents of {', '.join(intent.file_paths) if intent.file_paths else 'the file'}"
            else:
                analyze_desc = "Explain how the code works"

            tasks.append(
                {
                    "id": task_id,
                    "description": analyze_desc,
                    "mutate": False,
                    "tool": "analyze",
                    "args": {"request": intent.raw_request},
                }
            )

        elif intent.request_type == RequestType.ANALYZE_CODEBASE:
            # Use context-aware task generation for codebase analysis
            context = self.project_context.detect_context()
            return self.task_generator.generate_codebase_tasks(context)

        else:
            # For write/update operations, return None to use LLM planning
            return None

        return tasks if tasks else None

    def _build_precise_grep_pattern(self, search_term: str) -> Optional[str]:
        """Build a precise grep pattern using the CodeIndex.

        Args:
            search_term: The term to search for

        Returns:
            A precise regex pattern or None if clarification is needed
        """
        if not search_term:
            return None

        # For very short terms (1-2 chars), we need more context to avoid broad searches
        if len(search_term) <= 2:
            return None

        # Ensure the index is built
        if not self.code_index._indexed:
            self.code_index.build_index()

        # Look up files that might contain this term
        matching_files = self.code_index.lookup(search_term)

        if matching_files:
            # If we found exact file matches, build a pattern for the filename
            # Use word boundaries to avoid overly broad matches
            escaped_term = re.escape(search_term)
            return f"\\b{escaped_term}\\b"
        else:
            # If no files found, check if it might be a symbol (class/function)
            # Try different variations
            variations = [
                search_term,
                search_term.lower(),
                search_term.upper(),
                search_term.capitalize(),
            ]

            for variant in variations:
                matches = self.code_index.lookup(variant)
                if matches:
                    escaped_variant = re.escape(variant)
                    return f"\\b{escaped_variant}\\b"

            # If still no matches, it might be a general code pattern
            # Return the search term with word boundaries
            # This avoids the problematic single-letter patterns
            escaped_term = re.escape(search_term)
            return f"\\b{escaped_term}\\b"
