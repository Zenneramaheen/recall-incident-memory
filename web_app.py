"""Local browser demo. Serves only the UI; secrets stay in the Python process."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid
from checkout_lab import CheckoutLab
from threading import RLock

ROOT = Path(__file__).resolve().parent
HOST, PORT = "127.0.0.1", 8765
LABS = {}
LABS_LOCK = RLock()


def lab_request(path, data):
    if path == "/api/lab/start":
        with LABS_LOCK:
            if len(LABS) >= 100:
                raise ValueError("Demo session limit reached. Restart the local server to clear sessions.")
            session = uuid.uuid4().hex
            lab = CheckoutLab()
            LABS[session] = lab
        return {"session": session, "state": lab.snapshot()}
    session = data.get("session")
    with LABS_LOCK:
        lab = LABS.get(session) if isinstance(session, str) else None
    if lab is None:
        raise ValueError("Demo session expired. Reload the page to start again.")
    with lab.lock:
        if path == "/api/lab/state":
            return {"state": lab.snapshot()}
        if path == "/api/lab/fault":
            return {"state": lab.inject(data.get("scenario"))}
        if path == "/api/lab/checkout":
            status, state = lab.checkout()
            return {"checkout_status": status, "state": state}
        if path == "/api/lab/action":
            return {"state": lab.action(data.get("action"))}
        if path == "/api/lab/investigate":
            if not lab.failure_observed:
                raise ValueError("Place a demo order to collect failure evidence first.")
            if lab.verified:
                raise ValueError("Checkout is recovered. Save the lesson or start another failure.")
            if not lab.bank_ready:
                run_cli(lab.bank, ["init"])
                lab.bank_ready = True
            lab.diagnosis = process_request("/api/investigate", {
                "bank": lab.bank, "alert": lab.evidence(), "service": "checkout-lab", "environment": "simulation", "analyze_current": True})
            lab.diagnosis["comparison"] = lab.comparison(lab.diagnosis["evidence"])
            lab.record_investigation_result()
            return {"state": lab.snapshot()}
        if path == "/api/lab/learn":
            incident = lab.resolution()
            if not lab.bank_ready:
                run_cli(lab.bank, ["init"])
                lab.bank_ready = True
            process_request("/api/retain", {"bank": lab.bank, "incident": incident})
            if not lab.learned:
                lab.lessons_saved += 1
                lab.scorecard["lesson_saved"] = True
            lab.learned = True
            return {"state": lab.snapshot()}
    raise ValueError("Unknown demo action.")


def run_cli(bank, arguments):
    if not isinstance(bank, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", bank):
        raise ValueError("Use a bank name with letters, numbers, underscores, or hyphens.")
    result = subprocess.run(
        [sys.executable, str(ROOT / "incident_memory.py"), "--bank", bank, *arguments],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
    )
    if result.returncode:
        raise RuntimeError("Hindsight could not complete the request. Check your connection, configured credentials, and bank name. No successful result is claimed.")
    return json.loads(result.stdout)


def require_text(data, field, maximum=20000):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"Enter {field.replace('_', ' ')} (maximum {maximum} characters).")
    return value.strip()


def process_request(path, data):
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object.")
    if path.startswith("/api/lab/"):
        return lab_request(path, data)
    if path == "/api/new-bank":
        bank = "incident-ui-" + uuid.uuid4().hex[:12]
        return run_cli(bank, ["init"])
    if path not in ("/api/investigate", "/api/retain"):
        raise ValueError("Unknown action.")
    bank = require_text(data, "bank", 80)
    with tempfile.TemporaryDirectory(prefix="incident-memory-") as directory:
        source = Path(directory) / "input.json"
        if path == "/api/investigate":
            source.write_text(require_text(data, "alert"))
            args = ["investigate", str(source), "--service", require_text(data, "service", 100),
                    "--environment", require_text(data, "environment", 100)]
            if data.get("analyze_current") is True:
                args.append("--analyze-current")
        else:
            incident = data.get("incident")
            from incident_memory import load_incident
            source.write_text(json.dumps(incident))
            load_incident(source)
            args = ["retain", str(source)]
        return run_cli(bank, args)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # No request bodies, keys, or incident content in server logs.

    def respond(self, status, payload, content_type="application/json"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def valid_host(self):
        return self.headers.get("Host") in (f"{HOST}:{PORT}", f"localhost:{PORT}")

    def do_GET(self):
        if not self.valid_host():
            return self.respond(403, {"error": "Local access only."})
        files = {"/": ("lab.html", "text/html; charset=utf-8"),
                 "/console": ("index.html", "text/html; charset=utf-8"),
                 "/lab.css": ("lab.css", "text/css; charset=utf-8"),
                 "/lab.js": ("lab.js", "text/javascript; charset=utf-8"),
                 "/app.css": ("app.css", "text/css; charset=utf-8"),
                 "/app.js": ("app.js", "text/javascript; charset=utf-8")}
        if self.path in files:
            name, kind = files[self.path]
            return self.respond(200, (ROOT / "web" / name).read_bytes(), kind)
        if self.path == "/api/example":
            return self.respond(200, {"incident": json.loads((ROOT / "examples/resolved-incident.json").read_text()),
                                      "alert": (ROOT / "examples/alert.txt").read_text().strip()})
        self.respond(404, {"error": "Not found."})

    def do_POST(self):
        origin = self.headers.get("Origin")
        if (not self.valid_host() or self.headers.get("X-Incident-App") != "1"
                or origin not in (None, f"http://{HOST}:{PORT}", f"http://localhost:{PORT}")):
            return self.respond(403, {"error": "Requests must come from the local application."})
        if self.headers.get("Content-Type") != "application/json":
            return self.respond(415, {"error": "Expected application/json."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536:
                raise ValueError("Request must be between 1 and 65,536 bytes.")
            data = json.loads(self.rfile.read(length))
            result = process_request(self.path, data)
            self.respond(result.get("checkout_status", 200), result)
        except (ValueError, UnicodeError) as exc:
            self.respond(400, {"error": str(exc)})
        except subprocess.TimeoutExpired:
            self.respond(504, {"error": "Hindsight took too long. A save may still have completed; retry the same incident ID to avoid a duplicate."})
        except Exception:
            self.respond(502, {"error": "Hindsight request failed. Check your connection, credentials, and bank name, then retry. No result has been substituted."})


if __name__ == "__main__":
    print(f"Incident Memory Copilot: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
