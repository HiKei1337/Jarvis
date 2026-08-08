"""Tests for JARVIS Tool Registry

Run with: python -m pytest tests/test_tool_registry.py -v
Or: python tests/test_tool_registry.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tool_registry import ToolRegistry, Tool, ToolNotFoundError, DuplicateToolError, ToolValidationError


class TestToolRegistry:
    """Test suite for ToolRegistry."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()
        
        def sample_execute(x, y):
            return f"executed with x={x}, y={y}"
        
        self.sample_tool = Tool(
            name="test_tool",
            description="A test tool",
            schema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                },
                "required": ["x", "y"],
            },
            risk_level=2,
            execute=sample_execute
        )
    
    def test_create_registry(self):
        """Test 1: Create registry."""
        assert self.registry is not None
        print("PASS: Created ToolRegistry")
    
    def test_register_tool(self):
        """Test 2: Register a tool."""
        self.registry.register(self.sample_tool)
        assert self.registry.has_tool("test_tool")
        print("PASS: Registered tool")
    
    def test_get_tool(self):
        """Test 3: Get tool by name."""
        self.registry.register(self.sample_tool)
        retrieved = self.registry.get("test_tool")
        assert retrieved.name == "test_tool"
        print("PASS: Retrieved tool by name")
    
    def test_list_tools(self):
        """Test 4: List tools."""
        self.registry.register(self.sample_tool)
        tools_list = self.registry.list_tools()
        assert len(tools_list) == 1
        assert tools_list[0]["name"] == "test_tool"
        print("PASS: Listed tools")
    
    def test_execute_tool(self):
        """Test 5: Execute tool."""
        self.registry.register(self.sample_tool)
        result = self.registry.execute("test_tool", {"x": 10, "y": 20})
        assert result == "executed with x=10, y=20"
        print("PASS: Executed tool")
    
    def test_duplicate_registration(self):
        """Test 6: Duplicate registration raises error."""
        self.registry.register(self.sample_tool)
        try:
            self.registry.register(self.sample_tool)
            assert False, "Should have raised DuplicateToolError"
        except DuplicateToolError:
            print("PASS: DuplicateToolError raised correctly")
    
    def test_unknown_tool(self):
        """Test 7: Unknown tool raises error."""
        try:
            self.registry.execute("unknown_tool")
            assert False, "Should have raised ToolNotFoundError"
        except ToolNotFoundError:
            print("PASS: ToolNotFoundError raised correctly")
    
    def test_validation_missing_arg(self):
        """Test 8: Validation error for missing required argument."""
        self.registry.register(self.sample_tool)
        try:
            self.registry.execute("test_tool", {"x": 10})
            assert False, "Should have raised ToolValidationError"
        except ToolValidationError as e:
            assert "required" in str(e).lower() or "missing" in str(e).lower()
            print("PASS: ToolValidationError raised for missing argument")
    
    def test_has_tool(self):
        """Test 9: has_tool method."""
        self.registry.register(self.sample_tool)
        assert self.registry.has_tool("test_tool") == True
        assert self.registry.has_tool("nonexistent") == False
        print("PASS: has_tool works correctly")
    
    def test_unregister(self):
        """Test 10: Unregister tool."""
        self.registry.register(self.sample_tool)
        assert self.registry.unregister("test_tool") == True
        assert self.registry.unregister("test_tool") == False
        assert self.registry.has_tool("test_tool") == False
        print("PASS: unregister works correctly")


if __name__ == "__main__":
    # Run tests manually if pytest not available
    test_suite = TestToolRegistry()
    
    print("=== Tool Registry Tests ===\n")
    
    test_suite.setup_method()
    test_suite.test_create_registry()
    
    test_suite.setup_method()
    test_suite.test_register_tool()
    
    test_suite.setup_method()
    test_suite.test_get_tool()
    
    test_suite.setup_method()
    test_suite.test_list_tools()
    
    test_suite.setup_method()
    test_suite.test_execute_tool()
    
    test_suite.setup_method()
    test_suite.test_duplicate_registration()
    
    test_suite.setup_method()
    test_suite.test_unknown_tool()
    
    test_suite.setup_method()
    test_suite.test_validation_missing_arg()
    
    test_suite.setup_method()
    test_suite.test_has_tool()
    
    test_suite.setup_method()
    test_suite.test_unregister()
    
    print("\n=== All tests passed ===")
