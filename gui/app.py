import threading
import time
import traceback
import tkinter as tk
import subprocess
import customtkinter as ctk

try:
    import psutil
except ImportError:
    psutil = None

from core.agent import Agent, STOP_WORDS
from voice.speaker import Speaker
from voice.listener import Listener

MODELS = {"SMART": "gpt-oss:20b", "FAST": "qwen2.5-coder:7b"}

class JarvisGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("JARVIS")
        self.root.geometry("800x560")
        ctk.set_appearance_mode("dark")

        top = ctk.CTkFrame(self.root, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(top, text="Мозг:").pack(side="left", padx=(0, 8))
        self.model_var = ctk.StringVar(value="SMART")
        ctk.CTkSegmentedButton(top, values=["SMART", "FAST"],
                               variable=self.model_var,
                               command=self.switch_model).pack(side="left")
        self.trust_switch = ctk.CTkSwitch(top, text="полный доступ",
                                          onvalue="on", offvalue="off",
                                          command=self.toggle_trust)
        self.trust_switch.pack(side="left", padx=(10, 0))
        self.sandbox_switch = ctk.CTkSwitch(top, text="песочница",
                                            onvalue="on", offvalue="off",
                                            command=self.toggle_sandbox)
        self.sandbox_switch.pack(side="left", padx=(10, 0))
        self.voice_switch = ctk.CTkSwitch(top, text="слушать",
                                          onvalue="on", offvalue="off",
                                          command=self.toggle_voice)
        self.voice_switch.pack(side="left", padx=(10, 0))
        self.sys_label = ctk.CTkLabel(top, text="", text_color="#7f8794")
        self.sys_label.pack(side="right")

        self.chat = ctk.CTkTextbox(self.root, fg_color="#0b0e14")
        self.chat.pack(fill="both", expand=True, padx=10, pady=10)
        self.chat.configure(state="disabled")
        self.chat._textbox.configure(selectbackground="#2f6e9e")
        self.chat._textbox.bind("<Control-c>", self._copy_sel)
        self.chat._textbox.bind("<Control-C>", self._copy_sel)
        self.chat._textbox.bind("<Control-a>", self._select_all)
        self.chat._textbox.bind("<Control-A>", self._select_all)
        self.chat._textbox.bind("<Control-KeyPress>", self._ctrl_chat)

        self.bottom = ctk.CTkFrame(self.root, fg_color="transparent")
        self.bottom.pack(fill="x", padx=10, pady=(0, 10))

        self.entry = ctk.CTkEntry(self.bottom, placeholder_text="Команда или вопрос...")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.send_typed())
        self.entry.bind("<Control-KeyPress>", self._ctrl_entry)

        ctk.CTkButton(self.bottom, text="Отправить", width=90,
                      command=self.send_typed).pack(side="left", padx=(0, 8))
        ctk.CTkButton(self.bottom, text="MIC", width=50,
                      command=self.send_voice).pack(side="left", padx=(0, 8))
        ctk.CTkButton(self.bottom, text="СТОП", width=60,
                      fg_color="#8a2b2b", hover_color="#a83232",
                      command=self.on_stop).pack(side="left")

        self.status_frame = ctk.CTkFrame(self.root, fg_color="transparent", height=30)
        self.status_icon = ctk.CTkLabel(self.status_frame, text="", fg_color="transparent")
        self.status_icon.pack(side="left", padx=(14, 6))
        self.status_text = ctk.CTkLabel(self.status_frame, text="", fg_color="transparent")
        self.status_text.pack(side="left")
        self._status_after = None
        self._status_state = None
        self._status_tick = 0

        self.confirm_event = threading.Event()
        self.confirm_value = "cancel"
        self.confirm_frame = None
        self.speaker = None
        self.listener = None
        self.agent = None
        self.overlay = None
        self.voice_on = False
        self.voice_busy = False

        threading.Thread(target=self._init_agent, daemon=True).start()
        threading.Thread(target=self._sys_loop, daemon=True).start()
        threading.Thread(target=self._voice_loop, daemon=True).start()

    def _voice_loop(self):
        while True:
            if not self.voice_on or self.voice_busy or self.agent is None:
                time.sleep(0.5)
                continue
            try:
                if self.listener is None:
                    self.log("JARVIS: загружаю распознавание речи...")
                    self.listener = Listener()
                    self.log("JARVIS: слушаю в фоне — скажи 'джарвис'.")
                wake = self.listener.listen()
                low = (wake or "").lower()
                if "джарвис" not in low:
                    continue
                idx = low.find("джарвис")
                rest = wake[idx + len("джарвис"):].strip(" ,.-—!?")
                if rest:
                    text = rest
                else:
                    self.set_status("Слушаю", "🎙")
                    text = self.listener.listen()
                if text:
                    self.log(f"Вы (голос): {text}")
                    self.process(text, from_voice=True)
                    while self.voice_busy and self.voice_on:
                        time.sleep(0.5)
                    time.sleep(1.0)
            except Exception:
                time.sleep(1)

    def toggle_voice(self):
        self.voice_on = self.voice_switch.get() == "on"
        if self.voice_on:
            self.log("JARVIS: фоновое слушание ВКЛЮЧЕНО.")
        else:
            self.log("JARVIS: фоновое слушание выключено.")

    def _copy_sel(self, event=None):
        try:
            text = self.chat._textbox.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        except Exception:
            pass
        return "break"

    def _select_all(self, event=None):
        try:
            self.chat._textbox.tag_add("sel", "1.0", "end")
        except Exception:
            pass
        return "break"

    def _ctrl_chat(self, event):
        if event.keycode == 67:
            return self._copy_sel(event)
        if event.keycode == 65:
            return self._select_all(event)
        return None

    def _ctrl_entry(self, event):
        if event.keycode == 86:
            try:
                self.entry.insert("insert", self.root.clipboard_get())
            except Exception:
                pass
            return "break"
        if event.keycode == 67:
            try:
                sel = self.entry.get(self.entry.index("sel.first"),
                                     self.entry.index("sel.last"))
                self.root.clipboard_clear()
                self.root.clipboard_append(sel)
            except Exception:
                pass
            return "break"
        return None

    @staticmethod
    def _gpu_util():
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu",
                 "--format=csv,noheader,nounits"],
                timeout=2, creationflags=0x08000000)
            return int(out.decode().split()[0])
        except Exception:
            return None

    def _sys_loop(self):
        while True:
            try:
                if psutil:
                    cpu = psutil.cpu_percent(interval=1)
                    ram = psutil.virtual_memory()
                    text = f"CPU {cpu:.0f}% | RAM {ram.used / 2 ** 30:.1f}/{ram.total / 2 ** 30:.0f} ГБ"
                else:
                    text = "psutil не установлен"
                gpu = self._gpu_util()
                if gpu is not None:
                    text += f" | GPU {gpu}%"
                self.root.after(0, lambda t=text: self.sys_label.configure(text=t))
            except Exception:
                pass

    def _init_agent(self):
        self.log("JARVIS: загружаю голос и модель...")
        self.speaker = Speaker("eugene")
        self.agent = Agent(confirm_fn=self.gui_confirm, log_fn=self.log,
                           control_fn=self.set_control)
        self.agent.warmup()
        self.log("JARVIS: на связи.")
        self.set_status(None)

    def set_status(self, text, icon="", animate=True, color="#8b93a1"):
        def _do():
            if self._status_after:
                self.root.after_cancel(self._status_after)
                self._status_after = None
            if text is None:
                self.status_frame.pack_forget()
                self._status_state = None
                return
            self.status_frame.pack(fill="x", pady=(0, 4), before=self.bottom)
            self.status_icon.configure(text=icon)
            self._status_state = {"text": text, "animate": animate, "color": color}
            self._status_tick = 0
            self._tick_status()
        self.root.after(0, _do)

    def _tick_status(self):
        if not self._status_state:
            return
        st = self._status_state
        self._status_tick += 1
        if st["animate"]:
            dots = "." * (self._status_tick % 4)
            shades = ["#69707c", "#8b93a1", "#b3bac6", "#8b93a1"]
            color = shades[self._status_tick % 4]
        else:
            dots = ""
            color = st["color"]
        self.status_text.configure(text=st["text"] + dots, text_color=color)
        self._status_after = self.root.after(350, self._tick_status)

    def set_control(self, on):
        def _do():
            if on:
                if self.overlay is None:
                    self._overlay_create()
            elif self.overlay is not None:
                self._overlay_destroy()
        self.root.after(0, _do)

    def _overlay_create(self):
        try:
            ov = tk.Toplevel(self.root)
            ov.overrideredirect(True)
            ov.attributes("-topmost", True)
            ov.attributes("-transparentcolor", "#010101")
            w = self.root.winfo_screenwidth()
            h = self.root.winfo_screenheight()
            ov.geometry(f"{w}x{h}+0+0")
            canvas = tk.Canvas(ov, bg="#010101", highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            canvas.create_rectangle(6, 6, w - 6, h - 6, outline="#2f8cff", width=10)
            self.overlay = ov
        except Exception:
            self.overlay = None

    def _overlay_destroy(self):
        try:
            self.overlay.destroy()
        except Exception:
            pass
        self.overlay = None

    def toggle_trust(self):
        on = self.trust_switch.get() == "on"
        if self.agent is None:
            return
        self.agent.policy.trusted = on
        self.log("JARVIS: полный доступ " + ("ВКЛЮЧЁН." if on else "выключен."))

    def toggle_sandbox(self):
        on = self.sandbox_switch.get() == "on"
        if self.agent is None:
            return
        self.agent.policy.sandbox = on
        self.log("JARVIS: песочница " + ("ВКЛЮЧЕНА — только сайты, текст и зрение." if on else "выключена."))

    def on_stop(self):
        if self.agent:
            self.agent.stop()
        if self.speaker:
            self.speaker.stop()
        self.voice_busy = False
        self.log("JARVIS: СТОП.")
        self.set_status(None)

    def switch_model(self, value):
        def _do():
            if self.agent is None:
                self.log("JARVIS: ещё загружаюсь, секунду...")
                return
            self.log(f"JARVIS: переключаю мозг на {value}...")
            self.set_status("Смена мозга", "🧠")
            self.agent.set_model(MODELS[value])
            self.log(f"JARVIS: мозг {value} активен.")
            self.set_status(None)
        threading.Thread(target=_do, daemon=True).start()

    def log(self, text):
        def _do():
            self.chat.configure(state="normal")
            self.chat.insert("end", text + "\n\n")
            self.chat.see("end")
            self.chat.configure(state="disabled")
        self.root.after(0, _do)

    def gui_confirm(self, desc, risk):
        self.log(f"Jarvis: [риск {risk}] {desc}?")
        self.set_status("Жду подтверждения — кнопки внизу", "⏸", animate=False, color="#e0a35c")
        self.confirm_event.clear()
        self.root.after(0, self._show_confirm)
        if not self.confirm_event.wait(timeout=120):
            self.set_status(None)
            return "cancel"
        self.set_status("Выполняю", "⚙")
        return self.confirm_value

    def _show_confirm(self):
        if self.confirm_frame:
            self.confirm_frame.destroy()
        self.confirm_frame = ctk.CTkFrame(self.root)
        self.confirm_frame.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(self.confirm_frame, text="Разрешить?").pack(side="left", padx=8)
        ctk.CTkButton(self.confirm_frame, text="1 раз", width=70,
                      command=lambda: self._answer_confirm("once")).pack(side="left", padx=4)
        ctk.CTkButton(self.confirm_frame, text="5 мин", width=70,
                      command=lambda: self._answer_confirm("temp")).pack(side="left", padx=4)
        ctk.CTkButton(self.confirm_frame, text="Всегда", width=80,
                      fg_color="#2f6e33", hover_color="#3a8a3f",
                      command=lambda: self._answer_confirm("always")).pack(side="left", padx=4)
        ctk.CTkButton(self.confirm_frame, text="Отмена", width=70,
                      fg_color="#8a2b2b", hover_color="#a83232",
                      command=lambda: self._answer_confirm("cancel")).pack(side="left", padx=4)

    def _answer_confirm(self, value):
        self.confirm_value = value
        if self.confirm_frame:
            self.confirm_frame.destroy()
            self.confirm_frame = None
        self.confirm_event.set()

    def send_typed(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self.process(text)

    def send_voice(self):
        def _listen():
            if self.listener is None:
                self.log("JARVIS: загружаю распознавание речи...")
                self.listener = Listener()
            self.set_status("Слушаю", "🎙")
            text = self.listener.listen()
            self.process(text)
        threading.Thread(target=_listen, daemon=True).start()

    def process(self, text, from_voice=False):
        self.log(f"Вы: {text}")
        self.voice_busy = True
        threading.Thread(target=self._run_agent, args=(text,), daemon=True).start()

    def _run_agent(self, text):
        try:
            if self.agent is None:
                self.log("JARVIS: ещё загружаюсь, секунду...")
                return
            if text.lower() in STOP_WORDS and self.speaker:
                self.speaker.stop()
            self.set_status("Думаю", "💡")
            try:
                answer = self.agent.ask(text)
            except Exception:
                self.log("Ошибка:\n" + traceback.format_exc())
                self.set_status("Ошибка", "⚠", animate=False, color="#d05252")
                return
            self.log(f"Jarvis: {answer}")
            self.set_status(None)
            if self.speaker:
                self.speaker.say(answer)
        finally:
            self.voice_busy = False

    def run(self):
        self.root.mainloop()
