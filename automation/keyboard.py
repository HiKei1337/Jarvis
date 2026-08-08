import pyautogui
import pyperclip

class Keyboard:
    def type_text(self, text):
        # через буфер обмена — работает и с русским
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")

    def press(self, combo):
        # "ctrl+c" -> hotkey; "enter" -> press
        keys = [k.strip() for k in combo.split("+")]
        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)