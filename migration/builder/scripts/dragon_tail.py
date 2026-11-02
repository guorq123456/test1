

# =====================================================================================
# The rest of the Rotation pool
# =====================================================================================

def _on_field(state, inst) -> bool:
    return state.on_field(inst.uid) is inst


def _random_enemy_follower(ctx) -> list:
    """A random enemy follower (random effects can hit Aura), as a 0- or 1-item list."""
    return E.random_sample(ctx.state, ctx.opponent.followers, 1)


def _discard_chosen(ctx) -> None:
    for c in ctx.chosen_hand():
        E.discard(ctx.state, c)


def _evolve_self(ctx, super_: bool = False) -> None:
    """"Evolve / Super-evolve this follower": an effect, so no points are spent
    and the follower's own Evolve / Super-Evolve abilities don't fire."""
    if not ctx.source.evolved and _on_field(ctx.state, ctx.source):
        E.evolve(ctx.state, ctx.source, super_=super_)


def _attacked_leader_last_turn(ctx) -> bool:
    """"If an allied follower attacked a leader on your last turn"."""
    return ctx.me.attacked_leader_last_turn


def _ten_max_pp(ctx) -> bool:
    return ctx.me.max_pp >= 10


def _add_to_hand_with_cost(ctx, defn, cost: int):
    added = E.add_to_hand(ctx.state, ctx.controller, defn)
    if added:
        E.set_cost(added, cost)
    return added


def _buff_in_hand(state, inst, atk: int, life: int) -> None:
    """Buff a card in hand. The new stats are also noted in its counters: the
    engine tells identical hand cards apart by id, cost, keywords and counters
    only, so without this a buffed copy would be merged with unbuffed ones."""
    E.buff(state, inst, atk, life)
    E.counters(inst)["hand_stats"] = (inst.atk, inst.life)


def _destroy_strongest_enemy(ctx) -> None:
    """Destroy a random enemy follower with the highest attack."""
    enemies = ctx.opponent.followers
    if enemies:
        top = max(f.atk for f in enemies)
        for f in E.random_sample(ctx.state, [f for f in enemies if f.atk == top], 1):
            E.destroy(ctx.state, f)


class _AttackTwice(CardScript):
    """Granted: "Can attack 2 times per turn"."""
    attacks_per_turn = 2


class _CantAttack(CardScript):
    """Granted: "Can't attack followers or leaders"."""
    cant_attack = True


ATTACK_TWICE = _AttackTwice()
CANT_ATTACK = _CantAttack()


# --- crests ------------------------------------------------------------------------------

@register(SPIRIT_OF_WADATSUMI_CREST.card_id)
class SpiritOfWadatsumiCrest(CardScript):
    """Whenever an allied Marine follower enters the field, give it +1/+1."""

    def on_ally_enter(self, ctx):
        if E.has_trait(ctx.other, MARINE) and _on_field(ctx.state, ctx.other):
            E.buff(ctx.state, ctx.other, 1, 1)


@register(DRACHE_AND_ALUZARD_CREST.card_id)
class DracheAndAluzardCrest(CardScript):
    """Countdown (2). Last Words: add a Drache & Aluzard to your hand and set its cost to 2."""

    def last_words(self, ctx):
        _add_to_hand_with_cost(ctx, DRACHE_AND_ALUZARD, 2)


@register(DRAGONS_VALE_ELDER_CREST.card_id)
class DragonsValeElderCrest(CardScript):
    """Countdown (2). At the end of your turn, summon a Vastwing Dragon."""

    def on_turn_end(self, ctx):
        E.summon(ctx.state, ctx.controller, VASTWING_DRAGON)


@register(YUBE_CREST.card_id)
class YubeCrest(CardScript):
    """Whenever an allied Marine follower attacks, give it +1/+0 until the end of the
    turn and, once on each of your turns, add a Majestic Megalorca to your hand."""

    def on_attack(self, ctx):
        attacker = ctx.other
        if attacker.owner != ctx.controller or not E.has_trait(attacker, MARINE):
            return
        if _on_field(ctx.state, attacker):
            E.buff(ctx.state, attacker, 1, 0, until_turn=common.end_of_turn(ctx))
        if common.during_your_turn(ctx) and E.once_per_turn(ctx, "megalorca"):
            E.add_to_hand(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)


@register(CRESCENT_TUBE_RIDE_CREST.card_id)
class CrescentTubeRideCrest(CardScript):
    """Countdown (4). At the end of your turn, give a random allied follower +1/+1."""

    def on_turn_end(self, ctx):
        for f in E.random_sample(ctx.state, ctx.me.followers, 1):
            E.buff(ctx.state, f, 1, 1)


# --- set 10009: Revenants of Azvaldt -------------------------------------------------------

@register(RIPPER_CLAWED_THIEF.card_id)
class RipperClawedThief(CardScript):
    """Fanfare: if an allied follower attacked a leader on your last turn, gain Storm.
    Last Words: add a Ripper-Clawed Thief to your hand and remove its Last Words."""

    def fanfare(self, ctx):
        if _attacked_leader_last_turn(ctx):
            E.give_keywords(ctx.source, Keyword.STORM)

    def last_words(self, ctx):
        if (ctx.source.counters or {}).get(NO_LAST_WORDS):
            return
        thief = E.add_to_hand(ctx.state, ctx.controller, RIPPER_CLAWED_THIEF)
        if thief:
            E.counters(thief)[NO_LAST_WORDS] = True


@register(CAVE_DRAGON.card_id)
class CaveDragon(CardScript):
    """Fanfare: if you're in Overflow, evolve this follower. Ambush."""

    def fanfare(self, ctx):
        if E.overflow(ctx.state, ctx.controller):
            _evolve_self(ctx)


@register(DRAKE_WHELPS_TANTRUM.card_id)
class DrakeWhelpsTantrum(CardScript):
    """Summon a Fire Drake Whelp. Enhance (3): also deal 3 damage to a random enemy follower."""
    enhance = (3,)

    def cast(self, ctx):
        E.summon(ctx.state, ctx.controller, FIRE_DRAKE_WHELP)
        if ctx.enhanced:
            E.damage(ctx.state, _random_enemy_follower(ctx), 3, ctx.source)


@register(HIGH_SPIRITED_MARAUDER.card_id)
class HighSpiritedMarauder(CardScript):
    """Storm. Strike: if an allied follower attacked a leader on your last turn, gain
    +1/+0 until the end of the turn."""

    def strike(self, ctx):
        if _attacked_leader_last_turn(ctx):
            E.buff(ctx.state, ctx.source, 1, 0, until_turn=common.end_of_turn(ctx))


@register(DRAGONFOLK_BUTLER.card_id)
class DragonfolkButler(CardScript):
    """Fanfare: restore 3 defense to your leader and recover 3 play points. Evolve:
    select another allied follower and give it +3/+3."""
    evolve_targets = common.OTHER_ALLIED_FOLLOWER

    def fanfare(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 3)
        E.recover_pp(ctx.state, ctx.controller, 3)

    def on_evolve(self, ctx):
        for f in ctx.chosen():
            E.buff(ctx.state, f, 3, 3)


@register(PARTING_JAWS.card_id)
class PartingJaws(CardScript):
    """Select 2 cards in your hand and discard them. Deal 3 damage to a random enemy
    follower and the enemy leader."""
    play_targets = (TargetSpec(Target.HAND_CARD, 2),)

    def cast(self, ctx):
        _discard_chosen(ctx)
        E.damage(ctx.state, _random_enemy_follower(ctx) + [common.enemy_leader(ctx)], 3,
                 ctx.source)


@register(BARREN_EARTH_TYRANT.card_id)
class BarrenEarthTyrant(CardScript):
    """Fanfare: deal 4 damage to a random enemy follower, twice if an allied follower
    attacked a leader on your last turn. Evolve: summon a High-Spirited Marauder."""

    def fanfare(self, ctx):
        for _ in range(2 if _attacked_leader_last_turn(ctx) else 1):
            E.damage(ctx.state, _random_enemy_follower(ctx), 4, ctx.source)

    def on_evolve(self, ctx):
        E.summon(ctx.state, ctx.controller, HIGH_SPIRITED_MARAUDER)


@register(ARTIGLIO.card_id)
class Artiglio(CardScript):
    """Deal 3 damage split between all enemy followers, 6 if an allied follower
    attacked a leader on your last turn."""

    def cast(self, ctx):
        amount = 6 if _attacked_leader_last_turn(ctx) else 3
        E.split_damage(ctx.state, 1 - ctx.controller, amount, ctx.source)


@register(ANTEMARIA.card_id)
class Antemaria(CardScript):
    """Fanfare: if an allied follower attacked a leader on your last turn, gain Storm.
    Rush. Ignores Ward."""
    # APPROX: the engine has no "Ignores Ward" (engine._attack_actions always
    # enforces Ward), so enemy Ward followers still restrict this follower's
    # attacks. The flag below documents the property for when it is supported.
    ignores_ward = True

    def fanfare(self, ctx):
        if _attacked_leader_last_turn(ctx):
            E.give_keywords(ctx.source, Keyword.STORM)


# --- set 10008: Chronicle of Destiny --------------------------------------------------------

@register(GIDO.card_id)
class Gido(CardScript):
    """Fanfare: if your leader's defense is 10 or less, evolve this follower. Bane. Ward."""

    def fanfare(self, ctx):
        if ctx.me.leader_hp <= 10:
            _evolve_self(ctx)


@register(SANDSTORM_WATCHDRAGON.card_id)
class SandstormWatchdragon(CardScript):
    """Ward. Last Words: draw 3 cards."""

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller, 3)


@register(SPIRIT_OF_WADATSUMI.card_id)
class SpiritOfWadatsumi(CardScript):
    """Fanfare: add a Majestic Megalorca to your hand. Evolve: gain Crest: Spirit of
    Wadatsumi."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)

    def on_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, SPIRIT_OF_WADATSUMI_CREST)


@register(REEF_AND_LOLO.card_id)
class ReefAndLolo(CardScript):
    """Fanfare: summon a Reef & Lolo. Rush. At the end of your turn, add a Majestic
    Megalorca to your hand."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, REEF_AND_LOLO)

    def on_turn_end(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)


@register(ART_OF_DECAY.card_id)
class ArtOfDecay(CardScript):
    """Deal 4 damage to a random enemy follower. Deal 4 damage to the enemy leader."""

    def cast(self, ctx):
        E.damage(ctx.state, _random_enemy_follower(ctx), 4, ctx.source)
        E.damage(ctx.state, [common.enemy_leader(ctx)], 4, ctx.source)


@register(GIADA.card_id)
class Giada(CardScript):
    """Rush. Intimidate. Strike: gain Barrier; if attacking a follower, also gain
    "Can attack 2 times per turn" until the end of the turn."""

    def strike(self, ctx):
        E.give_keywords(ctx.source, Keyword.BARRIER)
        if ctx.other is not None and not any(g.script is ATTACK_TWICE
                                             for g in ctx.source.grants or ()):
            E.grant(ctx.source, ATTACK_TWICE, until_turn=common.end_of_turn(ctx))


@register(EPHEMERAL_FOXFIRE.card_id)
class EphemeralFoxfire(CardScript):
    """Select an enemy follower or the enemy leader and deal it 1 damage. Put an
    Ephemeral Foxfire into your deck. If you're in Overflow, draw a card."""
    play_targets = common.ENEMY_FOLLOWER_OR_LEADER

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 1, ctx.source)
        E.put_into_deck(ctx.state, ctx.controller, EPHEMERAL_FOXFIRE)
        if E.overflow(ctx.state, ctx.controller):
            E.draw(ctx.state, ctx.controller)


def _other_drache_entries(ctx) -> int:
    """Other allied Drache & Aluzards that entered the field this match."""
    # APPROX: the engine keeps no per-name log of field entries, so this counts
    # the allied copies destroyed this match plus the other copies on the field
    # now. Copies that left the field by being banished, returned to hand or
    # transformed are missed.
    me, cid = ctx.me, DRACHE_AND_ALUZARD.card_id
    destroyed = sum(d.card_id == cid for d in me.destroyed)
    on_field = sum(c.defn.card_id == cid and c is not ctx.source for c in me.field)
    return destroyed + on_field


@register(DRACHE_AND_ALUZARD.card_id)
class DracheAndAluzard(CardScript):
    """Fanfare: gain +X/+X, X = other allied Drache & Aluzards that entered the field
    this match; if X is at least 2, evolve this follower. Ward. Last Words: gain
    Crest: Drache & Aluzard."""

    def fanfare(self, ctx):
        x = _other_drache_entries(ctx)
        if x:
            E.buff(ctx.state, ctx.source, x, x)
        if x >= 2:
            _evolve_self(ctx)

    def last_words(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, DRACHE_AND_ALUZARD_CREST)


# --- set 10007: Anathema's Gambit -------------------------------------------------------------

@register(CARRIER_WYVERN.card_id)
class CarrierWyvern(CardScript):
    """Fanfare: select another allied follower and give it +2/+2. Evolve: select a
    follower in your hand and give it +2/+2."""
    play_targets = common.OTHER_ALLIED_FOLLOWER
    evolve_targets = (TargetSpec(Target.HAND_CARD,
                                 filter=lambda state, player, card: card.defn.is_follower),)

    def fanfare(self, ctx):
        for f in ctx.chosen():
            E.buff(ctx.state, f, 2, 2)

    def on_evolve(self, ctx):
        for c in ctx.chosen_hand():
            _buff_in_hand(ctx.state, c, 2, 2)


@register(APATHETIC_GAZE.card_id)
class ApatheticGaze(CardScript):
    """Gain 1 max play point. Transform every Apathetic Gaze in your hand and deck into
    a Lazing Flame."""

    def cast(self, ctx):
        E.gain_max_pp(ctx.state, ctx.controller)
        for c in [c for c in ctx.me.hand + ctx.me.deck if c.defn.card_id == APATHETIC_GAZE.card_id]:
            E.transform(ctx.state, c, LAZING_FLAME)


@register(GALLANT_GATEKEEPER.card_id)
class GallantGatekeeper(CardScript):
    """Fanfare: select an enemy follower and destroy it. Ward."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        for f in ctx.chosen():
            E.destroy(ctx.state, f)


@register(DRACONIC_PART_TIMER.card_id)
class DraconicPartTimer(CardScript):
    """Fanfare: if you have 10 max play points, evolve this follower. At the end of
    your turn, restore 1 defense to your leader (2 if this follower is evolved)."""

    def fanfare(self, ctx):
        if _ten_max_pp(ctx):
            _evolve_self(ctx)

    def on_turn_end(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 2 if ctx.source.evolved else 1)


@register(DRAGONEWT_PATHFINDER.card_id)
class DragonewtPathfinder(CardScript):
    """Fanfare: destroy a random enemy follower with the highest attack, and Mode:
    1. evolve this follower; 2. give this follower Ambush."""
    modes = (2, 1)

    def fanfare(self, ctx):
        _destroy_strongest_enemy(ctx)
        if 0 in ctx.modes:
            _evolve_self(ctx)
        if 1 in ctx.modes:
            E.give_keywords(ctx.source, Keyword.AMBUSH)


@register(BLACKFLAME_DELUGE.card_id)
class BlackflameDeluge(CardScript):
    """Deal 5 damage to all enemy followers. Deal 3 damage to the enemy leader."""

    def cast(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 5, ctx.source)
        E.damage(ctx.state, [common.enemy_leader(ctx)], 3, ctx.source)


@register(DRAGONS_VALE_ELDER.card_id)
class DragonsValeElder(CardScript):
    """Fanfare: summon a Vastwing Dragon and gain Crest: Dragon's Vale Elder. Ward.
    Super-Evolve: delay the count of that crest by 2."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, VASTWING_DRAGON)
        E.add_to_leader_area(ctx.state, ctx.controller, DRAGONS_VALE_ELDER_CREST)

    def on_super_evolve(self, ctx):
        crest = E.leader_area_card(ctx.state, ctx.controller, DRAGONS_VALE_ELDER_CREST)
        if crest is not None:
            E.advance_countdown(ctx.state, crest, -2)


# --- set 10006: Apocalypse Pact -----------------------------------------------------------------

@register(RESOLUTE_DRAGONEWT.card_id)
class ResoluteDragonewt(CardScript):
    """Fanfare: select a card in your hand and discard it. Last Words: draw 2 cards."""
    play_targets = common.HAND_CARD

    def fanfare(self, ctx):
        _discard_chosen(ctx)

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)


@register(FRUITFISH.card_id)
class Fruitfish(CardScript):
    """Enhance (6): summon 2 Fruitfish. Last Words: restore 1 defense to your leader."""
    enhance = (6,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            for _ in range(2):
                E.summon(ctx.state, ctx.controller, FRUITFISH)

    def last_words(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 1)


@register(ADVENT_OF_THE_ELD_BLADES.card_id)
class AdventOfTheEldBlades(CardScript):
    """Select an allied follower and give it +2/+2. When discarded, if its cost is 4,
    add an Advent of the Eld Blades to your hand and set its cost to 2."""
    play_targets = common.ALLIED_FOLLOWER

    def cast(self, ctx):
        for f in ctx.chosen():
            E.buff(ctx.state, f, 2, 2)

    def on_discard(self, ctx):
        if ctx.source.cost == 4:
            _add_to_hand_with_cost(ctx, ADVENT_OF_THE_ELD_BLADES, 2)


@register(DECISIVE_SWORDMASTER.card_id)
class DecisiveSwordmaster(CardScript):
    """Fanfare: select a card in your hand and discard it. Rush. Barrier."""
    play_targets = common.HAND_CARD

    def fanfare(self, ctx):
        _discard_chosen(ctx)


@register(SPIKED_DRAGON.card_id)
class SpikedDragon(CardScript):
    """At the end of your turn, evolve this follower. When this follower evolves (any
    way), deal 3 damage to all enemies."""

    def on_turn_end(self, ctx):
        _evolve_self(ctx)

    def on_evolved(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers) + [common.enemy_leader(ctx)], 3,
                 ctx.source)


@register(IMPEDING_PUGILIST.card_id)
class ImpedingPugilist(CardScript):
    """Fanfare: select a card in your hand and discard it; deal 6 damage to a random
    enemy follower. Ward. Barrier. Evolve: replicate the Fanfare."""
    play_targets = common.HAND_CARD
    evolve_targets = common.HAND_CARD

    def fanfare(self, ctx):
        self._impede(ctx)

    def on_evolve(self, ctx):
        self._impede(ctx)

    def _impede(self, ctx):
        _discard_chosen(ctx)
        E.damage(ctx.state, _random_enemy_follower(ctx), 6, ctx.source)


@register(BEHEADING_ELD_BLADES.card_id)
class BeheadingEldBlades(CardScript):
    """Deal X damage to all enemy followers, X = this card's cost. When discarded, if
    its cost is 7, add a Beheading Eld Blades costing 5 to your hand; if 5, one
    costing 3."""

    def cast(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), ctx.source.cost, ctx.source)

    def on_discard(self, ctx):
        new_cost = {7: 5, 5: 3}.get(ctx.source.cost)
        if new_cost is not None:
            _add_to_hand_with_cost(ctx, BEHEADING_ELD_BLADES, new_cost)


# --- set 10005: Blossoming Fate -------------------------------------------------------------------

@register(SPRINGWELL_STEWARD.card_id)
class SpringwellSteward(CardScript):
    """Evolve: select an enemy follower and deal it 5 damage. Super-Evolve: select 2
    enemy followers instead."""
    # APPROX: the engine offers one target list for both kinds of evolution, so two
    # picks are always offered. A normal evolve hits only the first pick; a
    # super-evolve hits both (picking the same follower twice hits it once).
    evolve_targets = (TargetSpec(Target.ENEMY_FOLLOWER), TargetSpec(Target.ENEMY_FOLLOWER))

    def on_evolve(self, ctx):
        uids = ctx.targets if ctx.super_ else ctx.targets[:1]
        victims = [f for f in (ctx.state.on_field(uid) for uid in dict.fromkeys(uids))
                   if f is not None]
        E.damage(ctx.state, victims, 5, ctx.source)


@register(STORMY_SHAMISEN_SHREDDER.card_id)
class StormyShamisenShredder(CardScript):
    """Fanfare: summon a Majestic Megalorca. Whenever an allied Marine follower enters
    the field, restore 2 defense to your leader."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)

    def on_ally_enter(self, ctx):
        if E.has_trait(ctx.other, MARINE):
            E.heal_leader(ctx.state, ctx.controller, 2)


@register(BLADE_OF_THE_CRESTPETAL.card_id)
class BladeOfTheCrestpetal(CardScript):
    """Draw a follower. Deal X damage to a random enemy follower, X = the cost of the
    card drawn."""

    def cast(self, ctx):
        followers = [c for c in ctx.me.deck if c.defn.is_follower]
        E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.is_follower)
        left = {id(c) for c in ctx.me.deck}
        drawn = [c for c in followers if id(c) not in left]
        if drawn:
            # UNSURE: with a full hand the drawn card is destroyed; X still uses its cost.
            E.damage(ctx.state, _random_enemy_follower(ctx), drawn[0].cost, ctx.source)


@register(IRONMACE_DRAGOON.card_id)
class IronmaceDragoon(CardScript):
    """Fanfare: select an enemy follower and deal it 7 damage. Summon a Vastwing Dragon."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 7, ctx.source)
        E.summon(ctx.state, ctx.controller, VASTWING_DRAGON)


@register(JELLYFISH_DANCER.card_id)
class JellyfishDancer(CardScript):
    """Fanfare: add a Majestic Megalorca to your hand. Whenever an allied Marine
    follower enters the field, give this follower Rush and Bane."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)

    def on_ally_enter(self, ctx):
        if E.has_trait(ctx.other, MARINE):
            E.give_keywords(ctx.source, Keyword.RUSH | Keyword.BANE)


@register(RUINBRINGER.card_id)
class Ruinbringer(CardScript):
    """Super-Evolve: banish every 1-, 3-, 5-, 7- and 9-cost card in your deck, then deal
    X damage split between all enemy followers, X = the number banished."""

    def on_super_evolve(self, ctx):
        doomed = [c for c in ctx.me.deck if c.cost in (1, 3, 5, 7, 9)]
        for c in doomed:
            E.banish(ctx.state, c)
        E.split_damage(ctx.state, 1 - ctx.controller, len(doomed), ctx.source)


@register(YUBE.card_id)
class Yube(CardScript):
    """Fanfare: summon a Majestic Megalorca. Evolve: select a card in your hand and
    discard it; gain Crest: Yube, Crestpetal."""
    evolve_targets = common.HAND_CARD

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)

    def on_evolve(self, ctx):
        _discard_chosen(ctx)
        E.add_to_leader_area(ctx.state, ctx.controller, YUBE_CREST)


# --- set 10000: Basic ---------------------------------------------------------------------------

@register(SEARING_FIRENEWT.card_id)
class SearingFirenewt(CardScript):
    """Fanfare: select an enemy follower and deal it 1 damage."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 1, ctx.source)


@register(WARRIOR_OF_THE_DEEP.card_id)
class WarriorOfTheDeep(CardScript):
    """Fanfare: deal 6 damage to the enemy leader."""

    def fanfare(self, ctx):
        E.damage(ctx.state, [common.enemy_leader(ctx)], 6, ctx.source)


@register(STRIKE_OF_THE_DRAGONEWT.card_id)
class StrikeOfTheDragonewt(CardScript):
    """Select an enemy follower and deal it 2 damage, 4 if you're in Overflow."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4 if E.overflow(ctx.state, ctx.controller) else 2,
                 ctx.source)


@register(DRACONIC_BERSERKER.card_id)
class DraconicBerserker(CardScript):
    """Evolve: select an enemy follower and deal it 4 damage. Super-Evolve: deal the
    damage to all enemy followers instead."""
    evolve_targets = common.ENEMY_FOLLOWER

    def on_evolve(self, ctx):
        targets = list(ctx.opponent.followers) if ctx.super_ else ctx.chosen()
        E.damage(ctx.state, targets, 4, ctx.source)


@register(BATTLEFORGED_DRAGON_KEEPER.card_id)
class BattleforgedDragonKeeper(CardScript):
    """Enhance (7): summon a Vastwing Dragon."""
    enhance = (7,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.summon(ctx.state, ctx.controller, VASTWING_DRAGON)


# --- set 10004: Skybound Dragons ------------------------------------------------------------------

@register(MARI.card_id)
class Mari(CardScript):
    """Activates in hand: whenever a 3-base-cost allied follower super-evolves, set this
    card's cost to 0 until the end of the turn. At the end of your turn, give a random
    super-evolved allied follower +1/+1."""
    listen_in_hand = True

    def on_ally_evolve(self, ctx):
        if (ctx.super_ and ctx.other.defn.cost == 3
                and ctx.state.in_hand(ctx.controller, ctx.source.uid) is ctx.source):
            E.set_cost(ctx.source, 0, until_turn=common.end_of_turn(ctx))

    def on_turn_end(self, ctx):
        if not _on_field(ctx.state, ctx.source):     # turn hooks also fire in hand
            return
        supers = [f for f in ctx.me.followers if f.super_evolved]
        for f in E.random_sample(ctx.state, supers, 1):
            E.buff(ctx.state, f, 1, 1)


@register(CRESCENT_TUBE_RIDE.card_id)
class CrescentTubeRide(CardScript):
    """Gain Crest: Crescent Tube Ride."""

    def cast(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, CRESCENT_TUBE_RIDE_CREST)


@register(IZMIR.card_id)
class Izmir(CardScript):
    """Fanfare: if you have 10 max play points, evolve this follower. When this
    follower evolves (any way), deal 3 damage to all enemy followers."""

    def fanfare(self, ctx):
        if _ten_max_pp(ctx):
            _evolve_self(ctx)

    def on_evolved(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 3, ctx.source)


@register(MUGEN.card_id)
class Mugen(CardScript):
    """Fanfare: Super Skybound Art - gain Storm. Super-Evolve: select 2 enemy followers
    and destroy them."""
    skybound = True
    evolve_targets = (TargetSpec(Target.ENEMY_FOLLOWER, 2),)

    def fanfare(self, ctx):
        if E.super_skybound_art(ctx):
            E.give_keywords(ctx.source, Keyword.STORM)

    def on_super_evolve(self, ctx):
        for f in ctx.chosen():
            E.destroy(ctx.state, f)


@register(MAXIMUM_LOVE_BOMB.card_id)
class MaximumLoveBomb(CardScript):
    """Select an enemy follower, deal it 3 damage, and give it "Can't attack followers
    or leaders" until the end of your opponent's turn."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        for f in ctx.chosen():
            E.damage(ctx.state, [f], 3, ctx.source)
            if _on_field(ctx.state, f):
                E.grant(f, CANT_ATTACK, until_turn=common.end_of_opponents_turn(ctx))


@register(MEG.card_id)
class Meg(CardScript):
    """Fanfare: Skybound Art - super-evolve this follower. Whenever a 2-base-cost
    allied follower enters the field, give this follower Ward."""
    skybound = True

    def fanfare(self, ctx):
        if E.skybound_art(ctx):
            _evolve_self(ctx, super_=True)

    def on_ally_enter(self, ctx):
        if ctx.other.defn.cost == 2:
            E.give_keywords(ctx.source, Keyword.WARD)


@register(PRIMAL_BEAST_ABSORPTION.card_id)
class PrimalBeastAbsorption(CardScript):
    """Select an enemy card on the field, banish it, and add a copy of it (a fresh card
    of the same name) to your hand."""
    play_targets = (TargetSpec(Target.ENEMY_CARD),)

    def cast(self, ctx):
        for target in ctx.chosen():
            if E.banish(ctx.state, target):
                E.add_to_hand(ctx.state, ctx.controller, target.defn)


@register(WILNAS.card_id)
class Wilnas(CardScript):
    """Fanfare: select an enemy follower and deal it 8 damage. Intimidate. Evolve:
    replicate the Fanfare."""
    play_targets = common.ENEMY_FOLLOWER
    evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 8, ctx.source)

    def on_evolve(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 8, ctx.source)
