import json
import re
from typing import List, Dict, Any, Optional, Tuple

VALID_ACTIONS = {
    "run", "url", "press", "type", "type_think", "click_see", "scroll",
    "music_play", "music_search", "youtube", "kinopoisk", "media", "volume", "chat"
}

REQUIRED_FIELDS = {
    "run": ["value"],
    "url": ["value"],
    "press": ["value"],
    "type": ["text"],
    "type_think": ["task"],
    "click_see": ["target"],
    "scroll": ["value"],
    "music_search": ["value"],
    "youtube": [],
    "kinopoisk": ["value"],
    "media": ["value"],
    "volume": ["value"],
    "music_play": [],
    "chat": []
}

PROMPT = """Ты командный модуль JARVIS.
Верни СТРОГО JSON вида {"steps": [ ... ]} — список шагов по порядку.
Каждый шаг — один объект:

- {"action": "run", "value": "команда"} — запустить программу/команду
- {"action": "url", "value": "адрес"} — открыть сайт
- {"action": "press", "value": "win+d"} — нажать клавиши
- {"action": "type", "text": "текст", "window": "окно"} — ввести дословно
- {"action": "type_think", "task": "что сочинить", "window": "окно"} — придумать и ввести
- {"action": "click_see", "target": "описание"} — найти на экране и кликнуть
- {"action": "scroll", "value": -3} — прокрутить
- {"action": "music_play"} — открыть Яндекс Музыку
- {"action": "music_search", "value": "запрос"} — найти и включить трек
- {"action": "youtube", "value": "запрос"} — включить видео на YouTube; "" если "что-нибудь/рандом/другое"
- {"action": "kinopoisk", "value": "название"} — найти и включить фильм/сериал на Кинопоиске
- {"action": "media", "value": "playpause|next|prev|volup|voldown|mute"} — медиа-клавиша
- {"action": "volume", "value": N} — установить громкость; N по шкале 0-10 (10 = 100%);
  если пользователь сказал проценты (>10) — передай как есть
- {"action": "chat"} — просто ответить пользователю

Правила:
- Сначала ПОДУМАЙ, что пользователь реально хочет, и только потом выбирай действия.
- Учитывай контекст диалога: короткие реплики ("давай другое", "ещё", "следующее")
  продолжай по предыдущему действию.
- Громкость: "громкость 5", "сделай на 5", или просто число 0-10 — это volume
  со шкалой 0-10. "тише" — 3 шага media voldown; "громче" — 2-3 шага media volup;
  "без звука" — media mute.
- Для music_search value — убери только слова-команды, название оставь как сказал пользователь.
- Если пользователь НЕ указал точный текст — type_think.
- Для разговора — один шаг chat.
- Без лишних слов и без markdown.

Контекст предыдущего диалога:
{context}

Примеры:
Пользователь: громкость 5
{"steps": [{"action": "volume", "value": 5}]}
Пользователь: 7
{"steps": [{"action": "volume", "value": 7}]}
Пользователь: сделай потише
{"steps": [{"action": "media", "value": "voldown"}, {"action": "media", "value": "voldown"}, {"action": "media", "value": "voldown"}]}
Пользователь: включи сериал бригада
{"steps": [{"action": "kinopoisk", "value": "бригада"}]}
Пользователь: включи что-нибудь на ютубе перед сном
{"steps": [{"action": "youtube", "value": ""}]}
(контекст: только что включал случайное видео YouTube) Пользователь: давай другое
{"steps": [{"action": "youtube", "value": ""}]}
Пользователь: как дела
{"steps": [{"action": "chat"}]}

Пользователь: {user}
"""


class Planner:
    def __init__(self, ai, log_fn=None):
        self.ai = ai
        self.log_fn = log_fn

    def plan(self, user: str, context: str = "") -> List[Dict[str, Any]]:
        raw = self.ai.ask_raw(
            PROMPT.replace("{context}", context or "(пусто)").replace("{user}", user),
            timeout=300,
        )
        if self.log_fn:
            self.log_fn(f"Мысли модели: {raw}")
        return self.parse(raw)

    @staticmethod
    def _extract_json(raw: str) -> Optional[str]:
        """Извлекает JSON из ответа модели."""
        # Сначала пробуем найти массив [...]
        arr_start = raw.find("[")
        arr_end = raw.rfind("]")
        if arr_start != -1 and arr_end > arr_start:
            return raw[arr_start:arr_end + 1]
        
        # Затем пробуем объект {...}
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            return None
        return raw[start:end + 1]

    @staticmethod
    def _fix_common_json_errors(json_str: str) -> str:
        """Исправляет распространённые ошибки JSON от LLM."""
        fixed = json_str
        # Убираем trailing commas перед } и ]
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        # Заменяем все одинарные кавычки на двойные (простой подход)
        fixed = fixed.replace("'", '"')
        return fixed

    @staticmethod
    def _validate_step(step: Dict[str, Any]) -> Tuple[bool, str]:
        """Валидирует отдельный шаг плана."""
        if not isinstance(step, dict):
            return False, "шаг не является объектом"
        
        action = step.get("action")
        if not action:
            return False, "отсутствует поле action"
        
        if action not in VALID_ACTIONS:
            return False, f"неизвестное действие '{action}'"
        
        required = REQUIRED_FIELDS.get(action, [])
        for field in required:
            if field not in step or step[field] is None:
                return False, f"отсутствует обязательное поле '{field}' для действия '{action}'"
        
        return True, ""

    @classmethod
    def parse(cls, raw: str) -> List[Dict[str, Any]]:
        """Разбирает ответ LLM в список шагов с обработкой ошибок."""
        json_str = cls._extract_json(raw)
        if not json_str:
            return [{"action": "chat"}]
        
        # Попытка 1: парсим как есть
        try:
            data = json.loads(json_str)
            return cls._process_data(data)
        except json.JSONDecodeError:
            pass
        
        # Попытка 2: исправляем распространённые ошибки
        try:
            fixed = cls._fix_common_json_errors(json_str)
            data = json.loads(fixed)
            return cls._process_data(data)
        except json.JSONDecodeError:
            pass
        
        # Попытка 3: ищем отдельные JSON объекты в тексте
        matches = re.findall(r'\{[^{}]*"action"[^{}]*\}', raw)
        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and "action" in data:
                    return cls._process_data([data])
            except json.JSONDecodeError:
                continue
        
        return [{"action": "chat"}]

    @classmethod
    def _process_data(cls, data: Any) -> List[Dict[str, Any]]:
        """Обрабатывает распарсенные данные и возвращает валидный список шагов."""
        steps = []
        
        if isinstance(data, dict):
            if "steps" in data and isinstance(data["steps"], list):
                items = data["steps"]
            elif "action" in data:
                items = [data]
            else:
                return [{"action": "chat"}]
        elif isinstance(data, list):
            # Прямой массив шагов
            items = data
        else:
            return [{"action": "chat"}]
        
        for item in items:
            valid, error = cls._validate_step(item)
            if valid:
                steps.append(item)
        
        return steps if steps else [{"action": "chat"}]
