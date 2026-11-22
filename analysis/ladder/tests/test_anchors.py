"""Anchor matches (ladder/anchors.py): the panel, fixed seeds, only new versions played, the ledger and the report.
Seeds 93400220-93400339 (host probe bank 2, SEEDS.md) in place of the real panel 91700000-91799999."""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE), str(HERE.parents[2])]
os.environ["LADDER_EXTRA_PATH"] = str(HERE)
from ladder import anchors as A  # noqa: E402
from ladder import deal  # noqa: E402
from ladder.pool import Pool  # noqa: E402
from test_pool import BASE_DECKS  # noqa: E402


def test_the_panel_is_the_baseline_snapshot_and_the_hall_of_fame(tmp_path):
    # Salem S9: 基线快照 + 名人堂; no other bot tier
    rows = A.table()
    assert len(rows) == 7 and {r["tier"] for r in rows} == {"基线快照"} and [r["slot"] for r in rows] == list(range(7))
    assert sorted({r["craft"] for r in rows}) == [1, 2, 3, 4, 5, 6, 7]
    assert all(r["strategy"] == "bot:mcts:100+plan" for r in rows)
    hof = tmp_path / "hof.json"
    hof.write_text(json.dumps([{"slot": 7, "period": 1, "craft": 1, "mid": "m0009", "version": 1,
                                "deck": rows[0]["deck"], "strategy": "py:sub_S0001:X"}]), encoding="utf-8")
    rows = A.table(hof)
    assert rows[-1]["tier"] == "名人堂" and rows[-1]["slot"] == 7 and rows[-1]["id"] == "A07"


def test_induct_takes_each_class_first_with_enough_games(tmp_path):
    import random
    pool = Pool.create(tmp_path / "pool", (10 ** 12, 2 * 10 ** 12), rng_seed=3, check=True)
    strengths = {}
    for i, (d, owner, s) in enumerate([(BASE_DECKS[0], "甲", 0.08), (BASE_DECKS[0], "乙", 0.0),
                                       (BASE_DECKS[1], "baseline", 0.04), (BASE_DECKS[1], "丙", -0.04),
                                       (BASE_DECKS[2], "baseline", 0.0), (BASE_DECKS[3], "baseline", 0.0),
                                       (BASE_DECKS[4], "baseline", 0.0)]):
        mid = pool.enter(d, "bot:greedy", owner, rng=random.Random(i))
        strengths[mid] = s
    rng = random.Random(4)
    for _ in range(4000):
        job = pool.next_job()
        a, b = job["labels"]["members"]
        pool.settle({"id": job["id"], "result": "normal",
                     "winner": 0 if rng.random() < 0.5 + strengths[a] - strengths[b] else 1})
    hof = tmp_path / "hof.json"
    new = A.induct(pool.dir, hof, period=1)
    forest = [m for m in Pool(pool.dir).active() if m.owner == "甲"][0]
    assert [(h["craft"], h["mid"], h["slot"]) for h in new] == [(1, forest.mid, 7)]   # the Sword first is a baseline
    assert all(h["games"] >= A.HOF_MIN_GAMES for h in new)
    import pytest
    with pytest.raises(A.AnchorError):
        A.induct(pool.dir, hof, period=1)
    assert A.induct(pool.dir, hof, period=2) == []                # the same version only once


def test_anchor_run_plays_new_versions_only(tmp_path, monkeypatch):
    monkeypatch.setattr(A, "ANCHOR_SEEDS", (93400220, 93400340))
    monkeypatch.setattr(A, "STRIDE", 4)
    kf = tmp_path / "k.key"
    deal.new_key_file(kf)
    table = tmp_path / "anchors.json"
    quick = [dict(r, strategy="bot:greedy") for r in A.table()[:2]]     # fast stand-ins for the test
    table.write_text(json.dumps(quick, ensure_ascii=False), encoding="utf-8")
    pool = Pool.create(tmp_path / "pool", (93400330, 93400340), rng_seed=1)
    for d in BASE_DECKS[:2]:
        pool.enter(d, "bot:greedy", "baseline")
    jobs, todo = A.plan(quick, pool.dir, tmp_path / "out", 2)
    assert len(jobs) == 8 and len(todo) == 4
    assert sorted(j["seed"] for j in jobs) == [93400220, 93400220, 93400221, 93400221,
                                               93400224, 93400224, 93400225, 93400225]
    res = A.run(table, pool.dir, tmp_path / "out", games=2, workers=2, key=str(kf))
    assert res["played"] == 8 and res["deal"] == deal.key_id(deal.load_key(kf))
    lines = [json.loads(x) for x in (tmp_path / "out" / "anchors.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 4 and all(l["won"] + l["lost"] + l["draw"] + l["void"] == 2 for l in lines)
    again = A.run(table, pool.dir, tmp_path / "out", games=2, workers=2, key=str(kf))
    assert again["jobs"] == 0                                    # same versions: nothing to play
    rows = A.report(tmp_path / "out", table)
    assert {(r["member"], r["tier"]) for r in rows} == {(m.mid, "基线快照") for m in pool.active()}
    assert all(r["decided"] <= 4 for r in rows)
