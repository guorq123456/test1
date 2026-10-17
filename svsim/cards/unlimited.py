"""Unlimited-format cards (not in Rotation) used by the supported Unlimited decks.

Only the cards a supported deck needs are scripted here; see decks.RHINO_FOREST.
Card stats come from the pool table (data/unlimited.json). Comments give the
official Simplified Chinese names.
"""
from svsim.cards import common
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.enums import Craft
from svsim.core.script import CardScript, Target, TargetSpec, register

# --- Forestcraft ---
FAIRY = card(90011110)                # 妖精 (token)
DEEPWOOD_BOUNTY = card(90011310)      # 森林的奥秘 (token)
FAIRY_CONVOCATION = card(10111310)    # 妖精召集令
BABY_CARBUNCLE = card(10112130)       # 年幼宝石兽
LAMBENT_CAIRN = card(10112210)        # 磷光辉岩
GLADE = card(10113120)                # 薰交的天宫·巴克伍德
BAYLE = card(10113130)                # 煌击战士·贝鲁
KILLER_RHINOCEROACH = card(10113140)  # 屠戮破魔虫
GODWOOD_STAFF = card(10113210)        # 圣树法杖
GARDENS_ALLURE = card(10213310)       # 花园的指引
ERADICATING_ARROW = card(10313310)    # 驱逐的死矢

FOREST_CARDS = [FAIRY_CONVOCATION, BABY_CARBUNCLE, LAMBENT_CAIRN, GLADE, BAYLE,
                KILLER_RHINOCEROACH, GODWOOD_STAFF, GARDENS_ALLURE, ERADICATING_ARROW]
OTHER_ALLIED_CARD = (TargetSpec(Target.ALLIED_CARD, other=True),)


@register(FAIRY_CONVOCATION.card_id)
class FairyConvocation(CardScript):
    """Add 2 Fairies to your hand."""

    def cast(self, ctx):
        for _ in range(2):
            E.add_to_hand(ctx.state, ctx.controller, FAIRY)


@register(BABY_CARBUNCLE.card_id)
class BabyCarbuncle(CardScript):
    """Fanfare: select another allied card on the field and return it to hand.
    Super-Evolve: recover 3 play points."""
    play_targets = OTHER_ALLIED_CARD

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.return_to_hand(ctx.state, target)

    def on_super_evolve(self, ctx):
        E.recover_pp(ctx.state, ctx.controller, 3)


@register(LAMBENT_CAIRN.card_id)
class LambentCairn(CardScript):
    """Fanfare: add a Fairy to your hand; Combo (3): also a Deepwood Bounty.
    Engage: destroy this card and give a selected allied follower +1/+1 (it can
    be engaged with no follower: it is just destroyed, official Q&A)."""
    engage_cost = 0
    engage_targets = common.ALLIED_FOLLOWER

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, FAIRY)
        if ctx.me.combo >= 3:
            E.add_to_hand(ctx.state, ctx.controller, DEEPWOOD_BOUNTY)

    def engage(self, ctx):
        targets = ctx.chosen()
        E.destroy(ctx.state, ctx.source)
        for target in targets:
            E.buff(ctx.state, target, 1, 1)


@register(GLADE.card_id)
class Glade(CardScript):
    """Fanfare: draw 2 cards. Evolve: deal X damage split between all enemy
    followers, X = cards in your hand (oldest first, official Q&A)."""

    def fanfare(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)

    def on_evolve(self, ctx):
        E.split_damage(ctx.state, 1 - ctx.controller, len(ctx.me.hand), ctx.source)


@register(BAYLE.card_id)
class Bayle(CardScript):
    """Activates in hand: whenever an allied follower leaves the field (on either
    player's turn, official Q&A), reduce this card's cost by 1. Fanfare: select an
    enemy follower and deal it 4 damage."""
    listen_in_hand = True
    play_targets = common.ENEMY_FOLLOWER

    def on_ally_leave(self, ctx):
        if any(c is ctx.source for c in ctx.me.hand):
            E.add_cost(ctx.source, -1)

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4, ctx.source)


@register(KILLER_RHINOCEROACH.card_id)
class KillerRhinoceroach(CardScript):
    """Fanfare: give this follower +X/+0, X = your Combo (counting this card).
    Storm."""

    def fanfare(self, ctx):
        E.buff(ctx.state, ctx.source, ctx.me.combo, 0)


@register(GODWOOD_STAFF.card_id)
class GodwoodStaff(CardScript):
    """At the end of your turn, Combo (3): draw a card. Engage: destroy this card,
    then return a selected other allied card on the field to hand (with nothing to
    select it is just destroyed, official Q&A)."""
    engage_cost = 0
    engage_targets = OTHER_ALLIED_CARD

    def on_turn_end(self, ctx):
        if ctx.me.combo >= 3:
            E.draw(ctx.state, ctx.controller)

    def engage(self, ctx):
        targets = ctx.chosen()
        E.destroy(ctx.state, ctx.source)
        for target in targets:
            E.return_to_hand(ctx.state, target)


@register(GARDENS_ALLURE.card_id)
class GardensAllure(CardScript):
    """Fuse: Forestcraft cards. Draw a card; if a card was fused to this one,
    draw 2 instead."""
    fuse_filter = staticmethod(lambda c: c.defn.craft == Craft.FOREST)

    def cast(self, ctx):
        fused = (ctx.source.counters or {}).get("fused")
        E.draw(ctx.state, ctx.controller, 2 if fused else 1)


@register(ERADICATING_ARROW.card_id)
class EradicatingArrow(CardScript):
    """X times, X = your Combo: give a random enemy follower on the field -0/-1
    (picked again each time)."""

    def cast(self, ctx):
        for _ in range(ctx.me.combo):
            for target in E.random_sample(ctx.state, list(ctx.opponent.followers), 1):
                E.buff(ctx.state, target, 0, -1)
