import json
import os
import subprocess
import time
from pathlib import Path

import requests
import websocket

BASE_DIR = Path(__file__).resolve().parent.parent.parent

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

GET_RECTS_JS = """
(() => {
  const imgs = [...document.querySelectorAll('img')].filter(i => {
    const r = i.getBoundingClientRect();
    return (i.src || '').includes('avatars') && r.width >= 40 && r.width <= 300 && r.y > 100;
  });
  return JSON.stringify(imgs.slice(0, 3).map(i => {
    const r = i.getBoundingClientRect();
    return {x: r.x + r.width / 2, y: r.y + r.height / 2};
  }));
})()
"""

PLAYER_JS = """
(() => {
  const els = [...document.querySelectorAll('div,span')].filter(e => e.children.length === 0);
  const t = els.filter(e => {
    const r = e.getBoundingClientRect();
    return r.y > window.innerHeight - 90 && r.x < 400 && r.width > 0;
  }).map(e => e.textContent.trim());
  return t.join(' | ');
})()
"""

class JarvisBrowser:
    def __init__(self, port=9222):
        self.port = port
        self.profile = str(BASE_DIR / "browser-profile")

    def _edge(self):
        for p in EDGE_CANDIDATES:
            if os.path.exists(p):
                return p
        return None

    def ensure(self):
        try:
            requests.get(f"http://127.0.0.1:{self.port}/json/version", timeout=2)
            return True
        except Exception:
            edge = self._edge()
            if not edge:
                return False
            subprocess.Popen([edge, f"--remote-debugging-port={self.port}",
                              f"--user-data-dir={self.profile}",
                              "--remote-allow-origins=*",
                              "--no-first-run", "--start-maximized"])
            time.sleep(4)
            return True

    def _tabs(self):
        return requests.get(f"http://127.0.0.1:{self.port}/json", timeout=3).json()

    def open_url(self, url):
        if not self.ensure():
            raise RuntimeError("Edge не найден")
        target = None
        try:
            tabs = self._tabs()
        except Exception:
            time.sleep(3)
            tabs = self._tabs()
        for t in tabs:
            if t.get("type") == "page":
                target = t
                break
        if target is None:
            try:
                requests.put(f"http://127.0.0.1:{self.port}/json/new?{url}", timeout=3)
            except Exception:
                requests.get(f"http://127.0.0.1:{self.port}/json/new?{url}", timeout=3)
            time.sleep(1)
            target = self._tabs()[0]
        ws = websocket.create_connection(target["webSocketDebuggerUrl"],
                                         timeout=15, suppress_origin=True)
        self._send(ws, "Page.enable")
        self._send(ws, "Runtime.evaluate",
                   {"expression": f"location.href = {json.dumps(url)}"})
        return ws

    def eval_js(self, ws, expr):
        return self._send(ws, "Runtime.evaluate", {"expression": expr})

    def js_value(self, ws, expr):
        res = self.eval_js(ws, expr)
        return res.get("result", {}).get("result", {}).get("value", "")

    def input_mouse(self, ws, type_, x, y, click_count=1):
        self._send(ws, "Input.dispatchMouseEvent",
                   {"type": type_, "x": int(x), "y": int(y),
                    "button": "left", "clickCount": click_count})

    def real_click(self, ws, x, y, double=False):
        self.input_mouse(ws, "mouseMoved", x, y)
        time.sleep(0.4)
        self.input_mouse(ws, "mousePressed", x, y, 1)
        self.input_mouse(ws, "mouseReleased", x, y, 1)
        if double:
            time.sleep(0.15)
            self.input_mouse(ws, "mousePressed", x, y, 2)
            self.input_mouse(ws, "mouseReleased", x, y, 2)

    @staticmethod
    def _send(ws, method, params=None):
        msg = {"id": 1, "method": method}
        if params:
            msg["params"] = params
        ws.send(json.dumps(msg))
        while True:
            data = json.loads(ws.recv())
            if data.get("id") == 1:
                return data
