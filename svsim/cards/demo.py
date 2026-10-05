"""A small synthetic card set for tests and engine development.

These are not real cards: they exist to exercise each rule (keywords,
Fanfare, Last Words, countdowns, Enhance, Mode, ...) without depending on
downloaded official data. Ids 1-99 are reserved for them.
"""
from svsim.core import effects as E
from svsim.core.carddef import CardDef
from svsim.core.enums import CardType, Craft, Keyword
from svsim.core.script import CardScript, Target, TargetSpec, register
from svsim.core.state import leader_uid

F, A, CA, S = CardType.FOLLOWER, CardType.AMULET, CardType.COUNTDOWN_AMULET, CardType.SPELL
N = Craft.NEUTRAL

FOOTMAN = CardDef(1, "Footman", N, F, 1, 1, 2)
SHIELDBEARER = CardDef(2, "Shieldbearer", N, F, 2, 1, 3, Keyword.WARD)
RAIDER = CardDef(3, "Raider", N, F, 2, 2, 1, Keyword.STORM)
LANCER = CardDef(4, "Lancer", N, F, 3, 3, 2, Keyword.RUSH)
ASSASSIN = CardDef(5, "Assassin", N, F, 2, 1, 1, Keyword.BANE)
LEECH = CardDef(6, "Leech", N, F, 3, 2, 3, Keyword.DRAIN)
SHADE = CardDef(7, "Shade", N, F, 2, 2, 2, Keyword.AMBUSH)
ARCHER = CardDef(8, "Archer", N, F, 2, 2, 1,
                 text="Fanfare: Select an enemy follower and deal it 1 damage.")
BOMBER = CardDef(9, "Bomber", N, F, 3, 2, 2, text="Last Words: Deal 2 damage to the enemy leader.")
FIREBOLT = CardDef(10, "Firebolt", N, S, 2, text="Select an enemy follower and deal it 3 damage.")
WISP = CardDef(12, "Wisp", N, F, 1, 1, 1, is_token=True)
TOTEM = CardDef(11, "Totem", N, CA, 2, countdown=2, related=(12,),
                text="Countdown (2). Last Words: Summon a Wisp.")
CAPTAIN = CardDef(13, "Captain", N, F, 4, 3, 4,
                  text="Whenever another allied follower enters the field, give it +1/+0.")
GIANT = CardDef(14, "Giant", N, F, 5, 5, 5, text="Evolve: Deal 2 damage to all enemy followers.")
BACKFIRE = CardDef(15, "Backfire", N, S, 1, text="Deal 3 damage to both leaders.")
MAGE = CardDef(16, "Mage", N, F, 3, 2, 2, text="Enhance (6): Gain +3/+3.")
ORACLE = CardDef(17, "Oracle", N, S, 2,
                 text="Select a Mode: 1. Draw a card. 2. Restore 3 defense to your leader.")
ANGEL = CardDef(18, "Angel", N, F, 3, 2, 3, Keyword.BARRIER)

ALL = [FOOTMAN, SHIELDBEARER, RAIDER, LANCER, ASSASSIN, LEECH, SHADE, ARCHER, BOMBER,
       FIREBOLT, TOTEM, WISP, CAPTAIN, GIANT, BACKFIRE, MAGE, ORACLE, ANGEL]
BY_ID = {c.card_id: c for c in ALL}


@register(ARCHER.card_id)
class Archer(CardScript):
    play_target = TargetSpec(Target.ENEMY_FOLLOWER)

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 1, ctx.source)


@register(BOMBER.card_id)
class Bomber(CardScript):
    def last_words(self, ctx):
        E.damage(ctx.state, [leader_uid(1 - ctx.controller)], 2, ctx.source)


@register(FIREBOLT.card_id)
class Firebolt(CardScript):
    play_target = TargetSpec(Target.ENEMY_FOLLOWER)

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 3, ctx.source)


@register(TOTEM.card_id)
class Totem(CardScript):
    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, WISP)


@register(CAPTAIN.card_id)
class Captain(CardScript):
    def on_ally_enter(self, ctx):
        E.buff(ctx.state, ctx.other, 1, 0)


@register(GIANT.card_id)
class Giant(CardScript):
    def on_evolve(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 2, ctx.source)


@register(BACKFIRE.card_id)
class Backfire(CardScript):
    def cast(self, ctx):
        E.damage(ctx.state, E.leaders_turn_order(ctx.state), 3, ctx.source)


@register(MAGE.card_id)
class Mage(CardScript):
    enhance = (6,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.buff(ctx.state, ctx.source, 3, 3)


@register(ORACLE.card_id)
class Oracle(CardScript):
    modes = (2, 1)

    def cast(self, ctx):
        if 0 in ctx.modes:
            E.draw(ctx.state, ctx.controller)
        if 1 in ctx.modes:
            E.heal_leader(ctx.state, ctx.controller, 3)


_DECK_COUNTS = {FOOTMAN: 3, SHIELDBEARER: 3, RAIDER: 3, ARCHER: 3, FIREBOLT: 3, LANCER: 3,
                GIANT: 3, ASSASSIN: 2, LEECH: 2, SHADE: 2, BOMBER: 2, TOTEM: 2, CAPTAIN: 2,
                MAGE: 2, ORACLE: 2, ANGEL: 2, BACKFIRE: 1}


def demo_deck() -> list[CardDef]:
    deck = [card for card, n in _DECK_COUNTS.items() for _ in range(n)]
    assert len(deck) == 40
    return deck
