"""tools.deckgate (the gate on decks given by code) and agent option +netany."""
from svsim.learn.setnet import SetNetEnded, load_cached
from svsim.tools import deckgate as G
from svsim.tools.arena import make_agent

from helpers import start

FIELD_LINES = ["a|1.4.c9w-.cJSM.cJSM.e3ls.e3ls.e3ls.e3_e.e3_e.e4Gg.eEFk.eEFk.eEFk.eSAM.eSAW.eShA.ecA-.ecE6.erJk.e-bU."
               "e-bU.e-uE.e_4u.fC_W.fDkE.fDkE.fMmM.fNIk.fNVE.fbwg.fc8k.flB0.flD-.flQe.flvu.f-Jc.g7q-.g84c.g8KE.g8KE.g8KE",
               "b|1.7.cQnG.cR0u.e3_e.e4IE.eLN-.eLae.eSAW.eSRY.ejG6.ejGG.ejoU.ej--.ej--.ej_8.er5g.erJu.f5gc.f5gc.f6PU."
               "f6PU.f6Pe.fDUc.fDkE.fUKu.fbPs.fbS-.fbfU.fbfU.fbv6.fbwg.ft1-.ftEe.f-Jc.f-ZE.f-ZE.gEwG.gF9u.gFCs.gFPM.gFPM"]
NET = "analysis/scaling/models/net-mid-ramp-t.npz"


def test_matchups_are_every_ordered_non_mirror_pair_balanced_per_block():
    m = G.matchups(7)
    assert len(m) == 42 and len(set(m)) == 42 and all(i != j for i, j in m)
    for start_ in range(0, 42, 7):
        block = m[start_:start_ + 7]
        assert sorted(i for i, _ in block) == list(range(7)) and sorted(j for _, j in block) == list(range(7))


def test_a_pair_plays_both_decks_from_both_seats(tmp_path):
    path = tmp_path / "field.txt"
    path.write_text("\n".join(FIELD_LINES) + "\n", encoding="utf-8")
    field = G.read_field(str(path))
    assert [label for label, _ in field] == ["a", "b"] and all(len(ids) == 40 for _, ids in field)
    res = G.play_pair((0, 5, 0, 1, field[0][1], field[1][1], "random", "random"))
    assert [(g["x_deck"], g["seat"]) for g in res["games"]] == [(0, 0), (0, 1), (1, 0), (1, 1)]
    assert 0 <= G.pair_score(res) <= 1
    assert G.play_pair((0, 5, 0, 1, field[0][1], field[1][1], "random", "random")) == res     # repeatable
    assert set(G.by_deck([res])) == {0, 1}


def test_time_match_rule():
    assert G.time_match(100, 1.02) == 100 and G.time_match(100, 0.97) == 100
    assert G.time_match(100, 1.25) == 80 and G.time_match(100, 0.8) == 125
    assert G.budget("mcts:83+plan+setnet=x") == 83 and G.budget("random") is None


def test_netany_scores_decks_the_net_never_saw():
    state = start()                                     # Footman decks: no deck name the net knows
    net = load_cached(NET)

    class Base:
        def score(self, state, player, player_moves_next=False):
            return 12345.0

    own = SetNetEnded(Base(), net, mid_turn=True)
    anyp = SetNetEnded(Base(), net, mid_turn=True, any_pairing=True)
    assert own.score(state, 0) == 12345.0                          # not its pairing: the base's score
    assert anyp.score(state, 0) != 12345.0                         # +netany: the net's
    assert make_agent(f"mcts:10+plan+setnet={NET}+netmid+netany", 0) is not None
