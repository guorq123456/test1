"""Play against the AI in a browser, on a computer or a phone (Chinese UI).

    python -m svsim.tools.web                   # http://localhost:8765, and the address for a phone on the same Wi-Fi
    python -m svsim.tools.web --port 9000
    python -m svsim.tools.web --build dist/web  # a copy that runs entirely in the browser (Pyodide), to publish

The page (web/index.html) only draws what svsim.ui.session.Session returns and
sends back the action the player taps. Served by this tool, the session runs
here and finished games are saved to replays/. The --build copy runs the same
session inside the page with Pyodide (Python compiled to WebAssembly), which it
downloads once into the build folder. Hosts such as claude.ai serve no archives,
so the Python sources (svsim and the standard library) ship as JSON text and
the page's worker writes them into Pyodide's file system.
"""
from __future__ import annotations

import argparse
import json
import socket
import urllib.request
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
PACKAGE = ROOT / "svsim"
PYODIDE_VERSION = "0.26.4"
PYODIDE_FILES = ["pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]
SKELETON = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<style>*,*::before,*::after{box-sizing:border-box}body{margin:0}[hidden]{display:none!important}</style>'
            '</head><body>{page}</body></html>')

ALLOWED = {"start", "view", "act", "mulligan", "ai_step", "hint", "lethal", "note", "code", "record_data"}


def page_html() -> str:
    """The page as a complete document (web/index.html is written for a host that
    adds the document skeleton, like claude.ai)."""
    return SKELETON.replace("{page}", (WEB / "index.html").read_text(encoding="utf-8"))


def package_sources() -> dict:
    """The svsim package (sources and card tables) as {path: text}."""
    return {f.relative_to(ROOT).as_posix(): f.read_text(encoding="utf-8")
            for f in sorted(PACKAGE.rglob("*"))
            if f.suffix in (".py", ".json") and "__pycache__" not in f.parts}


def stdlib_sources(stdlib_zip: Path) -> dict:
    """Pyodide's standard library (all text files) as {path: text}."""
    with zipfile.ZipFile(stdlib_zip) as z:
        return {name: z.read(name).decode("utf-8") for name in z.namelist() if not name.endswith("/")}


def build(out: Path, pyodide_from: Path | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "page.html").write_text((WEB / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
    (out / "index.html").write_text(page_html(), encoding="utf-8")
    (out / "worker.js").write_text((WEB / "worker.js").read_text(encoding="utf-8"), encoding="utf-8")
    (out / "svsim.json").write_text(json.dumps(package_sources(), ensure_ascii=False), encoding="utf-8")
    pyo = out / "pyodide"
    pyo.mkdir(exist_ok=True)
    for name in PYODIDE_FILES:
        target = pyo / name
        if target.exists():
            continue
        if pyodide_from is not None and (pyodide_from / name).exists():
            target.write_bytes((pyodide_from / name).read_bytes())
            continue
        url = f"https://cdn.jsdelivr.net/npm/pyodide@{PYODIDE_VERSION}/{name}"
        print(f"下载 {url}")
        with urllib.request.urlopen(url) as r:
            target.write_bytes(r.read())
    (pyo / "python_stdlib.json").write_text(json.dumps(stdlib_sources(pyo / "python_stdlib.zip")), encoding="utf-8")
    print(f"已生成 {out}：page.html（发布到 claude.ai 用）、index.html（任何静态网站都能放）、worker.js、"
          "svsim.json、pyodide/（python_stdlib.zip 只用来生成 python_stdlib.json，不必发布）")


class Handler(BaseHTTPRequestHandler):
    session = None
    saved = False
    replays = ROOT / "replays"                     # where finished games go

    def log_message(self, fmt, *args):          # keep the terminal quiet
        pass

    def _send(self, code: int, body: bytes, kind: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._send(200, page_html().encode(), "text/html; charset=utf-8")
        elif path == "/api/ping":
            self._send(200, b'{"ok": true}', "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/call":
            self._send(404, b"not found", "text/plain")
            return
        from svsim.tools import records
        from svsim.ui.session import Session
        cls = type(self)
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            method, args = data["method"], data.get("args", [])
            if method not in ALLOWED:
                raise ValueError(f"unknown method {method!r}")
            if method == "start" or cls.session is None:
                cls.session, cls.saved = Session(), False
            result = getattr(cls.session, method)(*args)
            state = cls.session.state
            if state is not None and state.over and not cls.saved:
                cls.saved = True
                print("对局记录已保存：" + records.save(cls.session.record, str(cls.replays)))
            body = json.dumps({"result": result}, ensure_ascii=False)
        except Exception as e:                       # report to the page instead of dying
            body = json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False)
        self._send(200, body.encode(), "application/json; charset=utf-8")


def lan_address() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 80))             # no packet is sent; picks the outgoing interface
            return s.getsockname()[0]
    except OSError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="0.0.0.0", help="0.0.0.0 lets a phone on the same network connect")
    parser.add_argument("--build", metavar="DIR", help="write the in-browser version to DIR instead of serving")
    parser.add_argument("--pyodide-from", metavar="DIR", help="(with --build) copy Pyodide files from DIR")
    args = parser.parse_args()
    if args.build:
        build(Path(args.build), Path(args.pyodide_from) if args.pyodide_from else None)
        return
    server = HTTPServer((args.host, args.port), Handler)
    print(f"在浏览器打开：http://localhost:{args.port}")
    ip = lan_address()
    if ip and args.host == "0.0.0.0":
        print(f"手机连同一个 Wi-Fi 后打开：http://{ip}:{args.port}")
    print("按 Ctrl+C 停止。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
