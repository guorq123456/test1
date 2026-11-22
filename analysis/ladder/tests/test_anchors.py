"""Anchor matches (ladder/anchors.py): the panel, every member against every anchor once a period on fresh seeds
(S11, A48), seeds used up in order, a period played once and resumed, setup voids played again, the ledger written
in one go and counted once marked done, the host rows and the public per-class figures.
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


def _ledger_games(out):
    return sum(l["won"] + l["lost"] + l["draw"] + l["void"] for l in A._ledger(out))


def test_every_member_plays_every_anchor_once_a_period_on_fresh_seeds(tmp_path, monkeypatch):
    kf, table, quick, pool = _setup(tmp_path, monkeypatch)
    out = tmp_path / "out"
    jobs, todo = A.plan(quick, pool.dir, 2, out=out)
    assert len(jobs) == 8 and len(todo) == 4
    assert sorted(j["seed"] for j in jobs) == list(range(93400220, 93400228))      # the segment's start, one a game
    res = A.run(table, pool.dir, out, games=2, workers=2, key=str(kf))
    assert res["played"] == 8 and res["deal"] == deal.key_id(deal.load_key(kf)) and res["period"] == 0
    assert (res["first_seed"], res["last_seed"]) == (93400220, 93400227)
    lines = A._ledger(out)
    assert len(lines) == 4 and all(l["won"] + l["lost"] + l["draw"] + l["void"] == 2 for l in lines)
    assert {l["period"] for l in lines} == {0} and {l["tier"] for l in lines} == {"基线快照"}
    assert len({l["batch"] for l in lines}) == 1 and A._plans(out)[0]["done"] == lines[0]["batch"]
    import pytest
    with pytest.raises(A.AnchorError):                           # a period once
        A.run(table, pool.dir, out, games=2, workers=2, key=str(kf))
    nxt = A.run(table, pool.dir, out, games=2, workers=2, key=str(kf), period=1)
    assert nxt["played"] == 8 and (nxt["first_seed"], nxt["last_seed"]) == (93400228, 93400235)   # right after P0
    rows = A.report(out, table)
    assert {(r["member"], r["tier"], r["period"]) for r in rows} == {(m.mid, "基线快照", 1) for m in pool.active()}
    assert all(r["decided"] <= 4 for r in rows)
    with pytest.raises(A.AnchorError):                           # past the segment: register a new one first
        A.plan(quick, pool.dir, 100, period=2, out=out)


def test_an_interrupted_period_picks_up_its_own_games_and_refuses_a_changed_plan(tmp_path, monkeypatch):
    kf, table, quick, pool = _setup(tmp_path, monkeypatch)
    out = tmp_path / "out"
    from ladder import runner
    real = runner.run

    def stops(jobs, path, **kw):
        real(jobs[:3], path, **kw)
        raise KeyboardInterrupt

    monkeypatch.setattr(runner, "run", stops)
    import pytest
    with pytest.raises(KeyboardInterrupt):
        A.run(table, pool.dir, out, games=2, workers=2, key=str(kf))
    assert not (out / "anchors.jsonl").exists() and not A._plans(out)[0].get("done")
    monkeypatch.setattr(runner, "run", real)
    res = A.run(table, pool.dir, out, games=2, workers=2, key=str(kf))
    assert res["played"] == 5                                    # the three played are not played again
    assert _ledger_games(out) == 8
    monkeypatch.setattr(runner, "run", stops)
    with pytest.raises(KeyboardInterrupt):
        A.run(table, pool.dir, out, games=2, workers=2, key=str(kf), period=1)
    monkeypatch.setattr(runner, "run", real)
    pool.enter(BASE_DECKS[2], "bot:greedy", "baseline")         # the pool changed after the period's run started
    with pytest.raises(A.AnchorError):
        A.run(table, pool.dir, out, games=2, workers=2, key=str(kf), period=1)
    # the unfinished period 1 keeps its seeds: period 2 starts after them
    assert A.plan(quick, pool.dir, 2, period=2, out=out)[0][0]["seed"] == 93400228 + 8


def test_a_setup_void_is_played_again_once_and_written_down_if_it_comes_back(tmp_path, monkeypatch):
    kf, table, quick, pool = _setup(tmp_path, monkeypatch)
    from ladder import runner
    real = runner.run
    calls = []

    def dies(jobs, path, **kw):                                  # the first job's worker dies (every time, or once)
        calls.append(len(jobs))
        if len(calls) > 1 and once:
            return real(jobs, path, **kw)
        res = real(jobs[1:], path, **kw)
        sealed = deal.seal(jobs[0], deal.load_key(kf))           # what the runner's stub line carries
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": jobs[0]["id"], "seed": jobs[0]["seed"], "labels": jobs[0]["labels"],
                                "deal": sealed["deal"], "result": "void", "error": "worker died (exit code 1)"}) + "\n")
        return res

    monkeypatch.setattr(runner, "run", dies)
    once = True                                                  # the machine: fine the second time
    res = A.run(table, pool.dir, tmp_path / "a", games=2, workers=2, key=str(kf))
    assert calls == [8, 1] and res["played"] == 8 and res["voids"] == {}
    assert _ledger_games(tmp_path / "a") == 8 and all(l["void"] == 0 for l in A._ledger(tmp_path / "a"))
    assert sorted(A._ledger(tmp_path / "a")[0]["logs"]) == ["games-P0-redo1.jsonl", "games-P0.jsonl"]
    once, calls[:] = False, []                                   # comes back on its own seed: deterministic
    res = A.run(table, pool.dir, tmp_path / "b", games=2, workers=2, key=str(kf))
    assert calls == [8, 1] and res["voids"] == {"worker died (exit code 1)": 1}
    assert sum(l["void"] for l in A._ledger(tmp_path / "b")) == 1 and A._plans(tmp_path / "b")[0]["done"]


def test_a_game_is_played_again_at_most_once_whatever_happens_to_the_runs(tmp_path, monkeypatch):
    kf, table, quick, pool = _setup(tmp_path, monkeypatch)
    out = tmp_path / "out"
    from ladder import runner
    real = runner.run

    def dies(jobs, path, **kw):                                  # the first job's worker dies every time
        res = real(jobs[1:], path, **kw)
        sealed = deal.seal(jobs[0], deal.load_key(kf))
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": jobs[0]["id"], "seed": jobs[0]["seed"], "labels": jobs[0]["labels"],
                                "deal": sealed["deal"], "result": "void", "error": "worker died (exit code 1)"}) + "\n")
        return res

    monkeypatch.setattr(runner, "run", dies)
    real_write = A._write_json

    def no_done(path, value):                                    # the run stops before the period is marked done
        if "done" in value:
            raise KeyboardInterrupt
        real_write(path, value)

    monkeypatch.setattr(A, "_write_json", no_done)
    import pytest
    with pytest.raises(KeyboardInterrupt):
        A.run(table, pool.dir, out, games=2, workers=2, key=str(kf))
    monkeypatch.setattr(A, "_write_json", real_write)
    res = A.run(table, pool.dir, out, games=2, workers=2, key=str(kf))
    assert not (out / "games-P0-redo2.jsonl").exists()            # voided twice already: written down, not replayed
    assert res["voids"] == {"worker died (exit code 1)": 1} and A._plans(out)[0]["done"]
    assert len(A._lines(out)[1]) == 4                             # the first, interrupted batch doesn't count


def test_a_torn_ledger_tail_does_not_swallow_the_next_write(tmp_path, monkeypatch):
    kf, table, quick, pool = _setup(tmp_path, monkeypatch)
    out = tmp_path / "out"
    A.run(table, pool.dir, out, games=2, workers=2, key=str(kf))
    led = out / "anchors.jsonl"
    text = led.read_text(encoding="utf-8")
    first = text.index("\n") + 1
    led.write_text(text[:first + 40] + "\x00" * 64, encoding="utf-8")      # a crash inside the one write
    plan = A._plans(out)[0]
    for k in ("done", "lines", "done_time"):
        plan.pop(k)
    A._write_json(out / "plan-P0.json", plan)
    assert A.classes(out) == (None, [])                           # not finished: nothing counts
    res = A.run(table, pool.dir, out, games=2, workers=2, key=str(kf))
    assert res["played"] == 0 and len(A._lines(out)[1]) == 4      # all four pairs of the new batch


def test_a_strategy_that_does_not_load_stops_the_run_before_any_game(tmp_path, monkeypatch):
    kf, table, quick, pool = _setup(tmp_path, monkeypatch)
    code = tmp_path / "code"
    code.mkdir()
    (code / "sub_T0001.py").write_text("from ladder.strategy import BotStrategy\n\n\n"
                                       "class Mine(BotStrategy):\n    def __init__(self, seed=0):\n"
                                       "        super().__init__('greedy', seed=seed)\n", encoding="utf-8")
    monkeypatch.delenv("LADDER_EXTRA_PATH", raising=False)
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != str(HERE)])
    pool.enter(BASE_DECKS[2], "py:sub_T0001:Mine", "baseline")     # owner aside: a received strategy
    out = tmp_path / "out"
    import pytest
    with pytest.raises(A.AnchorError) as e:
        A.run(table, pool.dir, out, games=2, workers=2, key=str(kf))
    assert "sub_T0001" in str(e.value) and not (out / "plan-P0.json").exists()
    res = A.run(table, pool.dir, out, games=2, workers=2, key=str(kf), code=code)
    assert res["played"] == 12 and res["voids"] == {}


def test_only_a_finished_period_counts_and_a_torn_ledger_line_is_skipped(tmp_path):
    def line(period, batch, won):
        return json.dumps({"period": period, "member": "m0001", "version": 1, "craft": 1, "anchor": "A00",
                           "tier": "基线快照", "games": 20, "won": won, "lost": 20 - won, "draw": 0, "void": 0,
                           "batch": batch}) + "\n"
    (tmp_path / "anchors.jsonl").write_text(line(1, "a", 2) + '{"period": 1, "memb' + "\x00" * 8 + "\n" +
                                            line(1, "b", 12) + line(2, "c", 18), encoding="utf-8")
    A._write_json(tmp_path / "plan-P1.json", {"period": 1, "jobs": 20, "first_seed": 1, "done": "b", "lines": 1})
    A._write_json(tmp_path / "plan-P2.json", {"period": 2, "jobs": 20, "first_seed": 21})       # not finished
    period, rows = A.classes(tmp_path)
    assert period == 1 and rows[0]["rate"] == 60                 # batch b only: not a's, not unfinished period 2
    A._write_json(tmp_path / "plan-P1.json", {"period": 1, "jobs": 20, "first_seed": 1, "done": "b", "lines": 2})
    assert A.classes(tmp_path) == (None, [])                      # the batch is missing a line: it doesn't count


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
                           "games": 20, "won": won, "lost": lost, "draw": 0, "void": 20 - won - lost,
                           "batch": f"b{period}"}) + "\n"
    for p in (1, 2):
        A._write_json(tmp_path / f"plan-P{p}.json", {"period": p, "jobs": 60, "first_seed": 60 * p, "done": f"b{p}"})
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
