import subprocess
import time
import webbrowser
from automation.keyboard import Keyboard
from automation.mouse import Mouse
from automation.windows import WindowManager
from core.policy import risk_for
from core.checker import Checker
from core.skills.music import MusicSkill
from core.skills.video import VideoSkill
from core.skills.volume import VolumeSkill

class Executor:
    def __init__(self, ai, vision, policy, log_fn=None, logger=None, control_fn=None):
        self.ai = ai
        self.vision = vision
        self.policy = policy
        self.log_fn = log_fn
        self.logger = logger
        self.control_fn = control_fn
        self.keyboard = Keyboard()
        self.mouse = Mouse()
        self.wm = WindowManager()
        self.checker = Checker()
        self.music = MusicSkill()
        self.video = VideoSkill()
        self.volume = VolumeSkill()

    def run_chain(self, steps, user_text=""):
        self.policy.abort.clear()
        results = []
        pending = []
        for step in steps:
            verdict, info = self.policy.evaluate(step)
            if verdict == "block":
                results.append(f"заблокировано ({info})")
                if self.log_fn:
                    self.log_fn(f"Заблокировано: {info}")
                if self.logger:
                    self.logger.log(event="block", info=info, step=step)
            else:
                pending.append(step)
        if not pending:
            return " | ".join(results) or "Все шаги заблокированы политикой."

        max_risk = max(risk_for(s) for s in pending)
        if not self.policy.allows(max_risk):
            desc = " -> ".join(self._describe(s) for s in pending)
            res = self.policy.ask_confirm(desc, max_risk)
            if res in ("cancel", None):
                return "Отменено."

        if self.control_fn:
            self.control_fn(True)
        try:
            shot_before = None
            if self.logger and max_risk >= 3:
                shot_before = self.logger.screenshot("before")

            for i, step in enumerate(pending, 1):
                if self.policy.abort.is_set():
                    results.append("остановлено пользователем")
                    break
                if self.log_fn:
                    self.log_fn(f"Шаг {i}: {self._describe(step)}")
                res = self._exec_one(step)
                results.append(f"{i}) {res}")
                if self.logger:
                    self.logger.log(event="step", step=step, result=res)

            if self.logger and max_risk >= 3:
                shot_after = self.logger.screenshot("after")
                self.logger.log(event="chain", steps=steps, results=results,
                                risk=max_risk, before=shot_before, after=shot_after)
        finally:
            if self.control_fn:
                self.control_fn(False)

        out = " | ".join(results)
        need_critic = any(s.get("action") in ("url", "click_see") for s in pending)
        if need_critic and not self.policy.abort.is_set():
            if self.log_fn:
                self.log_fn("Critic: проверяю результат по экрану...")
            verdict = self.vision.see(
                f"Пользователь просил: '{user_text}'. Судя по скриншоту, "
                "действие получилось? Ответь коротко."
            )
            out += f" | Critic: {verdict}"
            if self.logger:
                self.logger.log(event="critic", verdict=verdict)
        return out

    @staticmethod
    def _describe(step):
        a = step.get("action")
        if a == "run":
            return f"запустить {step.get('value')}"
        if a == "url":
            return f"открыть {step.get('value')}"
        if a == "press":
            return f"нажать {step.get('value')}"
        if a == "type":
            return f"ввести текст в {step.get('window', 'активное окно')}"
        if a == "type_think":
            return f"сочинить и ввести в {step.get('window', 'активное окно')}"
        if a == "click_see":
            return f"кликнуть {step.get('target')}"
        if a == "scroll":
            return "прокрутить"
        if a == "music_play":
            return "открыть Яндекс Музыку"
        if a == "music_search":
            return f"включить музыку: {step.get('value')}"
        if a == "youtube":
            return f"включить YouTube: {step.get('value') or 'рандом'}"
        if a == "kinopoisk":
            return f"включить Кинопоиск: {step.get('value')}"
        if a == "media":
            return f"медиа: {step.get('value')}"
        if a == "volume":
            return f"громкость: {step.get('value')}"
        return "ответить"

    def _exec_one(self, step):
        action = step.get("action")
        try:
            if action == "url":
                before = self.checker.titles()
                webbrowser.open(step.get("value", ""))
                win = self.checker.wait_change(before, timeout=8)
                if win:
                    return f"открыл {step.get('value')}"
                return f"открыл {step.get('value')} (окно не изменилось — проверь)"

            if action == "run":
                value = step.get("value", "").strip()
                before = self.checker.titles()
                subprocess.Popen(value, shell=True)
                win = self.checker.wait_change(before, timeout=6)
                if not win:
                    time.sleep(2)
                    win = self.checker.wait_change(before, timeout=4)
                if win:
                    return f"запустил {value} (окно: {win})"
                return f"запустил {value}, но окно не найдено"

            if action == "press":
                self.keyboard.press(step.get("value", ""))
                return f"нажал {step.get('value')}"

            if action == "type":
                window = step.get("window")
                if window and not self._activate_with_retry(window):
                    return f"окно '{window}' не найдено"
                self.keyboard.type_text(step.get("text", ""))
                return "ввёл текст"

            if action == "type_think":
                text = self.ai.ask_raw(
                    f"Задание: {step.get('task', '')}\n"
                    "Верни ТОЛЬКО готовый текст, без вступлений и подписей."
                )
                if self.log_fn:
                    self.log_fn(f"Сочинил: {text}")
                window = step.get("window")
                if window and not self._activate_with_retry(window):
                    return f"окно '{window}' не найдено"
                self.keyboard.type_text(text)
                return f"сочинил и ввёл: {text[:60]}..."

            if action == "click_see":
                target = step.get("target", "")
                coords = self.vision.find(target)
                if not coords:
                    time.sleep(1.0)
                    coords = self.vision.find(target)
                if not coords:
                    return f"не вижу: {target}"
                self.mouse.click(*coords)
                return f"кликнул {target}"

            if action == "scroll":
                try:
                    n = int(step.get("value", 3))
                except ValueError:
                    n = 3
                self.mouse.scroll(n)
                return "прокрутил"

            if action == "music_play":
                return self.music.open_app()

            if action == "music_search":
                return self.music.play_search(step.get("value", ""), self.vision, self.mouse, self.log_fn)

            if action == "youtube":
                return self.video.youtube(step.get("value", ""), self.log_fn)

            if action == "kinopoisk":
                return self.video.kinopoisk(step.get("value", ""), self.log_fn)

            if action == "media":
                key = step.get("value", "playpause")
                if self.music.media(key):
                    return f"медиа-команда: {key}"
                return f"не знаю медиа-команду {key}"

            if action == "volume":
                return self.volume.set_level(step.get("value"))

            return "не понял шаг"
        except Exception as e:
            return f"ошибка шага: {e}"

    def _activate_with_retry(self, window):
        if self.wm.activate(window):
            return True
        time.sleep(1.0)
        return self.wm.activate(window)
