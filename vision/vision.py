import base64
import re
import requests
import pyautogui
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Vision:
    def __init__(self, model="qwen3-vl:8b"):
        self.url = "http://localhost:11434/api/generate"
        self.model = model
        self.shot = BASE_DIR / "screenshots" / "last.png"

    def _ask_vl(self, prompt, timeout=300):
        self.shot.parent.mkdir(parents=True, exist_ok=True)
        pyautogui.screenshot(str(self.shot))
        b64 = base64.b64encode(self.shot.read_bytes()).decode()
        data = {
            "model": self.model,
            "prompt": prompt,
            "images": [b64],
            "stream": False,
        }
        r = requests.post(self.url, json=data, timeout=timeout)
        r.raise_for_status()
        return r.json()["response"].strip()

    def see(self, question):
        try:
            return self._ask_vl(question)
        except Exception as e:
            return f"[ошибка] Vision: {e}"

    def find(self, description):
        """Целится в объект: возвращает (x, y) центра в пикселях или None."""
        try:
            w, h = pyautogui.size()
            prompt = (
                "Это скриншот экрана компьютера.\n"
                f"Найди объект: {description}\n"
                "Выведи ТОЛЬКО его bounding box в формате [x1, y1, x2, y2], "
                "координаты от 0 до 1000 по обеим осям. Без слов.\n"
                "Если объекта нет: [-1, -1, -1, -1]"
            )
            raw = self._ask_vl(prompt)
            nums = re.findall(r"-?\d+", raw)
            if len(nums) < 4:
                return None
            x1, y1, x2, y2 = map(int, nums[:4])
            if x1 < 0 or y1 < 0:
                return None
            cx = (x1 + x2) / 2 / 1000 * w
            cy = (y1 + y2) / 2 / 1000 * h
            return int(cx), int(cy)
        except Exception:
            return None
