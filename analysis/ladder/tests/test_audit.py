"""The replay audit before a period advances (ladder/audit.py, LD-40). Seeds 99001232-99001235 (host probe bank,
SEEDS.md; the runner tests' block)."""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE), str(HERE.parents[2])]
os.environ["LADDER_EXTRA_PATH"] = str(HERE)
from ladder import audit, runner  # noqa: E402

ROOT = HERE.parents[2]
CODES = [l.strip().split("|")[1] for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(
    encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def job(i, s0, s1, a=1, b=4):
    return {"id": f"a-{i}", "seed": 99001200 + i, "first": 0, "decks": [CODES[a], CODES[b]],
            "strategies": [s0, s1], "strategy_seeds": [i * 2 + 1, i * 2 + 2]}


def test_a_change_undone_before_the_game_ends_fails_the_audit(tmp_path):
    out = tmp_path / "g.jsonl"
    runner.run([job(32, "py:helpers:ChangesUntilGuess", "py:helpers:Random"),
                job(33, "py:helpers:Random", "py:helpers:Random"),
                job(34, "py:helpers:Random", "py:helpers:Slow")], str(out), workers=1, step_limit=1.0, quiet=True)
    rows = {r["id"]: r for r in map(json.loads, out.read_text(encoding="utf-8").splitlines())}
    # the tripwire can't see it: the costs were put back before the game ended
    assert rows["a-32"]["result"] in ("normal", "draw")
    assert rows["a-34"]["result"] == "timeout"
    res = audit.audit([out], workers=2)
    assert res["checked"] == 2 and res["skipped"] == 1 and not res["ok"]
    assert [f["id"] for f in res["failed"]] == ["a-32"]
    assert "not legal on replay" in res["failed"][0]["why"] or "winner" in res["failed"][0]["why"]


def test_a_changed_log_fails_too(tmp_path):
    out = tmp_path / "g.jsonl"
    runner.run([job(35, "py:helpers:Random", "py:helpers:Random")], str(out), workers=1, quiet=True)
    g = json.loads(out.read_text(encoding="utf-8"))
    assert audit.audit([out])["ok"]
    g["winner"] = 1 - g["winner"] if g["winner"] in (0, 1) else 0
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps(g) + "\n", encoding="utf-8")
    res = audit.audit([out, bad])
    assert res["checked"] == 2 and [f["log"] for f in res["failed"]] == [str(bad)]
