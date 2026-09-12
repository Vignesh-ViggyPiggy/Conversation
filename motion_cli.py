import argparse
import asyncio
import json
import os
import sys

from dotenv import load_dotenv

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "lib"))

from motion.imported import load_imported_clips
from motion.library import LIBRARY

DEFAULT_WS_URL = (
    f"ws://{os.environ.get('AVATAR_SCENE_HOST', 'localhost')}:"
    f"{os.environ.get('AVATAR_SCENE_PORT', '9001')}"
)


def all_clips():
    return LIBRARY + load_imported_clips()


def cmd_list(args):
    for clip in all_clips():
        expression = clip.expression or "-"
        source = "imported" if clip.native_clip is not None else "hand-authored"
        print(f"{clip.id:20} {clip.duration:>4.1f}s  expression={expression:10} [{source}]  {clip.description[:60]}")


async def _send(ws_url: str, message: dict) -> None:
    import websockets

    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps(message))


def cmd_play(args):
    clip = next((c for c in all_clips() if c.id == args.clip_id), None)
    if clip is None:
        print(f"No clip named {args.clip_id!r}. Run 'motion_cli.py list' to see available clips.", file=sys.stderr)
        sys.exit(1)
    asyncio.run(_send(args.ws, clip.to_message()))
    print(f"Sent {clip.id!r} to {args.ws} -- check the avatar_scene page connected to it.")


def main():
    parser = argparse.ArgumentParser(
        description="Preview animation library clips (hand-authored in "
        "lib/motion/library.py, or imported into lib/motion/clips/) directly "
        "against a running avatar_scene page, bypassing the LLM/TTS/classifier "
        "pipeline entirely -- for fast iteration. Requires main.py already "
        "running with AVATAR_PROVIDER=local_scene and a browser tab connected "
        "to it."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all clips in the library").set_defaults(func=cmd_list)

    play = sub.add_parser("play", help="Play one clip immediately")
    play.add_argument("clip_id")
    play.add_argument("--ws", default=DEFAULT_WS_URL, help=f"Avatar scene WebSocket URL (default: {DEFAULT_WS_URL})")
    play.set_defaults(func=cmd_play)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
