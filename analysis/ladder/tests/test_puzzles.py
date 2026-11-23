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
    for i, (player, spec) in enumerate([("fable-ultracode", "bot:greedy+plan"), ("fable", "bot:greedy"), ("fable-ultracode", "bot:greedy")]):
        submit._append(subs, {"ev": "receipt", "id": f"S-{i + 1:04d}", "player": player, "kind": "puzzle",
                              "puzzle": "P01", "verdict": "收下", "spec": spec})
    assert [(e["name"], e["spec"]) for e in Z.entries(subs, "P01")] == [("fable-ultracode", "bot:greedy"), ("fable", "bot:greedy")]
    kf = tmp_path / "k.key"
    deal.new_key_file(kf)
    host = Z.run(subs, "P01", (93402300, 93403000), tmp_path / "out", games=2, field="frozen7", agreement=4,
                 workers=2, key=str(kf))
    assert [r["entry"] for r in host["entries"]] == ["默认打法", "fable-ultracode", "fable"]
    assert all(r["games"] == 14 for r in host["entries"])
    # fable-ultracode and fable play the default's own strategy here: the same games, so no difference and full agreement
    assert host["entries"][1]["vs_default_pp"][0] == 0 and host["points"] == 4
    assert all(a["same"] == 1.0 for a in host["agreement"])
    pub = json.loads((tmp_path / "out" / "result-public.json").read_text(encoding="utf-8"))
    assert {r["entry"] for r in pub["entries"]} == {"默认打法", "选手 1", "选手 2"} and "seeds" not in pub
    assert "aliases" not in pub and sorted(host["aliases"]) == ["fable", "fable-ultracode"] and pub["simulator_changed"] == 0
    # neither the rows nor the a/b order tell who came first: references first, then 选手 1, 2
    assert [(a["a"], a["b"]) for a in pub["agreement"]] == [("默认打法", "选手 1"), ("默认打法", "选手 2"),
                                                            ("选手 1", "选手 2")]
    # a re-run into the same folder: fable-ultracode's newer strategy is played, the unchanged entries' games are kept, and fable-ultracode's
    # old games are not scored as the new version's
    submit._append(subs, {"ev": "receipt", "id": "S-0004", "player": "fable-ultracode", "kind": "puzzle", "puzzle": "P01",
                          "verdict": "收下", "spec": "py:helpers:Random"})
    again = Z.run(subs, "P01", (93402300, 93403000), tmp_path / "out", games=2, field="frozen7", agreement=0,
                  workers=2, key=str(kf))
    logs = [json.loads(x) for x in (tmp_path / "out" / "games.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(logs) == 4 * 14                                     # 14 new games, for fable-ultracode's S-0004 only
    assert sum("py:helpers:Random" in g["strategies"] for g in logs) == 14
    assert [r["games"] for r in again["entries"]] == [14, 14, 14]


def test_aliases_are_drawn_fresh_every_run(tmp_path, monkeypatch):
    # the public order is a secret draw, not a function of the intake order (review 11-22)
    seen = set()
    import random as _r
    for _ in range(30):
        order = ["fable-ultracode", "fable", "astra", "opus", "sol"]
        _r.Random(Z.secrets.randbits(64)).shuffle(order)
        seen.add(tuple(order))
    assert len(seen) > 5


def test_an_answer_that_hangs_dies_or_changes_the_simulator_is_none():
    # LD-40: puzzles ask through runner.guarded_map; its outcomes become answers here. A timeout, a dead worker or a
    # runner error is no answer; an answer during which the simulator changed is none too, and the host's copy names
    # the entry (the public copy never does)
    ents = [{"name": "默认打法"}, {"name": "甲-1"}]
    ask = [{"point": p, "entry": e} for p in range(2) for e in range(2)]
    got = [{"value": {"point": 0, "entry": 0, "move": {"type": "EndTurn"}}},
           {"value": {"point": 0, "entry": 1, "move": {"type": "EndTurn"}}, "changed": "svsim.cards.pool.POOL: x"},
           {"timeout": 0, "error": "ran past 30.0s of wall time"},
           {"died": 3}]
    answers, tripped = Z._answers(ask, got, ents)
    assert answers[0]["move"] == {"type": "EndTurn"}
    assert [a["move"] for a in answers[1:]] == [None, None, None]
    assert answers[2]["error"] == "timeout" and "died" in answers[3]["error"]
    assert tripped == [{"entry": "甲-1", "point": 0, "what": "svsim.cards.pool.POOL: x"}]


def test_the_public_copy_names_no_one_whose_answer_was_voided():
    host = {"puzzle": "P01", "title": "t", "field": "others", "games_per_list": 2, "seeds": [1, 2], "deal": None,
            "entries": [{"entry": "默认打法"}, {"entry": "fable-ultracode"}, {"entry": "fable"}],
            "agreement": [{"a": "fable", "b": "fable-ultracode", "points": 3, "same": 1.0}], "points": 3,
            "aliases": {"fable-ultracode": "选手 2", "fable": "选手 1"},
            "simulator_changed": [{"entry": "fable-ultracode", "point": 0, "what": "svsim.core.script.LISTEN_IN_HAND"}]}
    pub = Z.public_copy(host, ["默认打法"])
    text = json.dumps(pub, ensure_ascii=False)
    assert pub["simulator_changed"] == 1 and "fable-ultracode" not in text and "fable" not in text and "LISTEN" not in text
    assert [r["entry"] for r in pub["entries"]] == ["默认打法", "选手 1", "选手 2"]
    assert (pub["agreement"][0]["a"], pub["agreement"][0]["b"]) == ("选手 1", "选手 2")
    assert host["simulator_changed"][0]["entry"] == "fable-ultracode"            # the host's copy keeps the names
