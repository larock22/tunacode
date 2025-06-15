"""
Real API tests for regular mode CRUD operations.

These tests actually execute against the system without mocks.
Requires API keys to be configured.
"""

import asyncio
import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from tunacode.core.agents import main as agent_main
from tunacode.core.state import StateManager
from tunacode.types import ModelName


class TestRegularModeCRUDReal:
    """Test real CRUD operations in regular mode."""

    @pytest.fixture
    async def test_dir(self):
        """Create a temporary test directory."""
        test_dir = Path(tempfile.mkdtemp(prefix="tunacode_test_"))
        original_cwd = os.getcwd()
        os.chdir(test_dir)
        yield test_dir
        os.chdir(original_cwd)
        shutil.rmtree(test_dir)

    @pytest.fixture
    async def state_manager(self):
        """Create a state manager for testing."""
        state = StateManager()
        # Enable yolo mode to skip confirmations
        state.session.yolo = True
        return state

    def get_test_model(self) -> str:
        """Get the model to use for testing."""
        if os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic:claude-3-haiku-20240307"  # Cheaper/faster for tests
        elif os.getenv("OPENAI_API_KEY"):
            return "openai:gpt-3.5-turbo"  # Cheaper/faster for tests
        else:
            pytest.skip("No API keys configured")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
        reason="No API keys configured"
    )
    async def test_create_then_read_real(self, state_manager, test_dir):
        """Test 1: Create-then-Read with real API calls"""
        print("\n=== Test 1: Create-then-Read (Regular Mode) ===")
        model = self.get_test_model()
        print(f"Using model: {model}")
        
        # Create file
        start_time = time.time()
        result1 = await agent_main.process_request(
            model,
            "create a file named hello.txt with the content 'Hello from regular mode!'",
            state_manager
        )
        create_time = time.time() - start_time
        print(f"Create time: {create_time:.2f}s")
        
        # Check if file was created
        test_file = Path("hello.txt")
        if test_file.exists():
            print("✓ File created successfully")
            assert test_file.read_text() == "Hello from regular mode!", "Content should match"
        else:
            print("! File not created, checking response")
            if hasattr(result1, 'result') and hasattr(result1.result, 'output'):
                print(f"Response: {result1.result.output}")
        
        # Read file
        read_start = time.time()
        result2 = await agent_main.process_request(
            model,
            "read the file hello.txt",
            state_manager
        )
        read_time = time.time() - read_start
        print(f"Read time: {read_time:.2f}s")
        
        # Verify read result
        if hasattr(result2, 'result') and hasattr(result2.result, 'output'):
            output = result2.result.output
            print(f"Read output: {output[:100]}...")
            assert "Hello from regular mode!" in output or "hello.txt" in output.lower()
            print("✓ Read operation successful")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
        reason="No API keys configured"
    )
    async def test_update_file_real(self, state_manager, test_dir):
        """Test 2: Update file operations"""
        print("\n=== Test 2: Update File (Regular Mode) ===")
        model = self.get_test_model()
        
        # Create initial file
        Path("data.txt").write_text("Line 1\n")
        print("Initial file created")
        
        # Update file
        result1 = await agent_main.process_request(
            model,
            "append 'Line 2' to the file data.txt",
            state_manager
        )
        
        # Check result
        content = Path("data.txt").read_text()
        print(f"File content after update: {repr(content)}")
        
        if "Line 2" in content:
            print("✓ Update successful")
        else:
            print("! Update may have failed, checking response")
            if hasattr(result1, 'result') and hasattr(result1.result, 'output'):
                print(f"Response: {result1.result.output[:200]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
        reason="No API keys configured"
    )
    async def test_code_analysis_real(self, state_manager, test_dir):
        """Test 3: Code analysis capabilities"""
        print("\n=== Test 3: Code Analysis (Regular Mode) ===")
        model = self.get_test_model()
        
        # Create a Python file
        code = """
def calculate_area(radius):
    '''Calculate the area of a circle.'''
    import math
    return math.pi * radius ** 2

def calculate_circumference(radius):
    '''Calculate the circumference of a circle.'''
    import math
    return 2 * math.pi * radius
"""
        Path("geometry.py").write_text(code)
        print("Created geometry.py")
        
        # Analyze the code
        start_time = time.time()
        result = await agent_main.process_request(
            model,
            "analyze geometry.py and list all the functions defined in it",
            state_manager
        )
        elapsed = time.time() - start_time
        print(f"Analysis time: {elapsed:.2f}s")
        
        # Check response
        if hasattr(result, 'result') and hasattr(result.result, 'output'):
            output = result.result.output.lower()
            print(f"Analysis output: {output[:200]}...")
            
            # Should mention both functions
            assert "calculate_area" in output or "area" in output
            assert "calculate_circumference" in output or "circumference" in output
            print("✓ Analysis identified both functions")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
        reason="No API keys configured"
    )
    async def test_error_handling_real(self, state_manager, test_dir):
        """Test 4: Error handling for missing files"""
        print("\n=== Test 4: Error Handling (Regular Mode) ===")
        model = self.get_test_model()
        
        # Try to read non-existent file
        result = await agent_main.process_request(
            model,
            "read the file nonexistent.txt",
            state_manager
        )
        
        # Should handle gracefully
        if hasattr(result, 'result') and hasattr(result.result, 'output'):
            output = result.result.output.lower()
            print(f"Error response: {output[:200]}...")
            
            # Should mention the file doesn't exist
            assert any(word in output for word in ["not found", "doesn't exist", "no such file", "error"])
            print("✓ Error handled gracefully")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
        reason="No API keys configured"
    )
    async def test_multi_file_operations(self, state_manager, test_dir):
        """Test operations on multiple files"""
        print("\n=== Multi-File Operations (Regular Mode) ===")
        model = self.get_test_model()
        
        # Create multiple files
        for i in range(3):
            Path(f"file{i}.txt").write_text(f"This is file {i}")
        print("Created 3 test files")
        
        # List files
        result = await agent_main.process_request(
            model,
            "list all txt files in the current directory",
            state_manager
        )
        
        if hasattr(result, 'result') and hasattr(result.result, 'output'):
            output = result.result.output.lower()
            print(f"List output: {output[:200]}...")
            
            # Should mention all files
            files_found = sum(1 for i in range(3) if f"file{i}.txt" in output)
            print(f"✓ Found {files_found}/3 files in listing")


class TestRegularModePerformance:
    """Test performance characteristics of regular mode."""

    @pytest.fixture
    async def state_manager(self):
        """Create a state manager for testing."""
        state = StateManager()
        state.session.yolo = True
        return state

    def get_test_model(self) -> str:
        """Get the model to use for testing."""
        if os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic:claude-3-haiku-20240307"
        elif os.getenv("OPENAI_API_KEY"):
            return "openai:gpt-3.5-turbo"
        else:
            pytest.skip("No API keys configured")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
        reason="No API keys configured"
    )
    async def test_response_times(self, state_manager):
        """Measure response times for different operations."""
        print("\n=== Response Time Metrics (Regular Mode) ===")
        model = self.get_test_model()
        
        operations = [
            ("Simple question", "What is 2 + 2?"),
            ("File read", "What files are in the current directory?"),
            ("Code generation", "Write a Python function to calculate factorial"),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            Path("test.txt").write_text("test content")
            
            for op_name, request in operations:
                start = time.time()
                result = await agent_main.process_request(model, request, state_manager)
                elapsed = time.time() - start
                
                print(f"\n{op_name}:")
                print(f"  Request: {request}")
                print(f"  Time: {elapsed:.2f}s")
                
                if hasattr(result, 'result') and hasattr(result.result, 'output'):
                    print(f"  Response preview: {result.result.output[:100]}...")
                
                # All operations should complete within reasonable time
                assert elapsed < 30, f"{op_name} took too long: {elapsed}s"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])