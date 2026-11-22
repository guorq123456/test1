"""Anchor matches (ladder/anchors.py): the panel, every member against every anchor once a period on fresh seeds
(S11, A48), a period played once and resumed, the ledger, the host rows and the public per-class figures.
Seeds 93400220-93400339 (host probe bank 2, SEEDS.md) in place of the real segment 93510000-94509999."""
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


def _setup(tmp_path, monkeypatch, members=2):
    monkeypatch.setattr(A, "ANCHOR_SEEDS", (93400220, 93400340))
    monkeypatch.setattr(A, "PERIOD_BLOCK", 40)
    kf = tmp_path / "k.key"
    deal.new_key_file(kf)
    table = tmp_path / "anchors.json"
    quick = [dict(r, strategy="bot:greedy") for r in A.table()[:2]]     # fast stand-ins for the test
    table.write_text(json.dumps(quick, ensure_ascii=False), encoding="utf-8")
    pool = Pool.create(tmp_path / "pool", (93400330, 93400340), rng_seed=1)
    for d in BASE_DECKS[:members]:
        pool.enter(d, "bot:greedy+plan", "baseline")
    return kf, table, quick, Pool(pool.dir)


def test_the_anchor_segment_is_formal():
    lo, hi = A.ANCHOR_SEEDS
    assert deal.formal(lo) and deal.formal(hi - 1) and not deal.formal(hi)
    assert (hi - lo) // A.PERIOD_BLOCK >= 20


def test_every_member_plays_every_anchor_once_a_period_on_fresh_seeds(tmp_path, monkeypatch):
    kf, table, quick, pool = _setup(tmp_path, monkeypatch)
    jobs, todo = A.plan(quick, pool.dir, 2)
    assert len(jobs) == 8 and len(todo) == 4
    assert sorted(j["seed"] for j in jobs) == list(range(93400220, 93400228))      # period 0's block, one seed a game
    res = A.run(table, pool.dir, tmp_path / "out", games=2, workers=2, key=str(kf))
    assert res["played"] == 8 and res["deal"] == deal.key_id(deal.load_key(kf)) and res["period"] == 0
    lines = [json.loads(x) for x in (tmp_path / "out" / "anchors.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 4 and all(l["won"] + l["lost"] + l["draw"] + l["void"] == 2 for l in lines)
    assert {l["period"] for l in lines} == {0} and {l["tier"] for l in lines} == {"基线快照"}
    import pytest
    with pytest.raises(A.AnchorError):                           # a period once
        A.run(table, pool.dir, tmp_path / "out", games=2, workers=2, key=str(kf))
    nxt = A.run(table, pool.dir, tmp_path / "out", games=2, workers=2, key=str(kf), period=1)
    assert nxt["played"] == 8
    seeds = {json.loads(x)["seed"] for x in (tmp_path / "out" / "games-P1.jsonl").read_text(encoding="utf-8").splitlines()}
    assert seeds == set(range(93400260, 93400268))               # a new block, not period 0's seeds
    rows = A.report(tmp_path / "out", table)
    assert {(r["member"], r["tier"], r["period"]) for r in rows} == {(m.mid, "基线快照", 1) for m in pool.active()}
    assert all(r["decided"] <= 4 for r in rows)
    with pytest.raises(A.AnchorError):                           # past the segment: register a new one first
        A.plan(quick, pool.dir, 2, period=3)


def test_an_interrupted_period_picks_up_its_own_games_and_refuses_a_changed_plan(tmp_path, monkeypatch):
    kf, table, quick, pool = _setup(tmp_path, monkeypatch)
    from ladder import runner
    real = runner.run

    def stops(jobs, out, **kw):
        real(jobs[:3], out, **kw)
        raise KeyboardInterrupt

    monkeypatch.setattr(runner, "run", stops)
    import pytest
    with pytest.raises(KeyboardInterrupt):
        A.run(table, pool.dir, tmp_path / "out", games=2, workers=2, key=str(kf))
    assert not (tmp_path / "out" / "anchors.jsonl").exists()
    monkeypatch.setattr(runner, "run", real)
    res = A.run(table, pool.dir, tmp_path / "out", games=2, workers=2, key=str(kf))
    assert res["played"] == 5                                    # the three played are not played again
    lines = (tmp_path / "out" / "anchors.jsonl").read_text(encoding="utf-8").splitlines()
    assert sum(json.loads(x)["won"] + json.loads(x)["lost"] + json.loads(x)["draw"] + json.loads(x)["void"]
               for x in lines) == 8
    monkeypatch.setattr(runner, "run", stops)
    with pytest.raises(KeyboardInterrupt):
        A.run(table, pool.dir, tmp_path / "out", games=2, workers=2, key=str(kf), period=1)
    monkeypatch.setattr(runner, "run", real)
    pool.enter(BASE_DECKS[2], "bot:greedy", "baseline")         # the pool changed after the period's run started
    with pytest.raises(A.AnchorError):
        A.run(table, pool.dir, tmp_path / "out", games=2, workers=2, key=str(kf), period=1)


def test_a_member_plays_its_own_frozen_copy_too(tmp_path):
    # A48: no skipped pairs, so every member plays the same number of games and the counts tell nothing (a baseline
    # member is its class's 基线快照 anchor; a hall-of-fame member may still be on the frozen version)
    rows = A.table()[:2]
    pool = Pool.create(tmp_path / "pool", (93400330, 93400340), rng_seed=1, check=True)
    from ladder.runner import load_deck
    for r in rows:
        pool.enter([c.card_id for c in load_deck(r["deck"])], r["strategy"], "baseline")
    jobs, todo = A.plan(rows, pool.dir, 2)
    assert len(todo) == 4 and len(jobs) == 8
    per = {}
    for j in jobs:
        per[j["labels"]["member"]] = per.get(j["labels"]["member"], 0) + 1
    assert sorted(per.values()) == [4, 4]


def test_public_figures_are_per_class_and_tier_without_ids_or_counts(tmp_path):
    def line(period, mid, craft, aid, tier, won, lost):
        return json.dumps({"period": period, "member": mid, "version": 1, "craft": craft, "anchor": aid, "tier": tier,
                           "games": 20, "won": won, "lost": lost, "draw": 0, "void": 20 - won - lost}) + "\n"
    (tmp_path / "anchors.jsonl").write_text(
        line(1, "m0001", 1, "A00", "基线快照", 1, 19) +                 # an older period: not shown
        line(2, "m0001", 1, "A00", "基线快照", 14, 6) + line(2, "m0002", 2, "A00", "基线快照", 8, 12) +
        line(2, "m0001", 1, "A07", "名人堂", 10, 10) +
        json.dumps({"member": "m0003", "version": 1, "anchor": "A00", "games": 10, "won": 9, "lost": 1}) + "\n",
        encoding="utf-8")                                             # a line of the old fixed panel: ignored
    period, rows = A.classes(tmp_path)
    assert period == 2
    assert [(r["craft"], r["tier"]) for r in rows] == [("精灵", "基线快照"), ("精灵", "名人堂"), ("皇家护卫", "基线快照"),
                                                       ("全池", "基线快照"), ("全池", "名人堂")]
    assert rows[0] == {"craft": "精灵", "tier": "基线快照", "rate": 70, "lo": 48, "hi": 85}
    assert rows[3]["rate"] == 55 and set(rows[3]) == {"craft", "tier", "rate", "lo", "hi"}
    assert A.classes(tmp_path, 1)[1][0]["rate"] == 5
    table = tmp_path / "anchors.json"
    table.write_text(json.dumps(A.table()[:1] + [{"id": "A07", "tier": "名人堂"}], ensure_ascii=False),
                     encoding="utf-8")
    host = A.report(tmp_path, table)
    assert {(r["member"], r["tier"], r["won"], r["decided"]) for r in host} == {
        ("m0001", "基线快照", 14, 20), ("m0002", "基线快照", 8, 20), ("m0001", "名人堂", 10, 20)}
