"""The puzzle bank (tests/puzzles, tools.puzzles): every puzzle loads, find_lethal at its defaults finds the lethal
ones, and the scoreboard plays and judges. Whether the bot solves them is the scoreboard's business, not a test."""
from svsim.search.lethal import find_lethal
from svsim.tools.puzzles import facts, judge, play, puzzles


def test_every_puzzle_loads_and_the_lethal_ones_have_a_sure_lethal():
    bank = puzzles()
    assert {"pirate-flags-lethal", "pirate-flags-setup"} <= {name for name, _, _ in bank}
    for name, build, answer in bank:
        assert answer["kind"] in ("lethal", "setup") and answer.get("source"), name
        state = build(1)
        assert state.phase.name == "MAIN" and not state.over, name
        if answer["kind"] == "lethal":
            assert find_lethal(state).sure, name


def test_the_scoreboard_plays_a_turn_and_judges_it():
    bank = {name: (build, answer) for name, build, answer in puzzles()}
    build, answer = bank["pirate-flags-lethal"]
    end, me, ms = play(build, "greedy", 1)
    f = facts(end, me)
    assert set(f) >= {"won", "enemy_hp", "pp_left"} and ms > 0
    assert judge(answer, dict(f, enemy_hp=0)) is True and judge(answer, dict(f, enemy_hp=4)) is False
    assert judge(bank["pirate-flags-setup"][1], f) is None                  # an open set-up
