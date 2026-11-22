"""Leaderboard (1.6) and frozen-pool evaluator (1.5): the interval machinery on series with known answers, rank
intervals, the window rules, freezing, and one short real evaluation through the runner (resume included).
The full fluctuation checks are tools/check_stats.py (made-up games) and the real-game checks in GATES.md.
Seeds: evaluation games 99001600-99001699 (host probe bank, SEEDS.md)."""
import dataclasses
import json
import math
import os
import random
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE), str(HERE.parents[2])]
os.environ["LADDER_EXTRA_PATH"] = str(HERE)
from ladder import evaluator as E  # noqa: E402
from ladder import leaderboard as L  # noqa: E402
from ladder import pool as P  # noqa: E402
from test_pool import BASE_DECKS, SEEDS, synth_deck  # noqa: E402


PLACEHOLDER = (10 ** 12, 2 * 10 ** 12)    # made-up results: these "seeds" are only reserved, never played


def ar1(n, phi, rng):
    x, out = 0.0, []
    for _ in range(n):
        x = phi * x + rng.gauss(0, 1)
        out.append(x)
    return out


def test_tau_on_independent_and_correlated_series():
    rng = random.Random(1)
    iid = [rng.gauss(0, 1) for _ in range(4000)]
    assert L.autocorr_time(iid) == pytest.approx(1.0, abs=0.35)
    phi = 0.9                                            # tau = (1 + phi) / (1 - phi) = 19
    taus = [L.autocorr_time(ar1(4000, phi, random.Random(k))) for k in range(10)]
    assert sum(taus) / len(taus) == pytest.approx(19, rel=0.2)


def test_tau_interval_covers_on_ar1():
    """Across many AR(1) series, the 95% interval for the mean covers 0 about 95% of the time."""
    cover, ratios = 0, []
    means, ses = [], []
    for k in range(120):
        xs = ar1(2000, 0.95, random.Random(100 + k))
        m, se, tau, df = L.tau_se(xs)
        half = L.t975(df) * se
        cover += (m - half) <= 0 <= (m + half)
        means.append(m), ses.append(se)
    sd = math.sqrt(sum(x * x for x in means) / len(means))
    assert 0.85 <= cover / 120 <= 1.0
    assert 0.8 <= sd / (sum(ses) / len(ses)) <= 1.3


def test_rank_intervals_ties_dont_chain():
    rows = [{"craft": "x", "ranked": True, "lo": lo, "hi": hi, "name": n}
            for n, lo, hi in (("a", 100, 140), ("b", 80, 110), ("c", 50, 90), ("d", -40, 0))]
    L.rank_intervals(rows)
    got = {r["name"]: (r["best"], r["worst"]) for r in rows}
    # a overlaps b only; b overlaps a and c; c overlaps b; d is below everyone
    assert got == {"a": (1, 2), "b": (1, 3), "c": (2, 3), "d": (4, 4)}


def made_up(tmp_path, n_games, strengths=(0.05, 0.0, -0.05, 0.0, 0.0, 0.0, 0.0)):
    # seven members: with three, S2 (nobody is matched past 200) soon leaves all three more than 200 apart and the
    # made-up ladder stalls (500-2200 games in a probe); seven stay together
    series = L.Series()
    pool = P.Pool.create(tmp_path / "lb", PLACEHOLDER, rng_seed=3, on_event=series)
    for i, craft in enumerate(range(1, len(strengths) + 1)):
        pool.enter(synth_deck(craft, 5), "bot:greedy", "baseline", rng=random.Random(50 + i))
    s = {m.mid: strengths[i] for i, m in enumerate(pool.active())}
    rng = random.Random(4)
    for _ in range(n_games):
        job = pool.next_job()
        a, b = job["labels"]["members"]
        pool.settle({"id": job["id"], "result": "normal",
                     "winner": 0 if rng.random() < 0.5 + s[a] - s[b] else 1})
    return pool, series


def test_board_window_unstable_and_update(tmp_path):
    pool, series = made_up(tmp_path, 8000)               # each of 7 members plays ~2/7 of the games
    rows = {r["mid"]: r for r in L.board(pool, series)}
    assert all(r["ranked"] and r["n"] == 2000 for r in rows.values())
    strong, mid_, weak = (pool.active()[i].mid for i in range(3))
    assert rows[strong]["rel_cr"] > rows[mid_]["rel_cr"] > rows[weak]["rel_cr"]
    # reading the log again gives the same board
    again_pool, again_series = L.load(tmp_path / "lb")
    assert [r["rel_cr"] for r in L.board(again_pool, again_series)] == [r["rel_cr"] for r in rows.values()]
    # a strategy update starts a new window: unstable, not ranked, until 2000 more games
    pool.advance(force="test"); pool.advance(force="test")
    pool.update(strong, "bot:greedy+plan", gate="G-test")
    rows = {r["mid"]: r for r in L.board(pool, series)}
    assert rows[strong]["n"] == 0 and not rows[strong]["ranked"] and rows[strong]["unstable"]
    # the public board still shows it (over its last 2000 games) and carries nothing private
    pub = L.public_board(pool, series)
    assert {r["anon"] for r in pub} == {m.anon for m in pool.active()}
    assert all(set(r) == {"anon", "craft", "baseline", "rel_cr", "lo", "hi", "best", "worst"} for r in pub)


def test_freeze_uses_the_last_1000_games(tmp_path):
    pool, series = made_up(tmp_path, 4500)
    body = E.freeze(tmp_path / "lb")
    for f in body["members"]:
        tail = series.points[f["mid"]][-1000:]
        assert f["cr"] == round(sum(c for c, _ in tail) / len(tail)) and f["cr_from"] == 1000
    frozen = [E.Frozen(**m) for m in body["members"]]
    others, mu = E.opponents_for(frozen, frozen[0].mid)
    assert frozen[0] not in others and mu == pytest.approx(sum(f.cr for f in others) / len(others))


def test_repeat_sync_finds_a_known_strength():
    frozen = [E.Frozen(mid=f"f{i}", anon="", craft=c, cr=1500, deck=[], strategy="") for i, c in
              enumerate((1, 2, 3, 4, 5, 6, 7))]
    others, mu = E.opponents_for(frozen, None)
    vals = [E.repeat_sync(lambda o, g: g.random() < 0.56, others, mu, 3000, 2000, random.Random(k))
            for k in range(6)]
    res = E.summarize(vals)
    # 6 pp over equals: CR gap where (16 + k) / 32 = 0.56 -> k = 1.92 -> between 48 and 75
    assert 40 < res["rel_cr"] < 85 and res["lo"] < res["rel_cr"] < res["hi"]


def test_repeat_sync_out_of_reach_waits_or_plays_the_closest(monkeypatch):
    """A candidate that wins everything climbs past 200 above the whole frozen pool. FAR "wait" (S2 strictly): it
    stays put there; FAR "closest" (A28): it goes on against the closest, +8 a win, so it walks on."""
    frozen = [E.Frozen(mid=f"f{i}", anon="", craft=c, cr=1500, deck=[], strategy="") for i, c in
              enumerate((1, 2, 3, 4, 5, 6, 7))]
    others, mu = E.opponents_for(frozen, None)
    monkeypatch.setattr(E, "FAR", "wait")
    v = E.repeat_sync(lambda o, g: True, others, mu, 400, 200, random.Random(1))
    assert 200 < v <= 208 and v == int(v)                # the first CR past 1700 (a win there is +8), all 200 at it
    monkeypatch.setattr(E, "FAR", "closest")
    v = E.repeat_sync(lambda o, g: True, others, mu, 400, 200, random.Random(1))
    assert v > 1000


def test_strict_waiting_reads_a_strong_candidate_too_high(monkeypatch):
    """LD-22: 6 pp over a pool all at 1500 (true gap 48-75). Waiting reads it near +200; the closest doesn't."""
    frozen = [E.Frozen(mid=f"f{i}", anon="", craft=c, cr=1500, deck=[], strategy="") for i, c in
              enumerate((1, 2, 3, 4, 5, 6, 7))]
    others, mu = E.opponents_for(frozen, None)
    out = {}
    for far in ("wait", "closest"):
        monkeypatch.setattr(E, "FAR", far)
        out[far] = E.summarize([E.repeat_sync(lambda o, g: g.random() < 0.56, others, mu, 3000, 2000,
                                              random.Random(k)) for k in range(6)])["rel_cr"]
    assert out["wait"] > 150 and 40 < out["closest"] < 85


def test_an_evaluation_out_of_reach_from_the_start_plays_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(E, "FAR", "wait")
    members = [E.Frozen(mid=f"f{i}", anon="", craft=c, cr=cr, deck=[], strategy="")
               for i, (c, cr) in enumerate(((2, 1000), (5, 2000)))]
    body = {"members": [dataclasses.asdict(m) for m in members], "hash": "test"}
    fz = tmp_path / "frozen.json"
    fz.write_text(json.dumps(body), encoding="utf-8")
    cand = E.Candidate("outside", 7, [], "py:helpers:Random")
    ev = E.Evaluation(fz, tmp_path / "eval", cand, (99001600, 99001700), games=10, tail=5, repeats=2, rng_seed=1)
    assert ev.done() and list(ev.jobs()) == []
    res = ev.run(workers=1)
    assert res["rel_cr"] == 0 and [s["after"] for s in res["stuck"]] == [0, 0]
    assert not (tmp_path / "eval" / "starts.jsonl").exists()


def test_a_short_real_evaluation_and_resume(tmp_path):
    pool = P.Pool.create(tmp_path / "pool", SEEDS, rng_seed=5)
    for craft in (2, 5, 7):
        pool.enter(BASE_DECKS[craft - 1], "py:helpers:Random", "baseline", rng=random.Random(craft))
    fz = tmp_path / "frozen.json"
    fz.write_text(json.dumps(E.freeze(tmp_path / "pool", cr="current")), encoding="utf-8")
    frozen, _ = E.load_frozen(fz)
    cand = E.candidate_from(frozen, mid=frozen[0].mid)
    out = tmp_path / "eval"
    ev = E.Evaluation(fz, out, cand, (99001600, 99001700), games=10, tail=5, repeats=2, rng_seed=1)
    res = ev.run(workers=2, step_limit=10.0)
    assert res["repeats"] == 2 and all(len(c) >= 10 for c in ev.crs)
    starts = [json.loads(l) for l in (out / "starts.jsonl").read_text().splitlines()]
    assert len({s["seed"] for s in starts}) == len(starts) and all(99001600 <= s["seed"] < 99001700 for s in starts)
    assert all(s["opp"] != cand.mid for s in starts)
    # a machine stop: the last finished game is lost from the log; on resume it is played again, same seed
    lines = (out / "games.jsonl").read_text().splitlines()
    lost = json.loads(lines[-1])
    (out / "games.jsonl").write_text("\n".join(lines[:-1]) + "\n")
    again = E.Evaluation(fz, out, cand, (99001600, 99001700), games=10, tail=5, repeats=2, rng_seed=1)
    assert [s["id"] for s in again.redo] == [lost["id"]]
    again.run(workers=1, step_limit=10.0)
    redone = [json.loads(l) for l in (out / "games.jsonl").read_text().splitlines() if lost["id"] in l]
    assert redone and redone[0]["seed"] == lost["seed"] and redone[0]["labels"]["rerun"]
    with pytest.raises(P.PoolError):                     # another evaluation can't reuse the folder
        E.Evaluation(fz, out, cand, (99001600, 99001700), games=12, tail=5, repeats=2)
