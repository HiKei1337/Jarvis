import json

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

    def plan(self, user, context=""):
        raw = self.ai.ask_raw(
            PROMPT.replace("{context}", context or "(пусто)").replace("{user}", user),
            timeout=300,
        )
        if self.log_fn:
            self.log_fn(f"Мысли модели: {raw}")
        return self.parse(raw)

    @staticmethod
    def parse(raw):
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            return [{"action": "chat"}]
        try:
            data = json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            return [{"action": "chat"}]
        if isinstance(data, dict) and isinstance(data.get("steps"), list):
            steps = [s for s in data["steps"] if isinstance(s, dict)]
            return steps or [{"action": "chat"}]
        if isinstance(data, dict) and "action" in data:
            return [data]
        return [{"action": "chat"}]
