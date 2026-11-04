"""Pins for docs/rulings.md section C: one minimal test per reading that had none. Each pins the CURRENT reading
(no behaviour change); if a ruling changes, the test fails and the register gets a new entry."""
from svsim.cards import demo
from svsim.core import effects as E
from svsim.core.actions import EndTurn, Evolve
from svsim.core.engine import apply, legal_actions

from helpers import put, start


def _evolves(state):
    return [a for a in legal_actions(state) if isinstance(a, Evolve)]


def _own_turn(state, player, turn):
    while not (state.active == player and state.players[player].turns_taken == turn):
        apply(state, EndTurn())


def test_r02_recovered_evolution_points_are_capped_at_two():
    state = start(first=0)
    p = state.players[0]
    assert (p.ep, p.sep) == (2, 2)
    E.recover_ep(state, 0)
    E.recover_sep(state, 0, 3)
    assert (p.ep, p.sep) == (2, 2)
    p.ep, p.sep = 0, 1
    E.recover_ep(state, 0, 5)
    E.recover_sep(state, 0, 5)
    assert (p.ep, p.sep) == (2, 2)


def test_r02_a_recovered_point_cannot_be_spent_before_the_unlock_turn():
    state = start(first=0)
    _own_turn(state, 0, 4)                          # going first: evolution unlocks on own turn 5
    p = state.players[0]
    put(state, 0, demo.FOOTMAN)
    p.ep, p.sep = 0, 0
    E.recover_ep(state, 0)
    E.recover_sep(state, 0)
    assert (p.ep, p.sep) == (1, 1) and not _evolves(state)
    _own_turn(state, 0, 5)
    assert _evolves(state) and not any(a.super_ for a in _evolves(state))   # super evolution still waits for 7


def test_r09_nocturne_summons_a_skeleton_when_a_clue_amulet_is_banished_by_a_merge():
    from svsim.cards import abyss, neutral
    from svsim.core.actions import PlayCard
    from svsim.core.state import BANISHED
    from helpers import give, set_pp
    state = start()
    put(state, 0, abyss.NOCTURNE)
    set_pp(state, 0, 10)
    first = give(state, 0, neutral.DIVINE_EVIDENCE)
    apply(state, PlayCard(first.uid))
    skeletons = lambda: [c for c in state.players[0].field if c.defn.card_id == abyss.SKELETON.card_id]  # noqa: E731
    assert skeletons() == []
    apply(state, PlayCard(give(state, 0, neutral.DIVINE_EVIDENCE).uid))   # the merge banishes the first amulet
    assert first.fate == BANISHED and E.clues(state, 0) == 2
    skeleton, = skeletons()
    assert (skeleton.atk, skeleton.life) == (3, 5)


def test_r08_a_clue_amulet_merged_in_this_turn_can_engage_again_this_turn():
    from svsim.cards import neutral
    from svsim.core.actions import Engage, PlayCard
    from svsim.core.state import BANISHED, IN_PLAY
    from helpers import give, set_pp
    state = start()
    state.players[0].hand.clear()
    set_pp(state, 0, 10)
    for _ in range(2):                                     # two plays: one amulet with 2 clues
        apply(state, PlayCard(give(state, 0, neutral.DIVINE_EVIDENCE).uid))
    engaged = E.clue_amulet(state, 0)
    apply(state, Engage(engaged.uid))
    assert engaged.fate == IN_PLAY and E.clues(state, 0) == 1      # it stays with 1 clue
    assert not any(isinstance(a, Engage) for a in legal_actions(state))   # once per amulet per turn
    third = give(state, 0, neutral.DIVINE_EVIDENCE)
    apply(state, PlayCard(third.uid))                      # merges: the engaged amulet is banished
    assert engaged.fate == BANISHED and E.clue_amulet(state, 0).uid == third.uid and E.clues(state, 0) == 2
    assert Engage(third.uid) in legal_actions(state)       # the merged-in amulet engages again this turn


def test_r07_a_spell_enters_the_graveyard_after_it_resolves():
    from svsim.core.actions import PlayCard
    from svsim.core.carddef import CardDef
    from svsim.core.enums import CardType, Craft
    from svsim.core.script import CardScript, register
    from helpers import give, set_pp
    seen = []
    probe = CardDef(7591, "Test Shadow Probe", Craft.NEUTRAL, CardType.SPELL, 1)

    @register(probe.card_id)
    class ShadowProbe(CardScript):                       # reads the shadow count while it resolves
        def cast(self, ctx):
            seen.append(ctx.me.shadows)

    state = start()
    p = state.players[0]
    p.shadows = 3
    set_pp(state, 0, 1)
    apply(state, PlayCard(give(state, 0, probe).uid))
    assert seen == [3] and p.shadows == 4                  # not yet counted during resolution, counted after


def test_r01_the_default_turn_limit_is_60_and_ending_the_last_turn_is_a_draw():
    from svsim.core.enums import DRAW
    state = start(first=0)
    assert state.max_turns == 60
    state.players[0].leader_hp = state.players[1].leader_hp = 20
    while state.turn < 60:
        apply(state, EndTurn())
    assert state.turn == 60 and state.winner is None       # the 60th turn is still played
    apply(state, EndTurn())
    assert state.winner == DRAW                            # a draw, not both players losing


def test_r04_a_non_super_evolved_follower_loses_barrier_to_zero_damage():
    from svsim.core.enums import Keyword
    state = start(first=0)
    plain = put(state, 0, demo.FOOTMAN)
    E.give_keywords(plain, Keyword.BARRIER)
    life = plain.life
    E.damage(state, [plain], 0, None)
    assert not plain.has(Keyword.BARRIER) and plain.life == life


def test_r05_a_random_effect_can_hit_an_ambush_follower():
    from svsim.cards import neutral
    from svsim.core.actions import PlayCard
    from svsim.core.enums import Keyword
    from helpers import give, set_pp
    state = start()
    state.players[0].hand.clear()
    set_pp(state, 0, 10)
    hidden = put(state, 1, demo.SHIELDBEARER)              # 1/3, so 2 damage leaves it at 1
    E.give_keywords(hidden, Keyword.AMBUSH)
    jailor = give(state, 0, neutral.JAILOR_OF_ANTIQUITY)
    assert [a.targets for a in legal_actions(state) if isinstance(a, PlayCard) and a.uid == jailor.uid] == [()]
    apply(state, PlayCard(jailor.uid))                     # nothing selectable: the 6 damage hits nothing
    assert hidden.life == 1                                # the random 2 damage still lands on the Ambush follower


def test_r12_a_second_crest_of_the_same_name_does_not_reset_the_countdown():
    from svsim.core.carddef import CardDef
    from svsim.core.enums import CardType, Craft
    crest = CardDef(7592, "Test Countdown Crest", Craft.NEUTRAL, CardType.CREST, 0, countdown=3)
    state = start()
    first = E.add_to_leader_area(state, 0, crest)
    first.countdown = 1                                    # two turns have ticked it down
    assert E.add_to_leader_area(state, 0, crest) is None   # the second one fizzles
    assert state.players[0].leader_area == [first] and first.countdown == 1


def test_r14_halving_an_odd_max_defense_rounds_up():
    from svsim.cards import portal as PORTAL
    from helpers import give, set_pp
    from test_cards_portal import EVIDENCE, fuse, play
    state = start()
    foe = state.players[1]
    foe.leader_max_hp = foe.leader_hp = 19
    lineage = give(state, 0, PORTAL.LINEAGE)
    fuse(state, lineage, give(state, 0, EVIDENCE))
    set_pp(state, 0, 9)
    play(state, lineage)
    assert foe.leader_max_hp == 10 and foe.leader_hp == 10  # 19 / 2 rounded up


# --- card rulings (docs/rulings.md section C, item 8) -----------------------------------------------------------

def test_c06_trap_in_the_woods_destroys_itself_even_when_the_follower_survives():
    from svsim.cards import forest
    from svsim.core.actions import PlayCard
    from svsim.core.carddef import CardDef
    from svsim.core.enums import CardType, Craft
    from svsim.core.script import CardScript, register
    from svsim.core.state import DESTROYED, IN_PLAY
    from helpers import give, set_pp
    sturdy = CardDef(7593, "Test Sturdy Follower", Craft.NEUTRAL, CardType.FOLLOWER, 1, 1, 1)

    @register(sturdy.card_id)
    class Sturdy(CardScript):                             # "can't be destroyed by abilities"
        indestructible = True

    state = start(first=0)
    trap = put(state, 0, forest.TRAP_IN_THE_WOODS)
    apply(state, EndTurn())
    set_pp(state, 1, 1)
    follower = give(state, 1, sturdy)
    apply(state, PlayCard(follower.uid))
    assert follower.fate == IN_PLAY and trap.fate == DESTROYED


def test_c10a_city_of_babelon_engage_with_an_empty_hand_still_delays():
    from svsim.cards import neutral
    from svsim.core.actions import Engage, PlayCard
    from helpers import give, set_pp
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 3)
    city = give(state, 0, neutral.CITY_OF_BABELON)
    apply(state, PlayCard(city.uid))
    assert p.hand == [] and city.countdown == 1
    assert Engage(city.uid, ()) in legal_actions(state)   # engage offered with nothing to discard
    apply(state, Engage(city.uid, ()))
    assert city.countdown == 2 and p.pp == 1


def _test_spell(card_id: int):
    """A 0-cost neutral spell that does nothing (registered once per id)."""
    from svsim.core.carddef import CardDef
    from svsim.core.enums import CardType, Craft
    from svsim.core.script import CardScript, has_script, register
    spell = CardDef(card_id, f"Test Spell {card_id}", Craft.NEUTRAL, CardType.SPELL, 0)
    if not has_script(card_id):
        register(card_id)(type(f"TestSpell{card_id}", (CardScript,), {"cast": lambda self, ctx: None}))
    return spell


def test_c10b_the_evolution_bonus_counts_as_a_buff():
    from svsim.cards import forest
    from svsim.core.actions import Evolve
    from helpers import unlock_evolution
    state = start(first=0)
    unlock_evolution(state, 0)
    ruflet = put(state, 0, forest.RUFLET)
    fairies = lambda: [c for c in state.players[0].field if c.defn.card_id == forest.FAIRY.card_id]  # noqa: E731
    assert fairies() == []
    apply(state, Evolve(ruflet.uid))                       # +2/+2 from evolving: "when buffed" fires
    assert len(fairies()) == 1


def test_c10e_katze_spends_its_once_per_turn_use_with_no_target():
    from svsim.cards import sword
    from svsim.core.actions import PlayCard
    from helpers import give
    spell = _test_spell(7594)
    state = start(first=0)
    put(state, 0, sword.KATZE)
    apply(state, PlayCard(give(state, 0, spell).uid))     # no enemy follower: nothing hit, the use is spent
    enemy = put(state, 1, demo.SHIELDBEARER)
    apply(state, PlayCard(give(state, 0, spell).uid))
    assert enemy.life == 3                                 # the second spell this turn deals nothing
    apply(state, EndTurn())
    apply(state, EndTurn())
    apply(state, PlayCard(give(state, 0, spell).uid))     # a new turn: the use is back
    assert enemy.life == 1


def test_c10f_cutthroat_crest_is_only_spent_on_an_actual_evolution():
    from svsim.cards import portal as PORTAL
    from svsim.core.actions import PlayCard
    from svsim.core.carddef import CardDef
    from svsim.core.enums import CardType, Craft
    from svsim.core.script import CardScript, register
    from helpers import give, set_pp
    fleeting = CardDef(7595, "Test Fleeting Follower", Craft.NEUTRAL, CardType.FOLLOWER, 1, 1, 1)

    @register(fleeting.card_id)
    class Fleeting(CardScript):                            # gone from the field by the time the crest looks
        def fanfare(self, ctx):
            E.banish(ctx.state, ctx.source)

    state = start(first=0)
    E.add_to_leader_area(state, 0, PORTAL.CUTTHROAT_CREST)
    set_pp(state, 0, 10)
    gone = give(state, 0, fleeting)
    apply(state, PlayCard(gone.uid))
    assert state.on_field(gone.uid) is None
    footman = give(state, 0, demo.FOOTMAN)
    apply(state, PlayCard(footman.uid))
    assert footman.evolved                                 # the use was not spent on the follower that left


def test_c10j_lhynkal_crest_can_take_max_defense_to_zero():
    from svsim.cards import rune
    state = start(first=0)
    foe = state.players[1]
    foe.leader_max_hp = foe.leader_hp = 2
    E.add_to_leader_area(state, 0, rune.LHYNKAL_CREST)
    E.summon(state, 0, rune.LHYNKAL)
    from svsim.core.engine import resolve_queue
    resolve_queue(state)
    assert foe.leader_max_hp == 0 and state.winner == 0


def test_c10k_sephie_still_spends_two_play_points_on_a_full_field():
    from svsim.cards import rune
    from svsim.core.state import FIELD_LIMIT
    from helpers import give
    from test_cards_portal import fuse
    state = start(first=0)
    p = state.players[0]
    sephie = give(state, 0, rune.SEPHIE)
    for _ in range(FIELD_LIMIT):
        put(state, 0, demo.FOOTMAN)
    p.pp = 5
    fuse(state, sephie, give(state, 0, demo.FOOTMAN))
    assert p.pp == 3 and len(p.field) == FIELD_LIMIT       # 2 spent, no Test Subject (no room)
    assert not any(c.defn.card_id == rune.OBSESSED_TEST_SUBJECT.card_id for c in p.field)


def test_c10l_blade_of_the_crestpetal_uses_the_burned_cards_cost_on_a_full_hand():
    from svsim.cards import dragon
    from svsim.core.actions import PlayCard
    from svsim.core.state import DESTROYED, HAND_LIMIT
    from helpers import set_pp
    state = start(first=0)
    p = state.players[0]
    p.deck[:] = [state.new_instance(demo.SHIELDBEARER, 0)]     # the only follower in the deck: cost 2
    enemy = put(state, 1, demo.SHIELDBEARER)                   # 1/3
    blade = state.new_instance(dragon.BLADE_OF_THE_CRESTPETAL, 0)
    p.hand[:] = [blade] + [state.new_instance(demo.FOOTMAN, 0) for _ in range(HAND_LIMIT)]
    set_pp(state, 0, 10)
    shadows = p.shadows
    apply(state, PlayCard(blade.uid))                          # after the cast the hand is full: the draw burns
    assert len(p.hand) == HAND_LIMIT and p.deck == [] and p.shadows == shadows + 2   # the spell and the burned card
    assert enemy.life == 1 and enemy.fate != DESTROYED         # X = 2, the burned card's cost


def test_c10m_istyndet_crest_destroys_the_enemy_even_if_the_ally_survives():
    from svsim.cards import abyss
    from svsim.core.carddef import CardDef
    from svsim.core.enums import CardType, Craft
    from svsim.core.script import CardScript, register
    from svsim.core.state import DESTROYED, IN_PLAY
    keeper = CardDef(7596, "Test Undying Last Words", Craft.NEUTRAL, CardType.FOLLOWER, 1, 1, 1)

    @register(keeper.card_id)
    class Keeper(CardScript):                              # Last Words, can't be destroyed by abilities
        indestructible = True

        def last_words(self, ctx):
            pass

    state = start(first=0)
    E.add_to_leader_area(state, 0, abyss.ISTYNDET_CREST)
    ally = put(state, 0, keeper)
    enemy = put(state, 1, demo.SHIELDBEARER)
    apply(state, EndTurn())
    assert ally.fate == IN_PLAY and enemy.fate == DESTROYED


def test_c10n_zoe_takes_her_self_damage_after_the_chosen_mode(monkeypatch):
    from svsim.cards import haven
    from svsim.core.actions import PlayCard
    from helpers import give, set_pp
    calls = []
    real = E.damage

    def recording(state, targets, amount, *a, **k):        # the order of the fanfare's damage calls
        calls.append(([getattr(t, "uid", t) for t in targets], amount))
        return real(state, targets, amount, *a, **k)

    monkeypatch.setattr(E, "damage", recording)
    state = start(first=0)
    enemy = put(state, 1, demo.SHIELDBEARER)
    set_pp(state, 0, 10)
    zoe = give(state, 0, haven.ZOE)
    apply(state, PlayCard(zoe.uid, (), (0,)))              # mode 1: 3 damage to all enemy followers
    assert calls[0] == ([enemy.uid], 3) and calls[-1] == ([zoe.uid], 3)   # the mode first, then the self-damage
    assert zoe.life == haven.ZOE.life - 3


def test_c10r_sofina_evolved_by_galleon_at_end_of_turn_does_not_activate_that_turn():
    from svsim.cards import haven as H
    from helpers import unlock_evolution
    state = start(first=0)
    galleon = put(state, 0, H.GALLEON)
    galleon.evolved = True                                 # so Galleon picks Sofina
    sofina = put(state, 0, H.SOFINA)
    enemy = put(state, 1, demo.SHIELDBEARER)               # 1/3
    unlock_evolution(state, 0)
    apply(state, EndTurn())                                # Galleon evolves Sofina at the end of the turn
    assert sofina.evolved and (enemy.atk, enemy.life) == (1, 3)   # her own end-of-turn ability did not fire
    apply(state, EndTurn())
    apply(state, EndTurn())                                # her next turn end: now -1/-1 to all other followers
    assert (enemy.atk, enemy.life) == (0, 2)


def _test_card(card_id, name, ctype, cost=1, atk=0, life=0, traits=(), last_words=False):
    from svsim.core.carddef import CardDef
    from svsim.core.enums import Craft
    from svsim.core.script import CardScript, has_script, register
    defn = CardDef(card_id, name, Craft.NEUTRAL, ctype, cost, atk, life, traits=traits)
    if not has_script(card_id):
        body = {"last_words": (lambda self, ctx: None)} if last_words else {}
        register(card_id)(type(f"Test{card_id}", (CardScript,), body))
    return defn


def _picks_of(make_state, act, picked, seeds=200):
    """How often `picked(state)` is true over `seeds` runs of act(make_state(seed))."""
    n = 0
    for seed in range(seeds):
        state = make_state(seed)
        act(state)
        n += bool(picked(state))
    return n


def test_c08_sublime_eld_tome_kandima_aika_and_zerk_pick_per_destruction_not_per_name():
    from svsim.cards import haven, neutral, portal
    from svsim.core.actions import PlayCard
    from svsim.core.engine import resolve_queue
    from svsim.core.enums import CardType
    from helpers import give, set_pp
    amulets = [_test_card(7598 + i, f"Test LW Amulet {i}", CardType.AMULET, last_words=True) for i in range(3)]
    artifacts = [_test_card(7601 + i, f"Test Artifact {i}", CardType.FOLLOWER, 1, 1, 1, traits=("Artifact",))
                 for i in range(2)]
    common, rare = amulets[0], amulets[1:]
    on_field = lambda s, d: any(c.defn.card_id == d.card_id for c in s.players[0].field)  # noqa: E731
    in_hand = lambda s, d: any(c.defn.card_id == d.card_id for c in s.players[0].hand)     # noqa: E731

    def fresh(seed, destroyed_amulets=(), destroyed=()):
        state = start(seed=seed)
        p = state.players[0]
        p.hand.clear()
        p.destroyed_amulets = list(destroyed_amulets)
        p.destroyed = list(destroyed)
        set_pp(state, 0, 10)
        return state

    def play(defn):
        def act(state):
            apply(state, PlayCard(give(state, 0, defn).uid))
        return act

    # Sublime Eld Tome, Last Words: one copy; the common amulet was destroyed 20 times, the other once
    def tome_dies(state):
        tome = put(state, 0, haven.SUBLIME_ELD_TOME)
        E.destroy(state, tome)
        resolve_queue(state)
    n = _picks_of(lambda s: fresh(s, [common] * 20 + [rare[0]]), tome_dies, lambda s: on_field(s, common))
    assert n >= 160                                        # per destruction ~182 (the Tome itself joins the pool); by name ~67
    # Kandima, Fanfare: 2 differently named; the common one is almost always among them
    n = _picks_of(lambda s: fresh(s, [common] * 20 + rare), play(haven.KANDIMA), lambda s: on_field(s, common))
    assert n >= 185                                        # per destruction ~199; by name ~133
    # Aika, Fanfare: a copy of a destroyed follower to the hand
    others = [demo.SHIELDBEARER, demo.LANCER, demo.ANGEL, demo.ASSASSIN, demo.LEECH]
    n = _picks_of(lambda s: fresh(s, destroyed=[demo.FOOTMAN] * 20 + others), play(neutral.AIKA),
                  lambda s: in_hand(s, demo.FOOTMAN))
    assert n >= 140                                        # per destruction ~160; by name ~33
    # Zerk, Fanfare: a destroyed Artifact follower's name to the hand
    n = _picks_of(lambda s: fresh(s, destroyed=[artifacts[0]] * 20 + [artifacts[1]]), play(portal.ZERK),
                  lambda s: in_hand(s, artifacts[0]))
    assert n >= 170                                        # per destruction ~190; by name ~100
