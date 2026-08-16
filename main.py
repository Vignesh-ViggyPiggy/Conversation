from brain import Brain
from persona import PERSONA_NAME


def main():
    brain = Brain()
    print(f"Talking to {PERSONA_NAME}. Type 'exit' to quit, 'reset' to clear memory.\n")

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
            brain.reset()
            print("(conversation reset)\n")
            continue

        reply = brain.respond(user_input)
        print(f"{PERSONA_NAME}> {reply}\n")


if __name__ == "__main__":
    main()
