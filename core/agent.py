from llm.ollama_client import OllamaClient
from memory.memory import Memory
from core.planner import Planner
from core.executor import Executor
from core.policy import PolicyEngine
from core.logger import ActionLogger
from vision.vision import Vision

CAPS = ("Я умею: общаться и отвечать на вопросы; выполнять цепочки команд — "
        "открывать программы и сайты, вводить текст, в том числе сочинённый мной; "
        "управлять клавиатурой и мышью — клавиши, клики, прокрутка; "
        "включать музыку в Яндекс Музыке, видео на YouTube и сериалы на Кинопоиске; "
        "понимать короткие реплики в контексте диалога ('давай другое', 'ещё'); "
        "видеть экран — описывать его и кликать по объектам по названию; "
        "понимать голос и отвечать голосом; помнить историю разговоров; "
        "действовать без спрашивания в режиме полного доступа; "
        "останавливаться по команде стоп; вести журнал действий.")

STOP_WORDS = ("стоп", "отмена", "хватит", "тишина")

class Agent:
    def __init__(self, model="gpt-oss:20b", confirm_fn=None, log_fn=None, control_fn=None):
        self.confirm_fn = confirm_fn
        self.log_fn = log_fn
        self.logger = ActionLogger()
        self.ai = OllamaClient(model=model)
        self.fast = OllamaClient(model="qwen2.5-coder:7b")
        self.memory = Memory()
        self.vision = Vision()
        self.planner = Planner(self.fast, log_fn)
        self.policy = PolicyEngine(confirm_fn, log_fn)
        self.executor = Executor(self.ai, self.vision, self.policy, log_fn, self.logger, control_fn)
        self.history = []

    def set_model(self, model):
        self.ai = OllamaClient(model=model)
        self.executor.ai = self.ai

    def warmup(self):
        self.fast.warmup()

    def stop(self):
        self.policy.abort.set()

    def _context(self):
        return "\n".join(f"Пользователь: {u}\nJARVIS: {a}" for u, a in self.history[-4:])

    def ask(self, user):
        low = user.lower()
        self.logger.log(event="request", user=user)
        ctx = self._context()
        if low in STOP_WORDS:
            self.stop()
            answer = "Остановлено."
        elif "жена пришла" in low or "кира пришла" in low:
            answer = ("Здравствуйте, любимая хозяйка Кира! "
                      "Я вас обожаю! Поиграем в Roblox?")
        elif "что ты умеешь" in low or "что ты можешь" in low:
            answer = CAPS
        elif "что на экране" in low or "опиши экран" in low:
            answer = self.vision.see("Коротко опиши, что видно на экране: какие окна открыты, что написано.")
        else:
            steps = self.planner.plan(user, ctx)
            if len(steps) == 1 and steps[0].get("action") == "chat":
                prompt = (f"Контекст диалога:\n{ctx}\n\nРеплика пользователя: {user}" if ctx else user)
                answer = self.ai.ask(prompt)
            else:
                if self.log_fn:
                    self.log_fn("План: " + " -> ".join(Executor._describe(s) for s in steps))
                self.logger.log(event="plan", steps=steps)
                answer = self.executor.run_chain(steps, user)
        self.logger.log(event="answer", answer=answer[:300])
        self.memory.remember(user, answer)
        self.history.append((user, answer))
        self.history = self.history[-8:]
        return answer
