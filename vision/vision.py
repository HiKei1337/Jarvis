import base64
import re
import json
import requests
import pyautogui
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


class Vision:
    """Vision system for JARVIS Computer Use.
    
    Provides screen analysis capabilities using vision models:
    - Capture screenshots
    - Analyze screen content
    - Find UI elements by description
    - Return structured results with coordinates
    
    Architecture:
        Screenshot → Base64 → Vision Model → Structured JSON → Coordinates
    """
    
    def __init__(self, model: str = "qwen3-vl:8b", url: str = "http://localhost:11434/api/generate"):
        """Initialize vision system.
        
        Args:
            model: Vision model name (default: qwen3-vl:8b)
            url: Ollama API endpoint
        """
        self.url = url
        self.model = model
        self.shot = BASE_DIR / "screenshots" / "last.png"
        self.confidence_threshold = 0.75  # Default confidence threshold
    
    def capture_screen(self, save_path: Optional[Path] = None) -> Path:
        """Capture current screen.
        
        Args:
            save_path: Optional custom save path
            
        Returns:
            Path to saved screenshot
        """
        shot_path = save_path or self.shot
        shot_path.parent.mkdir(parents=True, exist_ok=True)
        pyautogui.screenshot(str(shot_path))
        logger.debug(f"Screen captured: {shot_path}")
        return shot_path
    
    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded string
        """
        return base64.b64encode(image_path.read_bytes()).decode()
    
    def _ask_vl(self, prompt: str, image_path: Optional[Path] = None, timeout: int = 300) -> str:
        """Send request to vision model.
        
        Args:
            prompt: Text prompt for the model
            image_path: Optional image path (uses default screenshot if None)
            timeout: Request timeout in seconds
            
        Returns:
            Model response text
        """
        img_path = image_path or self.shot
        
        # Capture screenshot if needed
        if not img_path.exists():
            self.capture_screen()
        
        b64 = self._encode_image(img_path)
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "images": [b64],
            "stream": False,
        }
        
        try:
            r = requests.post(self.url, json=data, timeout=timeout)
            r.raise_for_status()
            response = r.json()["response"].strip()
            logger.debug(f"Vision response: {response[:200]}...")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Vision API error: {e}")
            raise
    
    def see(self, question: str) -> str:
        """Analyze screen and answer question.
        
        Args:
            question: Question about the screen content
            
        Returns:
            Answer from vision model or error message
        """
        try:
            return self._ask_vl(question)
        except Exception as e:
            logger.error(f"Vision see failed: {e}")
            return f"[ошибка] Vision: {e}"
    
    def find(self, description: str) -> Optional[Tuple[int, int]]:
        """Find UI element by description and return center coordinates.
        
        Legacy method for backward compatibility.
        
        Args:
            description: Description of the UI element to find
            
        Returns:
            (x, y) tuple of center coordinates or None if not found
        """
        result = self.find_elements(description)
        if result and result.get("elements"):
            element = result["elements"][0]
            return element.get("center_x"), element.get("center_y")
        return None
    
    def find_elements(self, description: str, confidence_threshold: Optional[float] = None) -> Dict[str, Any]:
        """Find UI elements by description with structured output.
        
        Args:
            description: Description of UI elements to find
            confidence_threshold: Minimum confidence level (uses default if None)
            
        Returns:
            Structured result:
            {
                "success": bool,
                "elements": [
                    {
                        "type": "button|input|text|icon|window",
                        "text": "Button label",
                        "x": int, "y": int,
                        "width": int, "height": int,
                        "center_x": int, "center_y": int,
                        "confidence": float
                    }
                ],
                "error": Optional[str]
            }
        """
        threshold = confidence_threshold or self.confidence_threshold
        screen_width, screen_height = pyautogui.size()
        
        prompt = (
            "Это скриншот экрана компьютера. Проанализируй интерфейс.\n"
            f"Найди следующие UI элементы: {description}\n\n"
            "Верни результат ТОЛЬКО в формате JSON:\n"
            '{\n'
            '  "success": true,\n'
            '  "elements": [\n'
            '    {\n'
            '      "type": "button",\n'
            '      "text": "Надпись на элементе",\n'
            '      "x": 100,\n'
            '      "y": 200,\n'
            '      "width": 150,\n'
            '      "height": 40,\n'
            '      "center_x": 175,\n'
            '      "center_y": 220,\n'
            '      "confidence": 0.92\n'
            '    }\n'
            '  ]\n'
            '}\n\n'
            "Координаты x, y, width, height должны быть в пикселях относительно реального разрешения экрана.\n"
            "Поле confidence должно быть от 0.0 до 1.0.\n"
            "Если элементов не найдено: {\"success\": false, \"elements\": []}\n"
            "НЕ добавляй никакого текста кроме JSON."
        )
        
        try:
            raw_response = self._ask_vl(prompt)
            
            # Try to parse JSON
            result = self._parse_vision_response(raw_response)
            
            if not result:
                return {
                    "success": False,
                    "elements": [],
                    "error": "Invalid JSON response from vision model"
                }
            
            # Filter by confidence threshold
            if "elements" in result:
                result["elements"] = [
                    elem for elem in result["elements"]
                    if elem.get("confidence", 0) >= threshold
                ]
            
            result["success"] = len(result.get("elements", [])) > 0
            return result
            
        except Exception as e:
            logger.error(f"find_elements failed: {e}")
            return {
                "success": False,
                "elements": [],
                "error": str(e)
            }
    
    def _parse_vision_response(self, raw: str) -> Optional[Dict[str, Any]]:
        """Parse vision model response into structured format.
        
        Args:
            raw: Raw response text from vision model
            
        Returns:
            Parsed dictionary or None
        """
        # Try direct JSON parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from text
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to parse coordinates from text
        nums = re.findall(r"\d+", raw)
        if len(nums) >= 6:
            try:
                x = int(nums[0])
                y = int(nums[1])
                w = int(nums[2])
                h = int(nums[3])
                return {
                    "success": True,
                    "elements": [{
                        "type": "detected",
                        "text": "",
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h,
                        "center_x": x + w // 2,
                        "center_y": y + h // 2,
                        "confidence": 0.5
                    }]
                }
            except (ValueError, IndexError):
                pass
        
        logger.warning(f"Failed to parse vision response: {raw[:100]}")
        return None
    
    def describe_screen(self) -> str:
        """Get general description of current screen.
        
        Returns:
            Text description of screen content
        """
        prompt = (
            "Опиши что ты видишь на этом скриншоте компьютера.\n"
            "Какие приложения открыты? Какие окна активны?\n"
            "Какие кнопки, поля ввода, меню видны?\n"
            "Будь краток но информативен."
        )
        return self.see(prompt)
    
    def wait_for_element(self, description: str, timeout: int = 30, interval: float = 1.0) -> Dict[str, Any]:
        """Wait for UI element to appear on screen.
        
        Args:
            description: Description of element to wait for
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds
            
        Returns:
            Structured result when element found, or {"success": False, "elements": []} on timeout
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.find_elements(description)
            if result.get("success"):
                logger.info(f"Element found: {description}")
                return result
            
            logger.debug(f"Waiting for element: {description}")
            time.sleep(interval)
        
        logger.warning(f"Timeout waiting for element: {description}")
        return {"success": False, "elements": [], "error": "timeout"}
