import ctypes
import time

import pygetwindow as gw

# модель может сказать "Блокнот" или "Notepad" — ищем оба
SYNONYMS = {
    "блокнот": ["notepad", "блокнот"],
    "notepad": ["notepad", "блокнот"],
    "калькулятор": ["calculator", "калькулятор"],
    "calculator": ["calculator", "калькулятор"],
    "chrome": ["chrome"],
    "cmd": ["cmd", "командная"],
    "проводник": ["проводник", "explorer"],
}

class WindowManager:
    def activate(self, title):
        variants = SYNONYMS.get(title.lower(), [title.lower()])
        try:
            windows = gw.getAllWindows()
        except Exception:
            return False

        for w in windows:
            if not w.title.strip():
                continue
            low = w.title.lower()
            if any(v in low for v in variants):
                try:
                    if w.isMinimized:
                        w.restore()
                    self._force_foreground(w._hWnd)
                    time.sleep(0.3)
                    return True
                except Exception:
                    return False
        return False

    @staticmethod
    def _force_foreground(hwnd):
        user32 = ctypes.windll.user32
        # трюк: имитируем нажатие ALT — это разрешает красть фокус
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        user32.SetForegroundWindow(hwnd)