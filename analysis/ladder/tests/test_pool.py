"""The pool manager (phase 1, item 1.4): every rule branch with synthetic members and made-up results, the
zero-sum check, resuming from the event log, and one short real ladder through the batch runner.
Ladder seeds 99001700-99001999 (host probe bank, SEEDS.md); deck seeds for synthetic lists 99001700+."""
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
os.environ["LADDER_EXTRA_PATH"] = str(HERE)
from ladder import pool as P  # noqa: E402
from ladder import rules  # noqa: E402
from ladder.runner import load_deck  # noqa: E402
from ladder.replay import replay_moves  # noqa: E402
from svsim.cards.decks import random_deck  # noqa: E402
from svsim.core.enums import Craft  # noqa: E402

ROOT = HERE.parents[2]
CODES = [l.strip().split("|")[1] for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(
    encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
BASE_DECKS = [[c.card_id for c in load_deck(code)] for code in CODES]       # one per class, classes 1..7 in order
SEEDS = (99001700, 99002000)


def synth_deck(craft, i):
    return [c.card_id for c in random_deck(Craft(craft), random.Random(99001700 + 100 * craft + i))]


def new_pool(tmp_path, name="p"):
    return P.Pool.create(tmp_path / name, SEEDS, rng_seed=7)


def finish(pool, job, winner, result="normal"):
    return pool.settle({"id": job["id"], "result": result, "winner": winner})


def baseline_pool(tmp_path, name="p"):
    pool = new_pool(tmp_path, name)
    for d in BASE_DECKS:
        pool.enter(d, "bot:mcts:100+plan", "baseline", rng=random.Random(len(pool.members)))
    return pool


def test_entry_and_mu(tmp_path):
    pool = baseline_pool(tmp_path)
    assert [m.craft for m in pool.active()] == [1, 2, 3, 4, 5, 6, 7]
    assert all(m.cr == 1500 for m in pool.active()) and pool.mu == 1500
    assert len({m.anon for m in pool.active()}) == 7
    for _ in range(40):                                  # move mu away from 1500, then a newcomer still enters at 1500
        job = pool.next_job()
        finish(pool, job, 0 if pool.members[job["labels"]["members"][0]].craft == 1 else 1)
    assert pool.mu == pytest.approx(1500)                # zero-sum: no removal, so mu stays
    pool.advance(force="test")                           # to the first deck period
    mid = pool.enter(synth_deck(1, 0), "py:helpers:Random", "fable-ultracode")
    assert pool.members[mid].cr == 1500


def test_zero_sum_and_settlement_by_the_rules(tmp_path):
    pool = baseline_pool(tmp_path)
    total = pool.total_cr()
    rng = random.Random(1)
    for _ in range(300):
        job = pool.next_job()
        a, b = (pool.members[x] for x in job["labels"]["members"])
        ca, cb = a.cr, b.cr
        w = rng.randrange(2)
        ev = finish(pool, job, w)
        winner, loser = (a, b) if w == 0 else (b, a)
        cw, cl = (ca, cb) if w == 0 else (cb, ca)
        assert winner.cr - cw == rules.delta(cw, cl, True) and loser.cr - cl == rules.delta(cl, cw, False)
        assert sum(ev["deltas"]) == 0
    assert pool.total_cr() == total and pool.cr_sum_check == 0


def test_draws_and_void_change_nothing(tmp_path):
    pool = baseline_pool(tmp_path)
    before = {m.mid: (m.cr, m.games) for m in pool.active()}
    j1, j2 = pool.next_job(), pool.next_job()
    finish(pool, j1, None, "draw")
    finish(pool, j2, None, "void")
    assert {m.mid: (m.cr, m.games) for m in pool.active()} == before
    assert sum(m.draws for m in pool.active()) == 2
    j3 = pool.next_job()
    finish(pool, j3, 1, "timeout")                       # a timeout (or crash, illegal) is a loss for its maker
    assert sum(m.games for m in pool.active()) == 2


def out_of_protection(*ms):
    for m in ms:
        m.full_strategy_period, m.games = True, 5000      # out of protection (test-only direct state)


def test_matching_only_within_200_and_redraws(tmp_path):
    """S2: a class with nobody within 200 is drawn again; nobody is ever matched past 200."""
    pool = new_pool(tmp_path)
    for craft in (1, 2):
        for i in range(2):
            pool.enter(synth_deck(craft, i), "bot:greedy", "baseline", rng=random.Random(craft * 10 + i))
    f1, f2, s1, s2 = pool.active()
    out_of_protection(f1, f2, s1, s2)
    f1.cr, f2.cr, s1.cr, s2.cr = 1600, 1560, 1550, 1380   # s2 reaches f2 (180) and s1 (170), not f1 (220)
    rng = random.Random(3)
    s2_vs, f1_vs = Counter(), Counter()
    for _ in range(20000):
        a, b, how = pool.draw_pair(rng)
        assert a is not b and how == "window" and rules.within_window(a.cr, b.cr)
        if a is s2:
            s2_vs[b.mid] += 1
        if a is f1:
            f1_vs[b.mid] += 1
    # s2 against Forest is always f2; Forest and Sword each half (Forest is not "nobody", f1 is just out of reach)
    assert set(s2_vs) == {f2.mid, s1.mid}
    assert s2_vs[f2.mid] / sum(s2_vs.values()) == pytest.approx(0.5, abs=0.03)
    assert set(f1_vs) == {f2.mid, s1.mid}                 # f1 never meets s2 (220 apart)
    assert pool.isolated() == []


def test_isolated_members_are_never_drawn(tmp_path):
    pool = new_pool(tmp_path)
    for craft in (1, 2):
        for i in range(2):
            pool.enter(synth_deck(craft, i), "bot:greedy", "baseline", rng=random.Random(craft * 10 + i))
    f1, f2, s1, s2 = pool.active()
    out_of_protection(f1, f2, s1, s2)
    f1.cr, f2.cr, s1.cr, s2.cr = 1600, 1560, 1550, 1290   # s2: 260 or more from everyone; mu 1500
    # the weight still follows §4.2: s2 is 210 below mu -> 1 - 0.8 * 10/100 = 0.92
    assert pool.weight(s2) == pytest.approx(0.92)
    assert pool.isolated() == [s2.mid]
    rng = random.Random(4)
    picks = Counter()
    for _ in range(9000):
        a, b, _ = pool.draw_pair(rng)
        assert s2 not in (a, b)
        picks[a.mid] += 1
    for m in (f1, f2, s1):                                # the initiator is drawn again among the rest
        assert picks[m.mid] / 9000 == pytest.approx(1 / 3, abs=0.02)
    with pytest.raises(P.NoOpponent):
        P.pick_opponent(s2, pool.active(), pool.mu, rng)
    # frozen pools only (A28): the closest instead, marked "far"
    far = Counter(P.pick_opponent(s2, pool.active(), pool.mu, rng, far="closest")[0].mid for _ in range(200))
    assert set(far) == {s1.mid}                           # 1550 is the closest to 1290
    assert P.pick_opponent(f1, pool.active(), pool.mu, rng, far="closest")[1] == "window"
    assert pool.stuck() is None
    # nobody within 200 of anybody: stalled, and the job stream ends instead of raising
    f1.cr, f2.cr, s1.cr, s2.cr = 2100, 1800, 1500, 1200
    assert sorted(pool.isolated()) == sorted(m.mid for m in (f1, f2, s1, s2))
    with pytest.raises(P.Stalled):
        pool.draw_pair(rng)
    assert pool.stuck()["why"] == "stalled"
    assert list(pool.jobs(games=5)) == []


def test_period_stops_when_only_isolated_members_are_short(tmp_path):
    pool = new_pool(tmp_path)
    for craft in (1, 2, 3):
        pool.enter(BASE_DECKS[craft - 1], "bot:greedy", "baseline", rng=random.Random(craft))
    a, b, c = pool.active()
    a.cr, b.cr, c.cr = 1600, 1600, 1300                   # c is out of reach (A27)
    a.period_games = b.period_games = P.period_target(pool.period)
    # Salem S8: c is short but can't play anyone, so it doesn't hold the period up
    assert pool.period_done() == []
    assert list(pool.jobs(until_period_done=True)) == []
    b.period_games = 0                                    # someone who can still play is short: go on
    assert pool.period_done() == [b.mid]
    job = next(pool.jobs(until_period_done=True))
    assert c.mid not in job["labels"]["members"]
    pool.settle({"id": job["id"], "result": "draw", "winner": None})
    b.period_games = P.period_target(pool.period)
    pool.advance()                                        # no force needed; c's shortfall goes in the log
    ev = [json.loads(x) for x in (tmp_path / "p" / "events.jsonl").read_text().splitlines()][-1]
    assert ev["forced"] is None and ev["short_isolated"] == [{"mid": c.mid, "games": 0, "cr": 1300}]


def test_excluded_seeds_are_never_drawn(tmp_path):
    lo, hi = 99001700, 99001720
    taken = set(range(lo, lo + 15))
    pool = P.Pool.create(tmp_path / "x", (lo, hi), rng_seed=1, exclude_seeds=taken | {5, 10 ** 9})
    for d in BASE_DECKS[:2]:
        pool.enter(d, "bot:greedy", "baseline", rng=random.Random(len(pool.members)))
    seeds = {pool.next_job()["seed"] for _ in range(5)}
    assert seeds == set(range(lo + 15, hi))
    with pytest.raises(P.PoolError):
        pool.next_job()
    again = P.Pool(tmp_path / "x")                        # the exclusion is in the create line: a resume keeps it
    assert again.used_seeds == taken | seeds
    assert again.params["excluded_seeds"] == sorted(taken)


def test_opponent_class_is_uniform_and_empty_classes_are_redrawn(tmp_path):
    pool = new_pool(tmp_path)
    for craft in (1, 3, 5):
        pool.enter(BASE_DECKS[craft - 1], "bot:greedy", "baseline", rng=random.Random(craft))
    rng = random.Random(5)
    seen = Counter()
    for _ in range(9000):
        a, b, _ = pool.draw_pair(rng)
        if a.craft == 1:
            seen[b.craft] += 1
    assert set(seen) == {3, 5}                           # no Forest mirror possible (only one Forest member)
    assert seen[3] / (seen[3] + seen[5]) == pytest.approx(0.5, abs=0.03)


def test_downweight_line_and_floor():
    mu = 1500
    assert rules.effective_weight(1300, mu, False) == pytest.approx(1.0)
    assert rules.effective_weight(1250, mu, False) == pytest.approx(0.6)
    assert rules.effective_weight(1200, mu, False) == pytest.approx(0.2)
    assert rules.effective_weight(1200, mu, True) == 1.0


def test_removal_protection_and_cascade(tmp_path):
    pool = new_pool(tmp_path)
    decks = [synth_deck(1, i) for i in range(2)] + [synth_deck(2, i) for i in range(2)] + [synth_deck(3, 0)]
    for i, d in enumerate(decks):
        pool.enter(d, "bot:greedy", "baseline", rng=random.Random(100 + i))
    ms = pool.active()
    for m in ms:
        m.full_strategy_period, m.games = True, 5000
    ms[0].cr, ms[1].cr, ms[2].cr, ms[3].cr, ms[4].cr = 1900, 1880, 1500, 1215, 1005   # mu = 1500
    ms[3].full_strategy_period = False                   # in protection (no whole strategy period yet, S7): stays
    removed = pool._remove_below_line()
    # 1005 <= 1500 - 300 goes; mu becomes (1900+1880+1500+1215)/4 = 1623.75; 1215 is protected, 1500 is above
    assert removed == [ms[4].mid]
    assert not ms[4].active and ms[3].active
    ms[3].full_strategy_period = True                    # protection over: 1215 <= 1623.75 - 300 goes too
    assert pool._remove_below_line() == [ms[3].mid]
    # after that mu = 1760 and 1500 > 1460: nobody else
    assert ms[2].active


def test_removal_cascades_in_one_settlement(tmp_path):
    """Taking out one member raises mu, which can put the next one under the line at once (A16)."""
    pool = new_pool(tmp_path)
    for i, d in enumerate([synth_deck(1, i) for i in range(2)] + [synth_deck(2, i) for i in range(3)]):
        pool.enter(d, "bot:greedy", "baseline", rng=random.Random(300 + i))
    ms = pool.active()
    for m in ms:
        m.full_strategy_period, m.games = True, 5000
    ms[0].cr, ms[1].cr, ms[2].cr, ms[3].cr, ms[4].cr = 1900, 1880, 1500, 1215, 1005   # mu 1500, line 1200
    assert pool._remove_below_line() == [ms[4].mid, ms[3].mid]   # 1005 first; then mu 1623.75 takes 1215
    assert pool.mu == pytest.approx(1760)


def test_protection_lasts_until_a_whole_strategy_period(tmp_path):
    # Salem S7 (11-22): protection by periods only; the games part of §4.5 ("the first 1000 games") is gone
    assert P.PROTECT_GAMES == 0
    pool = baseline_pool(tmp_path)
    m = pool.active()[0]
    assert m.protected
    m.games = 1500
    assert m.protected                                   # no whole strategy period yet
    pool.advance(force="test")                           # 0 -> 1 deck
    pool.advance(force="test")                           # 1 -> 2 strategy
    assert m.protected
    pool.advance(force="test")                           # 2 -> 3: the strategy period ended with m in the pool
    assert m.full_strategy_period and not m.protected
    m.games = 150                                        # few games: no longer matters
    assert not m.protected


def test_periods_entries_updates_and_unstable(tmp_path):
    pool = baseline_pool(tmp_path)
    mid = pool.active()[0].mid
    with pytest.raises(P.PoolError):
        pool.update(mid, "bot:mcts:200+plan", gate="G-x")       # not a strategy period
    with pytest.raises(P.PoolError):
        pool.enter(synth_deck(1, 1), "py:helpers:Random", "fable-ultracode")  # players start in period 1
    with pytest.raises(P.PoolError):
        pool.advance()                                   # nobody has 2000 games yet
    pool.advance(force="test")
    assert P.period_kind(pool.period) == "deck"
    pool.advance(force="test")
    assert P.period_kind(pool.period) == "strategy"
    with pytest.raises(P.PoolError):
        pool.enter(synth_deck(1, 2), "py:helpers:Random", "fable-ultracode")  # no new decks in a strategy period
    with pytest.raises(P.PoolError):
        pool.update(mid, "bot:mcts:200+plan", gate="")   # needs the gate that passed it
    m = pool.members[mid]
    cr, anon = m.cr, m.anon
    assert pool.update(mid, "bot:mcts:200+plan", gate="G-0001") == 2
    assert (m.cr, m.anon, m.version, m.since_change, m.unstable) == (cr, anon, 2, 0, True)
    m.since_change = 300
    assert not m.unstable


def test_period_ends_only_when_everyone_has_its_games(tmp_path):
    # the baseline run (period 0) needs 2000 each (A37); the players' periods 100 each (Salem S7)
    pool = baseline_pool(tmp_path)
    assert (P.period_target(0), P.period_target(1), P.period_target(2)) == (2000, 100, 100)
    for m in pool.active():
        m.period_games = 2000
    pool.active()[3].period_games = 1999
    assert pool.period_done() == [pool.active()[3].mid]
    pool.active()[3].period_games = 2000
    assert pool.period_done() == []
    pool.advance()
    assert all(m.period_games == 0 for m in pool.active())
    ev = [json.loads(x) for x in (tmp_path / "p" / "events.jsonl").read_text().splitlines()][-1]
    assert ev["rules"] == {"period_games": 100, "protect_games": 0}
    for m in pool.active():
        m.period_games = 100
    pool.active()[0].period_games = 99
    assert pool.period_done() == [pool.active()[0].mid]
    pool.active()[0].period_games = 100
    assert pool.period_done() == []


def test_quotas(tmp_path):
    pool = baseline_pool(tmp_path)
    pool.advance(force="test")
    pool.enter(BASE_DECKS[0], "py:helpers:Random", "fable-ultracode")             # the Forest baseline list, a second time
    with pytest.raises(P.ListFull) as e:
        pool.enter(BASE_DECKS[0], "py:helpers:Random", "fable")          # a third member with that list
    assert len(e.value.holders) == 2
    pool.enter(synth_deck(2, 0), "py:helpers:Random", "fable-ultracode")
    with pytest.raises(P.PoolError, match="one per class"):
        pool.enter(synth_deck(2, 1), "py:helpers:Random", "fable-ultracode")      # S5: one new deck per class per deck period
    pool.enter(synth_deck(4, 1), "py:helpers:Random", "fable-ultracode")          # ... a third class in the same period is fine
    pool.enter(synth_deck(2, 1), "py:helpers:Random", "fable")           # ... and another player's Sword is theirs
    for k in range(1, 7):                                             # S6: no cap on a player's members
        pool.advance(force="test"); pool.advance(force="test")
        pool.enter(synth_deck(3, k), "py:helpers:Random", "fable-ultracode")
    assert len([m for m in pool.active() if m.owner == "fable-ultracode"]) == 9


def test_an_opponent_removed_mid_game(tmp_path):
    """Two games in flight; the first one to end removes a member who is still playing the second (A4)."""
    pool = new_pool(tmp_path)
    decks = [synth_deck(1, 0), synth_deck(2, 0), synth_deck(1, 1), synth_deck(2, 1)]
    for i, d in enumerate(decks):
        pool.enter(d, "bot:greedy", "baseline", rng=random.Random(200 + i))
    ms = pool.active()
    for m in ms:
        m.full_strategy_period, m.games = True, 5000
    ms[0].cr, ms[1].cr, ms[2].cr, ms[3].cr = 1800, 1800, 1700, 1210         # mu 1627.5; line 1327.5
    # two games started by hand so the case is exact: ms[3] is in both
    g1 = {"ev": "start", "id": "x1", "seed": 99001990, "members": [ms[0].mid, ms[3].mid], "cr": [1800, 1210]}
    g2 = {"ev": "start", "id": "x2", "seed": 99001991, "members": [ms[3].mid, ms[2].mid], "cr": [1210, 1700]}
    pool._log(g1); pool._log(g2)
    finish(pool, {"id": "x1"}, 0)                        # ms[3] loses 8 (d < -175): 1202 <= mu - 300 -> removed
    assert not ms[3].active
    before = ms[2].cr
    ev = finish(pool, {"id": "x2"}, 0)                   # ms[3] "wins" a game it was playing when it left
    assert ms[2].cr == before + ev["deltas"][1]          # the side still in the pool is settled as usual
    assert pool.lost_to_removal == ev["deltas"][0]


def test_resume_rebuilds_the_same_state(tmp_path):
    pool = baseline_pool(tmp_path)
    rng = random.Random(9)
    for _ in range(120):
        finish(pool, pool.next_job(), rng.randrange(2))
    pool.next_job()                                      # started, never finished (the machine stopped)
    again = P.Pool(tmp_path / "p")
    assert again.private_rows() == pool.private_rows()
    assert again.used_seeds == pool.used_seeds and again.started == pool.started
    assert again.inflight == {}
    assert len(pool.used_seeds) == pool.started          # one fresh seed per game, never repeated
    assert all(SEEDS[0] <= s < SEEDS[1] for s in pool.used_seeds)


def test_public_view_hides_owner_age_and_version(tmp_path):
    pool = baseline_pool(tmp_path)
    row = pool.public_rows()[0]
    assert set(row) == {"anon", "craft", "rel_cr", "baseline"}


def test_a_short_real_ladder(tmp_path):
    pool = new_pool(tmp_path, "real")
    for craft in (2, 5, 7):
        pool.enter(BASE_DECKS[craft - 1], "py:helpers:Random", "baseline", rng=random.Random(craft))
    res = pool.ladder(workers=2, games=12, step_limit=10.0)
    assert res["played"] == 12
    lines = [json.loads(l) for l in pool.games_path.read_text().splitlines()]
    assert len(lines) == 12 and all(l["labels"]["members"] and l["labels"]["base"] for l in lines)
    assert all(l["result"] in ("normal", "draw") for l in lines), [l.get("error") for l in lines]
    again = P.Pool(tmp_path / "real")
    assert again.settled == 12 and again.total_cr() == 1500 * 3
    for l in lines[:4]:
        ok, why = replay_moves(l)
        assert ok, why


def test_a_check_pool_allows_other_starts_and_no_quotas_but_the_real_pool_doesnt(tmp_path):
    real = new_pool(tmp_path, "real")
    with pytest.raises(P.PoolError):
        real.enter(BASE_DECKS[0], "bot:greedy", "baseline", cr=1700)
    chk = P.Pool.create(tmp_path / "chk", SEEDS, rng_seed=1, check=True)
    for k, cr in enumerate((1300, 1500, 1700)):          # one list three times, other starting CRs
        chk.enter(BASE_DECKS[1], f"mix:0.{k}:greedy", "check", cr=cr, rng=random.Random(k))
    assert [m.cr for m in chk.active()] == [1300, 1500, 1700]
    assert P.Pool(tmp_path / "chk").params["check"] is True


# --- merged periods from period 4 (Salem S35/S36, 11-26) ------------------------------------------------------------

@pytest.mark.parametrize("n,kind,decks,updates", [
    (0, "baseline", False, False), (1, "deck", True, False), (2, "strategy", False, True), (3, "deck", True, False),
    (4, "merged", True, True), (5, "merged", True, True), (6, "merged", True, True)])
def test_period_kinds_and_what_they_take(n, kind, decks, updates):
    # periods 0-3 keep their kinds (the event replay calls period_kind); from 4 every period is merged
    assert P.MERGED_FROM == 4
    assert (P.period_kind(n), P.takes_decks(n), P.takes_updates(n)) == (kind, decks, updates)
    assert P.period_target(n) == (2000 if n == 0 else 100)


def at_period(pool, n):
    while pool.period < n:
        pool.advance(force="test")
    return pool


def test_a_merged_period_takes_entries_and_updates(tmp_path):
    pool = baseline_pool(tmp_path)
    old = pool.active()[0].mid
    at_period(pool, 1)
    with pytest.raises(P.PoolError, match="strategy period or a merged period"):
        pool.update(old, "bot:mcts:200+plan", gate="G-1")                    # period 1: decks only
    at_period(pool, 3)
    with pytest.raises(P.PoolError, match="strategy period or a merged period"):
        pool.update(old, "bot:mcts:200+plan", gate="G-1")                    # period 3 (special, a deck period)
    p3 = pool.enter(synth_deck(5, 0), "py:helpers:Random", "fable")
    at_period(pool, 4)
    new = pool.enter(synth_deck(1, 3), "py:helpers:Random", "fable-ultracode")   # a new deck ...
    assert pool.update(old, "bot:mcts:200+plan", gate="G-0001") == 2           # ... and an update, same period
    assert pool.update(p3, "bot:mcts:200+plan", gate="G-0002") == 2            # a period-3 member from period 4
    with pytest.raises(P.PoolError, match="entered in this period"):
        pool.update(new, "bot:mcts:200+plan", gate="G-0003")                 # not in the period-start frozen pool
    assert pool.members[new].version == 1
    with pytest.raises(P.PoolError, match="one per class"):
        pool.enter(synth_deck(1, 4), "py:helpers:Random", "fable-ultracode")  # S5/S36: at most one per class
    at_period(pool, 5)
    pool.enter(synth_deck(1, 4), "py:helpers:Random", "fable-ultracode")      # the next period: another one
    assert pool.update(new, "bot:mcts:200+plan", gate="G-0003") == 2           # and now it can be updated
    m = pool.members[new]
    assert (m.version, m.since_change, m.unstable) == (2, 0, True)


def test_entries_in_consecutive_merged_periods(tmp_path):
    # S36: at most one new deck per class per player per period, none required; counted by entry period
    pool = at_period(baseline_pool(tmp_path), 4)
    for n in (4, 5, 6):
        at_period(pool, n)
        pool.enter(synth_deck(3, n), "py:helpers:Random", "fable-ultracode")
        with pytest.raises(P.PoolError, match="one per class"):
            pool.enter(synth_deck(3, 10 + n), "py:helpers:Random", "fable-ultracode")
    assert [m.entry_period for m in pool.active() if m.owner == "fable-ultracode"] == [4, 5, 6]


def _period_events(path):
    return [e for e in (json.loads(x) for x in (path / "events.jsonl").read_text(encoding="utf-8").splitlines())
            if e["ev"] == "period"]


def test_protection_across_merged_periods_and_the_replay(tmp_path):
    """A member entered in period N is protected until period N+1 ends (A15 read for merged periods, S35/S36):
    period-3 members lose it when period 4 ends, period-4 members when period 5 ends. Period 2 marks as before."""
    pool = baseline_pool(tmp_path)
    base = [m.mid for m in pool.active()]
    at_period(pool, 1)
    p1 = pool.enter(synth_deck(1, 1), "py:helpers:Random", "fable")
    at_period(pool, 3)
    assert all(pool.members[x].full_strategy_period for x in base + [p1])       # 2 -> 3, as it always was
    p3 = pool.enter(synth_deck(2, 3), "py:helpers:Random", "fable")
    at_period(pool, 4)
    assert pool.members[p3].protected                                           # 3 -> 4: period 3 took no updates
    p4 = pool.enter(synth_deck(3, 4), "py:helpers:Random", "fable")
    at_period(pool, 5)
    assert not pool.members[p3].protected and pool.members[p4].protected       # 4 -> 5: p3 out, p4 still in
    p5 = pool.enter(synth_deck(4, 5), "py:helpers:Random", "fable")
    at_period(pool, 6)
    assert not pool.members[p4].protected and pool.members[p5].protected       # 5 -> 6: p4 out, p5 still in
    evs = _period_events(tmp_path / "p")
    assert [(e["period"], e["kind"]) for e in evs] == [(1, "deck"), (2, "strategy"), (3, "deck"), (4, "merged"),
                                                        (5, "merged"), (6, "merged")]
    assert [e["through_strategy_period"] for e in evs] == [[], [], base + [p1], [], base + [p1, p3],
                                                            base + [p1, p3, p4]]
    again = P.Pool(tmp_path / "p")                                              # rebuilt from events.jsonl
    assert again.private_rows() == pool.private_rows() and again.period == 6
    assert {m.mid: m.full_strategy_period for m in again.members.values()} == \
           {m.mid: m.full_strategy_period for m in pool.members.values()}


def test_the_old_3_to_4_period_line_replays_the_same(tmp_path):
    # LD-88: the real pool's 3 -> 4 line says kind "strategy" (written before S35); no code reads that field
    pool = baseline_pool(tmp_path)
    at_period(pool, 3)
    p3 = pool.enter(synth_deck(2, 3), "py:helpers:Random", "fable")
    at_period(pool, 5)
    path = tmp_path / "p" / "events.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    i = max(k for k, x in enumerate(lines) if json.loads(x)["ev"] == "period" and json.loads(x)["period"] == 4)
    ev = json.loads(lines[i])
    assert ev["kind"] == "merged" and ev["through_strategy_period"] == []
    ev["kind"] = "strategy"
    lines[i] = json.dumps(ev)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    again = P.Pool(tmp_path / "p")
    assert again.private_rows() == pool.private_rows()
    assert again.members[p3].full_strategy_period and not again.members[p3].protected
