"""The graphical front end's back end: the game session, the local server and the build."""
import json
import random
import threading
import urllib.request
import zipfile
from http.server import HTTPServer

from svsim.core.engine import legal_actions
from svsim.tools import records
from svsim.tools.web import Handler, build
from svsim.ui.session import Session


def play_out(call, seed=0, max_steps=3000):
    """Drive a session through `call(method, *args)` like the page does: mulligan,
    then random moves (mostly not ending the turn), letting the AI move in between."""
    rng = random.Random(seed)
    view = call("start", "rhino", "ramp", "fast", seed, "you")
    for _ in range(max_steps):
        if view["over"]:
            break
        if view["active"] == 1:
            view = call("ai_step")
        elif view.get("mulligan"):
            view = call("mulligan", [0])
        else:
            moves = [a for a in view["actions"] if a["type"] != "EndTurn"]
            end = next(a for a in view["actions"] if a["type"] == "EndTurn")
            view = call("act", (rng.choice(moves) if moves and rng.random() < 0.8 else end)["i"])
    return view


def test_a_session_plays_a_whole_game_and_keeps_its_record():
    session = Session()
    views = []

    def call(method, *args):
        result = getattr(session, method)(*args)
        if isinstance(result, dict):
            views.append(result)
        return result

    final = play_out(call, seed=4)
    assert final["over"] and final["winner"] in (0, 1, -1)
    # The page never sees the AI's hand, and gets moves only on the player's turn.
    assert all("hand" not in v["ai"] and "hand" in v["you"] for v in views)
    assert all(not v["actions"] for v in views if v["active"] == 1 or v["over"])
    # The record replays the same game, every action legal where it was taken.
    record = records.decode(final["code"])
    for state, action in records.steps(record):
        assert action in legal_actions(state)
    assert record["winner"] == final["winner"] and session.record_data() is session.record


def test_notes_and_help_on_the_players_turn():
    session = Session()
    view = session.start("rhino", "ramp", "fast", 11, "you")
    view = session.mulligan([])
    while view["active"] == 1:                          # the AI's mulligan
        view = session.ai_step()
    assert view["active"] == 0 and view["phase"] == "main"
    view = session.note("先垫一张")
    assert session.record["notes"][-1]["text"] == "先垫一张" and view["log"][-1] == "备注：先垫一张"
    assert session.hint().startswith("AI 会这样走：")
    assert "杀不了" in session.lethal() or "必杀" in session.lethal()


def test_the_local_server_runs_the_session_and_saves_finished_games(tmp_path):
    Handler.session, Handler.saved, Handler.replays = None, False, tmp_path
    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert json.loads(urllib.request.urlopen(base + "/api/ping").read()) == {"ok": True}
        page = urllib.request.urlopen(base + "/").read().decode()
        assert page.startswith("<!doctype html>") and "<title>超凡陪练台</title>" in page

        def call(method, *args):
            req = urllib.request.Request(base + "/api/call", json.dumps({"method": method, "args": list(args)}).encode(),
                                         {"Content-Type": "application/json"})
            data = json.loads(urllib.request.urlopen(req).read())
            assert "error" not in data, data
            return data["result"]

        final = play_out(call, seed=6)
        assert final["over"]
        saved = list(tmp_path.iterdir())
        assert len(saved) == 1 and records.decode(str(saved[0]))["winner"] == final["winner"]
        req = urllib.request.Request(base + "/api/call", json.dumps({"method": "__init__", "args": []}).encode())
        assert "error" in json.loads(urllib.request.urlopen(req).read())   # only the session's own methods
    finally:
        server.shutdown()
        Handler.session, Handler.replays = None, Handler.replays


def test_the_build_has_the_page_the_package_and_pyodide(tmp_path):
    fake = tmp_path / "pyodide-src"                    # stand-ins for the downloaded Pyodide files
    fake.mkdir()
    for name in ("pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "pyodide-lock.json"):
        (fake / name).write_text("stub")
    with zipfile.ZipFile(fake / "python_stdlib.zip", "w") as z:
        z.writestr("encodings/", "")
        z.writestr("encodings/__init__.py", "# stdlib")
    out = tmp_path / "dist"
    build(out, fake)
    assert (out / "index.html").read_text(encoding="utf-8").startswith("<!doctype html>")
    assert not (out / "page.html").read_text(encoding="utf-8").startswith("<!doctype")   # for a host that wraps it
    # Python sources ship as JSON text (hosts like claude.ai serve no archives).
    package = json.loads((out / "svsim.json").read_text(encoding="utf-8"))
    assert "svsim/ui/session.py" in package and "svsim/cards/data/unlimited.json" in package
    assert not any("__pycache__" in n for n in package)
    stdlib = json.loads((out / "pyodide" / "python_stdlib.json").read_text(encoding="utf-8"))
    assert stdlib == {"encodings/__init__.py": "# stdlib"}
