"""Class rating (CR): the player's ladder rules, and rating agents with them."""
import json
import math

import pytest

from svsim.learn import rating as R
from svsim.tools import cr


def test_points_per_game_follow_the_players_rules():
    assert R.START["diamond"] == R.START["钻石"] == 1600
    assert R.START["sapphire"] == 1550 and R.START["ruby"] == 1500
    assert (R.change(1600, 1600, True), R.change(1600, 1600, False)) == (16, -16)
    assert (R.change(1700, 1600, True), R.change(1700, 1600, False)) == (12, -20)     # 16 -/+ 100/25
    assert (R.change(1600, 1700, True), R.change(1600, 1700, False)) == (20, -12)
    assert (R.change(1775, 1600, True), R.change(1775, 1600, False)) == (9, -23)      # a gap of 175 still counts
    assert (R.change(1780, 1600, True), R.change(1780, 1600, False)) == (8, -24)      # more than 175 above
    assert (R.change(1600, 1780, True), R.change(1600, 1780, False)) == (24, -8)
    assert R.change(1610, 1600, True) == 16 and R.exact_change(1610, 1600, True) == pytest.approx(15.6)
    # What one side gains the other loses.
    for gap in (0, 37, 120, 175, 176, 199):
        for won in (True, False):
            assert R.exact_change(1600 + gap, 1600, won) == -R.exact_change(1600, 1600 + gap, not won)
    assert R.can_match(1800, 1600) and not R.can_match(1801, 1600)
    with pytest.raises(ValueError):
        R.change(1801, 1600, True)


def test_a_cr_gap_reads_as_the_win_rate_that_holds_it():
    for gap in (-175, -80, 0, 40, 175):
        p = R.steady_rate(gap)
        assert R.expected_change(gap, p) == pytest.approx(0, abs=1e-12)
        assert R.steady_gap(p) == pytest.approx(gap)
    assert R.steady_rate(0) == 0.5 and R.steady_rate(80) == pytest.approx(0.6)
    assert R.steady_rate(190) == 0.75 and R.expected_change(190, 0.75) == 0
    assert R.steady_gap(0.73) == 175                     # between 175 and the +8/-24 zone
    assert R.steady_gap(0.8) == math.inf and R.steady_gap(0.2) == -math.inf
    assert R.games_for(50) > R.games_for(100) > 0


def test_the_ladder_settles_where_expected_changes_balance():
    cr_ = R.ladder({("a", "b"): 0.6, ("b", "c"): 0.65}, {"a": 1600})
    assert cr_["a"] == 1600
    assert cr_["b"] == pytest.approx(1520, abs=0.5) and cr_["c"] == pytest.approx(1400, abs=0.5)
    # Two routes that disagree: the ladder lands in between (equal matches per pair).
    cr_ = R.ladder({("a", "b"): 0.6, ("b", "c"): 0.6, ("a", "c"): 0.6}, {"a": 1600})
    assert 1600 - 160 < cr_["c"] < 1600 - 80 and cr_["b"] < 1600
    # Beating someone 75% or more pushes them out of reach (more than 200 below).
    cr_ = R.ladder({("a", "b"): 0.9}, {"a": 1600})
    assert cr_["b"] < 1400 and not R.can_match(cr_["a"], cr_["b"])


def test_few_games_give_wide_ranges():
    few = R.bootstrap({("a", "b"): (3, 5)}, {"a": 0}, samples=200)
    many = R.bootstrap({("a", "b"): (300, 500)}, {"a": 0}, samples=200)
    assert few[0]["b"] == pytest.approx(-80, abs=1) and many[0]["b"] == pytest.approx(-80, abs=1)
    lo_few, hi_few = few[1]["b"]
    lo_many, hi_many = many[1]["b"]
    assert lo_few < lo_many < -80 < hi_many < hi_few and hi_few - lo_few > 3 * (hi_many - lo_many)
    assert R.connected([("a", "b"), ("c", "d")], "a") == {"a", "b"}


def test_the_tool_reads_the_players_records(tmp_path):
    from svsim.ui.session import Session
    session = Session()
    view = session.start("rhino", "ramp", "fast", 8, "you")
    while not view["over"]:                              # the player only ends turns: the AI wins
        if view["active"] == 1:
            view = session.ai_step()
        elif view.get("mulligan"):
            view = session.mulligan([])
        else:
            view = session.act(next(a["i"] for a in view["actions"] if a["type"] == "EndTurn"))
    (tmp_path / "1.json").write_text(json.dumps({"record": session.record_data(), "finished": True}))
    unfinished = Session()
    unfinished.start("rhino", "ramp", "fast", 9, "you")
    (tmp_path / "2.json").write_text(json.dumps(unfinished.record_data()))
    got = cr.human_results([str(tmp_path)])
    assert got == {("你:rhino", "ramp:greedy+plan+learned"): [0.0, 1]}
    assert cr.label("你:rhino") == "你 破魔虫精灵" and cr.label("ramp:mcts:100+plan") == "AI 跳费龙 mcts:100+plan"
    a, b, score = cr.play(("ramp:greedy", "rhino:greedy", 0, 1))
    assert (a, b) == ("ramp:greedy", "rhino:greedy") and score in (0.0, 0.5, 1.0)
    with pytest.raises(ValueError):
        cr.split("mcts:100")
