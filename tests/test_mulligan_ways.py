"""The opening redraw's rule extensions, the tournament draft rules, their variants and the simulated way."""
import pytest

from svsim.agents import mulligan as M


def _hand(deck, opponent, first, ids, seed=3):
    """A game at `deck`'s mulligan with exactly these card ids in hand (taken from its deck)."""
    state = M.opening(deck, opponent, first, seed)
    p = state.players[state.active]
    pool = p.hand + p.deck
    hand = []
    for cid in ids:
        card = next(c for c in pool if c.defn.card_id == cid and c not in hand)
        hand.append(card)
    p.deck = [c for c in pool if c not in hand]
    p.hand = hand
    return state


def _kept(state, spec):
    p = state.players[state.active]
    out = M.decide(state, spec)
    return [p.hand[i].defn.card_id for i in range(len(p.hand)) if i not in out]


def test_layers_go_base_side_opponent_and_partners_are_needed():
    base = M.Rules(keep=frozenset({1}), redraw=frozenset({2}),
                   first=M.Rules(keep=frozenset({2})), second=M.Rules(redraw=frozenset({1})),
                   vs={"x": M.Rules(redraw=frozenset({3}), first=M.Rules(keep=frozenset({3})))})
    r = M.resolve(base, True, None)
    assert r.keep == {1, 2} and r.redraw == frozenset()
    assert M.resolve(base, False, None).redraw == {1, 2}
    assert M.resolve(base, False, "x").redraw == {1, 2, 3}
    assert 3 in M.resolve(base, True, "x").keep and 3 not in M.resolve(base, True, "x").redraw

    class C:                                       # a card in hand: an id and a cost
        def __init__(self, cid, cost):
            self.defn = type("D", (), {"card_id": cid})()
            self.cost = cost
    hand = [C(10, 2), C(11, 2), C(12, 2), C(13, 6)]
    pair = M.Rules(needs={10: frozenset({11}), 11: frozenset({10})})
    assert M.by_rules(hand, pair) == (3,)
    assert M.by_rules([C(10, 2), C(12, 2)], pair) == (0,)                  # alone: back
    lonely = M.Rules(needs={12: frozenset()})                              # no partners: never for its own sake
    assert 2 in M.by_rules(hand, lonely)
    counted = M.Rules(needs={12: M.Need(frozenset({13}), 1, in_hand=True)})  # counts the hand, not the keeps
    assert 2 not in M.by_rules(hand, counted)
    assert M.by_rules(hand, M.Rules(need_one_of=frozenset({99}))) == (0, 1, 2, 3)
    rhino = M.PLAYER_RULES["rhino"]                                        # the old rules read as before
    assert M.resolve(rhino, True, "ramp").keep == rhino.keep


def test_the_draft_rules_for_tournament_ramp_follow_the_side_and_the_opponent():
    zooey, kimika, vorlalai, lyria, sign = M.ZOOEY, M.KIMIKA, M.VORLALAI, M.LYRIA, M.DRAGONSIGN
    s = _hand("ramp-t", "elf-t", True, [zooey, kimika, vorlalai, lyria])
    assert sorted(_kept(s, "rules")) == sorted([zooey, kimika, vorlalai])  # the pair stays; Lyria wants 龙之启示
    s = _hand("ramp-t", "elf-t", True, [zooey, kimika, sign, lyria])
    assert sorted(_kept(s, "rules")) == sorted([zooey, kimika, sign, lyria])   # going first with 龙之启示: R3
    s = _hand("ramp-t", "elf-t", False, [zooey, kimika, vorlalai, M.PROMOTER])
    assert _kept(s, "rules") == [M.PROMOTER]                               # second vs Elf: no 佐伊, no pair, 龙人
    s = _hand("ramp-t", "ramp-t", True, [kimika, vorlalai, lyria, sign])
    assert _kept(s, "rules") == [sign]                                     # the mirror: none of the three
    s = _hand("ramp-t", "pirate-t", True, [kimika, vorlalai, M.PROMOTER, M.FOXFIRE])
    assert sorted(_kept(s, "rules")) == sorted([kimika, vorlalai])
    assert _kept(s, "rules:allramp") == []                                 # no ramp card: all back


def test_the_variants_switch_the_conditional_keeps():
    cheap = sorted(M._cheap("elf-t", 2) - {M.QCY, M.WORLD_GAMES})[:2]
    s = _hand("elf-t", "pirate-t", True, [M.QCY] + cheap + [10913310])
    assert M.QCY not in _kept(s, "rules")
    assert M.QCY in _kept(s, "rules:qcy2") and M.QCY not in _kept(s, "rules:qcy3")
    s = _hand("elf-t", "ramp-t", True, [M.QCY] + cheap + [10913310])
    assert M.QCY not in _kept(s, "rules:qcy2")                             # never against Ramp
    from svsim.cards import decks
    nem = decks.build(decks.NAMED["nemesis-t"])
    four = next(c.card_id for c in nem if c.cost == 4)
    big = [c.card_id for c in nem if c.cost >= 5][:2]
    s = _hand("nemesis-t", "ramp-t", True, [M.CUTTHROAT, four] + big)
    assert four in _kept(s, "rules") and four not in _kept(s, "rules:nem4")   # nothing early but 机锋
    early = next(c.card_id for c in nem if c.cost <= 2 and c.is_follower and c.card_id != M.CUTTHROAT)
    s = _hand("nemesis-t", "ramp-t", True, [M.CUTTHROAT, four, early, big[0]])
    assert four in _kept(s, "rules:nem4")


def test_default_is_unchanged_and_a_mode_only_changes_the_redraw():
    from svsim.core.engine import apply, legal_actions
    from svsim.tools.arena import make_agent
    s = M.opening("ramp-t", "elf-t", True, 5)
    assert M.decide(s, "default") == M.mulligan(s).indices
    with pytest.raises(ValueError):
        make_agent("greedy+mull=rules:nothing", 0)
    agents = [make_agent("greedy+mull=rules:allramp", 0), make_agent("greedy", 1)]
    state = M.opening("ramp-t", "pirate-t", True, 9)
    first_move = agents[0].act(state, legal_actions(state))
    assert first_move.indices == M.decide(state, "rules:allramp")
    apply(state, first_move)
    for _ in range(30):                                 # and plays on as the base agent
        if state.over:
            break
        apply(state, agents[state.active].act(state, legal_actions(state)))


def test_the_simulated_redraw_is_a_subset_and_repeats_with_its_seed():
    s = M.opening("ramp-t", "elf-t", True, 4)
    a = M.decide(s, "sim:1:1", seed=2)
    assert set(a) <= set(range(len(s.players[s.active].hand))) and a == M.decide(s, "sim:1:1", seed=2)


def test_the_tournament_combo_forest_redraws_by_its_rules_by_default():
    from svsim.agents.greedy_agent import mulligan as agents_redraw
    from svsim.agents.mulligan import BY_DECK, decide, opening
    from svsim.tools.arena import make_agent
    assert BY_DECK == {"elf-t": "rules"}
    differs = 0
    for seed in range(40):
        for first in (True, False):
            elf = opening("elf-t", "ramp-t", first, seed)
            assert agents_redraw(elf).indices == decide(elf, "rules")             # elf-t: the rules
            differs += agents_redraw(elf).indices != decide(elf, "default")
            ramp = opening("ramp-t", "elf-t", first, seed)
            assert agents_redraw(ramp).indices == decide(ramp, "default")         # the others as before
    assert differs > 0
    state = opening("elf-t", "ramp-t", True, 3)
    from svsim.core.engine import legal_actions
    off = make_agent("mcts:5+plan+mull=default", 1).act(state, legal_actions(state))
    assert off.indices == decide(state, "default")                                 # "+mull=default": off


def test_a_mulligan_by_deck_pins_one_deck_s_way_and_leaves_the_others_at_the_default():
    from svsim.agents.mulligan import decide, decide_spec_ok, opening
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    for seed in range(20):
        for first in (True, False):
            elf = opening("elf-t", "ramp-t", first, seed)
            assert decide(elf, "by:elf-t=rules") == decide(elf, "rules")
            ramp = opening("ramp-t", "elf-t", first, seed)
            assert decide(ramp, "by:elf-t=rules") == decide(ramp, "default")
            assert decide(ramp, "by:elf-t=rules/ramp-t=rules") == decide(ramp, "rules")
    state = opening("elf-t", "ramp-t", True, 3)          # as an agent option (the ruler's pinned redraw)
    pinned = make_agent("mcts:5+plan+mull=by:elf-t=rules", 1).act(state, legal_actions(state))
    assert pinned.indices == decide(state, "rules")
    for bad in ("by:elf-t", "by:elf-t=nope", "by:elf-t=by:x=rules"):
        with pytest.raises(ValueError):
            decide_spec_ok(bad)
