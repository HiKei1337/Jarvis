"""JARVIS Computer Use Tools

Provides computer control tools for the Tool Registry:
- mouse_move, mouse_click
- keyboard_type, keyboard_press
- scroll
- launch_app
"""

from typing import Dict, Any, Optional
from automation.keyboard import Keyboard
from automation.mouse import Mouse
from automation.windows import WindowManager


class ComputerUseTools:
    """Computer control tools for JARVIS.
    
    These tools provide basic computer interaction capabilities:
    - Mouse movement and clicking
    - Keyboard input
    - Screen scrolling
    - Application launching
    """
    
    def __init__(self, log_fn=None):
        """Initialize computer use tools.
        
        Args:
            log_fn: Optional logging function
        """
        self.keyboard = Keyboard()
        self.mouse = Mouse()
        self.wm = WindowManager()
        self.log_fn = log_fn
    
    def _log(self, message: str):
        """Log a message if logging is enabled."""
        if self.log_fn:
            self.log_fn(message)
    
    # Mouse tools
    
    def mouse_move(self, x: int, y: int) -> str:
        """Move mouse to specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Status message
        """
        self.mouse.move(x, y)
        self._log(f"mouse_move: ({x}, {y})")
        return f"переместил мышь в ({x}, {y})"
    
    def mouse_click(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        """Click mouse at specified coordinates or current position.
        
        Args:
            x: X coordinate (optional, clicks at current position if not provided)
            y: Y coordinate (optional, clicks at current position if not provided)
            
        Returns:
            Status message
        """
        if x is not None and y is not None:
            self.mouse.click(x, y)
            self._log(f"mouse_click: ({x}, {y})")
            return f"кликнул в ({x}, {y})"
        else:
            self.mouse.click()
            self._log("mouse_click: current position")
            return "выполнил клик"
    
    # Keyboard tools
    
    def keyboard_type(self, text: str, window: Optional[str] = None) -> str:
        """Type text into the active window or specified window.
        
        Args:
            text: Text to type
            window: Optional window title to activate first
            
        Returns:
            Status message
        """
        if window:
            if not self.wm.activate(window):
                return f"окно '{window}' не найдено"
            self._log(f"keyboard_type: activated '{window}'")
        
        self.keyboard.type_text(text)
        self._log(f"keyboard_type: '{text[:50]}...'")
        return "ввёл текст"
    
    def keyboard_press(self, combo: str) -> str:
        """Press a key or key combination.
        
        Args:
            combo: Key combination like "enter", "ctrl+c", "win+d"
            
        Returns:
            Status message
        """
        self.keyboard.press(combo)
        self._log(f"keyboard_press: {combo}")
        return f"нажал {combo}"
    
    # Scroll tool
    
    def scroll(self, value: int) -> str:
        """Scroll by the specified amount.
        
        Args:
            value: Number of scroll units (positive=up, negative=down)
            
        Returns:
            Status message
        """
        try:
            n = int(value)
        except (ValueError, TypeError):
            n = 3
        
        self.mouse.scroll(n)
        self._log(f"scroll: {n}")
        return "прокрутил"
    
    # Application launch tool
    
    def launch_app(self, command: str) -> str:
        """Launch an application or run a command.
        
        Args:
            command: Command to execute
            
        Returns:
            Status message
        """
        import subprocess
        import time
        
        from core.checker import Checker
        
        checker = Checker()
        value = command.strip()
        
        before = checker.titles()
        subprocess.Popen(value, shell=True)
        
        win = checker.wait_change(before, timeout=6)
        if not win:
            time.sleep(2)
            win = checker.wait_change(before, timeout=4)
        
        if win:
            self._log(f"launch_app: {value} (window: {win})")
            return f"запустил {value} (окно: {win})"
        
        self._log(f"launch_app: {value} (no window detected)")
        return f"запустил {value}, но окно не найдено"


def create_computer_use_tools(log_fn=None) -> Dict[str, Any]:
    """Create and return computer use tools for registry registration.
    
    Args:
        log_fn: Optional logging function
        
    Returns:
        Dictionary mapping tool names to Tool instances
    """
    from core.tool_registry import Tool
    
    tools_instance = ComputerUseTools(log_fn=log_fn)
    
    tools = {}
    
    # Mouse move tool
    tools["mouse_move"] = Tool(
        name="mouse_move",
        description="Move mouse to specified screen coordinates",
        schema={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate"},
                "y": {"type": "integer", "description": "Y coordinate"},
            },
            "required": ["x", "y"],
        },
        risk_level=2,
        execute=tools_instance.mouse_move,
    )
    
    # Mouse click tool
    tools["mouse_click"] = Tool(
        name="mouse_click",
        description="Click mouse at specified coordinates or current position",
        schema={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate (optional)"},
                "y": {"type": "integer", "description": "Y coordinate (optional)"},
            },
            "required": [],
        },
        risk_level=2,
        execute=tools_instance.mouse_click,
    )
    
    # Keyboard type tool
    tools["keyboard_type"] = Tool(
        name="keyboard_type",
        description="Type text into the active or specified window",
        schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to type"},
                "window": {"type": "string", "description": "Window title to activate (optional)"},
            },
            "required": ["text"],
        },
        risk_level=2,
        execute=tools_instance.keyboard_type,
    )
    
    # Keyboard press tool
    tools["keyboard_press"] = Tool(
        name="keyboard_press",
        description="Press a key or key combination",
        schema={
            "type": "object",
            "properties": {
                "combo": {"type": "string", "description": "Key combination like 'enter', 'ctrl+c'"},
            },
            "required": ["combo"],
        },
        risk_level=2,
        execute=tools_instance.keyboard_press,
    )
    
    # Scroll tool
    tools["scroll"] = Tool(
        name="scroll",
        description="Scroll by the specified amount",
        schema={
            "type": "object",
            "properties": {
                "value": {"type": "integer", "description": "Number of scroll units"},
            },
            "required": ["value"],
        },
        risk_level=1,
        execute=tools_instance.scroll,
    )
    
    # Launch app tool
    tools["launch_app"] = Tool(
        name="launch_app",
        description="Launch an application or run a command",
        schema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute"},
            },
            "required": ["command"],
        },
        risk_level=4,
        execute=tools_instance.launch_app,
    )
    
    return tools
