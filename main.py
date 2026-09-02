import os
import sys

from dotenv import load_dotenv

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "lib"))

from brain import Brain
from persona import PERSONA_NAME
from voice import get_voice_provider


def main():
    brain = Brain()
    voice = get_voice_provider()
    print(f"Talking to {PERSONA_NAME}. Session {brain.session_id}.")
    print("Type 'exit' to quit, 'reset' to save & start a new session.\n")

    try:
        while True:
            try:
                user_input = input("you> ").strip()
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
