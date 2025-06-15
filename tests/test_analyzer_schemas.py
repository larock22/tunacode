"""
Tests for analyzer schemas and validation.
"""

import pytest
from pydantic import ValidationError

from tunacode.core.analysis.schemas import TaskSchema, LLMAnalysisResponse


class TestSchemas:
    """Test Pydantic schemas for the analyzer."""
    
    def test_task_schema_valid(self):
        """Test valid task schema."""
        task = TaskSchema(
            id=1,
            description="Read file",
            tool="read_file",
            args={"file_path": "test.py"}
        )
        assert task.id == 1
        assert task.tool == "read_file"
    
    def test_task_schema_invalid_tool(self):
        """Test invalid tool name."""
        with pytest.raises(ValidationError) as exc_info:
            TaskSchema(
                id=1,
                description="Invalid tool",
                tool="invalid_tool",
                args={}
            )
        assert "Invalid tool" in str(exc_info.value)
    
    def test_llm_response_valid(self):
        """Test valid LLM response."""
        response = LLMAnalysisResponse(
            request_type="read_file",
            confidence="high",
            file_paths=["test.py"],
            search_terms=[],
            operations=["read"],
            tasks=[
                {
                    "id": 1,
                    "description": "Read test.py",
                    "tool": "read_file",
                    "args": {"file_path": "test.py"}
                }
            ]
        )
        assert response.request_type == "read_file"
        assert len(response.tasks) == 1
        assert isinstance(response.tasks[0], TaskSchema)
    
    def test_llm_response_invalid_request_type(self):
        """Test invalid request type."""
        with pytest.raises(ValidationError) as exc_info:
            LLMAnalysisResponse(
                request_type="invalid_type",
                confidence="high"
            )
        assert "request_type" in str(exc_info.value)
    
    def test_llm_response_invalid_confidence(self):
        """Test invalid confidence level."""
        with pytest.raises(ValidationError) as exc_info:
            LLMAnalysisResponse(
                request_type="read_file",
                confidence="very_high"  # Should be high/medium/low
            )
        assert "confidence" in str(exc_info.value)
    
    def test_llm_response_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError) as exc_info:
            LLMAnalysisResponse(
                request_type="read_file",
                confidence="high",
                extra_field="not allowed"
            )
        assert "extra" in str(exc_info.value).lower()
    
    def test_llm_response_malformed_json_examples(self):
        """Test common malformed JSON scenarios."""
        # Missing required fields
        with pytest.raises(ValidationError):
            LLMAnalysisResponse(confidence="high")  # Missing request_type
        
        # Wrong types
        with pytest.raises(ValidationError):
            LLMAnalysisResponse(
                request_type="read_file",
                confidence="high",
                file_paths="not_a_list"  # Should be a list
            )
        
        # Invalid task structure
        with pytest.raises(ValidationError):
            LLMAnalysisResponse(
                request_type="read_file",
                confidence="high",
                tasks=[{"description": "Missing required fields"}]  # Missing id and tool
            )