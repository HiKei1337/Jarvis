import subprocess
import pyautogui

class Commands:
    def execute(self, text):
        t = text.lower()

        if "открой браузер" in t or "открой chrome" in t:
            subprocess.Popen("start chrome", shell=True)
            return "Открываю браузер."

        if "открой проводник" in t:
            subprocess.Popen("explorer")
            return "Открываю проводник."

        if "открой блокнот" in t:
            subprocess.Popen("notepad")
            return "Открываю блокнот."

        if "открой терминал" in t or "открой cmd" in t:
            subprocess.Popen("start cmd", shell=True)
            return "Открываю терминал."

        if "скриншот" in t:
            pyautogui.screenshot("screenshots/last.png")
            return "Скриншот сохранён в screenshots/last.png"

        return None