"""+discard (search.combo, opt-in): cards that discard a card from hand as they are played are measured with a filler
in hand, the planner picks which card goes and counts its "when discarded" damage, and realize discards that card.
Measured from the engine, no table per card; the plain planner unchanged."""
from svsim.cards import dragon
from svsim.search import combo


def test_discards_and_their_payoff_are_measured_from_the_engine():
    assert combo.discard_face(dragon.DEPTHS_OF_THE_ELD_BLADES) == 1          # "does the same when discarded"
    assert combo.discard_face(dragon.SAGATSUMATSU) == 0
    red = combo.profile_at(dragon.SPILLING_RED, False, 10, 10, True)
    assert [(v[0].discards, v[0].hit, v[0].spread, v[0].needs_foe) for v in red] == [(1, 99, "target", True)]
    assert combo.profile_at(dragon.SPILLING_RED, False, 10, 10) == ()        # no play with an empty hand
    saga = combo.profile_at(dragon.SAGATSUMATSU, False, 10, 10, True)
    assert sorted((v[0].discards, v[0].bare_hand) for v in saga) == [(0, True), (1, False)]   # compulsory with cards
    assert all(e.discards == 0 and not e.needs_foe for v in combo.profile(dragon.SAGATSUMATSU) for e in v)


def _g546():
    """Ramp g546's shape: 10 play points, one super-evolution; a ready Vorlalai (its super-evolution adds two Depths
    of the Eld Blades), Sagatsumatsu in hand; the enemy at 10, no followers. Ten is Vorlalai 3 + discarding a Depths
    to Sagatsumatsu 1 + Sagatsumatsu 5 + the other Depths 1."""
    from helpers import give, put, set_pp, start
    s = start()
    s.turn, s.players[0].turns_taken = 17, 8
    v = put(s, 0, dragon.VORLALAI)
    v.attacks_made = 0
    give(s, 0, dragon.SAGATSUMATSU)
    s.players[0].ep, s.players[0].sep = 0, 1
    set_pp(s, 0, 10)
    s.players[1].leader_hp = 10
    return s


def test_the_discard_planner_finds_a_lethal_that_needs_the_discard_and_the_plain_one_does_not():
    s = _g546()
    assert combo.planned_lethal(s, 20000, tickers=True, fix=True, eot=True)[0] is None
    line, p = combo.planned_lethal(s, 20000, tickers=True, fix=True, eot=True, discard=True)
    assert line and combo.verify(s, line) and p.discard
    assert any(len(step) == 7 and step[6][0] == dragon.DEPTHS_OF_THE_ELD_BLADES.card_id for step in p.steps)


def test_the_flag_reaches_the_agent_and_is_off_by_default():
    from svsim.tools.arena import make_agent
    assert make_agent("level-strong+lethal3+discard", 0).discard
    assert not make_agent("level-strong+lethal3", 0).discard and not make_agent("level-strong", 0).discard
