"""
Hybrid request analyzer for architect mode.

Uses simple patterns for obvious cases and LLM for complex requests.
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from ..code_index import CodeIndex
from .project_context import ProjectContext
from .schemas import LLMAnalysisResponse
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


@dataclass
class ParsedIntent:
    """Result of analyzing a user request."""

    request_type: RequestType
    confidence: str  # "high", "medium", "low"
    file_paths: List[str]
    search_terms: List[str]
    operations: List[str]
    raw_request: str
    tasks: Optional[List[Dict[str, Any]]] = None


class HybridRequestAnalyzer:
    """Analyzes user requests using a hybrid approach."""

    def __init__(self, model: Optional[str] = None):
        # Initialize code index for file lookups
        self.code_index = CodeIndex()
        # Initialize project context detector
        self.project_context = ProjectContext(self.code_index)
        # Initialize task generator
        self.task_generator = AdaptiveTaskGenerator(self.project_context)

        # Store model for LLM fallback
        self.model = model
        self._llm_agent = None
        self._llm_prompt = None

        # Compile simple patterns for fast matching
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for common cases."""
        # Patterns for file operations
        self.file_ref_pattern = re.compile(r"@([\w\-./]+\.[\w]+)")
        self.operation_pattern = re.compile(
            r"\b(summarize|explain|analyze|describe)\b", re.IGNORECASE
        )

        # Define which tools mutate the system
        self.mutating_tools = {"write_file", "update_file", "run_command", "bash"}

        # Pattern for simple file reads
        self.read_pattern = re.compile(
            r"^(?:read|show|view|cat)\s+(?:the\s+)?(?:contents\s+of\s+)?@?([\w\-./]+\.[\w]+)$",
            re.IGNORECASE,
        )

        # Pattern for search operations
        self.search_pattern = re.compile(
            r'^(?:find|search|grep)\s+(?:for\s+)?["\']?([^"\']+)["\']?', re.IGNORECASE
        )

        # Pattern for TODO/FIXME searches (very common)
        self.todo_pattern = re.compile(
            r"(?:find|search|show)\s+(?:all\s+)?(?:the\s+)?(?:for\s+)?(TODO|FIXME|XXX|HACK)s?(?:\s+comments?)?",
            re.IGNORECASE,
        )

        # Pattern for simple write operations
        self.write_pattern = re.compile(
            r"^(?:create|write|put|make)\s+(?:a\s+)?(?:new\s+)?(?:file\s+)?@?([\w\-./]+\.[\w]+)?\s*(?:with\s+)?(?:content\s+)?[\"']?(.+?)[\"']?$",
            re.IGNORECASE | re.DOTALL,
        )

        # Pattern for "just put X" style commands
        self.simple_put_pattern = re.compile(
            r"^(?:just\s+)?(?:put|write|create)\s+(.+)$", re.IGNORECASE | re.DOTALL
        )

        # Pattern for update/append operations
        self.update_pattern = re.compile(
            r"(?:add|append|update|modify|change|edit)\s+(?:.*?)\s+(?:to|in|at|the\s+end\s+of)\s+(?:the\s+)?(?:file\s+)?@?([\w\-./]+\.[\w]+)",
            re.IGNORECASE,
        )

    async def analyze(self, request: str) -> ParsedIntent:
        """Analyze a user request using LLM for everything."""
        request = request.strip()

        # Just use LLM for everything - it's fast and accurate
        return await self._llm_analyze(request)

    def _build_search_pattern(self, search_term: str) -> str:
        """Build a smart search pattern."""
        # If it's a short term, add word boundaries
        if len(search_term) <= 3:
            return f"\\b{re.escape(search_term)}\\b"
        # Otherwise use as-is
        return re.escape(search_term)

    async def _llm_analyze(self, request: str) -> ParsedIntent:
        """Use LLM for complex request analysis with validation and retry."""
        # Initialize LLM agent if needed
        await self._ensure_llm_agent()

        # Get project context
        project_info = self.project_context.detect_context()
        context = {
            "request": request,
            "project_type": project_info.project_type.value,
        }

        # Try twice with validation
        for attempt in range(2):
            try:
                # Ask LLM
                result = await self._llm_agent.run(
                    f"Analyze this request and return ONLY the JSON response: {request}\n\nProject context: {json.dumps(context)}"
                )

                # Parse and validate response
                validated = self._parse_and_validate_llm_response(result.data)

                # Convert to ParsedIntent
                tasks = None
                if validated.tasks:
                    tasks = [task.dict() for task in validated.tasks]

                return ParsedIntent(
                    request_type=RequestType(validated.request_type),
                    confidence=validated.confidence,
                    file_paths=validated.file_paths,
                    search_terms=validated.search_terms,
                    operations=validated.operations,
                    raw_request=request,
                    tasks=tasks,
                )

            except (json.JSONDecodeError, ValidationError) as e:
                if attempt == 0:
                    # Retry with clearer instructions
                    print(f"LLM response validation failed, retrying: {e}")
                    continue
                else:
                    print(f"LLM analysis failed after retry: {e}")
                    break
            except Exception as e:
                print(f"LLM analysis error: {e}")
                break

        # Ultimate fallback
        return ParsedIntent(
            request_type=RequestType.COMPLEX,
            confidence="low",
            file_paths=self._extract_file_paths(request),
            search_terms=[],
            operations=[],
            raw_request=request,
            tasks=None,
        )

    async def _ensure_llm_agent(self):
        """Ensure LLM agent is initialized."""
        if self._llm_agent is None:
            import importlib
            import os

            pydantic_ai = importlib.import_module("pydantic_ai")
            Agent = pydantic_ai.Agent

            # Load prompt
            if self._llm_prompt is None:
                prompt_path = (
                    Path(__file__).parent.parent.parent / "prompts" / "request_analyzer.md"
                )
                with open(prompt_path, "r") as f:
                    self._llm_prompt = f.read()

            # Initialize agent
            model_str = self.model or os.getenv("TUNACODE_MODEL", "openai:gpt-4")
            if isinstance(model_str, str) and ":" not in model_str:
                model_str = f"openai:{model_str}"

            self._llm_agent = Agent(
                model=model_str,
                system_prompt=self._llm_prompt,
            )

    def _parse_and_validate_llm_response(self, response_text: str) -> LLMAnalysisResponse:
        """Parse and validate LLM response with Pydantic."""
        # Extract JSON from response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1

        if json_start < 0 or json_end <= json_start:
            raise json.JSONDecodeError("No JSON found in response", response_text, 0)

        json_text = response_text[json_start:json_end]
        parsed = json.loads(json_text)

        # Validate with Pydantic
        return LLMAnalysisResponse(**parsed)

    def _extract_file_paths(self, request: str) -> List[str]:
        """Simple file path extraction."""
        pattern = r'@([\w\-./]+\.[\w]+)|(?:["\'`])([\w\-./]+\.[\w]+)(?:["\'`])'
        matches = re.findall(pattern, request)
        paths = []
        for match in matches:
            for path in match:
                if path:
                    paths.append(path)
        return paths

    def generate_simple_tasks(self, intent: ParsedIntent) -> Optional[List[dict]]:
        """Use the tasks from analysis or generate based on intent."""
        # If tasks were already generated, use them
        if intent.tasks:
            return intent.tasks

        # For complex or low confidence, return None to trigger full LLM planning
        if intent.request_type == RequestType.COMPLEX or intent.confidence == "low":
            return None

        # For codebase analysis, use the adaptive task generator
        if intent.request_type == RequestType.ANALYZE_CODEBASE:
            context = self.project_context.detect_context()
            return self.task_generator.generate_codebase_tasks(context)

        # Otherwise, no simple tasks available
        return None
