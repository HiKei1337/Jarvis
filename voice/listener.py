import json
import queue
from pathlib import Path

import sounddevice as sd
from vosk import Model, KaldiRecognizer

BASE_DIR = Path(__file__).resolve().parent.parent

class Listener:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = str(BASE_DIR / "models" / "vosk-ru")
        self.model = Model(model_path)
        self.sample_rate = 16000

    def listen(self):
        """Слушает микрофон, возвращает распознанную фразу."""
        q = queue.Queue()

        def callback(indata, frames, time_info, status):
            q.put(bytes(indata))

        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000,
                               dtype="int16", channels=1, callback=callback):
            rec = KaldiRecognizer(self.model, self.sample_rate)
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    text = json.loads(rec.Result()).get("text", "")
                    if text:
                        return text