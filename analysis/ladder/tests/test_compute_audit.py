"""ladder/compute_audit.py: which games are replayed, and the calibrated ratio (LD-57), split by turns with the two
rules (A68, Salem 11-27). No games are played here."""
import random
import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pytest  # noqa: E402

from ladder import compute_audit as CA  # noqa: E402
from ladder import submit  # noqa: E402
from ladder.submit import COMPUTE_REFUSE, DEFAULT, TURN_REFUSE  # noqa: E402

MEMBERS = {"b1": NS(owner="baseline", strategy=DEFAULT, anon="X1", craft=1),
           "b2": NS(owner="baseline", strategy=DEFAULT, anon="X2", craft=2),
           "p1": NS(owner="fable-ultracode", strategy="py:sub_S0001:A", anon="X3", craft=3)}


# two mulligans, seat 0's turn (a first decision, then its EndTurn), seat 1's turn: kinds M M F R F
MOVES = [{"type": "Mulligan"}, {"type": "Mulligan"}, {"type": "PlayCard"}, {"type": "EndTurn"}, {"type": "EndTurn"}]
KINDS = ["M", "M", "F", "R", "F"]


def g(i, mids, period=1, result="normal", versions=(1, 1)):
    return {"id": f"L{period}-{i:07d}", "result": result, "steps": [[0, 1, 0], [1, 1, 0], [0, 10, 0], [0, 18, 0],
                                                                       [1, 30, 0]],
            "actions": MOVES, "labels": {"members": list(mids), "versions": list(versions), "period": period}}


def sh(*cpu, kinds=KINDS):
    return {"value": {"steps": [[s, c] for (s, _, _), c in zip(g(0, ())["steps"], cpu)], "kinds": kinds}}


def test_plan_takes_this_periods_whole_games_by_member_version_and_baseline_pairs():
    games = [g(1, ("b1", "b2")), g(2, ("p1", "b1")), g(3, ("b2", "p1"), versions=(1, 2)), g(4, ("p1", "b1"), period=2),
             g(5, ("p1", "b2"), result="void"), g(6, ("b1", "p1"))]
    items, cal = CA.plan(games, MEMBERS, period=1)
    assert [(k, x["id"], seat) for k, x, seat in items] == [(("p1", 1), "L1-0000002", 0), (("p1", 1), "L1-0000006", 1),
                                                           (("p1", 2), "L1-0000003", 1)]
    assert [x["id"] for _, x, _ in cal] == ["L1-0000001"]
    many = [g(i, ("p1", "b1")) for i in range(50)]
    items, _ = CA.plan(many, MEMBERS, period=1, per_member=30)
    again, _ = CA.plan(many, MEMBERS, period=1, per_member=30)
    assert len(items) == 30 and [x["id"] for _, x, _ in items] == [x["id"] for _, x, _ in again]   # a fixed draw


def test_rows_count_the_members_seat_and_both_seats_for_calibration():
    items = [(("p1", 1), g(2, ("p1", "b1")), 0), (("baseline", None), g(1, ("b1", "b2")), None),
             (("p1", 1), g(3, ("b1", "p1")), 1)]
    got = [sh(1, 1, 5, 4, 15), sh(1, 1, 5, 8, 15), {"value": {"steps": [[0, 1]]}}]   # the third: not the same game
    rows, bad = CA.rows_of(items, got)
    # (all: game, shadow; in turn (the mulligan with them): game, shadow; turn starts: game, shadow; shadow MAIN)
    assert rows == {("p1", 1): [(29, 10, 19, 5, 10, 5, 9)], ("baseline", None): [(60, 30, 20, 10, 40, 20, 28)]}
    assert len(bad) == 1
    assert CA.ratio(rows[("p1", 1)], 60 / 30) == 1.45 and CA.in_turn(rows[("p1", 1)], 2.0) == 1.9
    assert CA.turn_start(rows[("p1", 1)], 2.0, 2) == pytest.approx(5 / (1.08 * 5 + 2 * 9))
    assert CA.extra_turns(rows[("p1", 1)], 2.0) == pytest.approx((5 - 1.08 * 5) / 9)
    assert CA.turn_start(rows[("p1", 1)], 2.0, 0) == pytest.approx(5 / 5.4)
    lo, hi = CA.interval([(40, 10, 0, 0, 0, 0, 0)] * 5, [(60, 30)] * 5)
    assert lo == hi == 2.0
    lo, hi = CA.interval([(29, 10, 19, 5, 10, 5, 9)] * 5, [(60, 30)] * 5, stat=CA.in_turn)
    assert lo == hi == 1.9
    with pytest.raises(SystemExit, match="两种认法对不上"):          # the engine and the moves disagree: the host's
        CA.rows_of(items[:1], [sh(1, 1, 5, 4, 15, kinds=["M", "M", "F", "F", "F"])])   # rule is wrong, no report


def test_over_takes_both_rules_and_never_lists_more_than_the_old_line():
    """A68: a member is over when the receipt's two rules both fail on its pool games: its whole interval of all
    decisions above 1.15 and (with a turn-start budget) its in-turn one above 1.15 or its turn-start one above Q. A
    planner within its budget is not; K = 0 is exactly the old line."""
    high, low = (1.4, 1.6), (0.9, 1.1)
    assert not CA.over_both(high, low, (0.5, 0.8), 2)                  # a planner within its budget
    assert CA.over_both(high, (1.2, 1.4), (0.5, 0.8), 2)               # too much within the turn
    assert CA.over_both(high, low, (TURN_REFUSE + 0.01, 1.5), 2)       # too much at the turn starts
    assert not CA.over_both(low, (1.2, 1.4), (1.2, 1.4), 2)            # the old rule holds
    assert CA.over_both(high, low, (0.5, 0.8), 0) and not CA.over_both(low, high, high, 0)    # K = 0: the old line
    assert not CA.over_both((None, None), high, high, 2)
    # a turn rule that can't be measured doesn't hold: the old line decides, as at the receipt (11-28 review)
    assert CA.over_both(high, (None, None), (None, None), 2) and CA.over_both(high, low, (None, None), 2)
    assert submit.compute_verdict(1.5, {"in_turn": None, "turn_start_q": None}, 25, 2)[2] is None
    rng = random.Random(3)
    for _ in range(2000):
        iv = [tuple(sorted((rng.uniform(0.8, 1.6), rng.uniform(0.8, 1.6)))) for _ in range(3)]
        k = rng.choice((0, 1, 2, 4))
        old = iv[0][0] > COMPUTE_REFUSE
        assert CA.over_both(*iv, k) <= old and CA.over_both(*iv, 0) == old


def test_the_calibration_is_spread_over_the_batch_after_a_warm_up():
    items = [(("p1", 1), g(i, ("p1", "b1")), 0) for i in range(100)]
    cal = [(("baseline", None), g(1000 + i, ("b1", "b2")), None) for i in range(20)]
    order, warm = CA.run_order(items, cal, period=3, workers=4)
    assert warm == 4 and [k for k, _, _ in order[:4]] == [("warm", None)] * 4
    rest = order[warm:]
    assert sorted(x["id"] for _, x, _ in rest) == sorted(x["id"] for _, x, _ in items + cal)
    at = [i for i, (k, _, _) in enumerate(rest) if k == ("baseline", None)]
    assert min(at) < 30 and max(at) > 90 and sum(i < 60 for i in at) not in (0, 20)    # not bunched at either end
    again, _ = CA.run_order(items, cal, period=3, workers=4)
    assert [x["id"] for _, x, _ in again] == [x["id"] for _, x, _ in order]           # a fixed draw


def test_halves_show_the_drift():
    cal = [(("baseline", None), g(i, ("b1", "b2")), None) for i in range(4)]
    got = [sh(1, 1, 10, 18, 30)] * 2 + [sh(1, 1, 5, 8, 15)] * 2
    assert CA.halves(cal, got) == [1.0, 2.0]
