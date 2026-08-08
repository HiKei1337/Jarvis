"""JARVIS Core Exceptions"""


class ToolRegistryError(Exception):
    """Base exception for tool registry errors."""
    pass


class ToolNotFoundError(ToolRegistryError):
    """Raised when a requested tool is not found in the registry."""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' not found in registry")


class ToolValidationError(ToolRegistryError):
    """Raised when tool arguments fail validation."""
    
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        self.message = message
        super().__init__(f"Tool '{tool_name}' validation error: {message}")


class ToolExecutionError(ToolRegistryError):
    """Raised when tool execution fails."""
    
    def __init__(self, tool_name: str, message: str, original_error: Exception = None):
        self.tool_name = tool_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' execution error: {message}")


class DuplicateToolError(ToolRegistryError):
    """Raised when attempting to register a tool with an already registered name."""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' is already registered")
