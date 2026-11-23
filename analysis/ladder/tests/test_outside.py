"""ladder/outside.py (S17): the runner's game without the tripwire, for the host's own strategies only (the pilots of
2.5 and 2.6, LD-59). The same game as the runner's on the same job; a player's code is refused; resuming by id.
Seeds 93402300-93402999 (host probe bank 2, SEEDS.md; the puzzle tests' range, games on other seats/lists)."""
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE), str(HERE.parents[2])]
os.environ["LADDER_EXTRA_PATH"] = str(HERE)
from ladder import deal, outside, runner  # noqa: E402
from ladder import puzzles as Z  # noqa: E402
from ladder import submit  # noqa: E402

ROOT = HERE.parents[2]
CODES = [l.strip().split("|")[1] for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(
    encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def job(i, specs=("bot:greedy+plan", "bot:greedy")):
    return {"id": f"o-{i}", "seed": 93402900 + i, "first": None, "decks": [CODES[0], CODES[3]],
            "strategies": list(specs), "labels": {"i": i}}


def test_only_host_strategies_and_pilots_are_recognised():
    with pytest.raises(outside.OutsideError):
        outside.run([job(0, ("py:helpers:Random", "bot:greedy"))], "/nonexistent/x.jsonl")
    with pytest.raises(outside.OutsideError):
        outside.map_tasks("ladder.puzzles:_ask", [{"spec": "py:sub_S0001:A"}])
    from svsim.ui.session import pilot_native_spec
    assert outside.trained("bot:" + pilot_native_spec("T1-SWORD-1"))
    assert not outside.trained("bot:mcts:100+plan") and not outside.trained("py:x:setnet=y")
    assert outside.trained("bot:pilot-T1-SWORD-1") and outside.trained("mix:0.1:pilot-T1-SWORD-1+mull=default")
    assert not outside.trained("bot:level-normal") and not outside.trained("mix:0.1:mcts:100+plan")


def test_the_same_game_as_the_runner_and_resumed_by_id(tmp_path):
    kf = tmp_path / "k.key"
    deal.new_key_file(kf)
    jobs = [job(0), job(1)]
    r = outside.run(jobs, tmp_path / "o.jsonl", workers=2, key=str(kf))
    assert r["played"] == 2 and r["referee"] == "outside"
    runner.run(jobs, str(tmp_path / "r.jsonl"), workers=2, quiet=True, key=str(kf))
    a = {g["id"]: g for g in map(json.loads, (tmp_path / "o.jsonl").read_text(encoding="utf-8").splitlines())}
    b = {g["id"]: g for g in map(json.loads, (tmp_path / "r.jsonl").read_text(encoding="utf-8").splitlines())}
    for k in a:
        assert a[k]["referee"] == "outside" and "referee" not in b[k]
        for f in ("deal", "strategy_seeds", "actions", "result", "winner", "first"):
            assert a[k][f] == b[k][f], f
    again = outside.run(jobs + [job(2)], tmp_path / "o.jsonl", workers=2, key=str(kf))
    assert again["played"] == 1 and again["skipped"] == 2


def test_a_trained_reference_plays_outside_in_a_puzzle(tmp_path, monkeypatch):
    monkeypatch.setattr(Z, "DEFAULT", "bot:greedy")
    monkeypatch.setattr(outside, "trained", lambda spec: spec == "bot:greedy+plan")   # stands in for a pilot
    subs = tmp_path / "subs"
    Z.add(subs, "P01", CODES[1], "皇家护卫一题")
    submit._append(subs, {"ev": "receipt", "id": "S-0001", "player": "fable-ultracode", "kind": "puzzle", "puzzle": "P01",
                          "verdict": "收下", "spec": "bot:greedy"})
    kf = tmp_path / "k.key"
    deal.new_key_file(kf)
    host = Z.run(subs, "P01", (93402300, 93403000), tmp_path / "out", games=2, field="frozen7", agreement=4,
                 refs=["驾驶员=bot:greedy+plan"], workers=2, key=str(kf))
    logs = [json.loads(x) for x in (tmp_path / "out" / "games.jsonl").read_text(encoding="utf-8").splitlines()]
    by = {}
    for g in logs:
        by.setdefault("bot:greedy+plan" in g["strategies"], set()).add(g.get("referee"))
    assert by == {True: {"outside"}, False: {None}}
    assert host["outside_tripwire"] == ["驾驶员"] and [r["games"] for r in host["entries"]] == [14, 14, 14]
    assert host["points"] == 4 and all(a["points"] == 4 for a in host["agreement"])
    pub = json.loads((tmp_path / "out" / "result-public.json").read_text(encoding="utf-8"))
    assert "outside_tripwire" not in pub
