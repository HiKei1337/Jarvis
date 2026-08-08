import json
import subprocess
import time
import winreg
import ctypes
from urllib.parse import quote

from core.skills.browser_ctl import JarvisBrowser, PLAYER_JS

VK_MEDIA = {"playpause": 0xB3, "next": 0xB0, "prev": 0xB1,
            "stop": 0xB2, "volup": 0xAF, "voldown": 0xAE, "mute": 0xAD}

FIND_JS = """
(() => {
  const key = %s;
  const leaves = [...document.querySelectorAll('div,span,a')].filter(e => e.children.length === 0);
  let title = leaves.find(e => (e.textContent || '').trim().toLowerCase().includes(key));
  if (!title) return 'null';
  let row = title;
  for (let i = 0; i < 6 && row; i++) {
    row = row.parentElement;
    if (row && row.querySelector('img')) break;
  }
  const img = row ? row.querySelector('img') : null;
  const rc = img ? img.getBoundingClientRect() : null;
  const rt = title.getBoundingClientRect();
  return JSON.stringify({
    cover: rc ? {x: rc.x + rc.width / 2, y: rc.y + rc.height / 2} : null,
    text: title.textContent.trim()
  });
})()
"""

FIRST_JS = """
(() => {
  const imgs = [...document.querySelectorAll('img')].filter(i => {
    const r = i.getBoundingClientRect();
    return (i.src || '').includes('avatars') && r.width >= 60 && r.y > 80;
  });
  if (!imgs.length) return 'null';
  const r = imgs[0].getBoundingClientRect();
  return JSON.stringify({x: r.x + r.width / 2, y: r.y + r.height / 2});
})()
"""

LISTEN_JS = """
(() => {
  const els = [...document.querySelectorAll('div,span,button')].filter(e => {
    const r = e.getBoundingClientRect();
    return (e.textContent || '').trim() === 'Слушать' && r.width > 0 && r.width < 300;
  });
  if (!els.length) return 'null';
  const r = els[els.length - 1].getBoundingClientRect();
  return JSON.stringify({x: r.x + r.width / 2, y: r.y + r.height / 2});
})()
"""

class MusicSkill:
    def __init__(self):
        self.browser = JarvisBrowser()

    def open_app(self):
        if self._has_protocol():
            subprocess.Popen("start yandexmusic://", shell=True)
            time.sleep(1.5)
            return "открыл Яндекс Музыку (приложение)"
        try:
            ws = self.browser.open_url("https://music.yandex.ru")
            ws.close()
            return "открыл Яндекс Музыку (браузер JARVIS)"
        except Exception:
            return "не смог открыть Яндекс Музыку"

    @staticmethod
    def _clean(query):
        q = query.lower()
        for w in ("включи", "включить", "запусти", "поставь", "трек", "песню",
                  "песня", "музыку", "музыка", "плейлист", "слушать"):
            q = q.replace(w, " ")
        q = " ".join(q.split()).strip()
        return q or query

    def play_search(self, query, vision=None, mouse=None, log_fn=None):
        q = self._clean(query)
        url = "https://music.yandex.ru/search?text=" + quote(q) + "&type=track"
        key = next((w for w in q.lower().split() if len(w) >= 4), q.lower()[:5])
        try:
            ws = self.browser.open_url(url)
            time.sleep(5)
        except Exception as e:
            return f"ошибка браузера: {e}"

        before = self.browser.js_value(ws, PLAYER_JS)

        def player():
            return self.browser.js_value(ws, PLAYER_JS)

        def success(t):
            return (key in t.lower()) or (t.strip() and t != before)

        def get(expr):
            raw = self.browser.js_value(ws, expr)
            try:
                return json.loads(raw) if raw and raw != "null" else None
            except Exception:
                return None

        done = False

        def attempt(pt, label):
            nonlocal done
            if done or not pt:
                return
            if log_fn:
                log_fn(label)
            self.browser.real_click(ws, pt["x"], pt["y"])
            time.sleep(2.5)
            if success(player()):
                done = True

        result = f"не смог включить '{q}' — проверь плеер"
        try:
            data = get(FIND_JS % json.dumps(key))
            if data:
                if log_fn:
                    log_fn(f"Нашёл в списке: '{data.get('text')}'")
                attempt(data.get("cover"), "Клик по обложке найденного трека")
            attempt(get(LISTEN_JS), "Кнопка Слушать")
            attempt(get(FIRST_JS), "Клик по первой карточке поиска")
            attempt(get(LISTEN_JS), "Кнопка Слушать на открытой странице")
            if not done and vision and mouse:
                coords = vision.find("жёлтая кнопка с надписью Слушать")
                if coords:
                    if log_fn:
                        log_fn(f"Зрение: Слушать -> {coords}")
                    mouse.move(*coords)
                    time.sleep(0.6)
                    mouse.click(*coords)
                    time.sleep(2.5)
                    if success(player()):
                        done = True
            if done:
                result = f"включил '{q}'"
        finally:
            try:
                ws.close()
            except Exception:
                pass
        return result

    @staticmethod
    def media(key):
        vk = VK_MEDIA.get(key)
        if not vk:
            return False
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
        return True

    @staticmethod
    def _has_protocol():
        try:
            k = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "yandexmusic")
            winreg.CloseKey(k)
            return True
        except OSError:
            return False
