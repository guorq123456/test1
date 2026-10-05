"""Engine mechanics for the full pool, tested with synthetic cards (ids 7000+)."""
from svsim.cards import demo
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Engage, Evolve, Fuse, PlayCard
from svsim.core.carddef import CardDef
from svsim.core.engine import apply, legal_actions, resolve_queue
from svsim.core.enums import CardType, Craft, Keyword
from svsim.core.script import CardScript, Target, TargetSpec, register
from svsim.core.state import BANISHED, DESTROYED, IN_PLAY, leader_uid

from helpers import give, plays, put, set_pp, start, unlock_evolution

N, F, A, CA, S = Craft.NEUTRAL, CardType.FOLLOWER, CardType.AMULET, CardType.COUNTDOWN_AMULET, CardType.SPELL
LOG: list = []

SHRINE = CardDef(7001, "Shrine", N, A, 1)              # Engage (1): draw a card
WATCHER = CardDef(7002, "Watcher", N, F, 3, 1, 3)      # whenever you Engage, +1/+0
PATIENT = CardDef(7003, "Patient Spell", N, S, 5)      # in hand: Engage reduces its cost by 1
FORGE = CardDef(7004, "Forge", N, F, 3, 1, 1)          # Fuse: spells; +1/+1 per fused card
SCROLL = CardDef(7005, "Scroll", N, S, 2)              # On Spellboost: cost -1
INSIGHT = CardDef(7006, "Insight", N, S, 1)            # draw a card
SAGE = CardDef(7007, "Sage", N, F, 6, 3, 3)            # Skybound Art
SIGIL = CardDef(7008, "Sigil Stone", N, A, 1, traits=("Earth Sigil",))
SEDIMENT = CardDef(7009, "Sediment", N, A, 1, traits=("Earth Sigil",), is_token=True)
SKELETON = CardDef(7010, "Skeleton", N, F, 1, 1, 1, is_token=True)
SEER = CardDef(7011, "Seer", N, F, 4, 2, 2)            # Invoked from the deck at turn start
CRYSTAL_FORM = CardDef(7013, "Crystal (Crystallize)", N, CA, 2, countdown=2)
CRYSTAL = CardDef(7012, "Crystal", N, F, 6, 6, 6, crystallize=CRYSTAL_FORM)
DUELIST = CardDef(7014, "Duelist", N, F, 2, 2, 2)      # strike logging
GHOST = CardDef(7015, "Ghost", N, F, 1, 1, 1)          # banished when it leaves the field
GOLEM = CardDef(7016, "Golem", N, F, 5, 3, 3)          # can't be destroyed by abilities; damage cap 2
SPY = CardDef(7017, "Spy", N, F, 2, 1, 1)              # listens to many events


@register(SHRINE.card_id)
class Shrine(CardScript):
    engage_cost = 1

    def engage(self, ctx):
        E.draw(ctx.state, ctx.controller)


@register(WATCHER.card_id)
class Watcher(CardScript):
    def on_engage(self, ctx):
        E.buff(ctx.state, ctx.source, 1, 0)


@register(PATIENT.card_id)
class Patient(CardScript):
    listen_in_hand = True

    def on_engage(self, ctx):
        E.add_cost(ctx.source, -1)


@register(FORGE.card_id)
class Forge(CardScript):
    fuse_filter = staticmethod(lambda card: card.defn.is_spell)

    def on_fuse(self, ctx):
        E.buff(ctx.state, ctx.source, len(ctx.cards), len(ctx.cards))


@register(SCROLL.card_id)
class Scroll(CardScript):
    def on_spellboost(self, ctx):
        E.add_cost(ctx.source, -1)


@register(INSIGHT.card_id)
class Insight(CardScript):
    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller)


@register(SAGE.card_id)
class Sage(CardScript):
    skybound = True

    def fanfare(self, ctx):
        LOG.append(("sage", E.skybound_art(ctx), E.super_skybound_art(ctx)))


@register(SEER.card_id)
class Seer(CardScript):
    invoke_at = "turn_start"

    def can_invoke(self, state, card):
        return state.players[card.owner].evolutions >= 2

    def on_invoked(self, ctx):
        LOG.append("invoked")


@register(DUELIST.card_id)
class Duelist(CardScript):
    def strike(self, ctx):
        LOG.append("strike")

    def follower_strike(self, ctx):
        LOG.append("follower_strike")

    def leader_strike(self, ctx):
        LOG.append("leader_strike")


@register(GHOST.card_id)
class Ghost(CardScript):
    banish_on_leave = True

    def last_words(self, ctx):
        LOG.append("ghost last words")


@register(GOLEM.card_id)
class Golem(CardScript):
    indestructible = True
    damage_cap = 2


@register(SPY.card_id)
class Spy(CardScript):
    def on_attack(self, ctx):
        LOG.append(("attack", ctx.other.defn.name))

    def on_card_destroyed(self, ctx):
        LOG.append(("destroyed", ctx.other.defn.name))

    def on_draw(self, ctx):
        LOG.append(("draw", ctx.other.defn.name))

    def on_enemy_enter(self, ctx):
        LOG.append(("enemy enters", ctx.other.defn.name))

    def on_ally_evolve(self, ctx):
        LOG.append(("ally evolves", ctx.other.defn.name, ctx.super_))

    def on_opponent_turn_end(self, ctx):
        LOG.append("opponent turn end")


INCENSE = CardDef(7018, "Incense", N, S, 4)             # in hand: end of turn, Combo (2) - cost -1


@register(INCENSE.card_id)
class Incense(CardScript):
    listen_in_hand = True

    def on_turn_end(self, ctx):
        if ctx.me.combo >= 2:
            E.add_cost(ctx.source, -1)


class CantAttack(CardScript):
    cant_attack = True


class TwoAttacks(CardScript):
    attacks_per_turn = 2


def setup_function():
    LOG.clear()


# --- Engage --------------------------------------------------------------------------

def test_engage_once_per_turn_and_listeners():
    state = start()
    p = state.players[0]
    shrine = put(state, 0, SHRINE)
    watcher = put(state, 0, WATCHER)
    patient = give(state, 0, PATIENT)
    set_pp(state, 0, 3)
    hand = len(p.hand)
    assert Engage(shrine.uid) in legal_actions(state)
    apply(state, Engage(shrine.uid))
    assert p.pp == 2 and len(p.hand) == hand + 1          # drew a card
    assert watcher.atk == 2 and patient.cost == 4         # field and in-hand listeners
    assert Engage(shrine.uid) not in legal_actions(state)
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert Engage(shrine.uid) in legal_actions(state)


# --- Fuse ----------------------------------------------------------------------------

def test_fuse_removes_cards_without_shadows():
    state = start()
    p = state.players[0]
    p.hand.clear()
    forge = give(state, 0, FORGE)
    a, b = give(state, 0, INSIGHT), give(state, 0, SCROLL)
    give(state, 0, demo.FOOTMAN)                          # not a spell: can't be fused
    fuses = [x for x in legal_actions(state) if isinstance(x, Fuse)]
    assert {x.cards for x in fuses} == {(a.uid,), (b.uid,), (a.uid, b.uid)}
    apply(state, Fuse(forge.uid, (a.uid, b.uid)))
    assert (forge.atk, forge.life, p.shadows, len(p.hand)) == (3, 3, 0, 2)
    assert forge.counters["fused"] == [INSIGHT.card_id, SCROLL.card_id]
    assert not any(isinstance(x, Fuse) for x in legal_actions(state))   # once per turn


# --- Spellboost ------------------------------------------------------------------------

def test_spellboost_after_the_spell_resolves():
    state = start(deck=[SCROLL] * 40)
    p = state.players[0]
    p.hand.clear()
    scroll = give(state, 0, SCROLL)
    insight = give(state, 0, INSIGHT)
    set_pp(state, 0, 1)
    apply(state, PlayCard(insight.uid))
    drawn = p.hand[-1]
    assert scroll.counters["spellboost"] == 1 and scroll.cost == 1
    assert drawn.counters["spellboost"] == 1               # drawn by the spell, then boosted


# --- Skybound Art ----------------------------------------------------------------------

def test_skybound_gauge_counts_turns_and_evolutions_in_hand():
    state = start()
    unlock_evolution(state, 0)                             # own turn 8
    sage = give(state, 0, SAGE)
    a, b = put(state, 0, demo.FOOTMAN), put(state, 0, demo.FOOTMAN)
    apply(state, Evolve(a.uid))
    E.evolve(state, b)                                     # effect evolutions count too
    resolve_queue(state)
    assert E.skybound_gauge(state, sage) == 10
    set_pp(state, 0, 6)
    apply(state, PlayCard(sage.uid))
    assert LOG == [("sage", True, False)]


# --- Earth sigils ----------------------------------------------------------------------

def test_earth_sigils_merge_and_earth_rite_spends_them():
    state = start()
    E.gain_earth_sigils(state, 0, 2, SEDIMENT)
    sediment = state.players[0].field[0]
    assert sediment.defn == SEDIMENT and sediment.counters["sigils"] == 2
    stone = put(state, 0, SIGIL)                           # merges: the old one is banished
    assert state.players[0].field == [stone] and stone.counters["sigils"] == 3
    assert E.unselectable(stone) and not E.destroy(state, stone)   # can't be destroyed by abilities
    assert E.earth_rite(state, 0, 2) and stone.counters["sigils"] == 1
    assert not E.earth_rite(state, 0, 2)
    assert E.earth_rite(state, 0, 1) and stone.fate == DESTROYED


# --- Necromancy, Reanimate ----------------------------------------------------------------

def test_necromancy_and_reanimate():
    state = start()
    p = state.players[0]
    p.shadows = 5
    assert E.necromancy(state, 0, 4) and p.shadows == 1 and not E.necromancy(state, 0, 4)
    p.destroyed += [demo.FOOTMAN, demo.LANCER, demo.GIANT]          # costs 1, 3, 5
    revived = E.reanimate(state, 0, 4)
    assert revived.defn == demo.LANCER and E.has_trait(revived, "Departed")


# --- Transform, copies, returns -----------------------------------------------------------

def test_transform_keeps_place_and_skips_last_words():
    state = start()
    bomber = put(state, 1, demo.BOMBER)
    other = put(state, 1, demo.FOOTMAN)
    E.buff(state, bomber, 3, 3)
    E.transform(state, bomber, SKELETON)
    resolve_queue(state)
    assert state.players[1].field == [bomber, other] and bomber.defn == SKELETON
    assert (bomber.atk, bomber.life, bomber.fate) == (1, 1, IN_PLAY)
    assert state.players[0].leader_hp == 20


def test_exact_copy_keeps_buffs_and_return_to_hand_resets():
    state = start()
    lancer = put(state, 0, demo.LANCER)
    E.buff(state, lancer, 2, 2)
    clone = E.summon_copy(state, 0, lancer)
    assert (clone.atk, clone.life) == (5, 4) and clone.uid != lancer.uid
    fresh = E.return_to_hand(state, lancer)
    assert fresh in state.players[0].hand and (fresh.atk, fresh.life) == (3, 2)
    E.add_cost(fresh, -2)
    E.return_to_deck(state, fresh)
    assert fresh in state.players[0].deck and fresh.cost == 1     # keeps its cost change


# --- Timed effects -------------------------------------------------------------------------

def test_until_end_of_turn_effects_expire():
    state = start(first=0)
    footman = put(state, 0, demo.FOOTMAN)
    E.buff(state, footman, 2, 2, until_turn=state.turn)
    E.give_keywords(footman, Keyword.WARD, until_turn=state.turn + 1)
    assert (footman.atk, footman.life) == (3, 4) and footman.has(Keyword.WARD)
    apply(state, EndTurn())
    assert (footman.atk, footman.life) == (1, 2) and footman.has(Keyword.WARD)
    apply(state, EndTurn())
    assert not footman.has(Keyword.WARD)


def test_granted_abilities():
    state = start(first=0)
    raider = put(state, 0, demo.RAIDER)
    E.grant(raider, CantAttack(), until_turn=state.turn)
    assert not any(isinstance(a, Attack) for a in legal_actions(state))
    apply(state, EndTurn())
    apply(state, EndTurn())
    E.grant(raider, TwoAttacks())
    for _ in range(2):
        apply(state, Attack(raider.uid, leader_uid(1)))
    assert state.players[1].leader_hp == 16


def test_cost_changes_apply_in_order():
    state = start()
    card = give(state, 0, demo.GIANT)                      # 5
    E.add_cost(card, -1)
    E.halve_cost(card)
    assert card.cost == 2                                  # (5 - 1) / 2
    E.set_cost(card, 7)
    E.add_cost(card, -9)
    assert card.cost == 0
    E.add_cost(card, 1)
    assert card.cost == 0                                  # reductions run below 0
    timed = give(state, 0, demo.GIANT)
    E.set_cost(timed, 0, until_turn=state.turn)
    apply(state, EndTurn())
    assert timed.cost == 5


# --- Turn structure ------------------------------------------------------------------------

def test_invoke_from_deck_at_turn_start():
    state = start(first=0)
    p = state.players[0]
    p.deck.append(state.new_instance(SEER, 0))
    p.evolutions = 2
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert [c.defn for c in p.field] == [SEER] and LOG == ["invoked"]


def test_crystallize_when_the_normal_cost_is_unaffordable():
    state = start()
    p = state.players[0]
    crystal = give(state, 0, CRYSTAL)
    set_pp(state, 0, 2)
    apply(state, PlayCard(crystal.uid))
    assert p.field == [crystal] and crystal.defn == CRYSTAL_FORM and crystal.countdown == 2
    assert 2 in p.played_base_costs


def test_strike_variants_and_attack_listeners():
    state = start(first=0)
    duelist = put(state, 0, DUELIST)
    put(state, 1, SPY)
    enemy = put(state, 1, demo.FOOTMAN)
    apply(state, Attack(duelist.uid, enemy.uid))
    assert LOG == ["strike", "follower_strike", ("attack", "Duelist"), ("destroyed", "Footman")]
    apply(state, EndTurn())
    apply(state, EndTurn())
    LOG.clear()
    apply(state, Attack(duelist.uid, leader_uid(1)))
    assert LOG[:2] == ["strike", "leader_strike"]
    assert state.players[0].attacked_leader_this_turn


def test_event_listeners():
    state = start(first=0)
    put(state, 1, SPY)
    footman = put(state, 0, demo.FOOTMAN)
    unlock_evolution(state, 0)
    apply(state, Evolve(footman.uid))
    E.destroy(state, footman)
    resolve_queue(state)
    apply(state, EndTurn())
    assert ("enemy enters", "Footman") in LOG
    assert ("destroyed", "Footman") in LOG
    assert "opponent turn end" in LOG
    assert ("draw", "Footman") in LOG                      # player 1 drew at turn start


def test_split_damage_oldest_first():
    state = start()
    a, b = put(state, 1, demo.FOOTMAN), put(state, 1, demo.GIANT)    # 1/2, 5/5
    E.split_damage(state, 1, 4)
    assert a.fate == DESTROYED and b.life == 3
    E.split_damage(state, 1, 9, followers_only=False)          # 3 to the Giant, 6 to the leader
    assert b.fate == DESTROYED and state.players[1].leader_hp == 14


def test_banish_on_leave_indestructible_and_damage_cap():
    state = start()
    ghost = put(state, 0, GHOST)
    E.destroy(state, ghost)
    resolve_queue(state)
    assert ghost.fate == BANISHED and LOG == [] and state.players[0].shadows == 0
    golem = put(state, 0, GOLEM)
    assert not E.destroy(state, golem)
    E.damage(state, [golem], 5)
    assert golem.life == 1                                  # took at most 2


def test_filtered_and_other_targets():
    class Picky(CardScript):
        play_targets = (TargetSpec(Target.ANY_FOLLOWER, filter=lambda s, p, c: c.cost >= 3),)

    register(7020)(Picky)
    state = start()
    put(state, 0, demo.FOOTMAN)
    giant = put(state, 1, demo.GIANT)
    set_pp(state, 0, 2)
    card = give(state, 0, CardDef(7020, "Picky", N, S, 2))
    assert plays(state, card.uid) == [PlayCard(card.uid, (giant.uid,))]


def test_hand_cards_get_turn_hooks_when_active_in_hand():
    state = start(first=0)
    incense = give(state, 0, INCENSE)
    state.players[0].combo = 2
    apply(state, EndTurn())
    assert incense.cost == 3


# --- Engine follow-ups: rules the full pool needs ------------------------------------------

PIERCER = CardDef(7021, "Piercer", N, F, 2, 2, 2, Keyword.STORM)   # Ignores Ward
HERALD = CardDef(7022, "Herald", N, F, 2, 1, 1)        # when this enters the field, log it
CHOOSER = CardDef(7023, "Chooser", N, F, 3, 2, 2)      # Super-Evolve: select an enemy follower
MUTER = CardDef(7024, "Muter Crest", N, CardType.CREST, 0)   # allied Fanfare / Enhance off
LOOKOUT = CardDef(7025, "Lookout", N, F, 2, 2, 2)      # end of turn, if evolved: log it


@register(PIERCER.card_id)
class Piercer(CardScript):
    ignores_ward = True


@register(HERALD.card_id)
class Herald(CardScript):
    def on_enter(self, ctx):
        LOG.append(("enters", ctx.source.uid))


@register(CHOOSER.card_id)
class Chooser(CardScript):
    super_evolve_targets = (TargetSpec(Target.ENEMY_FOLLOWER),)

    def on_super_evolve(self, ctx):
        E.destroy(ctx.state, ctx.chosen()[0])


@register(MUTER.card_id)
class Muter(CardScript):
    suppresses_fanfare = True


@register(LOOKOUT.card_id)
class Lookout(CardScript):
    queue_checks = ("on_turn_end",)

    def queue_condition(self, hook, ctx):
        return ctx.source.evolved

    def on_turn_end(self, ctx):
        LOG.append("lookout")


class EvolveOtherAtTurnEnd(CardScript):
    def on_turn_end(self, ctx):
        for f in ctx.me.followers:
            E.evolve(ctx.state, f)


def test_ignores_ward():
    state = start(first=0)
    piercer = put(state, 0, PIERCER, ready=False)
    raider = put(state, 0, demo.RAIDER, ready=False)
    footman = put(state, 1, demo.FOOTMAN)
    wall = put(state, 1, demo.SHIELDBEARER)
    attacks = {(a.attacker, a.target) for a in legal_actions(state) if isinstance(a, Attack)}
    assert {(piercer.uid, footman.uid), (piercer.uid, wall.uid), (piercer.uid, leader_uid(1)),
            (raider.uid, wall.uid)} == attacks


def test_on_enter_fires_however_it_enters():
    state = start(first=0)
    set_pp(state, 0, 2)
    played = give(state, 0, HERALD)
    apply(state, PlayCard(played.uid))
    summoned = E.summon(state, 0, HERALD)
    resolve_queue(state)
    assert LOG == [("enters", played.uid), ("enters", summoned.uid)]
    assert state.players[0].entered[HERALD.card_id] == 2


def test_super_evolve_only_targets():
    state = start(first=0)
    unlock_evolution(state, 0)
    chooser = put(state, 0, CHOOSER)
    enemy = put(state, 1, demo.FOOTMAN)
    evolves = [a for a in legal_actions(state) if isinstance(a, Evolve)]
    assert set(evolves) == {Evolve(chooser.uid, False, ()), Evolve(chooser.uid, True, (enemy.uid,))}
    apply(state, Evolve(chooser.uid, True, (enemy.uid,)))
    assert enemy.fate == DESTROYED


def test_fanfare_and_enhance_suppressed():
    state = start(first=0)
    E.add_to_leader_area(state, 0, MUTER)
    set_pp(state, 0, 6)
    mage = give(state, 0, demo.MAGE)                       # Enhance (6): +3/+3
    archer = give(state, 0, demo.ARCHER)                   # Fanfare: 1 damage
    apply(state, PlayCard(mage.uid))
    assert (mage.atk, mage.life, state.players[0].pp) == (2, 2, 3)   # paid 3, not 6
    enemy = put(state, 1, demo.SHIELDBEARER)
    apply(state, PlayCard(archer.uid, (enemy.uid,)))
    assert enemy.life == 3


def test_queue_checked_condition_uses_the_moment_it_triggers():
    state = start(first=0)
    lookout = put(state, 0, LOOKOUT)
    E.grant(lookout, EvolveOtherAtTurnEnd())               # evolves it during the same end of turn
    apply(state, EndTurn())
    assert lookout.evolved and LOG == []
    apply(state, EndTurn())
    apply(state, EndTurn())
    assert LOG == ["lookout"]


def test_silence_and_remove_last_words():
    state = start(first=0)
    bomber = put(state, 1, demo.BOMBER)                    # Last Words: 2 damage to enemy leader
    angel = put(state, 1, demo.ANGEL)                      # Barrier
    E.buff(state, angel, 1, 1)
    E.grant(angel, TwoAttacks())
    E.silence(angel)
    assert angel.keywords == Keyword.NONE and (angel.atk, angel.life) == (3, 4)
    assert not E.has_last_words(angel) and E.has_last_words(bomber)
    E.remove_last_words(bomber)
    assert not E.has_last_words(bomber)
    E.destroy(state, bomber)
    resolve_queue(state)
    assert state.players[0].leader_hp == 20
    golem = put(state, 1, GOLEM)                           # damage cap 2, indestructible
    E.silence(golem)
    assert E.destroy(state, golem)


def test_barrier_survives_zero_damage_and_invincibility():
    state = start(first=0)
    angel = put(state, 1, demo.ANGEL)
    E.damage(state, [angel], 0)
    assert angel.has(Keyword.BARRIER)
    E.damage(state, [angel], 2)
    assert not angel.has(Keyword.BARRIER) and angel.life == 3


def test_timed_keywords_and_debuffs_expire_cleanly():
    state = start(first=0)
    footman = put(state, 0, demo.FOOTMAN)                  # 1/2
    E.give_keywords(footman, Keyword.WARD, until_turn=state.turn)
    E.give_keywords(footman, Keyword.WARD)                 # also permanently
    E.buff(state, footman, -3, 0, until_turn=state.turn)   # attack floors at 0
    apply(state, EndTurn())
    assert footman.has(Keyword.WARD) and footman.atk == 1


def test_leader_takes_extra_damage():
    state = start(first=0)
    state.players[1].extra_damage = 1
    E.damage(state, [leader_uid(1)], 3)
    E.damage(state, [leader_uid(1)], 0)
    assert state.players[1].leader_hp == 16


def test_buffed_hand_cards_are_not_merged():
    state = start(first=0)
    set_pp(state, 0, 1)
    a, b = give(state, 0, demo.FOOTMAN), give(state, 0, demo.FOOTMAN)
    for c in list(state.players[0].hand):
        if c is not a and c is not b:
            E.discard(state, c)
    b.atk = 3
    assert {x.uid for x in legal_actions(state) if isinstance(x, PlayCard)} == {a.uid, b.uid}
