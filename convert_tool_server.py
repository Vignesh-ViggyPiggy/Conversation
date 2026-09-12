import argparse
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

AVATAR_SCENE_DIR = Path(_PROJECT_ROOT) / "avatar_scene"
CLIPS_DIR = Path(_PROJECT_ROOT) / "lib" / "motion" / "clips"


class ConvertToolHandler(SimpleHTTPRequestHandler):
    """Serves avatar_scene/ as static files -- same as `python -m
    http.server` run from inside that directory -- plus a small JSON API
    under /api/clips that convert_mixamo.html's "existing animations"
    selector uses to list and delete imported clips. Listing/deleting
    needs real filesystem access, which neither plain static serving nor
    browser JS alone can provide."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(AVATAR_SCENE_DIR), **kwargs)

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/clips":
            clips = []
            for path in sorted(CLIPS_DIR.glob("*.json")):
                try:
                    clips.append(json.loads(path.read_text()))
                except (json.JSONDecodeError, OSError):
                    continue
            self._send_json(200, clips)
            return
        super().do_GET()

    def do_DELETE(self):
        if self.path.startswith("/api/clips/"):
            clip_id = self.path[len("/api/clips/"):]
            deleted = False
            for path in CLIPS_DIR.glob("*.json"):
                try:
                    data = json.loads(path.read_text())
                except (json.JSONDecodeError, OSError):
                    continue
                if data.get("id") == clip_id:
                    path.unlink()
                    deleted = True
                    break
            self._send_json(200 if deleted else 404, {"deleted": deleted})
            return
        self._send_json(404, {"error": "not found"})


def main():
    parser = argparse.ArgumentParser(
        description="Serves avatar_scene/ (for convert_mixamo.html and "
        "index.html), plus a JSON API for listing/deleting imported clips "
        "in lib/motion/clips/. Use this instead of `python -m http.server` "
        "when using convert_mixamo.html's existing-animations selector."
    )
    parser.add_argument("--port", type=int, default=int(os.environ.get("CONVERT_TOOL_PORT", "8080")))
    args = parser.parse_args()

    server = HTTPServer(("localhost", args.port), ConvertToolHandler)
    print(f"Serving avatar_scene/ at http://localhost:{args.port}/ (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
