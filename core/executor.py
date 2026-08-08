import subprocess
import time
import webbrowser
from typing import List, Dict, Any, Optional
from automation.keyboard import Keyboard
from automation.mouse import Mouse
from automation.windows import WindowManager
from core.policy import risk_for
from core.checker import Checker
from core.skills.music import MusicSkill
from core.skills.video import VideoSkill
from core.skills.volume import VolumeSkill

# Статусы выполнения
STATUS_PLANNED = "planned"
STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"

# Максимальное количество шагов для предотвращения бесконечных циклов
MAX_STEPS = 20

# Таймауты для операций (в секундах)
ACTION_TIMEOUTS = {
    "run": 10,
    "url": 15,
    "press": 2,
    "type": 5,
    "type_think": 60,
    "click_see": 10,
    "scroll": 3,
    "music_play": 10,
    "music_search": 30,
    "youtube": 30,
    "kinopoisk": 30,
    "media": 3,
    "volume": 5,
    "chat": 30,
}


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
        self._current_status = STATUS_PLANNED
        self._step_results = []

    def _log_step(self, step_num: int, action: str, status: str, result: str = ""):
        """Логирует результат выполнения шага."""
        msg = f"Шаг {step_num}/{action}: {status}"
        if result:
            msg += f" — {result}"
        if self.log_fn:
            self.log_fn(msg)
        if self.logger:
            self.logger.log(event="step_exec", step_num=step_num, action=action, status=status, result=result)

    def run_chain(self, steps: List[Dict[str, Any]], user_text: str = "") -> str:
        """Выполняет цепочку шагов с обработкой ошибок и статусов."""
        self.policy.abort.clear()
        self._current_status = STATUS_PLANNED
        self._step_results = []
        
        # Ограничиваем количество шагов для предотвращения бесконечных циклов
        if len(steps) > MAX_STEPS:
            steps = steps[:MAX_STEPS]
            if self.log_fn:
                self.log_fn(f"План сокращён до {MAX_STEPS} шагов (защита от циклов)")
        
        # Фильтрация заблокированных шагов
        pending = []
        blocked_results = []
        for i, step in enumerate(steps):
            verdict, info = self.policy.evaluate(step)
            if verdict == "block":
                blocked_results.append(f"шаг {i+1} заблокирован ({info})")
                if self.log_fn:
                    self.log_fn(f"Заблокировано: {info}")
                if self.logger:
                    self.logger.log(event="block", info=info, step=step, step_num=i+1)
            else:
                pending.append(step)
        
        if not pending:
            result = " | ".join(blocked_results) or "Все шаги заблокированы политикой."
            self._current_status = STATUS_CANCELLED
            return result

        # Проверка максимального риска и запрос подтверждения
        max_risk = max(risk_for(s) for s in pending)
        if not self.policy.allows(max_risk):
            desc = " -> ".join(self._describe(s) for s in pending)
            res = self.policy.ask_confirm(desc, max_risk)
            if res in ("cancel", None):
                self._current_status = STATUS_CANCELLED
                return "Отменено."

        self._current_status = STATUS_RUNNING
        if self.control_fn:
            self.control_fn(True)
        
        try:
            shot_before = None
            if self.logger and max_risk >= 3:
                shot_before = self.logger.screenshot("before")

            for i, step in enumerate(pending, 1):
                # Проверка остановки по команде пользователя
                if self.policy.abort.is_set():
                    self._log_step(i, step.get("action", "unknown"), STATUS_CANCELLED)
                    self._step_results.append(f"{i}) остановлено пользователем")
                    self._current_status = STATUS_CANCELLED
                    break
                
                # Логирование начала шага
                if self.log_fn:
                    self.log_fn(f"Шаг {i}: {self._describe(step)} [{STATUS_RUNNING}]")
                
                # Выполнение шага с таймаутом
                action = step.get("action", "unknown")
                timeout = ACTION_TIMEOUTS.get(action, 10)
                res = self._exec_one_with_timeout(step, timeout)
                
                # Определение статуса результата
                if res.startswith("ошибка") or res.startswith("не ") or "не смог" in res:
                    status = STATUS_FAILED
                else:
                    status = STATUS_SUCCESS
                
                self._log_step(i, action, status, res)
                self._step_results.append(f"{i}) {res}")
                
                if self.logger:
                    self.logger.log(event="step", step=step, result=res, status=status)

            # Скриншот после выполнения高风险 шагов
            if self.logger and max_risk >= 3:
                shot_after = self.logger.screenshot("after")
                self.logger.log(event="chain", steps=steps, results=self._step_results,
                                risk=max_risk, before=shot_before, after=shot_after)
        finally:
            if self.control_fn:
                self.control_fn(False)

        # Формирование итогового результата
        if self._current_status == STATUS_CANCELLED:
            out = " | ".join(self._step_results)
        elif any(STATUS_FAILED in r for r in self._step_results):
            self._current_status = STATUS_FAILED
            out = " | ".join(self._step_results)
        else:
            self._current_status = STATUS_SUCCESS
            out = " | ".join(self._step_results)

        # Critic проверка для url и click_see действий
        need_critic = any(s.get("action") in ("url", "click_see") for s in pending)
        if need_critic and not self.policy.abort.is_set() and self._current_status != STATUS_CANCELLED:
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

    def _exec_one_with_timeout(self, step: Dict[str, Any], timeout: int) -> str:
        """Выполняет один шаг с таймаутом."""
        import threading
        
        result = {"value": None, "error": None}
        
        def worker():
            try:
                result["value"] = self._exec_one(step)
            except Exception as e:
                result["error"] = str(e)
        
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            return f"таймаут ({timeout}с)"
        if result["error"]:
            return f"ошибка: {result['error']}"
        return result["value"] or "выполнено"

    @staticmethod
    def _describe(step: Dict[str, Any]) -> str:
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

    def _exec_one(self, step: Dict[str, Any]) -> str:
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
                    "Верни ТОЛЬКО готовый текст, без вступлений и подписей.",
                    timeout=60
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
                except (ValueError, TypeError):
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

    def _activate_with_retry(self, window: str) -> bool:
        if self.wm.activate(window):
            return True
        time.sleep(1.0)
        return self.wm.activate(window)

    @property
    def current_status(self) -> str:
        return self._current_status
