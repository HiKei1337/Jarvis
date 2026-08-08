import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"

class ActionLogger:
    def __init__(self):
        LOG_DIR.mkdir(exist_ok=True)
        self.path = LOG_DIR / "actions.log"

    def log(self, **kwargs):
        rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), **kwargs}
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def screenshot(self, tag):
        try:
            import pyautogui
            p = LOG_DIR / f"{int(time.time())}_{tag}.png"
            pyautogui.screenshot(str(p))
            return str(p)
        except Exception:
            return None
