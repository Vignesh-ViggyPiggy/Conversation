import os
import queue
import sys
import threading

from dotenv import load_dotenv

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "lib"))

from brain import Brain
from persona import PERSONA_NAME
from voice import get_voice_provider, strip_narration

VOICE_INPUT = os.environ.get("VOICE_INPUT", "text").lower()

_idle_seconds_raw = os.environ.get("IDLE_TRIGGER_SECONDS")
IDLE_TRIGGER_SECONDS = float(_idle_seconds_raw) if _idle_seconds_raw else None

AVATAR_PROVIDER = os.environ.get("AVATAR_PROVIDER", "none").lower()


def make_avatar_client():
    """Returns None unless AVATAR_PROVIDER is set. "vtube_studio" drives an
    existing VTube Studio instance; "local_scene" runs the local server
    that avatar_scene/index.html connects to instead."""
    if AVATAR_PROVIDER == "vtube_studio":
        from avatar import VTubeStudioProvider

        return VTubeStudioProvider()
    if AVATAR_PROVIDER == "local_scene":
        from avatar import LocalSceneProvider

        return LocalSceneProvider()
    return None


class InputWatcher:
    """Wraps a blocking zero-arg input function so the main loop can poll
    for a result with a timeout instead of blocking forever -- used to
    detect "nothing happened in N seconds" for the idle trigger, without
    ever having two threads reading input at once. Only one read is ever
    in flight: a timed-out poll re-checks the *same* pending read; a new
    thread only starts once that read actually completes."""

    _EOF = object()

    def __init__(self, input_fn):
        self._input_fn = input_fn
        self._queue: queue.Queue = queue.Queue()
        self._start_thread()

    def _start_thread(self):
        def worker():
            try:
                self._queue.put(self._input_fn())
            except EOFError:
                self._queue.put(InputWatcher._EOF)

        threading.Thread(target=worker, daemon=True).start()

    def get(self, timeout: float) -> str | None:
        """Returns the next input within `timeout` seconds, or None if
        nothing arrived yet. Raises EOFError if the input source hit EOF."""
        try:
            result = self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
        if result is InputWatcher._EOF:
            raise EOFError
        self._start_thread()
        return result


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
    print("Warming up the local model...")
    brain.provider.warm_up()

    voice = get_voice_provider()
    avatar = make_avatar_client()
    get_input = make_input_fn()
    watcher = InputWatcher(get_input) if IDLE_TRIGGER_SECONDS else None

    print(f"Talking to {PERSONA_NAME}. Session {brain.session_id}.")
    if VOICE_INPUT == "push_to_talk":
        key = os.environ.get("PUSH_TO_TALK_KEY", "space")
        print(f"Hold [{key}] to talk. Say 'exit' or 'reset' to use those commands by voice.")
    print("Type 'exit' to quit, 'reset' to save & start a new session.\n")

    try:
        while True:
            try:
                if watcher:
                    user_input = watcher.get(timeout=IDLE_TRIGGER_SECONDS)
                    if user_input is None:
                        reply = brain.idle_response()
                        print(f"{PERSONA_NAME}> {reply}\n")
                        if voice:
                            spoken = strip_narration(reply)
                            if spoken:
                                voice.speak(spoken, avatar=avatar)
                        continue
                else:
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
                spoken = strip_narration(reply)
                if spoken:
                    voice.speak(spoken, avatar=avatar)
    finally:
        finished = brain.reset()
        if finished:
            print(f"Session {finished} saved. Use memory_cli.py to review or delete it.")
        if avatar:
            avatar.close()


if __name__ == "__main__":
    main()
