#!/usr/bin/env python3
"""Zero-dependency web server:  python run_web.py [port]   then open http://localhost:8000

  GET  /                 chat UI
  POST /api/chat         {"session_id": "...", "message": "..."}  -> reply + parsed profile + scheme results
  POST /api/evaluate     {"profile": {...}, "lang": "en"}          -> stateless eligibility check
  GET  /api/schemes      catalogue (names, tags, documents)
"""
import json
import pathlib
import sys
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app.dialogue import Assistant, Session

BOT = Assistant()
SESSIONS = {}
WEB = pathlib.Path(__file__).parent / "app" / "web"


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/schemes":
            return self._send(200, [{"id": s["id"], "name": s["name"], "tags": s["tags"], "level": s["level"]}
                                    for s in BOT.catalog.schemes])
        self._send(404, {"error": "not found"})

    def do_POST(self):
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            return self._send(400, {"error": "invalid JSON"})
        if self.path == "/api/chat":
            sid = payload.get("session_id") or uuid.uuid4().hex
            if len(SESSIONS) > 5000:
                SESSIONS.clear()
            sess = SESSIONS.setdefault(sid, Session())
            out = BOT.handle(sess, str(payload.get("message", ""))[:2000])
            out["session_id"] = sid
            return self._send(200, out)
        if self.path == "/api/evaluate":
            return self._send(200, BOT.evaluate_profile(payload.get("profile", {}), payload.get("lang", "en")))
        self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Serving on http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
