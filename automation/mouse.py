import pyautogui

class Mouse:
    def click(self, x=None, y=None):
        if x is not None and y is not None:
            pyautogui.click(x, y)
        else:
            pyautogui.click()

    def move(self, x, y):
        pyautogui.moveTo(x, y, duration=0.3)

    def scroll(self, clicks):
        pyautogui.scroll(clicks)