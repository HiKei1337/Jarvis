import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class OllamaClient:
    def __init__(self, model="qwen2.5-coder:7b"):
        self.url = "http://localhost:11434/api/generate"
        self.model = model

        p = BASE_DIR / "config" / "personality.txt"
        if p.exists():
            self.system = p.read_text(encoding="utf-8")
        else:
            self.system = "Ты JARVIS, локальный ИИ-ассистент. Отвечай коротко и по делу."

    def ask(self, prompt, model=None, timeout=180):
        data = {
            "model": model or self.model,
            "prompt": f"{self.system}\n\nПользователь: {prompt}\nJARVIS:",
            "stream": False,
            "keep_alive": "1h",
        }
        try:
            r = requests.post(self.url, json=data, timeout=timeout)
            r.raise_for_status()
            return r.json()["response"].strip()
        except requests.ConnectionError:
            return "[ошибка] Ollama не запущена. Запусти приложение Ollama или 'ollama serve'."
        except requests.HTTPError:
            return f"[ошибка] Ollama статус {r.status_code}: {r.text[:200]}"
        except Exception as e:
            return f"[ошибка] {e}"

    def ask_raw(self, prompt, timeout=120):
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "1h",
        }
        try:
            r = requests.post(self.url, json=data, timeout=timeout)
            r.raise_for_status()
            return r.json()["response"].strip()
        except Exception as e:
            return f"[ошибка] {e}"

    def warmup(self):
        """Прогрев: загружает модель в память заранее."""
        try:
            requests.post(
                self.url,
                json={"model": self.model, "prompt": "ping",
                      "stream": False, "keep_alive": "1h"},
                timeout=300,
            )
        except Exception:
            pass
