"""The graphical front end's back end: the game session, the local server and the build."""
import json
import random
import threading
import urllib.request
import zipfile
from http.server import HTTPServer
from pathlib import Path

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


def _fingerprint(state) -> list:
    return [[[c.uid for c in p.hand], [(c.uid, c.atk, c.life) for c in p.field], p.leader_hp, p.pp, len(p.deck)]
            for p in state.players]


def _half_game(first: str, level: str = "strong", turns: int = 6):
    """A session part-way through a game, the player's moves picked at random."""
    session, rng = Session(), random.Random(2)
    view = session.start("rhino", "ramp", level, 195489856, first)
    while not view["over"] and session.state.turn <= turns:
        if view["active"] == 1:
            view = session.ai_step()
        elif view.get("mulligan"):
            view = session.mulligan([1])
        else:
            moves = [a for a in view["actions"] if a["type"] != "EndTurn"]
            end = next(a for a in view["actions"] if a["type"] == "EndTurn")
            view = session.act((rng.choice(moves) if moves and rng.random() < 0.7 else end)["i"])
    return session


def _replay(record: dict):
    """The final position of a replay, asserting every action was legal where it was taken."""
    state = None
    for state, action in records.steps(record):
        assert action in legal_actions(state)
    return state                          # steps() applies each action after yielding it, the last one too


def test_a_game_with_a_random_first_player_replays():
    # Drawing the first player uses up a random number: the replay must draw it too.
    session = _half_game("random")
    record = json.loads(json.dumps(session.record_data()))
    assert record["first_arg"] is None
    assert _fingerprint(_replay(record)) == _fingerprint(session.state)
    # Records saved before first_arg existed (the first games played on the phone) still replay.
    old = {k: v for k, v in record.items() if k != "first_arg"}
    assert _fingerprint(_replay(old)) == _fingerprint(session.state)


def test_replaying_in_a_fresh_python_process_gives_the_same_game(tmp_path):
    # The replay must not depend on what else the process has loaded (it once missed
    # the card scripts: Lambent Cairn then added no Fairy) or on string hashing.
    import subprocess
    import sys
    session = _half_game("random")
    path = tmp_path / "game.json"
    path.write_text(json.dumps(session.record_data()))
    code = ("import json, sys\n"
            "from svsim.tools import records\n"
            "from svsim.core.actions import from_dict\n"
            "from svsim.core.engine import apply\n"
            "rec = json.load(open(sys.argv[1]))\n"
            "state = records.start(rec)\n"
            "for data in rec['actions']:\n"
            "    apply(state, from_dict(data))\n"
            "print(json.dumps([[[c.uid for c in p.hand], [(c.uid, c.atk, c.life) for c in p.field], p.leader_hp, p.pp,"
            " len(p.deck)] for p in state.players]))\n")
    done = subprocess.run([sys.executable, "-c", code, str(path)], capture_output=True, text=True,
                          env={"PYTHONHASHSEED": "123", "PYTHONPATH": str(Path(__file__).resolve().parents[1])})
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout) == json.loads(json.dumps(_fingerprint(session.state)))


def test_an_interrupted_game_resumes_where_it_stopped():
    session = _half_game("random", level="fast")
    record = json.loads(json.dumps(session.record_data()))         # as saved by the page
    resumed = Session()
    view = resumed.resume(record)
    assert _fingerprint(resumed.state) == _fingerprint(session.state)
    assert view["turn"] == session.state.turn and view["log"][0] == "继续之前没下完的对局。"
    assert resumed.summary() == session.summary()
    # ... and the game goes on to the end.
    rng = random.Random(5)
    for _ in range(3000):
        if view["over"]:
            break
        if view["active"] == 1:
            view = resumed.ai_step()
        else:
            moves = [a for a in view["actions"] if a["type"] != "EndTurn"]
            end = next(a for a in view["actions"] if a["type"] == "EndTurn")
            view = resumed.act((rng.choice(moves) if moves and rng.random() < 0.8 else end)["i"])
    assert view["over"] and all(a in legal_actions(s) for s, a in records.steps(resumed.record_data()))
