import os
import sys

from dotenv import load_dotenv

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "lib"))

from brain import Brain
from persona import PERSONA_NAME
from voice import get_voice_provider

VOICE_INPUT = os.environ.get("VOICE_INPUT", "text").lower()


def make_input_fn():
    """Returns a zero-arg function that produces the next user message,
    either from the keyboard or from push-to-talk speech. Voice input still
    goes through the same text (transcribed speech), so saying "exit" or
    "reset" out loud works exactly like typing it -- no special-casing
    needed downstream."""
    if VOICE_INPUT != "push_to_talk":
        return lambda: input("you> ").strip()

    from push_to_talk import SAMPLE_RATE, record_push_to_talk
    from stt import get_stt_provider

    stt = get_stt_provider()

    def listen() -> str:
        audio = record_push_to_talk()
        if audio.size == 0:
            return ""
        text = stt.transcribe(audio, sample_rate=SAMPLE_RATE).strip()
        print(f"you (voice)> {text}")
        return text

    return listen


def main():
    brain = Brain()
    voice = get_voice_provider()
    get_input = make_input_fn()

    print(f"Talking to {PERSONA_NAME}. Session {brain.session_id}.")
    if VOICE_INPUT == "push_to_talk":
        key = os.environ.get("PUSH_TO_TALK_KEY", "space")
        print(f"Hold [{key}] to talk. Say 'exit' or 'reset' to use those commands by voice.")
    print("Type 'exit' to quit, 'reset' to save & start a new session.\n")

    try:
        while True:
            try:
                user_input = get_input()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                break
            if user_input.lower() == "reset":
                finished = brain.reset()
                if finished:
                    print(f"(session {finished} saved, memory reset)\n")
                else:
                    print("(nothing to save, memory reset)\n")
                continue

            reply = brain.respond(user_input)
            print(f"{PERSONA_NAME}> {reply}\n")
            if voice:
                voice.speak(reply)
    finally:
        finished = brain.reset()
        if finished:
            print(f"Session {finished} saved. Use memory_cli.py to review or delete it.")


if __name__ == "__main__":
    main()
