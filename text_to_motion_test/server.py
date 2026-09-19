"""Serves preview.html and a small JSON API for the text-to-motion test
tool -- same role as ../convert_tool_server.py plays for
convert_mixamo.html, but for testing MDM's raw output quality rather than
converting a downloaded file.

Requires --mdm-repo and --model-path (see generate.py's docstring for
prerequisites); MDM inference runs synchronously inside the /api/generate
handler, so the browser's "Generate" button just waits -- this is a
single-user local test tool, not a production service.
"""
import argparse
import json
import os
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import generate
from smpl_joints import as_skeleton_dict

_TOOL_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = _TOOL_DIR / "outputs"

_VALID_SLUG = re.compile(r"[a-z0-9_]+")

MDM_REPO: Path
MODEL_PATH: Path


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return (slug or "motion")[:60]


class TestToolHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(_TOOL_DIR), **kwargs)

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/skeleton":
            self._send_json(200, as_skeleton_dict())
            return
        if self.path == "/api/outputs":
            items = []
            for path in sorted(OUTPUTS_DIR.glob("*.json")):
                try:
                    data = json.loads(path.read_text())
                except (json.JSONDecodeError, OSError):
                    continue
                items.append({"slug": path.stem, "text": data.get("text")})
            self._send_json(200, items)
            return
        if self.path.startswith("/api/outputs/"):
            slug = self.path[len("/api/outputs/"):]
            if not _VALID_SLUG.fullmatch(slug):
                self._send_json(404, {"error": "not found"})
                return
            path = OUTPUTS_DIR / f"{slug}.json"
            if not path.is_file():
                self._send_json(404, {"error": "not found"})
                return
            self._send_json(200, json.loads(path.read_text()))
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/generate":
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length))
            except json.JSONDecodeError:
                self._send_json(400, {"error": "invalid JSON body"})
                return

            text = (body.get("text") or "").strip()
            if not text:
                self._send_json(400, {"error": "text is required"})
                return
            motion_length = float(body.get("motion_length", 4.0))
            seed = int(body.get("seed", 10))
            fps = float(body.get("fps", generate.DEFAULT_FPS))

            try:
                clip = generate.generate(MDM_REPO, MODEL_PATH, text, motion_length, seed, fps)
            except Exception as err:  # noqa: BLE001 -- surface any MDM failure to the browser as-is
                self._send_json(500, {"error": str(err)})
                return

            OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
            slug = _slugify(text)
            path = OUTPUTS_DIR / f"{slug}.json"
            suffix = 2
            while path.exists():
                path = OUTPUTS_DIR / f"{slug}_{suffix}.json"
                suffix += 1
            path.write_text(json.dumps(clip))

            self._send_json(200, {"slug": path.stem, **clip})
            return
        self._send_json(404, {"error": "not found"})


def main():
    global MDM_REPO, MODEL_PATH

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mdm-repo", required=True, type=Path, help="Path to your local motion-diffusion-model checkout.")
    parser.add_argument("--model-path", required=True, type=Path, help="Path to the .pt checkpoint.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("TEXT_TO_MOTION_TEST_PORT", "8090")))
    args = parser.parse_args()

    MDM_REPO = args.mdm_repo
    MODEL_PATH = args.model_path

    server = HTTPServer(("localhost", args.port), TestToolHandler)
    print(f"Serving text_to_motion_test/ at http://localhost:{args.port}/preview.html (Ctrl+C to stop)")
    print(f"MDM repo: {MDM_REPO}")
    print(f"Model checkpoint: {MODEL_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
