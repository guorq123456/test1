"""Dragoncraft: the Ramp Dragon starter deck and its tokens.

Only gameplay stats are hard-coded here (no card text or art); see sword.py.
Comments give the official Simplified Chinese names.
"""
from svsim.core import effects as E
from svsim.core.carddef import CardDef
from svsim.core.enums import CardType, Craft, Keyword
from svsim.core.script import CardScript, Target, TargetSpec, register
from svsim.core.state import leader_uid

F, S = CardType.FOLLOWER, CardType.SPELL
DR = Craft.DRAGON
HAND = TargetSpec(Target.HAND_CARD)

# --- generated cards ---
DEPTHS_OF_THE_ELD_BLADES = CardDef(90044330, "Depths of the Eld Blades", DR, S, 2,
                                   is_token=True)                                           # 天刀深渊
SPILLING_RED = CardDef(10642310, "Spilling Red", DR, S, 1)       # 赤流 (also a collectible card)

# --- leader area / alternate forms (names are ours) ---
BURNITE_CREST = CardDef(10744112, "Crest: Burnite, Anathema of Ash", DR, CardType.CREST, 0)
LUMIORE_ACCELERATE = CardDef(10844122, "Lumiore & Argente, Shining Wings (Accelerate)",
                            DR, S, 3)

# --- deck cards ---
VORLALAI = CardDef(10644120, "Vorlalai, Eld Blades", DR, F, 2, 0, 2, Keyword.BANE)          # 古旧天刀·波菈莱
DRAGONEWT_PROMOTER = CardDef(10741110, "Dragonewt Promoter", DR, F, 2, 2, 1, Keyword.RUSH)  # 宣扬的龙人
KIMIKA = CardDef(10842120, "Kimika, Cook of Happiness", DR, F, 2, 2, 1)                     # 满面笑容的烹饪·琪米卡
SLOTH_OF_THE_CRESTPETAL = CardDef(10543310, "Sloth of the Crestpetal", DR, S, 2)            # 懒惰的波摇花
DRAGONSIGN = CardDef(10042310, "Dragonsign", DR, S, 3)                                      # 龙之启示
LAZING_FLAME = CardDef(10742310, "Lazing Flame", DR, S, 3)                                  # 焦龙的午睡
ROAR_OF_PROMINENCE = CardDef(10542310, "Roar of Prominence", DR, S, 4)                      # 日珥咆哮
ZOOEY = CardDef(10444120, "Zooey, Ally of the World", DR, F, 5, 5, 5)                       # 世界的伙伴·佐伊
SAGATSUMATSU = CardDef(10644110, "Sagatsumatsu, Fair Beheader", DR, F, 7, 5, 4,
                       Keyword.STORM | Keyword.BANE | Keyword.AURA)                         # 断头的斩姬·相枛津
NORMAGDALA = CardDef(10944120, "Normagdala, Ravening Revenant", DR, F, 7, 5, 6,
                     Keyword.WARD)                                                          # 禁牙的变貌·诺玛格达拉
LUMIORE_AND_ARGENTE = CardDef(10844120, "Lumiore & Argente, Shining Wings", DR, F, 8, 6, 6,
                              accelerate=LUMIORE_ACCELERATE)                                # 金银绚烂·璐米欧儿&雅尔贞特
BURNITE = CardDef(10744110, "Burnite, Anathema of Ash", DR, F, 9, 9, 9)                     # 焦灰的安纳提玛·班德奈特
ERNTZ = CardDef(10544110, "Erntz, Governing Justice", DR, F, 10, 8, 8, Keyword.WARD)        # 约束的《正义》·伊兰翠

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
        for card in ctx.chosen_hand():
            E.discard(ctx.state, card)
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
        for card in ctx.chosen_hand():
            E.discard(ctx.state, card)
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
        for card in ctx.chosen_hand():
            E.discard(ctx.state, card)
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
        for card in ctx.chosen_hand():
            E.discard(ctx.state, card)
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
