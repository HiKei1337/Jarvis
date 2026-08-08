from core.agent import Agent, STOP_WORDS
from voice.speaker import Speaker
from voice.listener import Listener

VOICE = True

def main():
    agent = Agent()
    speaker = Speaker("eugene")
    listener = Listener() if VOICE else None

    print("JARVIS v1.1. Прогреваю модель...")
    agent.warmup()
    print("Модель в памяти. На связи.")

    while True:
        if listener:
            print("... жду слово 'джарвис' ...")
            wake = listener.listen()
            print(f"Услышал: {wake}")
            low = wake.lower()
            if "джарвис" not in low:
                continue
            idx = low.find("джарвис")
            rest = wake[idx + len("джарвис"):].strip(" ,.-—!?")
            if rest:
                user = rest
            else:
                speaker.say("Слушаю.")
                user = listener.listen()
            print(f"Вы: {user}")
        else:
            try:
                user = input("\nВы: ").strip()
            except (KeyboardInterrupt, EOFError):
                break

        if not user:
            continue
        if user.lower() in ("выход", "exit", "quit"):
            print("Jarvis: завершаю работу.")
            speaker.say("Завершаю работу.")
            break

        if user.lower() in STOP_WORDS:
            speaker.stop()

        print("Jarvis: думаю...")
        answer = agent.ask(user)
        print(f"\nJarvis: {answer}")
        speaker.say(answer)

if __name__ == "__main__":
    main()
