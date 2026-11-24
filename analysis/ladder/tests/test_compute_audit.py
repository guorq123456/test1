"""ladder/compute_audit.py: which games are replayed, and the calibrated ratio (LD-57). No games are played here."""
import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ladder import compute_audit as CA  # noqa: E402
from ladder.submit import DEFAULT  # noqa: E402

MEMBERS = {"b1": NS(owner="baseline", strategy=DEFAULT, anon="X1", craft=1),
           "b2": NS(owner="baseline", strategy=DEFAULT, anon="X2", craft=2),
           "p1": NS(owner="fable-ultracode", strategy="py:sub_S0001:A", anon="X3", craft=3)}


def g(i, mids, period=1, result="normal", versions=(1, 1)):
    return {"id": f"L{period}-{i:07d}", "result": result, "steps": [[0, 10, 0], [1, 20, 0], [0, 30, 0]],
            "labels": {"members": list(mids), "versions": list(versions), "period": period}}


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
    got = [{"value": {"steps": [[0, 5], [1, 1], [0, 5]]}}, {"value": {"steps": [[0, 5], [1, 10], [0, 15]]}},
           {"value": {"steps": [[0, 1]]}}]                                # the third is not the same game
    rows, bad = CA.rows_of(items, got)
    assert rows == {("p1", 1): [(40, 10)], ("baseline", None): [(60, 30)]} and len(bad) == 1
    assert CA.ratio(rows[("p1", 1)], 60 / 30) == 2.0
    lo, hi = CA.interval([(40, 10)] * 5, [(60, 30)] * 5)
    assert lo == hi == 2.0


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
    got = [{"value": {"steps": [[0, 10], [1, 20], [0, 30]]}}] * 2 + [{"value": {"steps": [[0, 5], [1, 10], [0, 15]]}}] * 2
    assert CA.halves(cal, got) == [1.0, 2.0]
