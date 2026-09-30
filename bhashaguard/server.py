"""Loopback-only development UI. No telemetry, external assets or saved drafts."""
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .core import Guard, LANGUAGES
from .models import generate_local

WEB = Path(__file__).parent / "web"


def make_server(guard: Guard, port: int = 8765, llm_endpoint: str | None = None,
                llm_model: str = "local-model") -> ThreadingHTTPServer:
    token = secrets.token_urlsafe(32)
    model_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Never put response text into server logs.

        def send(self, code, data, content_type="application/json; charset=utf-8"):
            raw = json.dumps(data, ensure_ascii=False).encode() if isinstance(data, (dict, list)) else data
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def valid_host(self):
            return self.headers.get("Host") in (f"127.0.0.1:{self.server.server_port}",
                                                f"localhost:{self.server.server_port}")

        def do_GET(self):
            if not self.valid_host():
                return self.send(403, {"error": "Invalid local Host header"})
            if self.path == "/api/config":
                demos = json.loads((Path(__file__).parent / "data" / "demo_cases.json").read_text(encoding='utf-8'))
                return self.send(200, {"token": token, "languages": LANGUAGES,
                                       "locales": sorted({e["locale"] for e in guard.pack["entries"]}),
                                       "pack_kind": guard.pack["kind"], "demo_cases": demos,
                                       "generation_enabled": bool(llm_endpoint), "backend": "CPU"})
            if self.path == "/api/health":
                return self.send(200, {"status": "ok", "backend": "CPU", "npu_used": False})
            assets = {"/": ("index.html", "text/html; charset=utf-8"),
                      "/style.css": ("style.css", "text/css; charset=utf-8"),
                      "/app.js": ("app.js", "text/javascript; charset=utf-8")}
            if self.path not in assets:
                return self.send(404, {"error": "Not found"})
            name, mime = assets[self.path]
            return self.send(200, (WEB / name).read_bytes(), mime)

        def do_POST(self):
            origin = self.headers.get("Origin")
            allowed = (None, f"http://127.0.0.1:{self.server.server_port}",
                       f"http://localhost:{self.server.server_port}")
            if not self.valid_host() or origin not in allowed or self.headers.get("X-BhashaGuard-Token") != token:
                return self.send(403, {"error": "Invalid local request token or origin"})
            if self.path not in ("/api/analyze", "/api/generate"):
                return self.send(404, {"error": "Not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 160000:
                    raise ValueError("Invalid request size")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("Expected a JSON object")
                if self.path == "/api/generate":
                    if not llm_endpoint:
                        raise ValueError("Generation is disabled. Start with a loopback model endpoint to enable it.")
                    prompt = payload.get("prompt", "")
                    language = payload.get("language", "te")
                    if not isinstance(prompt, str) or not 0 < len(prompt.strip()) <= 12000 or language not in LANGUAGES:
                        raise ValueError("Provide a prompt and a supported language")
                    with model_lock:
                        answer = generate_local(prompt, LANGUAGES[language], llm_endpoint, llm_model)
                    return self.send(200, {"text": answer, "model": llm_model,
                                           "backend": "external loopback server; execution device unverified"})
                allowed_keys = {"text", "language", "locale", "prompt", "allow_latin"}
                if set(payload) - allowed_keys:
                    raise ValueError("Unexpected analysis fields")
                with model_lock:
                    report = guard.analyze(**payload)
                return self.send(200, report)
            except (ValueError, TypeError, KeyError) as exc:
                return self.send(400, {"error": str(exc)})
            except Exception:
                return self.send(500, {"error": "Local processing failed. Check the optional model setup."})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
