"""Balance patch of 2026-11-26 (official notice 2026-11-24, shadowverse-wb.com news
"11/26メンテナンス時のカード能力変更について" / "Changes to Cards – November 26").
One test per changed card, checking the new text."""
from svsim.cards import demo, dragon, forest, rune, abyss
from svsim.core import effects as E
from svsim.core.actions import Evolve, PlayCard
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Keyword

from helpers import give, put, set_pp, start, unlock_evolution


def test_new_stats():
    assert rune.LILANTHIM.cost == 6
    assert abyss.SHAKDOH.cost == 9
    m = dragon.OBLIVIATIONIST_MUGGER
    assert (m.cost, m.atk, m.life) == (4, 4, 4)


def test_wolfraud_evolve_copies_six_at_full_cost():
    state = start(first=0)
    p = state.players[0]
    state.players[1].deck = [state.new_instance(demo.GIANT, 1) for _ in range(20)]
    wolf = put(state, 0, forest.WOLFRAUD)
    give(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    apply(state, Evolve(wolf.uid))
    assert [c.defn for c in p.hand] == [demo.GIANT] * 6
    assert all(c.cost == demo.GIANT.cost for c in p.hand)


def test_wolfraud_super_evolve_reduces_the_copies_by_one():
    state = start(first=0)
    p = state.players[0]
    state.players[1].deck = [state.new_instance(demo.GIANT, 1) for _ in range(20)]
    wolf = put(state, 0, forest.WOLFRAUD)
    unlock_evolution(state, 0)
    apply(state, Evolve(wolf.uid, True))
    assert [c.defn for c in p.hand] == [demo.GIANT] * 6
    assert all(c.cost == demo.GIANT.cost - 1 for c in p.hand)


def test_emperor_of_elements_super_evolve_gives_a_golem_storm():
    state = start(first=0)
    set_pp(state, 0, 7)
    emperor = give(state, 0, rune.EMPEROR_OF_ELEMENTS)
    apply(state, PlayCard(emperor.uid))
    golems = [f for f in state.players[0].field if f.defn == rune.GUARDIAN_GOLEM]
    assert len(golems) == 2
    unlock_evolution(state, 0)
    supers = [a for a in legal_actions(state)
              if isinstance(a, Evolve) and a.uid == emperor.uid and a.super_]
    # only Golems can be chosen (not the Emperor itself, not the enemy)
    assert {a.targets for a in supers} == {(g.uid,) for g in golems}
    apply(state, supers[0])
    chosen = next(g for g in golems if g.uid == supers[0].targets[0])
    other = next(g for g in golems if g is not chosen)
    assert chosen.has(Keyword.STORM) and not other.has(Keyword.STORM)


def test_emperor_of_elements_plain_evolve_gives_nothing():
    state = start(first=0)
    golem = put(state, 0, rune.GUARDIAN_GOLEM)
    emperor = put(state, 0, rune.EMPEROR_OF_ELEMENTS)
    unlock_evolution(state, 0)
    plain = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == emperor.uid
             and not a.super_]
    apply(state, plain[0])
    assert not golem.has(Keyword.STORM)


def test_yube_evolve_gains_a_max_play_point():
    state = start(first=0)
    p = state.players[0]
    p.hand.clear()
    yube = put(state, 0, dragon.YUBE)
    junk = give(state, 0, demo.GIANT)
    before = p.max_pp
    unlock_evolution(state, 0)
    apply(state, Evolve(yube.uid, targets=(junk.uid,)))
    assert junk not in p.hand
    assert p.max_pp == min(10, before + 1)
    assert E.leader_area_card(state, 0, dragon.YUBE_CREST) is not None


def test_mugger_evolve_deals_four():
    state = start(first=0)
    unlock_evolution(state, 0)
    giant = put(state, 1, demo.GIANT)
    mugger = put(state, 0, dragon.OBLIVIATIONIST_MUGGER)
    apply(state, Evolve(mugger.uid, False, (giant.uid,)))
    assert giant.life == 1                                  # 5/5 Giant
