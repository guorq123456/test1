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


def test_the_panel():
    rows = A.table()
    assert len(rows) == 28 and {r["tier"] for r in rows} == set(A.TIERS)
    assert sorted({r["craft"] for r in rows}) == [1, 2, 3, 4, 5, 6, 7]
    assert all(r["strategy"] == A.TIERS[r["tier"]] for r in rows)


def test_anchor_run_plays_new_versions_only(tmp_path, monkeypatch):
    monkeypatch.setattr(A, "ANCHOR_SEEDS", (93400220, 93400340))
    monkeypatch.setattr(A, "STRIDE", 4)
    kf = tmp_path / "k.key"
    deal.new_key_file(kf)
    table = tmp_path / "anchors.json"
    quick = [r for r in A.table() if r["tier"] == "快速"][:2]
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
    assert {(r["member"], r["tier"]) for r in rows} == {(m.mid, "快速") for m in pool.active()}
    assert all(r["decided"] <= 4 for r in rows)
