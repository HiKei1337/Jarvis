"""JARVIS Communication Tools

Provides communication tools for the Tool Registry:
- press (keyboard shortcuts)
- type (text input)
- type_think (AI-generated text input)
- click_see (vision-based click)
- chat (conversation)
"""

from typing import Dict, Any, Optional


class CommunicationTools:
    """Communication tools for JARVIS.
    
    These tools provide interaction capabilities:
    - Keyboard input
    - Vision-based clicking
    - Chat responses
    """
    
    def __init__(self, ai, vision, log_fn=None):
        """Initialize communication tools.
        
        Args:
            ai: LLM client for generating text
            vision: Vision module for screen analysis
            log_fn: Optional logging function
        """
        self.ai = ai
        self.vision = vision
        self.log_fn = log_fn
        
        # Import lazily
        self._keyboard = None
        self._mouse = None
        self._wm = None
    
    @property
    def keyboard(self):
        """Lazy load keyboard."""
        if self._keyboard is None:
            from automation.keyboard import Keyboard
            self._keyboard = Keyboard()
        return self._keyboard
    
    @property
    def mouse(self):
        """Lazy load mouse."""
        if self._mouse is None:
            from automation.mouse import Mouse
            self._mouse = Mouse()
        return self._mouse
    
    @property
    def wm(self):
        """Lazy load window manager."""
        if self._wm is None:
            from automation.windows import WindowManager
            self._wm = WindowManager()
        return self._wm
    
    def _log(self, message: str):
        """Log a message if logging is enabled."""
        if self.log_fn:
            self.log_fn(message)
    
    def press(self, combo: str) -> str:
        """Press a key or key combination.
        
        Args:
            combo: Key combination like "enter", "ctrl+c", "win+d"
            
        Returns:
            Status message
        """
        self.keyboard.press(combo)
        self._log(f"press: {combo}")
        return f"нажал {combo}"
    
    def type_text(self, text: str, window: Optional[str] = None) -> str:
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
            self._log(f"type: activated '{window}'")
        
        self.keyboard.type_text(text)
        self._log(f"type: '{text[:50]}...'")
        return "ввёл текст"
    
    def type_think(self, task: str, window: Optional[str] = None) -> str:
        """Generate text using AI and type it.
        
        Args:
            task: Task description for text generation
            window: Optional window title to activate first
            
        Returns:
            Status message
        """
        text = self.ai.ask_raw(
            f"Задание: {task}\n"
            "Верни ТОЛЬКО готовый текст, без вступлений и подписей.",
            timeout=60
        )
        
        if self._log:
            self._log(f"Сочинил: {text}")
        
        if window:
            if not self.wm.activate(window):
                return f"окно '{window}' не найдено"
        
        self.keyboard.type_text(text)
        self._log(f"type_think: '{text[:50]}...'")
        return f"сочинил и ввёл: {text[:60]}..."
    
    def click_see(self, target: str) -> str:
        """Find an object on screen by description and click it.
        
        Args:
            target: Description of the object to find and click
            
        Returns:
            Status message
        """
        coords = self.vision.find(target)
        
        if not coords:
            import time
            time.sleep(1.0)
            coords = self.vision.find(target)
        
        if not coords:
            self._log(f"click_see: не вижу '{target}'")
            return f"не вижу: {target}"
        
        self.mouse.click(*coords)
        self._log(f"click_see: кликнул '{target}' в {coords}")
        return f"кликнул {target}"
    
    def chat(self) -> str:
        """Placeholder for chat action (handled by agent).
        
        Returns:
            Status message
        """
        return "готов ответить"


def create_communication_tools(ai, vision, log_fn=None) -> Dict[str, Any]:
    """Create and return communication tools for registry registration.
    
    Args:
        ai: LLM client for text generation
        vision: Vision module for screen analysis
        log_fn: Optional logging function
        
    Returns:
        Dictionary mapping tool names to Tool instances
    """
    from core.tool_registry import Tool
    
    tools_instance = CommunicationTools(ai, vision, log_fn)
    tools = {}
    
    # Press tool
    tools["press"] = Tool(
        name="press",
        description="Press a key or key combination",
        schema={
            "type": "object",
            "properties": {
                "combo": {"type": "string", "description": "Key combination like 'enter', 'ctrl+c'"},
            },
            "required": ["combo"],
        },
        risk_level=3,
        execute=tools_instance.press,
    )
    
    # Type tool
    tools["type"] = Tool(
        name="type",
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
        execute=tools_instance.type_text,
    )
    
    # Type think tool
    tools["type_think"] = Tool(
        name="type_think",
        description="Generate text using AI and type it",
        schema={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task description for text generation"},
                "window": {"type": "string", "description": "Window title to activate (optional)"},
            },
            "required": ["task"],
        },
        risk_level=2,
        execute=tools_instance.type_think,
    )
    
    # Click see tool
    tools["click_see"] = Tool(
        name="click_see",
        description="Find an object on screen by description and click it",
        schema={
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Description of the object to find"},
            },
            "required": ["target"],
        },
        risk_level=3,
        execute=tools_instance.click_see,
    )
    
    # Chat tool
    tools["chat"] = Tool(
        name="chat",
        description="Placeholder for chat action (handled by agent)",
        schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        risk_level=0,
        execute=tools_instance.chat,
    )
    
    return tools
