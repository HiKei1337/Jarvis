"""JARVIS Vision Control Tools

Provides vision-based computer control tools:
- vision_screenshot: Capture screen and analyze
- vision_find: Find UI element by description
- vision_click_see: Find and click UI element
- vision_verify: Verify action result
- vision_describe: Describe current screen
"""

from typing import Dict, Any, Optional
from vision.vision import Vision
from automation.mouse import Mouse
from automation.keyboard import Keyboard


class VisionControlTools:
    """Vision-based computer control tools for JARVIS.
    
    These tools implement the SEE → THINK → ACT → VERIFY cycle:
    - Capture screenshot
    - Analyze with vision model
    - Find UI elements dynamically
    - Execute actions based on vision
    - Verify results
    """
    
    def __init__(self, log_fn=None, vision_model: str = "qwen3-vl:8b"):
        """Initialize vision control tools.
        
        Args:
            log_fn: Optional logging function
            vision_model: Vision model name
        """
        self.vision = Vision(model=vision_model)
        self.mouse = Mouse()
        self.keyboard = Keyboard()
        self.log_fn = log_fn
    
    def _log(self, message: str):
        """Log a message if logging is enabled."""
        if self.log_fn:
            self.log_fn(message)
    
    def vision_screenshot(self, analyze: bool = False, question: Optional[str] = None) -> str:
        """Capture screenshot and optionally analyze it.
        
        Args:
            analyze: If True, analyze screenshot with vision model
            question: Optional question to ask about the screen
            
        Returns:
            Screenshot path or analysis result
        """
        try:
            shot_path = self.vision.capture_screen()
            self._log(f"vision_screenshot: captured {shot_path}")
            
            if analyze and question:
                result = self.vision.see(question)
                return f"скриншот: {shot_path}, анализ: {result}"
            elif analyze:
                result = self.vision.describe_screen()
                return f"скриншот: {shot_path}, описание: {result}"
            else:
                return f"скриншот сохранён: {shot_path}"
                
        except Exception as e:
            self._log(f"vision_screenshot failed: {e}")
            return f"ошибка скриншота: {e}"
    
    def vision_find(self, description: str, confidence_threshold: Optional[float] = None) -> str:
        """Find UI element by description using vision.
        
        Args:
            description: Description of UI element to find
            confidence_threshold: Minimum confidence (0.0-1.0)
            
        Returns:
            Element coordinates or not found message
        """
        try:
            self._log(f"[VISION] Searching: {description}")
            
            result = self.vision.find_elements(description, confidence_threshold)
            
            if result.get("success") and result.get("elements"):
                element = result["elements"][0]
                cx = element.get("center_x", 0)
                cy = element.get("center_y", 0)
                elem_type = element.get("type", "element")
                text = element.get("text", "")
                confidence = element.get("confidence", 0)
                
                self._log(f"[VISION] Found: {elem_type} '{text}' at ({cx}, {cy}) conf={confidence:.2f}")
                
                return f"найдено: {elem_type} '{text}' на координатах ({cx}, {cy}), уверенность {confidence:.0%}"
            else:
                error_msg = result.get("error", "элемент не найден")
                self._log(f"[VISION] Not found: {description}")
                return f"не найдено: {description} ({error_msg})"
                
        except Exception as e:
            self._log(f"vision_find failed: {e}")
            return f"ошибка поиска: {e}"
    
    def vision_click_see(self, description: str, confidence_threshold: Optional[float] = None) -> str:
        """Find UI element by description and click it.
        
        Implements: SEE (find element) → ACT (click) → VERIFY (check result)
        
        Args:
            description: Description of UI element to click
            confidence_threshold: Minimum confidence (0.0-1.0)
            
        Returns:
            Click result with verification
        """
        try:
            # SEE: Find the element
            self._log(f"[COMPUTER] Task: Click '{description}'")
            self._log("[COMPUTER] Capturing screen...")
            
            result = self.vision.find_elements(description, confidence_threshold)
            
            if not result.get("success") or not result.get("elements"):
                error_msg = result.get("error", "элемент не найден")
                self._log(f"[VISION] Element not found: {description}")
                return f"не удалось найти '{description}': {error_msg}"
            
            element = result["elements"][0]
            cx = element.get("center_x", 0)
            cy = element.get("center_y", 0)
            elem_type = element.get("type", "element")
            text = element.get("text", "")
            confidence = element.get("confidence", 0)
            
            self._log(f"[VISION] Detected: {elem_type} '{text}'")
            self._log(f"[VISION] Found: {text} at ({cx}, {cy})")
            
            # Check confidence threshold
            if confidence < (confidence_threshold or self.vision.confidence_threshold):
                self._log(f"[COMPUTER] Low confidence {confidence:.2f}, requiring reanalysis")
                return f"низкая уверенность {confidence:.0%}, требуется подтверждение"
            
            # ACT: Click the element
            self._log(f"[PLANNER] Action: click target")
            self._log(f"[EXECUTOR] Click: (x={cx}, y={cy})")
            
            self.mouse.click(cx, cy)
            
            self._log(f"[COMPUTER] Clicked ({cx}, {cy})")
            
            # Small delay for UI response
            import time
            time.sleep(0.5)
            
            # VERIFY: Capture new screenshot and check
            self._log("[COMPUTER] Capturing screen...")
            self._log("[VISION] Analyzing result...")
            
            verify_result = self.vision.see(
                f"Была ли нажата кнопка/элемент '{text}'? Что изменилось на экране после клика?"
            )
            
            self._log(f"[VERIFY] Result: {verify_result[:100]}...")
            
            return f"кликнул по '{text}' ({cx}, {cy}), результат: {verify_result[:200]}"
            
        except Exception as e:
            self._log(f"vision_click_see failed: {e}")
            return f"ошибка выполнения: {e}"
    
    def vision_verify(self, expected_state: str) -> str:
        """Verify current screen state matches expectation.
        
        Args:
            expected_state: Description of expected screen state
            
        Returns:
            Verification result (SUCCESS/FAILED with details)
        """
        try:
            self._log(f"[VERIFY] Checking: {expected_state}")
            
            # Capture new screenshot
            self.vision.capture_screen()
            
            # Ask vision model to verify
            prompt = (
                f"Проверь соответствует ли текущий экран следующему описанию: {expected_state}\n"
                "Ответь ДА если соответствует, или НЕТ и объясни что не так."
            )
            
            result = self.vision.see(prompt)
            
            is_success = "да" in result.lower() or "соответствует" in result.lower()
            
            status = "SUCCESS" if is_success else "FAILED"
            self._log(f"[VERIFY] {status}: {result[:100]}")
            
            return f"{status}: {result}"
            
        except Exception as e:
            self._log(f"vision_verify failed: {e}")
            return f"FAILED: ошибка проверки: {e}"
    
    def vision_describe(self) -> str:
        """Get detailed description of current screen.
        
        Returns:
            Screen description from vision model
        """
        try:
            self._log("[VISION] Describing screen...")
            
            result = self.vision.describe_screen()
            
            self._log(f"[VISION] Screen described: {len(result)} chars")
            
            return f"экран: {result}"
            
        except Exception as e:
            self._log(f"vision_describe failed: {e}")
            return f"ошибка описания: {e}"
    
    def vision_wait_and_click(self, description: str, timeout: int = 30, confidence_threshold: Optional[float] = None) -> str:
        """Wait for UI element to appear and then click it.
        
        Args:
            description: Description of UI element to wait for
            timeout: Maximum wait time in seconds
            confidence_threshold: Minimum confidence (0.0-1.0)
            
        Returns:
            Click result or timeout message
        """
        try:
            self._log(f"[COMPUTER] Waiting for: {description} (timeout={timeout}s)")
            
            # Wait for element
            result = self.vision.wait_for_element(description, timeout=timeout)
            
            if not result.get("success") or not result.get("elements"):
                error_msg = result.get("error", "timeout")
                self._log(f"[VISION] Timeout waiting for: {description}")
                return f"таймаут ожидания '{description}': {error_msg}"
            
            element = result["elements"][0]
            cx = element.get("center_x", 0)
            cy = element.get("center_y", 0)
            text = element.get("text", "")
            confidence = element.get("confidence", 0)
            
            self._log(f"[VISION] Element appeared: {text} at ({cx}, {cy})")
            
            # Check confidence
            if confidence < (confidence_threshold or self.vision.confidence_threshold):
                return f"элемент найден но низкая уверенность {confidence:.0%}"
            
            # Click
            self._log(f"[EXECUTOR] Clicking: ({cx}, {cy})")
            self.mouse.click(cx, cy)
            
            return f" дождался и кликнил '{text}' ({cx}, {cy})"
            
        except Exception as e:
            self._log(f"vision_wait_and_click failed: {e}")
            return f"ошибка ожидания: {e}"


def create_vision_control_tools(log_fn=None) -> Dict[str, Any]:
    """Create and return vision control tools for registry registration.
    
    Args:
        log_fn: Optional logging function
        
    Returns:
        Dictionary mapping tool names to Tool instances
    """
    from core.tool_registry import Tool
    
    tools_instance = VisionControlTools(log_fn=log_fn)
    
    tools = {}
    
    # Vision screenshot tool
    tools["vision_screenshot"] = Tool(
        name="vision_screenshot",
        description="Capture screenshot and optionally analyze it with vision AI",
        schema={
            "type": "object",
            "properties": {
                "analyze": {"type": "boolean", "description": "Analyze screenshot with AI"},
                "question": {"type": "string", "description": "Question to ask about screen"},
            },
            "required": [],
        },
        risk_level=0,
        execute=tools_instance.vision_screenshot,
    )
    
    # Vision find tool
    tools["vision_find"] = Tool(
        name="vision_find",
        description="Find UI element by description using vision AI, returns coordinates",
        schema={
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Description of UI element to find"},
                "confidence_threshold": {"type": "number", "description": "Minimum confidence 0.0-1.0"},
            },
            "required": ["description"],
        },
        risk_level=0,
        execute=tools_instance.vision_find,
    )
    
    # Vision click_see tool
    tools["vision_click_see"] = Tool(
        name="vision_click_see",
        description="Find UI element by description and click it (SEE→ACT→VERIFY cycle)",
        schema={
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Description of UI element to click"},
                "confidence_threshold": {"type": "number", "description": "Minimum confidence 0.0-1.0"},
            },
            "required": ["description"],
        },
        risk_level=2,
        execute=tools_instance.vision_click_see,
    )
    
    # Vision verify tool
    tools["vision_verify"] = Tool(
        name="vision_verify",
        description="Verify current screen state matches expected description",
        schema={
            "type": "object",
            "properties": {
                "expected_state": {"type": "string", "description": "Expected screen state description"},
            },
            "required": ["expected_state"],
        },
        risk_level=0,
        execute=tools_instance.vision_verify,
    )
    
    # Vision describe tool
    tools["vision_describe"] = Tool(
        name="vision_describe",
        description="Get detailed AI description of current screen content",
        schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        risk_level=0,
        execute=tools_instance.vision_describe,
    )
    
    # Vision wait and click tool
    tools["vision_wait_and_click"] = Tool(
        name="vision_wait_and_click",
        description="Wait for UI element to appear then click it",
        schema={
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Description of UI element to wait for"},
                "timeout": {"type": "integer", "description": "Maximum wait time in seconds"},
                "confidence_threshold": {"type": "number", "description": "Minimum confidence 0.0-1.0"},
            },
            "required": ["description"],
        },
        risk_level=2,
        execute=tools_instance.vision_wait_and_click,
    )
    
    return tools
