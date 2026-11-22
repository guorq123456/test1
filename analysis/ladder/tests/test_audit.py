"""The replay audit before a period advances (ladder/audit.py, LD-40). Seeds 99001232-99001236 (host probe bank,
SEEDS.md; the runner tests' block)."""
import json
import os
import sys
from pathlib import Path

import pytest

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


def test_a_torn_line_is_skipped_and_listed_and_the_next_game_starts_on_its_own_line(tmp_path):
    # LD-41: a power cut can leave half a line; the runner starts its next line on a fresh one, and the audit lists
    # the torn line instead of stopping
    out = tmp_path / "g.jsonl"
    out.write_text('{"id": "a-0", "seed": 1, "res', encoding="utf-8")
    runner.run([job(36, "py:helpers:Random", "py:helpers:Random")], str(out), workers=1, quiet=True)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and json.loads(lines[1])["id"] == "a-36"
    res = audit.audit([out])
    assert res["ok"] and res["checked"] == 1 and res["unreadable"] == [f"{out}:1"]


def test_patterns_that_may_match_nothing_and_the_out_folder(tmp_path, monkeypatch):
    log = tmp_path / "pool" / "games.jsonl"
    log.parent.mkdir()
    log.write_text("", encoding="utf-8")
    gates = str(tmp_path / "gates" / "*" / "games.jsonl")
    assert audit.expand([str(log)], [gates]) == [log]
    with pytest.raises(SystemExit) as e:
        audit.expand([str(log), gates])
    assert e.value.code == 2
    with pytest.raises(SystemExit) as e:
        audit.expand([str(tmp_path / "missing.jsonl")])
    assert e.value.code == 2
    report = tmp_path / "audit" / "P1.json"
    monkeypatch.setattr(sys, "argv", ["audit", str(log), "--allow-empty", gates, "--out", str(report)])
    with pytest.raises(SystemExit) as e:
        audit.main()
    assert e.value.code == 0 and json.loads(report.read_text(encoding="utf-8"))["checked"] == 0


def test_voids_are_counted_per_strategy_and_while_losing(tmp_path):
    log = tmp_path / "g.jsonl"
    rows = [{"id": "v-1", "result": "void", "strategies": ["py:a:A", "py:b:B"], "voided_result": "normal",
             "voided_winner": 1},
            {"id": "v-2", "result": "void", "strategies": ["py:b:B", "py:a:A"], "voided_result": "normal",
             "voided_winner": 0},
            {"id": "v-3", "result": "void", "strategies": ["py:a:A", "py:b:B"], "error": "worker died"}]
    log.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    res = audit.audit([log])
    assert res["checked"] == 0 and res["skipped"] == 3 and res["ok"]
    assert res["voids"] == {"py:a:A": {"void": 3, "was_losing": 2}, "py:b:B": {"void": 3, "was_losing": 0}}


def test_nul_lines_are_listed_and_a_log_named_twice_is_read_once(tmp_path):
    # LD-42: a power cut can leave a line of NULs; it is listed like a torn line. A log given twice (a path and a
    # pattern that matches it) is read once
    log = tmp_path / "g.jsonl"
    row = {"id": "v-1", "result": "void", "strategies": ["py:a:A", "py:b:B"], "error": "x"}
    log.write_bytes(b"\x00\x00\x00\n" + (json.dumps(row) + "\n").encode())
    paths = audit.expand([str(log), str(tmp_path / "*.jsonl")])
    assert paths == [log]
    res = audit.audit(paths)
    assert res["unreadable"] == [f"{log}:1"] and res["skipped"] == 1


def test_a_game_the_pool_counted_without_a_log_line_is_listed(tmp_path, monkeypatch):
    # LD-43: a power cut can keep the pool's "game" event and lose the game's line; the pool never plays that id
    # again, so the audit lists it (--events) instead of letting it pass unreplayed
    log, events = tmp_path / "games.jsonl", tmp_path / "events.jsonl"
    row = {"id": "L1-0000001", "result": "void", "strategies": ["py:a:A", "py:b:B"], "error": "x"}
    log.write_bytes((json.dumps(row) + "\n").encode() + b"\x00" * 40 + b"\n")
    events.write_text("".join(json.dumps(e) + "\n" for e in (
        {"n": 1, "ev": "start", "id": "L1-0000001"}, {"n": 2, "ev": "game", "id": "L1-0000001"},
        {"n": 3, "ev": "game", "id": "L1-0000002"})), encoding="utf-8")
    res = audit.audit([log], events=[events])
    assert res["unlogged"] == ["L1-0000002"] and res["ok"] and res["unreadable"] == [f"{log}:2"]
    assert audit.audit([log])["unlogged"] == []
    report = tmp_path / "a.json"
    monkeypatch.setattr(sys, "argv", ["audit", str(log), "--events", str(events), "--out", str(report)])
    with pytest.raises(SystemExit) as e:
        audit.main()
    assert e.value.code == 0 and json.loads(report.read_text(encoding="utf-8"))["unlogged"] == ["L1-0000002"]
