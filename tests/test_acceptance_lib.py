"""analysis/acceptance (process item 5): positions rebuilt from stored action lists, checked by fingerprint, tiers."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis" / "acceptance"))
import lib  # noqa: E402


def _positions():
    return {p["id"]: p for p in lib.load()}


def test_every_stored_position_rebuilds_to_its_fingerprint():
    positions = _positions()
    assert {"rune-g1t3-snack", "rune-g2t3-pot", "rune-g3t4-evidence", "rune-g1t7-tico",
            "haven-bunny-board-2026-11-01"} <= set(positions)
    for pos in positions.values():
        for v in range(lib.variants(pos)):
            state, seat = lib.rebuild(pos, v)
            assert state.players[seat].deck_name == pos["deck"]
            assert state.players[1 - seat].deck_name == pos["opponent"]


def test_the_replay_fingerprints_are_prior_acceptance_py_s():
    # analysis/pilot/logs/prior-acceptance.log, printed by the old recipe (mcts:100+plan from the deal)
    fp = _positions()["rune-g2t3-pot"]["fingerprint"]
    assert (fp["hand"], fp["field"], fp["pp"], fp["leader_hp"]) == (
        [10031210, 10031310, 10732110, 10732310, 10732310, 10833310], [], 2, 20)


def test_a_moved_position_is_reported_not_scored():
    pos = copy.deepcopy(_positions()["rune-g1t3-snack"])
    pos["fingerprint"]["pp"] += 1
    with pytest.raises(lib.Moved, match="fingerprint"):
        lib.rebuild(pos)
    pos = copy.deepcopy(_positions()["rune-g1t3-snack"])
    pos["rebuild"]["actions"][-1][1] = "a step the engine no longer offers"
    with pytest.raises(lib.Moved, match="no longer"):
        lib.rebuild(pos)


def test_tally_counts_each_tier_apart():
    rows = [({"tier": "clear"}, {"turn_end": {"pass": True}, "prior": {"pass": False}}),
            ({"tier": "marginal"}, {"turn_end": {"pass": False}}),
            ({"tier": "clear"}, {"turn_end": {"pass": True}})]
    assert lib.tally(rows) == {"turn_end": {"clear": [2, 2], "marginal": [0, 1]}, "prior": {"clear": [0, 1]}}


def test_the_handset_evaluation_fails_the_bunny_board_as_reported():
    pos = _positions()["haven-bunny-board-2026-11-01"]
    r = lib.judge(pos)["handset"]
    assert not r["pass"] and round(r["salem"], 2) == 3.39 and round(r["wrong"], 2) == 3.72
