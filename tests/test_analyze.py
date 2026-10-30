"""The deck analyzer (tools.analyze): facts read back from game records."""
from svsim.tools.analyze import game_facts, summarize
from svsim.tools.survival import play


def test_the_damage_read_from_a_game_adds_up_to_what_the_leaders_lost():
    from svsim.tools import records as R
    record = play((0, 0, "face", "ramp", "greedy", "greedy"))
    facts = game_facts(record)
    state = R.start(record)
    for data in record["actions"]:
        from svsim.core.actions import from_dict
        from svsim.core.engine import apply
        apply(state, from_dict(data))
    for side in (0, 1):
        foe = state.players[1 - side]
        dealt = sum(facts[side]["damage"].values())
        assert dealt == sum(facts[side]["kinds"].values())
        assert dealt == foe.leader_max_hp + facts[1 - side]["healed"] - foe.leader_hp
    assert facts[0]["won"] != facts[1]["won"] or record["winner"] not in (0, 1)
    assert {facts[0]["deck"], facts[1]["deck"]} == {"face", "ramp"}
    summary = summarize([record])
    assert summary["face"]["games"] == summary["ramp"]["games"] == 1
    assert summary["face"]["wins"] + summary["ramp"]["wins"] == (record["winner"] in (0, 1))
