"""
Pydantic schemas for request analysis validation.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskSchema(BaseModel):
    """Schema for a single task."""

    id: int = Field(..., description="Task ID")
    description: str = Field(..., description="Task description")
    tool: str = Field(..., description="Tool to use")
    args: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    mutate: bool = Field(default=False, description="True if task modifies files/system")

    @field_validator("tool")
    def validate_tool(cls, v):
        valid_tools = {
            "read_file",
            "write_file",
            "update_file",
            "list_dir",
            "grep",
            "bash",
            "run_command",
            "analyze",
        }
        if v not in valid_tools:
            raise ValueError(f"Invalid tool: {v}. Must be one of {valid_tools}")
        return v


class LLMAnalysisResponse(BaseModel):
    """Schema for LLM analysis response."""

    request_type: Literal[
        "read_file",
        "write_file",
        "update_file",
        "search_code",
        "explain_code",
        "analyze_codebase",
        "run_command",
        "complex",
    ] = Field(..., description="Type of request")

    confidence: Literal["high", "medium", "low"] = Field(..., description="Confidence level")

    file_paths: List[str] = Field(default_factory=list, description="Extracted file paths")

    search_terms: List[str] = Field(default_factory=list, description="Search terms")

    operations: List[str] = Field(default_factory=list, description="Operations to perform")

    tasks: Optional[List[TaskSchema]] = Field(None, description="Generated tasks")

    @field_validator("tasks", mode="before")
    def validate_tasks(cls, v):
        if v is None:
            return v
        # Convert dict tasks to TaskSchema
        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
            return [TaskSchema(**task) for task in v]
        return v

    model_config = ConfigDict(extra="forbid")  # No extra fields allowed
