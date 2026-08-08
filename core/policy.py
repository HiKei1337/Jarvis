import threading
import time

FORBIDDEN = ("format ", "rd /s", "del /s", "remove-item", "shutdown",
             "cipher", "diskpart", "reg delete")

SAFE_APPS = ("notepad", "calc", "mspaint", "explorer", "chrome", "msedge",
             "winword", "excel", "powerpnt", "code", "telegram",
             "discord", "steam", "spotify")

ACTION_RISK = {
    "chat": 0,
    "url": 1,
    "run": 1,
    "music_play": 1,
    "music_search": 1,
    "youtube": 1,
    "kinopoisk": 1,
    "volume": 2,
    "type": 2,
    "type_think": 2,
    "media": 2,
    "press": 3,
    "click": 3,
    "click_see": 3,
    "scroll": 3,
}

def risk_for(step):
    a = step.get("action")
    if a == "run":
        v = (step.get("value") or "").lower()
        if any(v.startswith(app) for app in SAFE_APPS):
            return 1
        return 5
    return ACTION_RISK.get(a, 5)

class PolicyEngine:
    def __init__(self, confirm_fn=None, log_fn=None):
        self.confirm_fn = confirm_fn
        self.log_fn = log_fn
        self.trusted = False
        self.trust_until = 0.0
        self.sandbox = False
        self.abort = threading.Event()

    SANDBOX_OK = {"chat", "url", "type", "type_think", "click_see", "scroll",
                  "music_play", "music_search", "media", "youtube", "kinopoisk",
                  "volume"}

    def evaluate(self, step):
        a = step.get("action")
        if a == "run":
            v = (step.get("value") or "").lower()
            for bad in FORBIDDEN:
                if bad in v:
                    return "block", f"запрещено: {v}"
        if self.sandbox and a not in self.SANDBOX_OK:
            return "block", f"песочница: действие '{a}' отключено"
        return "ok", None

    def allows(self, risk):
        if self.trusted:
            return True
        return risk <= 3 and time.time() < self.trust_until

    def ask_confirm(self, desc, risk):
        if self.confirm_fn:
            res = self.confirm_fn(desc, risk)
        else:
            res = self._input_confirm(desc, risk)
        if res == "always":
            self.trusted = True
        elif res == "temp":
            self.trust_until = time.time() + 300
        if self.log_fn:
            self.log_fn(f"Твоё решение: {res}")
        return res

    @staticmethod
    def _input_confirm(desc, risk):
        ans = input(f"Jarvis: [риск {risk}] {desc}? (да/5мин/всегда/нет): ").strip().lower()
        if ans in ("y", "да", "д", "yes"):
            return "once"
        if ans in ("5", "5мин", "времено"):
            return "temp"
        if ans in ("всегда", "в", "always"):
            return "always"
        return "cancel"
