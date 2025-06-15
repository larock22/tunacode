"""
LLM-based request analyzer for architect mode.

Uses an LLM to understand user intent instead of brittle regex patterns.
"""

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..code_index import CodeIndex
from .project_context import ProjectContext
from .task_generator import AdaptiveTaskGenerator

# Lazy imports for pydantic_ai


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


class LLMRequestAnalyzer:
    """Analyzes user requests using an LLM to extract intent and generate tasks."""

    def __init__(self, model: Optional[str] = None):
        # Initialize code index for file lookups
        self.code_index = CodeIndex()
        # Initialize project context detector
        self.project_context = ProjectContext(self.code_index)
        # Initialize task generator
        self.task_generator = AdaptiveTaskGenerator(self.project_context)

        # Load the prompt
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "request_analyzer.md"
        with open(prompt_path, "r") as f:
            self.prompt = f.read()

        # Store model for lazy initialization
        self.model = model or os.getenv("TUNACODE_MODEL", "openai:gpt-4")
        self._agent = None

    def _get_agent(self):
        """Lazy initialization of the agent."""
        if self._agent is None:
            # Lazy import pydantic_ai
            import importlib

            pydantic_ai = importlib.import_module("pydantic_ai")
            Agent = pydantic_ai.Agent

            # Convert model string to proper format if needed
            model_str = self.model
            if isinstance(model_str, str) and ":" in model_str:
                # Already in provider:model format
                model = model_str
            else:
                # Assume it's just a model name, default to openai
                model = f"openai:{model_str}" if model_str else "openai:gpt-4"

            self._agent = Agent(
                model=model,
                system_prompt=self.prompt,
            )
        return self._agent

    async def analyze(self, request: str) -> ParsedIntent:
        """Analyze a user request and extract intent using LLM."""
        try:
            # Get project context
            project_info = self.project_context.detect_context()

            # Build context for the LLM
            context = {
                "request": request,
                "project_type": project_info.project_type.value,
                "available_files": self._get_available_files_summary(),
            }

            # Ask the LLM to analyze the request
            agent = self._get_agent()
            result = await agent.run(
                f"Analyze this request and return the JSON response: {request}\n\nProject context: {json.dumps(context)}"
            )

            # Parse the LLM response
            response_text = result.data

            # Extract JSON from the response (handle markdown code blocks)
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                parsed = json.loads(json_text)
            else:
                # Fallback if no JSON found
                return self._fallback_intent(request)

            # Convert to ParsedIntent
            return ParsedIntent(
                request_type=RequestType(parsed.get("request_type", "complex")),
                confidence=parsed.get("confidence", "low"),
                file_paths=parsed.get("file_paths", []),
                search_terms=parsed.get("search_terms", []),
                operations=parsed.get("operations", []),
                raw_request=request,
                tasks=parsed.get("tasks", []),
            )

        except Exception as e:
            # If LLM fails, return a safe fallback
            print(f"LLM request analysis failed: {e}")
            return self._fallback_intent(request)

    def _get_available_files_summary(self) -> Dict[str, Any]:
        """Get a summary of available files for context."""
        # Build index if needed
        if not self.code_index._indexed:
            self.code_index.build_index()

        # Get top-level structure
        return {
            "total_files": len(self.code_index._file_map),
            "has_readme": "README.md" in self.code_index._file_map
            or "readme.md" in self.code_index._file_map,
            "sample_files": list(self.code_index._file_map.keys())[:10],  # First 10 files
        }

    def _fallback_intent(self, request: str) -> ParsedIntent:
        """Create a fallback intent when LLM fails."""
        return ParsedIntent(
            request_type=RequestType.COMPLEX,
            confidence="low",
            file_paths=self._extract_file_paths(request),
            search_terms=[],
            operations=[],
            raw_request=request,
            tasks=None,
        )

    def _extract_file_paths(self, request: str) -> List[str]:
        """Simple file path extraction as fallback."""
        import re

        pattern = r'@([\w\-./]+\.[\w]+)|(?:["\'`])([\w\-./]+\.[\w]+)(?:["\'`])'
        matches = re.findall(pattern, request)
        paths = []
        for match in matches:
            for path in match:
                if path:
                    paths.append(path)
        return paths

    def generate_simple_tasks(self, intent: ParsedIntent) -> Optional[List[dict]]:
        """Use the tasks from LLM analysis or generate based on intent."""
        # If LLM provided tasks, use them
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
