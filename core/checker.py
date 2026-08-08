import time
import pygetwindow as gw

class Checker:
    @staticmethod
    def titles():
        try:
            return {w.title for w in gw.getAllWindows() if w.title.strip()}
        except Exception:
            return set()

    def wait_change(self, before, timeout=6):
        """Ждёт появление нового окна, возвращает его заголовок."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            now = self.titles()
            new = now - before
            if new:
                return sorted(new)[0]
            time.sleep(0.7)
        return None
