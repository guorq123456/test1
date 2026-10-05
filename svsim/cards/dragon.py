"""Dragoncraft: the Ramp Dragon starter deck and its tokens.

Card stats come from the pool table (svsim/cards/pool.py); this module holds
the abilities. Comments give the official Simplified Chinese names.
"""
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.enums import Keyword
from svsim.core.script import CardScript, Target, TargetSpec, register
from svsim.core.state import leader_uid

HAND = TargetSpec(Target.HAND_CARD)

# --- generated cards ---
DEPTHS_OF_THE_ELD_BLADES = card(90044330)  # 天刀深渊
SPILLING_RED = card(10642310)  # 赤流 (also a collectible card)

# --- leader area / alternate forms ---
BURNITE_CREST = card(10744112)
LUMIORE_ACCELERATE = card(10844122)

# --- deck cards ---
VORLALAI = card(10644120)  # 古旧天刀·波菈莱
DRAGONEWT_PROMOTER = card(10741110)  # 宣扬的龙人
KIMIKA = card(10842120)  # 满面笑容的烹饪·琪米卡
SLOTH_OF_THE_CRESTPETAL = card(10543310)  # 懒惰的波摇花
DRAGONSIGN = card(10042310)  # 龙之启示
LAZING_FLAME = card(10742310)  # 焦龙的午睡
ROAR_OF_PROMINENCE = card(10542310)  # 日珥咆哮
ZOOEY = card(10444120)  # 世界的伙伴·佐伊
SAGATSUMATSU = card(10644110)  # 断头的斩姬·相枛津
NORMAGDALA = card(10944120)  # 禁牙的变貌·诺玛格达拉
LUMIORE_AND_ARGENTE = card(10844120)  # 金银绚烂·璐米欧儿&雅尔贞特
BURNITE = card(10744110)  # 焦灰的安纳提玛·班德奈特
ERNTZ = card(10544110)  # 约束的《正义》·伊兰翠

CARDS = [VORLALAI, DRAGONEWT_PROMOTER, KIMIKA, SLOTH_OF_THE_CRESTPETAL, DRAGONSIGN,
         LAZING_FLAME, ROAR_OF_PROMINENCE, ZOOEY, SAGATSUMATSU, NORMAGDALA,
         LUMIORE_AND_ARGENTE, BURNITE, ERNTZ, SPILLING_RED]
TOKENS = [DEPTHS_OF_THE_ELD_BLADES]
LEADER_AREA = [BURNITE_CREST]
ALTERNATE_FORMS = [LUMIORE_ACCELERATE]


def _drain_one(ctx):
    E.damage(ctx.state, [leader_uid(1 - ctx.controller)], 1, ctx.source)
    E.heal_leader(ctx.state, ctx.controller, 1)


# --- generated cards -----------------------------------------------------------------

@register(DEPTHS_OF_THE_ELD_BLADES.card_id)
class DepthsOfTheEldBlades(CardScript):
    """Deal 1 damage to the enemy leader and restore 1 defense to your leader.
    Does the same when discarded."""

    def cast(self, ctx):
        _drain_one(ctx)

    def on_discard(self, ctx):
        _drain_one(ctx)


@register(SPILLING_RED.card_id)
class SpillingRed(CardScript):
    """Select a card in your hand and discard it. Select an enemy follower and
    destroy it. (Needs both targets: official Q&A.)"""
    play_targets = (HAND, TargetSpec(Target.ENEMY_FOLLOWER))

    def cast(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        for target in ctx.chosen():
            E.destroy(ctx.state, target)


# --- leader area / alternate forms ------------------------------------------------------

@register(BURNITE_CREST.card_id)
class BurniteCrest(CardScript):
    """Given to the opponent. At the start of your turn, deal 2 damage to your leader.
    Once on each of your turns, when your leader's defense is restored, deal 1
    damage to it (also when 0 is restored: official Q&A on the set 1 Burnite)."""

    def on_turn_start(self, ctx):
        E.damage(ctx.state, [leader_uid(ctx.controller)], 2, ctx.source)

    def on_leader_healed(self, ctx):
        counters = E.counters(ctx.source)
        if ctx.state.active == ctx.controller and counters.get("turn") != ctx.state.turn:
            counters["turn"] = ctx.state.turn
            E.damage(ctx.state, [leader_uid(ctx.controller)], 1, ctx.source)


@register(LUMIORE_ACCELERATE.card_id)
class LumioreAccelerate(CardScript):
    """Accelerate (3): gain 1 max play point."""

    def cast(self, ctx):
        E.gain_max_pp(ctx.state, ctx.controller)


# --- deck cards ------------------------------------------------------------------------

@register(VORLALAI.card_id)
class Vorlalai(CardScript):
    """When discarded, summon a Vorlalai. Bane. Evolve: add a Depths of the Eld
    Blades to your hand. Super-Evolve: add 3 instead."""

    def on_discard(self, ctx):
        E.summon(ctx.state, ctx.controller, VORLALAI)

    def on_evolve(self, ctx):
        # Super-evolving with points also fires this Evolve ability; "3 instead".
        for _ in range(3 if ctx.source.super_evolved else 1):
            E.add_to_hand(ctx.state, ctx.controller, DEPTHS_OF_THE_ELD_BLADES)


@register(DRAGONEWT_PROMOTER.card_id)
class DragonewtPromoter(CardScript):
    """Enhance (4): summon 2 Dragonewt Promoters. Rush."""
    enhance = (4,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            for _ in range(2):
                E.summon(ctx.state, ctx.controller, DRAGONEWT_PROMOTER)


@register(KIMIKA.card_id)
class Kimika(CardScript):
    """Fanfare: select a card in your hand and discard it; draw a card; restore 1
    defense to your leader. Evolve: replicate the Fanfare."""
    play_targets = (HAND,)
    evolve_targets = (HAND,)

    def fanfare(self, ctx):
        self._cook(ctx)

    def on_evolve(self, ctx):
        self._cook(ctx)

    def _cook(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        E.draw(ctx.state, ctx.controller)
        E.heal_leader(ctx.state, ctx.controller, 1)


@register(SLOTH_OF_THE_CRESTPETAL.card_id)
class SlothOfTheCrestpetal(CardScript):
    """Twice: deal 2 damage to a random enemy follower. If you're in Overflow,
    deal 2 damage to the enemy leader."""

    def cast(self, ctx):
        for _ in range(2):
            E.damage(ctx.state, E.random_sample(ctx.state, ctx.opponent.followers, 1), 2,
                     ctx.source)
        if E.overflow(ctx.state, ctx.controller):
            E.damage(ctx.state, [leader_uid(1 - ctx.controller)], 2, ctx.source)


@register(DRAGONSIGN.card_id)
class Dragonsign(CardScript):
    """Gain 1 max play point. Then, if you have 10 max play points, draw a card."""

    def cast(self, ctx):
        E.gain_max_pp(ctx.state, ctx.controller)
        if ctx.me.max_pp >= 10:
            E.draw(ctx.state, ctx.controller)


@register(LAZING_FLAME.card_id)
class LazingFlame(CardScript):
    """Restore 3 defense to your leader. If you're in Overflow, draw a card."""

    def cast(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 3)
        if E.overflow(ctx.state, ctx.controller):
            E.draw(ctx.state, ctx.controller)


@register(ROAR_OF_PROMINENCE.card_id)
class RoarOfProminence(CardScript):
    """Deal X damage to all followers, X = the number of followers on the field."""

    def cast(self, ctx):
        everyone = ctx.me.followers + ctx.opponent.followers
        E.damage(ctx.state, everyone, len(everyone), ctx.source)


@register(ZOOEY.card_id)
class Zooey(CardScript):
    """Fanfare: gain 1 max play point. Enhance (10): give this follower Storm, set
    your leader's max defense to 1, and give your leader "Can't take more than 0
    damage at a time" until the end of your opponent's turn."""
    enhance = (10,)

    def fanfare(self, ctx):
        E.gain_max_pp(ctx.state, ctx.controller)
        if ctx.enhanced:
            ctx.source.keywords |= Keyword.STORM
            E.set_leader_max_hp(ctx.state, ctx.controller, 1)
            E.give_leader_damage_cap(ctx.state, ctx.controller, 0, until_turn=ctx.state.turn + 1)


@register(SAGATSUMATSU.card_id)
class Sagatsumatsu(CardScript):
    """Fanfare: select a card in your hand and discard it; add 2 Spilling Red to
    your hand. Storm, Bane, Aura."""
    play_targets = (HAND,)

    def fanfare(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        for _ in range(2):
            E.add_to_hand(ctx.state, ctx.controller, SPILLING_RED)


@register(NORMAGDALA.card_id)
class Normagdala(CardScript):
    """Fanfare: Mode: 1. Draw a card and restore 3 defense to your leader. 2. Give
    all enemy followers -0/-4. Ward. Evolve: replicate the Fanfare (choose again)."""
    modes = (2, 1)
    evolve_modes = (2, 1)

    def fanfare(self, ctx):
        self._decree(ctx)

    def on_evolve(self, ctx):
        self._decree(ctx)

    def _decree(self, ctx):
        if 0 in ctx.modes:
            E.draw(ctx.state, ctx.controller)
            E.heal_leader(ctx.state, ctx.controller, 3)
        if 1 in ctx.modes:
            for f in list(ctx.opponent.followers):
                E.buff(ctx.state, f, 0, -4)


@register(LUMIORE_AND_ARGENTE.card_id)
class LumioreAndArgente(CardScript):
    """Fanfare: select 2 cards in your hand and discard them; deal 4 damage to all
    enemies. Super-Evolve: draw 3 cards. Accelerate (3): see LumioreAccelerate."""
    play_targets = (TargetSpec(Target.HAND_CARD, 2),)

    def fanfare(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        E.damage(ctx.state, list(ctx.opponent.followers) + [leader_uid(1 - ctx.controller)], 4,
                 ctx.source)

    def on_super_evolve(self, ctx):
        E.draw(ctx.state, ctx.controller, 3)


@register(BURNITE.card_id)
class Burnite(CardScript):
    """Fanfare: deal 9 damage to all enemy followers. Super-Evolve: give your
    opponent Crest: Burnite, Anathema of Ash."""

    def fanfare(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 9, ctx.source)

    def on_super_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, 1 - ctx.controller, BURNITE_CREST)


@register(ERNTZ.card_id)
class Erntz(CardScript):
    """Ward. At the end of your turn: if unevolved, deal 8 damage to 2 random enemy
    followers and restore 8 defense to your leader; if evolved, deal 8 damage to the
    enemy leader. Evolve: remove Ward, gain Intimidate."""

    def on_turn_end(self, ctx):
        if ctx.source.evolved:
            E.damage(ctx.state, [leader_uid(1 - ctx.controller)], 8, ctx.source)
        else:
            E.damage(ctx.state, E.random_sample(ctx.state, ctx.opponent.followers, 2), 8,
                     ctx.source)
            E.heal_leader(ctx.state, ctx.controller, 8)

    def on_evolve(self, ctx):
        ctx.source.keywords = (ctx.source.keywords & ~Keyword.WARD) | Keyword.INTIMIDATE
