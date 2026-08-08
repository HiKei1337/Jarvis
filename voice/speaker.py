import torch
import sounddevice as sd

class Speaker:
    def __init__(self, speaker="eugene", depth=1.0):
        print("[Speaker] загружаю голос Silero...")
        try:
            self.model, _ = torch.hub.load(
                'snakers4/silero-models', 'silero_tts',
                language='ru', speaker='v4_ru'
            )
            self.speaker = speaker
            self.play_rate = int(48000 * depth)
            self.ok = True
            print(f"[Speaker] голос '{speaker}' готов (depth={depth})")
        except Exception as e:
            print(f"[Speaker] ошибка загрузки: {e}")
            self.ok = False

    def say(self, text):
        if not self.ok or not text:
            return
        try:
            audio = self.model.apply_tts(
                text=text[:400],
                speaker=self.speaker,
                sample_rate=48000
            )
            sd.play(audio, self.play_rate)
            sd.wait()
        except Exception as e:
            print(f"[Speaker] ошибка озвучки: {e}")

    def stop(self):
        try:
            sd.stop()
        except Exception:
            pass
