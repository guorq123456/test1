"""+plannerfix and +eot (search.combo, opt-in): cards measured at the play points there (and the real maximum, which
Overflow reads), face-first realize, and allied followers' end-of-turn damage to the enemy leader; the plain planner
unchanged."""
from svsim.cards import dragon, sword
from svsim.cards.pool import POOL
from svsim.search import combo

from helpers import put, set_pp, start


def test_cards_are_measured_at_the_play_points_left_and_the_maximum():
    depths = sword.DEPTHS_OF_THE_ELD_SWORD                       # 0 cost, Enhance (1): 3 damage instead of 1
    plain = combo.profile(depths)[0][0]
    assert (plain.paid, plain.recovered, plain.hit) == (0, 0, 3)  # the plain profile: enhanced, and free
    rich = combo.profile_at(depths, False, 5)[0][0]
    poor = combo.profile_at(depths, False, 0)[0][0]
    assert (rich.recovered, rich.hit) == (-1, 3) and (poor.recovered, poor.hit) == (0, 1)
    sloth = POOL[dragon.SLOTH_OF_THE_CRESTPETAL.card_id]          # 2 to the leader in Overflow (max play points 7+)
    assert combo.profile_at(sloth, False, 4, 9)[0][0].face == 2
    assert combo.profile_at(sloth, False, 4, 6)[0][0].face == 0


def test_end_of_turn_damage_is_measured_and_planned():
    erntz = POOL[dragon.ERNTZ.card_id]
    assert [combo.end_turn_damage(erntz, e) for e in (0, 1, 2)] == [0, 8, 8]
    s = start()
    s.turn, s.players[0].turns_taken = 13, 7
    e = put(s, 0, erntz)
    from svsim.core import effects as E
    E.evolve(s, e)
    e.attacks_made = e.max_attacks                               # it has attacked: only its end of turn can win
    set_pp(s, 0, 0)
    s.players[1].leader_hp = 8
    assert combo.plan(s, 2000).damage < 8
    p = combo.plan(s, 2000, eot=True)
    assert p.damage >= 8 and p.steps[-1] == ("end",)
    line = combo.realize(s, p.steps, face_first=p.face_first)
    assert line is not None and combo.verify(s, line)


def test_the_flags_reach_the_agent():
    from svsim.tools.arena import make_agent
    a = make_agent("level-strong+plannerfix+eot", 0)
    assert a.plannerfix and a.eot and not a.tickers
    b = make_agent("level-strong", 0)
    assert not (b.plannerfix or b.eot or b.tickers)
