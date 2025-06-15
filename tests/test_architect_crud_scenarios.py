"""
Test the four critical CRUD scenarios for architect mode.

These tests verify the end-to-end functionality of architect mode:
1. Create-then-Read (Happy Path)
2. Update-with-Diff (Idempotent Modification)
3. Read-Then-Summarize (Hybrid Fallback Trigger)
4. Delete-and-Gracefully-Fail Read (Clean-Up / D)
"""

import asyncio
import os
import tempfile
import time
from pathlib import Path

import pytest

from tunacode.core.agents.adaptive_orchestrator import AdaptiveOrchestrator
from tunacode.core.state import StateManager


class TestArchitectCRUD:
    """Test critical CRUD operations in architect mode."""

    @pytest.fixture
    async def orchestrator(self):
        """Create an orchestrator instance for testing."""
        state_manager = StateManager()
        orchestrator = AdaptiveOrchestrator(state_manager)
        yield orchestrator
        # Cleanup any created files
        test_file = Path("notes/hello.txt")
        if test_file.exists():
            test_file.unlink()
        if test_file.parent.exists():
            test_file.parent.rmdir()

    @pytest.mark.asyncio
    async def test_create_then_read_happy_path(self, orchestrator):
        """Test 1: Create-then-Read (Happy Path)"""
        start_time = time.time()

        # Create file
        create_result = await orchestrator.run("create notes/hello.txt with content 'hi world'")
        create_time = time.time() - start_time

        # Verify file was created
        test_file = Path("notes/hello.txt")
        assert test_file.exists(), "File should be created"
        assert test_file.read_text() == "hi world", "Content should match"

        # Read file
        read_start = time.time()
        read_result = await orchestrator.run("show notes/hello.txt")
        read_time = time.time() - read_start

        # Verify timing (should be fast via regex)
        assert create_time < 2.0, f"Create should be fast, took {create_time}s"
        assert read_time < 0.5, f"Read should be very fast, took {read_time}s"

        # Verify results have output
        assert len(create_result) > 0, "Create should return results"
        assert len(read_result) > 0, "Read should return results"

        # Check the analyzer used regex path (high confidence)
        analyzer_result = await orchestrator.analyzer.analyze("show notes/hello.txt")
        assert analyzer_result.confidence == "high", "Should use regex pattern"

    @pytest.mark.asyncio
    async def test_update_with_diff_idempotent(self, orchestrator):
        """Test 2: Update-with-Diff (Idempotent Modification)"""
        # First create a file
        await orchestrator.run("create notes/hello.txt with content 'hi world'")
        
        # Append content first time
        result1 = await orchestrator.run("append 'foo' to notes/hello.txt")
        content1 = Path("notes/hello.txt").read_text()
        
        # Append same content second time
        result2 = await orchestrator.run("append 'foo' to notes/hello.txt")
        content2 = Path("notes/hello.txt").read_text()
        
        # Verify first append worked
        assert "foo" in content1, "First append should add content"
        
        # Verify idempotency (content grows each time for append)
        # But we should see both operations complete
        assert len(result1) > 0, "First append should have results"
        assert len(result2) > 0, "Second append should have results"
        
        # Note: append is not idempotent by design, it adds each time
        assert content2.count("foo") == 2, "Append should add content each time"

    @pytest.mark.asyncio
    async def test_read_then_summarize_hybrid_fallback(self, orchestrator):
        """Test 3: Read-Then-Summarize (Hybrid Fallback Trigger)"""
        # Create a file first
        await orchestrator.run("create notes/hello.txt with content 'This is a test file with some content to summarize.'")
        
        # Use conversational phrasing that should trigger LLM fallback
        start_time = time.time()
        result = await orchestrator.run("@notes/hello.txt could you summarize this file for me?")
        elapsed = time.time() - start_time
        
        # Should still complete reasonably fast even with LLM
        assert elapsed < 5.0, f"Should complete within 5s, took {elapsed}s"
        
        # Should have results
        assert len(result) > 0, "Should return summary results"
        
        # Verify the analyzer detects this as EXPLAIN_CODE
        intent = await orchestrator.analyzer.analyze("@notes/hello.txt could you summarize this file for me?")
        assert intent.request_type.value in ["explain_code", "complex"], f"Should recognize as explain or complex, got {intent.request_type.value}"

    @pytest.mark.asyncio
    async def test_delete_and_gracefully_fail_read(self, orchestrator):
        """Test 4: Delete-and-Gracefully-Fail Read (Clean-Up / D)"""
        # Create file first
        await orchestrator.run("create notes/hello.txt with content 'temporary file'")
        assert Path("notes/hello.txt").exists(), "File should exist initially"
        
        # Delete file
        delete_result = await orchestrator.run("delete notes/hello.txt")
        assert not Path("notes/hello.txt").exists(), "File should be deleted"
        assert len(delete_result) > 0, "Delete should return results"
        
        # Try to read deleted file
        read_result = await orchestrator.run("show notes/hello.txt")
        
        # Should handle gracefully without exceptions
        # The orchestrator may return empty results or an error message
        # but should not crash
        assert isinstance(read_result, list), "Should return a list even on error"
        
        # The analyzer should still parse the request correctly
        intent = await orchestrator.analyzer.analyze("show notes/hello.txt")
        assert intent.request_type.value == "read_file", "Should still recognize as read request"
        assert intent.confidence == "high", "Should have high confidence even if file doesn't exist"


class TestArchitectAnalyzerMetrics:
    """Test analyzer path selection and metrics."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for metrics testing."""
        state_manager = StateManager()
        return AdaptiveOrchestrator(state_manager)

    @pytest.mark.asyncio
    async def test_regex_vs_llm_path_detection(self, orchestrator):
        """Verify which analyzer path is used for different requests."""
        test_cases = [
            # (request, expected_confidence, description)
            ("show file.txt", "high", "Simple read should use regex"),
            ("create test.py with content 'print()'", "low", "Create pattern needs LLM"),
            ("find TODO", "high", "Search pattern should use regex"),
            ("@README.md summarize", "high", "File+operation should use regex"),
            ("refactor the authentication system", "low", "Complex request needs LLM"),
            ("could you please help me understand what this code does?", "low", "Conversational needs LLM"),
        ]
        
        metrics = []
        for request, expected_confidence, description in test_cases:
            start = time.time()
            intent = await orchestrator.analyzer.analyze(request)
            elapsed = time.time() - start
            
            metrics.append({
                "request": request,
                "confidence": intent.confidence,
                "expected": expected_confidence,
                "time_ms": elapsed * 1000,
                "description": description,
                "request_type": intent.request_type.value,
            })
            
            # High confidence = regex path (fast)
            # Low confidence = LLM path (slower)
            if expected_confidence == "high":
                assert elapsed < 0.01, f"Regex path should be <10ms, got {elapsed*1000}ms for: {request}"
        
        # Print metrics summary
        print("\nAnalyzer Path Metrics:")
        print("-" * 80)
        for m in metrics:
            status = "✓" if m["confidence"] == m["expected"] else "✗"
            print(f"{status} {m['description']}")
            print(f"   Request: {m['request'][:50]}...")
            print(f"   Type: {m['request_type']}, Confidence: {m['confidence']}, Time: {m['time_ms']:.1f}ms")
        
        # Verify expectations
        for m in metrics:
            assert m["confidence"] == m["expected"], f"Failed for: {m['description']}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])