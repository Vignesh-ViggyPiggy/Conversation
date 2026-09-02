import argparse
import os
import sys

from dotenv import load_dotenv

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "lib"))

from memory.store import delete_session, get_session_facts, list_sessions
from persona import PERSONA_NAME


def cmd_list(args):
    sessions = list_sessions(PERSONA_NAME)
    if not sessions:
        print(f"No saved sessions for {PERSONA_NAME}.")
        return
    for s in sessions:
        print(f"{s['session_id']}  {s['fact_count']} facts  {s['started_at']} -> {s['ended_at']}")


def cmd_show(args):
    facts = get_session_facts(PERSONA_NAME, args.session_id)
    if not facts:
        print(f"No facts found for session {args.session_id}.", file=sys.stderr)
        sys.exit(1)
    for fact in facts:
        print(f"- {fact}")


def cmd_delete(args):
    deleted = delete_session(PERSONA_NAME, args.session_id)
    if deleted == 0:
        print(f"No facts found for session {args.session_id}.", file=sys.stderr)
        sys.exit(1)
    print(f"Deleted {deleted} fact(s) from session {args.session_id}.")


def main():
    parser = argparse.ArgumentParser(description=f"Manage persistent memory for {PERSONA_NAME}.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List saved sessions").set_defaults(func=cmd_list)

    show = sub.add_parser("show", help="Show facts saved by one session")
    show.add_argument("session_id")
    show.set_defaults(func=cmd_show)

    delete = sub.add_parser("delete", help="Delete one session's facts")
    delete.add_argument("session_id")
    delete.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
