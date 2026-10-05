"""Neutral cards used by the starter decks. Comments give official Chinese names."""
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.script import CardScript, register
from svsim.core.state import leader_uid

LYRIA = card(10403120)  # 掌握天空命运的少女·露莉亚
FATE_OF_THE_WORLD = card(10503310)  # 《世界》的呈现

CARDS = [LYRIA, FATE_OF_THE_WORLD]


@register(LYRIA.card_id)
class Lyria(CardScript):
    """Enhance (8): draw a follower that costs 7 or more, then recover 7 play points. Barrier."""
    enhance = (8,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.draw_matching(ctx.state, ctx.controller,
                            lambda c: c.defn.is_follower and c.cost >= 7)
            E.recover_pp(ctx.state, ctx.controller, 7)


@register(FATE_OF_THE_WORLD.card_id)
class FateOfTheWorld(CardScript):
    """Draw 2 cards. Destroy a random enemy follower with the highest attack.
    Enhance (10): also deal 4 damage to all enemies."""
    enhance = (10,)

    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)
        enemies = ctx.opponent.followers
        if enemies:
            top = max(f.atk for f in enemies)
            for target in E.random_sample(ctx.state, [f for f in enemies if f.atk == top], 1):
                E.destroy(ctx.state, target)
        if ctx.enhanced:
            E.damage(ctx.state, list(ctx.opponent.followers) + [leader_uid(1 - ctx.controller)],
                     4, ctx.source)
