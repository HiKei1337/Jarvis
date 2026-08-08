"""JARVIS Tool Registry

Provides a simple, extensible registry for computer control tools.
Tools can be registered, validated, and executed through a unified interface.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from core.exceptions import (
    ToolNotFoundError,
    ToolValidationError,
    ToolExecutionError,
    DuplicateToolError,
)


@dataclass
class Tool:
    """Represents a single tool in the registry.
    
    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description of what the tool does
        schema: Dictionary describing required and optional arguments
        risk_level: Risk level 0-5 (0=safe, 5=dangerous)
        execute: Function that performs the tool's action
    """
    name: str
    description: str
    schema: Dict[str, Any] = field(default_factory=dict)
    risk_level: int = 1
    execute: Optional[Callable[..., Any]] = None
    
    def validate(self, args: Dict[str, Any]) -> bool:
        """Validate arguments against the tool's schema.
        
        Args:
            args: Dictionary of arguments to validate
            
        Returns:
            True if validation passes
            
        Raises:
            ToolValidationError: If validation fails
        """
        required = self.schema.get("required", [])
        properties = self.schema.get("properties", {})
        
        # Check required fields
        for field_name in required:
            if field_name not in args or args[field_name] is None:
                raise ToolValidationError(
                    self.name,
                    f"missing required argument '{field_name}'"
                )
        
        # Check types if specified
        for field_name, field_def in properties.items():
            if field_name in args and args[field_name] is not None:
                expected_type = field_def.get("type")
                value = args[field_name]
                
                if expected_type == "string" and not isinstance(value, str):
                    raise ToolValidationError(
                        self.name,
                        f"argument '{field_name}' must be a string"
                    )
                elif expected_type == "integer" and not isinstance(value, int):
                    raise ToolValidationError(
                        self.name,
                        f"argument '{field_name}' must be an integer"
                    )
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    raise ToolValidationError(
                        self.name,
                        f"argument '{field_name}' must be a number"
                    )
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise ToolValidationError(
                        self.name,
                        f"argument '{field_name}' must be a boolean"
                    )
        
        return True


class ToolRegistry:
    """Registry for managing and executing computer control tools.
    
    The registry provides:
    - Tool registration with unique names
    - Argument validation based on schemas
    - Risk level tracking
    - Unified execution interface
    """
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a new tool in the registry.
        
        Args:
            tool: Tool instance to register
            
        Raises:
            DuplicateToolError: If a tool with the same name already exists
        """
        if tool.name in self._tools:
            raise DuplicateToolError(tool.name)
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> bool:
        """Remove a tool from the registry.
        
        Args:
            name: Name of the tool to remove
            
        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False
    
    def get(self, name: str) -> Tool:
        """Get a tool by name.
        
        Args:
            name: Name of the tool to retrieve
            
        Returns:
            Tool instance
            
        Raises:
            ToolNotFoundError: If tool is not found
        """
        if name not in self._tools:
            raise ToolNotFoundError(name)
        return self._tools[name]
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with their metadata.
        
        Returns:
            List of dictionaries containing tool information
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "schema": tool.schema,
                "risk_level": tool.risk_level,
            }
            for tool in self._tools.values()
        ]
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered.
        
        Args:
            name: Name of the tool to check
            
        Returns:
            True if tool exists, False otherwise
        """
        return name in self._tools
    
    def execute(self, name: str, args: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a tool with the given arguments.
        
        Args:
            name: Name of the tool to execute
            args: Dictionary of arguments to pass to the tool
            
        Returns:
            Result of tool execution
            
        Raises:
            ToolNotFoundError: If tool is not found
            ToolValidationError: If arguments fail validation
            ToolExecutionError: If execution fails
        """
        tool = self.get(name)
        
        # Validate arguments
        if args:
            tool.validate(args)
        
        # Execute
        try:
            if args:
                return tool.execute(**args)
            else:
                return tool.execute()
        except Exception as e:
            raise ToolExecutionError(name, str(e), original_error=e)
