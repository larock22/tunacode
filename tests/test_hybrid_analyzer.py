"""
Comprehensive tests for the hybrid request analyzer.

Tests regex patterns with 30-40 common phrases to ensure no regressions.
"""

import pytest
import asyncio
from typing import List, Tuple

from tunacode.core.analysis.hybrid_request_analyzer import (
    HybridRequestAnalyzer, RequestType, ParsedIntent
)


# Test cases: (request, expected_type, expected_confidence, expected_files, expected_search_terms)
PATTERN_TEST_CASES: List[Tuple[str, RequestType, str, List[str], List[str]]] = [
    # File + operation patterns
    ("@CAPABILITIES.md summarize this file", RequestType.EXPLAIN_CODE, "high", ["CAPABILITIES.md"], []),
    ("@README.md explain", RequestType.EXPLAIN_CODE, "high", ["README.md"], []),
    ("@src/main.py analyze", RequestType.EXPLAIN_CODE, "high", ["src/main.py"], []),
    ("@package.json describe the dependencies", RequestType.EXPLAIN_CODE, "high", ["package.json"], []),
    
    # Simple read patterns
    ("read file.txt", RequestType.READ_FILE, "high", ["file.txt"], []),
    ("show README.md", RequestType.READ_FILE, "high", ["README.md"], []),
    ("view @config.json", RequestType.READ_FILE, "high", ["config.json"], []),
    ("cat main.py", RequestType.READ_FILE, "high", ["main.py"], []),
    
    # TODO/FIXME patterns
    ("find all TODO comments", RequestType.SEARCH_CODE, "high", [], ["TODO"]),
    ("search for TODOs", RequestType.SEARCH_CODE, "high", [], ["TODO"]),
    ("show FIXME", RequestType.SEARCH_CODE, "high", [], ["FIXME"]),
    ("find the XXX comments", RequestType.SEARCH_CODE, "high", [], ["XXX"]),
    ("search HACK", RequestType.SEARCH_CODE, "high", [], ["HACK"]),
    
    # General search patterns
    ('find "authentication"', RequestType.SEARCH_CODE, "high", [], ["authentication"]),
    ("search for 'logger'", RequestType.SEARCH_CODE, "high", [], ["logger"]),
    ("grep handleRequest", RequestType.SEARCH_CODE, "high", [], ["handleRequest"]),
    ("find parseJSON", RequestType.SEARCH_CODE, "high", [], ["parseJSON"]),
    
    # Edge cases that should fall through to LLM
    ("refactor the authentication system", RequestType.COMPLEX, "low", [], []),
    ("implement a new feature", RequestType.COMPLEX, "low", [], []),
    ("fix the bug in user module", RequestType.COMPLEX, "low", [], []),
    ("create tests for the API", RequestType.COMPLEX, "low", [], []),
    
    # Mixed patterns
    ("summarize @docs/api.md and explain the endpoints", RequestType.EXPLAIN_CODE, "high", ["docs/api.md"], []),
    ("@test.py summarize", RequestType.EXPLAIN_CODE, "high", ["test.py"], []),
    
    # More read variations
    ("read src/utils.js", RequestType.READ_FILE, "high", ["src/utils.js"], []),
    ("show the contents of data.csv", RequestType.READ_FILE, "high", ["data.csv"], []),
    ("view @components/Header.tsx", RequestType.READ_FILE, "high", ["components/Header.tsx"], []),
    
    # Search variations
    ("find for TODO", RequestType.SEARCH_CODE, "high", [], ["TODO"]),
    ("search 'config'", RequestType.SEARCH_CODE, "high", [], ["config"]),
    ("grep for errors", RequestType.SEARCH_CODE, "high", [], ["errors"]),
    
    # Case sensitivity tests
    ("FIND todo COMMENTS", RequestType.SEARCH_CODE, "high", [], ["TODO"]),
    ("Search FIXME", RequestType.SEARCH_CODE, "high", [], ["FIXME"]),
    ("READ main.py", RequestType.READ_FILE, "high", ["main.py"], []),
    
    # Whitespace handling
    ("  read   file.txt  ", RequestType.READ_FILE, "high", ["file.txt"], []),
    ("find   TODO", RequestType.SEARCH_CODE, "high", [], ["TODO"]),
    
    # Special characters in filenames
    ("read my-file.txt", RequestType.READ_FILE, "high", ["my-file.txt"], []),
    ("show test_module.py", RequestType.READ_FILE, "high", ["test_module.py"], []),
    ("@app.config.js analyze", RequestType.EXPLAIN_CODE, "high", ["app.config.js"], []),
]


class TestHybridAnalyzer:
    """Test the hybrid request analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an analyzer instance with mocked LLM."""
        analyzer = HybridRequestAnalyzer()
        
        # Mock the LLM analyze method to avoid API calls
        async def mock_llm_analyze(request):
            return ParsedIntent(
                request_type=RequestType.COMPLEX,
                confidence="low",
                file_paths=analyzer._extract_file_paths(request),
                search_terms=[],
                operations=[],
                raw_request=request,
                tasks=None
            )
        
        analyzer._llm_analyze = mock_llm_analyze
        return analyzer
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_request,expected_type,expected_confidence,expected_files,expected_search_terms", PATTERN_TEST_CASES)
    async def test_pattern_matching(self, analyzer, test_request, expected_type, expected_confidence, expected_files, expected_search_terms):
        """Test pattern matching for various requests."""
        # Analyze the request
        intent = await analyzer.analyze(test_request)
        
        # Check results
        assert intent.request_type == expected_type, f"Request '{test_request}' should be {expected_type}, got {intent.request_type}"
        assert intent.confidence == expected_confidence, f"Request '{test_request}' should have {expected_confidence} confidence, got {intent.confidence}"
        assert sorted(intent.file_paths) == sorted(expected_files), f"Request '{test_request}' should extract files {expected_files}, got {intent.file_paths}"
        assert sorted(intent.search_terms) == sorted(expected_search_terms), f"Request '{test_request}' should extract search terms {expected_search_terms}, got {intent.search_terms}"
    
    @pytest.mark.asyncio
    async def test_task_generation(self, analyzer):
        """Test that appropriate tasks are generated."""
        # Test file + operation
        intent = await analyzer.analyze("@README.md summarize")
        assert len(intent.tasks) == 2
        assert intent.tasks[0]["tool"] == "read_file"
        assert intent.tasks[0]["args"]["file_path"] == "README.md"
        assert intent.tasks[1]["tool"] == "analyze"
        
        # Test simple read
        intent = await analyzer.analyze("read config.json")
        assert len(intent.tasks) == 1
        assert intent.tasks[0]["tool"] == "read_file"
        assert intent.tasks[0]["args"]["file_path"] == "config.json"
        
        # Test search
        intent = await analyzer.analyze("find TODO")
        assert len(intent.tasks) == 1
        assert intent.tasks[0]["tool"] == "grep"
        assert "TODO" in intent.tasks[0]["args"]["pattern"]
    
    @pytest.mark.asyncio
    async def test_search_pattern_building(self, analyzer):
        """Test search pattern building for different term lengths."""
        # Short term should get word boundaries
        pattern = analyzer._build_search_pattern("id")
        assert pattern == "\\bid\\b"
        
        # Longer term should be escaped as-is
        pattern = analyzer._build_search_pattern("authentication")
        assert pattern == "authentication"
        
        # Special characters should be escaped
        pattern = analyzer._build_search_pattern("foo.bar")
        assert pattern == "foo\\.bar"
    
    @pytest.mark.asyncio
    async def test_file_path_extraction(self, analyzer):
        """Test file path extraction fallback."""
        paths = analyzer._extract_file_paths('Check @file1.txt and "file2.py" and `file3.js`')
        assert sorted(paths) == ["file1.txt", "file2.py", "file3.js"]
    
    @pytest.mark.asyncio
    async def test_complex_request_fallback(self, analyzer):
        """Test that complex requests fall back to LLM analysis."""
        # Override _llm_analyze to return a predictable result
        async def mock_llm_analyze(request):
            return ParsedIntent(
                request_type=RequestType.COMPLEX,
                confidence="low",
                file_paths=[],
                search_terms=[],
                operations=[],
                raw_request=request,
                tasks=None
            )
        
        analyzer._llm_analyze = mock_llm_analyze
        
        intent = await analyzer.analyze("refactor the entire authentication system to use OAuth2")
        assert intent.request_type == RequestType.COMPLEX
        assert intent.confidence == "low"
        assert intent.tasks is None  # No tasks for fallback


def test_sync_wrapper():
    """Test running async tests in sync context."""
    test = TestHybridAnalyzer()
    analyzer = HybridRequestAnalyzer()
    
    # Run a few critical tests synchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test the most important pattern
        intent = loop.run_until_complete(
            analyzer.analyze("@CAPABILITIES.md summarize this file")
        )
        assert intent.request_type == RequestType.EXPLAIN_CODE
        assert intent.confidence == "high"
        assert intent.file_paths == ["CAPABILITIES.md"]
        print("✓ Core pattern test passed")
        
    finally:
        loop.close()


if __name__ == "__main__":
    # Run the sync test
    test_sync_wrapper()
    
    # Run all tests with pytest
    pytest.main([__file__, "-v"])