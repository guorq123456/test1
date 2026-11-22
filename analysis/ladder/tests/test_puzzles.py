"""Public puzzles (ladder/puzzles.py): the registry the submission check reads, the run (the same games for every
entry, paired with the default), agreement on the same decision points, and the anonymous public copy.
Seeds 93402300-93402999 (host probe bank 2, SEEDS.md)."""
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE), str(HERE.parents[2])]
os.environ["LADDER_EXTRA_PATH"] = str(HERE)
from ladder import deal  # noqa: E402
from ladder import puzzles as Z  # noqa: E402
from ladder import submit  # noqa: E402

ROOT = HERE.parents[2]
CODES = [l.strip().split("|")[1] for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(
    encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def test_add_and_run(tmp_path, monkeypatch):
    monkeypatch.setattr(Z, "DEFAULT", "bot:greedy")             # fast stand-in for the default strategy
    subs = tmp_path / "subs"
    Z.add(subs, "P01", CODES[1], "皇家护卫一题", public=tmp_path / "pub")
    with pytest.raises(Z.PuzzleError):
        Z.add(subs, "P01", CODES[1], "again")
    assert "P01" in (tmp_path / "pub" / "puzzles.md").read_text(encoding="utf-8")
    reg = json.loads((subs / "puzzles.json").read_text(encoding="utf-8"))
    assert sorted(reg["P01"]["deck"]) == sorted(submit.check_deck(CODES[1])[0])
    for i, (player, spec) in enumerate([("甲", "bot:greedy+plan"), ("乙", "bot:greedy"), ("甲", "bot:greedy")]):
        submit._append(subs, {"ev": "receipt", "id": f"S-{i + 1:04d}", "player": player, "kind": "puzzle",
                              "puzzle": "P01", "verdict": "收下", "spec": spec})
    assert [(e["name"], e["spec"]) for e in Z.entries(subs, "P01")] == [("甲", "bot:greedy"), ("乙", "bot:greedy")]
    kf = tmp_path / "k.key"
    deal.new_key_file(kf)
    host = Z.run(subs, "P01", (93402300, 93403000), tmp_path / "out", games=2, field="frozen7", agreement=4,
                 workers=2, key=str(kf))
    assert [r["entry"] for r in host["entries"]] == ["默认打法", "甲", "乙"]
    assert all(r["games"] == 14 for r in host["entries"])
    # 甲 and 乙 play the default's own strategy here: the same games, so no difference and full agreement
    assert host["entries"][1]["vs_default_pp"][0] == 0 and host["points"] == 4
    assert all(a["same"] == 1.0 for a in host["agreement"])
    pub = json.loads((tmp_path / "out" / "result-public.json").read_text(encoding="utf-8"))
    assert {r["entry"] for r in pub["entries"]} == {"默认打法", "选手 1", "选手 2"} and "seeds" not in pub
    assert "aliases" not in pub and sorted(host["aliases"]) == ["乙", "甲"]
    # neither the rows nor the a/b order tell who came first: references first, then 选手 1, 2
    assert [(a["a"], a["b"]) for a in pub["agreement"]] == [("默认打法", "选手 1"), ("默认打法", "选手 2"),
                                                            ("选手 1", "选手 2")]
    # a re-run into the same folder: 甲's newer strategy is played, the unchanged entries' games are kept, and 甲's
    # old games are not scored as the new version's
    submit._append(subs, {"ev": "receipt", "id": "S-0004", "player": "甲", "kind": "puzzle", "puzzle": "P01",
                          "verdict": "收下", "spec": "py:helpers:Random"})
    again = Z.run(subs, "P01", (93402300, 93403000), tmp_path / "out", games=2, field="frozen7", agreement=0,
                  workers=2, key=str(kf))
    logs = [json.loads(x) for x in (tmp_path / "out" / "games.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(logs) == 4 * 14                                     # 14 new games, for 甲's S-0004 only
    assert sum("py:helpers:Random" in g["strategies"] for g in logs) == 14
    assert [r["games"] for r in again["entries"]] == [14, 14, 14]


def test_aliases_are_drawn_fresh_every_run(tmp_path, monkeypatch):
    # the public order is a secret draw, not a function of the intake order (review 11-22)
    seen = set()
    import random as _r
    for _ in range(30):
        order = ["甲", "乙", "丙", "丁", "戊"]
        _r.Random(Z.secrets.randbits(64)).shuffle(order)
        seen.add(tuple(order))
    assert len(seen) > 5
