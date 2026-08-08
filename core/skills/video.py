import json
import random
import time
from urllib.parse import quote

from core.skills.browser_ctl import JarvisBrowser

RANDOM_YT = [
    "интересные факты о космосе",
    "расслабляющая музыка с видом на город",
    "документальный фильм про природу",
    "asmr для сна",
    "ночная поездка по городу 4k",
    "как устроена вселенная",
]

HOME_JS = """
(() => {
  const els = [...document.querySelectorAll('a[href*="/watch"]')].filter(a => {
    const r = a.getBoundingClientRect();
    return r.width > 200 && r.y > 80 && r.y < window.innerHeight - 50;
  }).slice(0, 8);
  return JSON.stringify(els.map(a => {
    const r = a.getBoundingClientRect();
    return {x: r.x + r.width / 2, y: r.y + r.height / 2};
  }));
})()
"""

FIRST_YT_JS = """
(() => {
  const els = [...document.querySelectorAll('a[href*="/watch"]')].filter(a => {
    const r = a.getBoundingClientRect();
    return r.width > 200 && r.y > 60;
  });
  if (!els.length) return 'null';
  const r = els[0].getBoundingClientRect();
  return JSON.stringify({x: r.x + r.width / 2, y: r.y + r.height / 2});
})()
"""

KP_TYPE_JS = """
(() => {
  const inp = document.querySelector('input[placeholder*="ильмы"]')
    || document.querySelector('input[type="search"]')
    || document.querySelectorAll('input')[0];
  if (!inp) return 'null';
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(inp, %s);
  inp.focus();
  inp.dispatchEvent(new Event('input', {bubbles: true}));
  return 'ok';
})()
"""

KP_SUGGEST_CLICK_JS = """
(() => {
  const open = [...document.querySelectorAll('div,span,a,button')].some(e =>
    (e.textContent || '').trim() === 'Показать все' && e.children.length === 0);
  if (!open) return 'nosuggest';
  const links = [...document.querySelectorAll('a')].filter(a => {
    const h = a.getAttribute('href') || '';
    const r = a.getBoundingClientRect();
    return /\\/film\\/\\d+/.test(h) && r.width > 50 && r.y > 60 && r.y < 900;
  });
  if (!links.length) return 'null';
  links[0].click();
  return 'ok';
})()
"""

KP_PLAY_JS = """
(() => {
  const els = [...document.querySelectorAll('div,span,button,a')].filter(e => {
    const t = (e.textContent || '').trim();
    const r = e.getBoundingClientRect();
    return (t.startsWith('Смотреть') || t.startsWith('Продолжить') || t.startsWith('Начать'))
      && t.length < 30 && r.width > 0 && r.width < 600 && r.y > 50;
  });
  if (!els.length) return 'null';
  const r = els[0].getBoundingClientRect();
  return JSON.stringify({x: r.x + r.width / 2, y: r.y + r.height / 2});
})()
"""

class VideoSkill:
    def __init__(self):
        self.browser = JarvisBrowser()

    def youtube(self, query, log_fn=None):
        q = (query or "").strip()
        try:
            if not q or q.lower() in ("рандом", "что-нибудь", "любое", "что-то"):
                ws = self.browser.open_url("https://www.youtube.com")
                time.sleep(6)
                raw = self.browser.js_value(ws, HOME_JS)
                rects = json.loads(raw) if raw and raw != "null" else []
                if not rects:
                    ws.close()
                    return "не вижу рекомендаций на главной YouTube"
                pt = random.choice(rects)
                if log_fn:
                    log_fn(f"YouTube: выбрал случайное видео из {len(rects)} видимых")
                self.browser.real_click(ws, pt["x"], pt["y"])
                time.sleep(3)
                href = self.browser.js_value(ws, "location.href")
                ws.close()
                if "/watch" in href:
                    return "включил случайное видео из твоих рекомендаций"
                return "кликнул по рекомендации — проверь плеер"
            url = "https://www.youtube.com/results?search_query=" + quote(q)
            ws = self.browser.open_url(url)
            time.sleep(5)
            raw = self.browser.js_value(ws, FIRST_YT_JS)
            pt = json.loads(raw) if raw and raw != "null" else None
            if not pt:
                ws.close()
                return f"не нашёл видео по '{q}'"
            self.browser.real_click(ws, pt["x"], pt["y"])
            time.sleep(3)
            href = self.browser.js_value(ws, "location.href")
            ws.close()
            if "/watch" in href:
                return f"включил на YouTube: {q}"
            return f"открыл YouTube по '{q}' — проверь"
        except Exception as e:
            return f"ошибка YouTube: {e}"

    def kinopoisk(self, query, log_fn=None):
        q = (query or "").strip() or "сериал"
        try:
            ws = self.browser.open_url("https://www.kinopoisk.ru")
            time.sleep(4)
            self.browser.js_value(ws, KP_TYPE_JS % json.dumps(q))
            time.sleep(2.5)
            res = self.browser.js_value(ws, KP_SUGGEST_CLICK_JS)
            if res == "ok":
                if log_fn:
                    log_fn("Кинопоиск: кликнул по первому результату подсказки")
                time.sleep(4)
            else:
                if log_fn:
                    log_fn("Кинопоиск: подсказка не открылась, иду на страницу поиска")
                ws.close()
                ws = self.browser.open_url("https://www.kinopoisk.ru/search/?text=" + quote(q))
                time.sleep(4)
                self.browser.js_value(ws, KP_SUGGEST_CLICK_JS.replace("open = true;", "").replace("if (!open) return 'nosuggest';", ""))
                time.sleep(3)
            raw = self.browser.js_value(ws, KP_PLAY_JS)
            play = json.loads(raw) if raw and raw != "null" else None
            if play:
                if log_fn:
                    log_fn("Кинопоиск: жму кнопку запуска плеера")
                self.browser.real_click(ws, play["x"], play["y"])
                time.sleep(2)
                ws.close()
                return f"включил на Кинопоиске: {q}"
            ws.close()
            return f"открыл Кинопоиск по '{q}', но кнопки запуска нет — проверь вход/подписку в браузере JARVIS"
        except Exception as e:
            return f"ошибка Кинопоиска: {e}"
