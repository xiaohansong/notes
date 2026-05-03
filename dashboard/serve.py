"""
Local dashboard server.

Serves the static dashboard files and regenerates data.json on every request
to /data.json — so editing a workout log + browser refresh shows the new data.

Run:
    python3 dashboard/serve.py            # default port 8765
    python3 dashboard/serve.py --port 8000

Then open http://localhost:8765
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DASH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DASH_DIR))

from parse import build_dashboard_data  # noqa: E402

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quieter logs
        sys.stderr.write(f"[{self.log_date_time_string()}] {fmt % args}\n")

    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/":
            path = "/index.html"

        if path == "/data.json":
            try:
                data = build_dashboard_data()
                payload = json.dumps(data, default=str).encode("utf-8")
            except Exception as e:  # noqa: BLE001
                self.send_response(500)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"parse error: {e}".encode("utf-8"))
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        # Static file
        target = (DASH_DIR / path.lstrip("/")).resolve()
        try:
            target.relative_to(DASH_DIR)
        except ValueError:
            self.send_error(403)
            return
        if not target.exists() or not target.is_file():
            self.send_error(404)
            return
        ext = target.suffix.lower()
        ctype = CONTENT_TYPES.get(ext, "application/octet-stream")
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Strength dashboard → http://{args.host}:{args.port}", flush=True)
    print("Edit logs in workout/, then refresh the page.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.server_close()


if __name__ == "__main__":
    main()
