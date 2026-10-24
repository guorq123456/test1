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
from datetime import datetime, timezone
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

ALLOWED = {"start", "resume", "summary", "view", "act", "mulligan", "ai_step", "hint", "lethal", "note", "code",
           "record_data", "review", "goto", "mark", "impact", "ratings", "card_info"}


def page_html() -> str:
    """The page as a complete document (web/index.html is written for a host that
    adds the document skeleton, like claude.ai)."""
    return SKELETON.replace("{page}", (WEB / "index.html").read_text(encoding="utf-8"))


def _specs(extra=()) -> list:
    """The agent specs the build carries: the page's levels and their matchup bots (ui.session.MATCHUPS), plus `extra`
    (build --spec, a candidate tried in the page before any level names it)."""
    from svsim.ui.session import LEVELS, MATCHUPS
    specs = list(LEVELS.values()) + list(MATCHUPS.values()) + list(extra)
    for spec in specs:                     # +oracle sees the opponent's hand: a diagnostic, never in the page
        if "oracle" in spec.split("+"):
            raise ValueError(f"{spec}: +oracle is a diagnostic and never goes into the page")
    return specs


def _candidate(f: Path, extra=()) -> bool:
    """A model kept beside the installed ones (phased_models/<folder>/), which only "+phased=FOLDER" loads,
    and no level of the page (nor an `extra` spec) names (the original level plays phased_models/orig-f631e14)."""
    models = PACKAGE / "learn" / "phased_models"
    named = {part[len("phased="):] for spec in _specs(extra) for part in spec.split("+") if part.startswith("phased=")}
    return models in f.parents and f.parent != models and f.parent.name not in named


def model_files(extra=()) -> list:
    """The binary models (.npz, relative to the repository root) the specs name: "+setnet=PATH" (learn.setnet) and
    "+puct=PATH[:C[:T]]" (learn.setpolicy). They need numpy in the page."""
    out = []
    for spec in _specs(extra):
        for part in spec.split("+"):
            for opt in ("setnet=", "puct="):
                if part.startswith(opt):
                    path = part[len(opt):].split(":")[0]
                    if path not in out:
                        out.append(path)
    return out


def package_sources(commit: str | None = None, extra=()) -> dict:
    """The svsim package (sources and card tables) as {path: text}; with `commit`, svsim/build.py
    says it was built from that commit (the page has no git). The binary models the specs name ship as base64 text
    at "<path>.b64" (hosts like claude.ai serve no archives); learn.setnet / learn.setpolicy's load_cached read
    them where the .npz itself is missing."""
    import base64
    out = {f.relative_to(ROOT).as_posix(): f.read_text(encoding="utf-8")
           for f in sorted(PACKAGE.rglob("*"))
           if f.suffix in (".py", ".json") and "__pycache__" not in f.parts and not _candidate(f, extra)}
    for path in model_files(extra):
        out[path + ".b64"] = base64.b64encode((ROOT / path).read_bytes()).decode("ascii")
    if commit is not None:
        line = "COMMIT = None "
        assert out["svsim/build.py"].count(line) == 1
        out["svsim/build.py"] = out["svsim/build.py"].replace(line, f"COMMIT = {commit!r} ")
        ratings = json.loads(out["svsim/ui/ratings.json"])     # the levels' ratings say which build they ship in
        ratings["commit"] = commit
        ratings["published_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        out["svsim/ui/ratings.json"] = json.dumps(ratings, ensure_ascii=False, indent=1)
    return out


def stdlib_sources(stdlib_zip: Path) -> dict:
    """Pyodide's standard library (all text files) as {path: text}."""
    with zipfile.ZipFile(stdlib_zip) as z:
        return {name: z.read(name).decode("utf-8") for name in z.namelist() if not name.endswith("/")}


MODEL_PART = 6_000_000      # characters of base64 per models-N.json (svsim.json "_more" lists them; worker.js reads them)


def _write_part(out: Path, n: int, part: dict) -> str:
    name = f"models-{n}.json"
    (out / name).write_text(json.dumps(part), encoding="utf-8")
    return name


def build(out: Path, pyodide_from: Path | None = None, extra=()) -> None:
    """The in-browser version in `out`. `extra`: agent specs to carry besides the levels' (a candidate tried in the
    page; the levels, ratings.json and the installed models are unchanged). When the specs name a binary model, the
    page also gets numpy: Pyodide's numpy wheel as base64 JSON (pyodide/numpy.json), which the worker loads."""
    out.mkdir(parents=True, exist_ok=True)
    (out / "page.html").write_text((WEB / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
    (out / "index.html").write_text(page_html(), encoding="utf-8")
    (out / "worker.js").write_text((WEB / "worker.js").read_text(encoding="utf-8"), encoding="utf-8")
    from svsim.build import git_commit
    commit = git_commit(ROOT) or "unknown"
    package = package_sources(commit, extra)
    core = {path: text for path, text in package.items() if not path.endswith(".b64")}
    core["_more"] = []                                 # the models in files of their own, each under a host's 16 MB
    part: dict = {}
    for path in sorted(p for p in package if p.endswith(".b64")):
        if part and sum(map(len, part.values())) + len(package[path]) > MODEL_PART:
            core["_more"].append(_write_part(out, len(core["_more"]) + 1, part))
            part = {}
        part[path] = package[path]
    if part:
        core["_more"].append(_write_part(out, len(core["_more"]) + 1, part))
    (out / "svsim.json").write_text(json.dumps(core, ensure_ascii=False), encoding="utf-8")
    from svsim.ui.session import LEVELS, MATCHUPS      # ratings.json beside the page, specs filled in, for readers
    ratings = json.loads(package["svsim/ui/ratings.json"])
    for level, spec in LEVELS.items():
        ratings["tiers"].setdefault(level, {})["spec"] = spec
        matchups = {f"{you} vs {opponent}": m for (lv, you, opponent), m in MATCHUPS.items() if lv == level}
        if matchups:
            ratings["tiers"][level]["matchups"] = matchups
    (out / "ratings.json").write_text(json.dumps(ratings, ensure_ascii=False, indent=1), encoding="utf-8")
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
    if model_files(extra):                             # numpy for the nets, as text (no archive on the host)
        import base64
        lock = json.loads((pyo / "pyodide-lock.json").read_text(encoding="utf-8"))
        wheel = lock["packages"]["numpy"]["file_name"]
        source = pyodide_from / wheel if pyodide_from is not None else None
        if source is not None and source.exists():
            data = source.read_bytes()
        else:
            url = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/{wheel}"   # packages: the full release
            print(f"下载 {url}")
            with urllib.request.urlopen(url) as r:
                data = r.read()
        (pyo / "numpy.json").write_text(json.dumps({"file": wheel, "base64": base64.b64encode(data).decode("ascii")}),
                                        encoding="utf-8")
    print(f"版本：提交 {commit}" + ("（有未提交的改动）" if commit.endswith("+") else ""))
    print(f"已生成 {out}：page.html（发布到 claude.ai 用）、index.html（任何静态网站都能放）、worker.js、"
          "svsim.json、models-*.json（模型，有的话）、ratings.json、pyodide/（python_stdlib.zip 只用来生成 "
          "python_stdlib.json，不必发布）")


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
            if method in ("start", "resume", "review") or cls.session is None:
                cls.session, cls.saved = Session(), False
            result = getattr(cls.session, method)(*args)
            state = cls.session.state
            if state is not None and state.over and not cls.saved and not cls.session.reviewing:
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
    parser.add_argument("--spec", action="append", default=[], metavar="SPEC",
                        help="(with --build) also carry this agent spec's models (a candidate; the levels unchanged)")
    args = parser.parse_args()
    if args.build:
        build(Path(args.build), Path(args.pyodide_from) if args.pyodide_from else None, args.spec)
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
