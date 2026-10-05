"""Swordcraft: the Pirate Sword starter deck and its tokens.

Only gameplay stats are hard-coded here (no card text or art), so tests run
without downloaded data; tests/test_card_data.py checks them against the
official database when it has been fetched. Comments give the official
Simplified Chinese names.
"""
from svsim.core import effects as E
from svsim.core.carddef import CardDef
from svsim.core.enums import CardType, Craft, Keyword
from svsim.core.script import CardScript, Target, TargetSpec, register
from svsim.core.state import leader_uid

F, CA, S = CardType.FOLLOWER, CardType.COUNTDOWN_AMULET, CardType.SPELL
SW = Craft.SWORD
ENEMY = (TargetSpec(Target.ENEMY_FOLLOWER),)
ALLY = (TargetSpec(Target.ALLIED_FOLLOWER),)

# --- tokens ---
STEELCLAD_KNIGHT = CardDef(90021120, "Steelclad Knight", SW, F, 1, 2, 2, is_token=True)       # 铁甲骑士
DEPTHS_OF_THE_ELD_SWORD = CardDef(90024320, "Depths of the Eld Sword", SW, S, 0, is_token=True)  # 天剑深渊
DREAD_PIRATES_FLAG = CardDef(90021210, "Dread Pirate's Flag", SW, CA, 1, countdown=7,
                             is_token=True)                                                 # 令人战栗的海盗旗
GILDED_BLADE = CardDef(90021310, "Gilded Blade", SW, S, 1, is_token=True)                   # 黄金短剑
GILDED_GOBLET = CardDef(90021320, "Gilded Goblet", SW, S, 1, is_token=True)                 # 黄金之杯
GILDED_BOOTS = CardDef(90021330, "Gilded Boots", SW, S, 1, is_token=True)                   # 黄金之靴
GILDED_NECKLACE = CardDef(90021340, "Gilded Necklace", SW, S, 1, is_token=True)             # 黄金项链
GLITTERING_GOLD = CardDef(90021350, "Glittering Gold", SW, S, 0, is_token=True)             # 闪耀的金币

# --- leader area (names are ours: the official data gives these no name) ---
ELD_SWORD_FAITH = CardDef(10624122, "Faith of Yidmetra, Eld Sword", SW, CardType.FAITH, 0)
UNKEI_CREST = CardDef(10524122, "Crest: Unkei, Goldbloom", SW, CardType.CREST, 0, countdown=4)

# --- deck cards ---
FLASHSTEP_QUICKBLADER = CardDef(10021110, "Flashstep Quickblader", SW, F, 1, 1, 1,
                                Keyword.STORM)                                              # 须臾剑士
ORCHESTRATED_SILENCE = CardDef(10722310, "Orchestrated Silence", SW, S, 1)                  # 无音的包围
YIDMETRA = CardDef(10624120, "Yidmetra, Eld Sword", SW, F, 2, 1, 2,
                   faith=ELD_SWORD_FAITH)                                                   # 古旧天剑·伊德梅塔
OPEN_SEA_SCOUT = CardDef(10921110, "Open-Sea Scout", SW, F, 2, 2, 2)                        # 海域斥候
WHIRLPOOL_GUNNER = CardDef(10922110, "Whirlpool Gunner", SW, F, 3, 4, 2, Keyword.RUSH)      # 漩涡炮手
SPLENDOR_OF_THE_GOLDBLOOM = CardDef(10523310, "Splendor of the Goldbloom", SW, S, 3)        # 荣耀的丽金花
SEVERED_TIES = CardDef(10922310, "Severed Ties", SW, S, 3)                                  # 燃尽之缘
ZETA_AND_BEA = CardDef(10424110, "Zeta & Bea, Crimson and Blue", SW, F, 4, 3, 2,
                       Keyword.RUSH)                                                        # 真红与群青·塞达&贝阿朵丽丝
LAGE_DOR = CardDef(10923310, "L'Age d'Or", SW, S, 4)                                       # 黄金时代
UNKEI = CardDef(10524120, "Unkei, Goldbloom", SW, F, 5, 2, 4)                               # 丽金花·云庆
ROUGHWATER_FIRST_MATE = CardDef(10923110, "Roughwater First Mate", SW, F, 5, 3, 3)          # 波涛副船长
GOLDEN_KNIGHT = CardDef(10423110, "Golden Knight, True King's Blade", SW, F, 6, 6, 6)       # 真王之刃·黄金骑士
BARBAROS = CardDef(10924110, "Barbaros, Rebellious Convict", SW, F, 7, 4, 3,
                   Keyword.STORM)                                                           # 逆行的罪人·巴巴洛丝
BELTEZORE = CardDef(10924120, "Beltezore, Valorous Revenant", SW, F, 10, 2, 12,
                    Keyword.STORM | Keyword.BANE | Keyword.WARD | Keyword.AURA)            # 武皇的变貌·贝尔铁佐

CARDS = [FLASHSTEP_QUICKBLADER, ORCHESTRATED_SILENCE, YIDMETRA, OPEN_SEA_SCOUT,
         WHIRLPOOL_GUNNER, SPLENDOR_OF_THE_GOLDBLOOM, SEVERED_TIES, ZETA_AND_BEA, LAGE_DOR,
         UNKEI, ROUGHWATER_FIRST_MATE, GOLDEN_KNIGHT, BARBAROS, BELTEZORE]
TOKENS = [STEELCLAD_KNIGHT, DEPTHS_OF_THE_ELD_SWORD, DREAD_PIRATES_FLAG, GILDED_BLADE,
          GILDED_GOBLET, GILDED_BOOTS, GILDED_NECKLACE, GLITTERING_GOLD]
LEADER_AREA = [ELD_SWORD_FAITH, UNKEI_CREST]


def flags(player_state) -> list:
    return [c for c in player_state.field if c.defn.card_id == DREAD_PIRATES_FLAG.card_id]


# --- tokens ----------------------------------------------------------------------

@register(DEPTHS_OF_THE_ELD_SWORD.card_id)
class DepthsOfTheEldSword(CardScript):
    """Select an enemy follower and deal it 1 damage. Enhance (1): 3 instead."""
    play_targets = ENEMY
    enhance = (1,)

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 3 if ctx.enhanced else 1, ctx.source)


@register(DREAD_PIRATES_FLAG.card_id)
class DreadPiratesFlag(CardScript):
    """Countdown (7). Whenever you play a spell, advance the count by 1.
    Last Words: deal 2 damage to the enemy leader."""

    def on_play(self, ctx):
        if ctx.as_spell:
            E.advance_countdown(ctx.state, ctx.source, 1)

    def last_words(self, ctx):
        E.damage(ctx.state, [leader_uid(1 - ctx.controller)], 2, ctx.source)


@register(GILDED_BLADE.card_id)
class GildedBlade(CardScript):
    """Select an enemy follower or the enemy leader and deal it 1 damage."""
    play_targets = (TargetSpec(Target.ENEMY_FOLLOWER_OR_LEADER),)

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 1, ctx.source)


@register(GILDED_GOBLET.card_id)
class GildedGoblet(CardScript):
    """Restore 2 defense to your leader."""

    def cast(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 2)


@register(GILDED_BOOTS.card_id)
class GildedBoots(CardScript):
    """Select an allied follower and give it +1/+0 and Rush."""
    play_targets = ALLY

    def cast(self, ctx):
        for f in ctx.chosen():
            E.buff(ctx.state, f, 1, 0)
            f.keywords |= Keyword.RUSH


@register(GILDED_NECKLACE.card_id)
class GildedNecklace(CardScript):
    """Select an allied follower and give it +0/+1 and Ward."""
    play_targets = ALLY

    def cast(self, ctx):
        for f in ctx.chosen():
            E.buff(ctx.state, f, 0, 1)
            f.keywords |= Keyword.WARD


@register(GLITTERING_GOLD.card_id)
class GlitteringGold(CardScript):
    """Mode: 1. Draw a card. 2. Deal 2 damage to a random enemy follower."""
    modes = (2, 1)

    def cast(self, ctx):
        if 0 in ctx.modes:
            E.draw(ctx.state, ctx.controller)
        if 1 in ctx.modes:
            E.damage(ctx.state, E.random_sample(ctx.state, ctx.opponent.followers, 1), 2,
                     ctx.source)


# --- leader area -------------------------------------------------------------------

@register(ELD_SWORD_FAITH.card_id)
class EldSwordFaith(CardScript):
    """Value starts at 0; +1 whenever you play an Enhanced card. Yidmetra's Evolve
    can give it "Whenever you play an Enhanced card, give all allied followers on
    the field +1/+1" (counted in counters["buffs"])."""

    def on_play(self, ctx):
        if not ctx.enhanced:
            return
        counters = E.counters(ctx.source)
        counters["value"] = counters.get("value", 0) + 1
        for _ in range(counters.get("buffs", 0)):
            for f in list(ctx.me.followers):
                E.buff(ctx.state, f, 1, 1)


@register(UNKEI_CREST.card_id)
class UnkeiCrest(CardScript):
    """Countdown (4). At the end of your turn, add a Glittering Gold to your hand."""

    def on_turn_end(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, GLITTERING_GOLD)


# --- deck cards --------------------------------------------------------------------

@register(ORCHESTRATED_SILENCE.card_id)
class OrchestratedSilence(CardScript):
    """Add a Steelclad Knight to your hand and give it Rush. Rally (10): add 2 instead."""

    def cast(self, ctx):
        for _ in range(2 if ctx.me.rally >= 10 else 1):
            knight = E.add_to_hand(ctx.state, ctx.controller, STEELCLAD_KNIGHT)
            if knight:
                knight.keywords |= Keyword.RUSH


@register(YIDMETRA.card_id)
class Yidmetra(CardScript):
    """Fanfare: add a Depths of the Eld Sword to your hand. Evolve: reduce your
    faith's value by 5 to give it the +1/+1 ability."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, DEPTHS_OF_THE_ELD_SWORD)

    def on_evolve(self, ctx):
        faith = E.leader_area_card(ctx.state, ctx.controller, ELD_SWORD_FAITH)
        if faith is None:
            return
        counters = E.counters(faith)
        if counters.get("value", 0) >= 5:      # ASSUMPTION: nothing happens below 5
            counters["value"] -= 5
            counters["buffs"] = counters.get("buffs", 0) + 1   # ASSUMPTION: grants stack


@register(OPEN_SEA_SCOUT.card_id)
class OpenSeaScout(CardScript):
    """Fanfare: summon a Dread Pirate's Flag. Evolve: add a Gilded Boots to your hand."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, DREAD_PIRATES_FLAG)

    def on_evolve(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, GILDED_BOOTS)


@register(WHIRLPOOL_GUNNER.card_id)
class WhirlpoolGunner(CardScript):
    """Fanfare: summon a Dread Pirate's Flag and add a Gilded Goblet to your hand. Rush."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, DREAD_PIRATES_FLAG)
        E.add_to_hand(ctx.state, ctx.controller, GILDED_GOBLET)


@register(SPLENDOR_OF_THE_GOLDBLOOM.card_id)
class SplendorOfTheGoldbloom(CardScript):
    """Add 2 Glittering Gold to your hand. Enhance (5): add 4 instead."""
    enhance = (5,)

    def cast(self, ctx):
        for _ in range(4 if ctx.enhanced else 2):
            E.add_to_hand(ctx.state, ctx.controller, GLITTERING_GOLD)


@register(SEVERED_TIES.card_id)
class SeveredTies(CardScript):
    """Select an enemy follower and deal it 5 damage. If this card's cost is 3,
    add a Severed Ties to your hand and set its cost to 1."""
    play_targets = ENEMY

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 5, ctx.source)
        if ctx.source.cost == 3:
            copy = E.add_to_hand(ctx.state, ctx.controller, SEVERED_TIES)
            if copy:
                copy.cost = 1


@register(ZETA_AND_BEA.card_id)
class ZetaAndBea(CardScript):
    """Fanfare: summon a Zeta & Bea. Enhance (6): give it Bane and this follower Storm. Rush."""
    enhance = (6,)

    def fanfare(self, ctx):
        twin = E.summon(ctx.state, ctx.controller, ZETA_AND_BEA)
        if ctx.enhanced:
            if twin:
                twin.keywords |= Keyword.BANE
            ctx.source.keywords |= Keyword.STORM


@register(LAGE_DOR.card_id)
class LAgeDOr(CardScript):
    """Summon a Dread Pirate's Flag and deal 2 damage to all enemy followers.
    Enhance (6): summon 2 and deal 4 instead."""
    enhance = (6,)

    def cast(self, ctx):
        for _ in range(2 if ctx.enhanced else 1):
            E.summon(ctx.state, ctx.controller, DREAD_PIRATES_FLAG)
        E.damage(ctx.state, list(ctx.opponent.followers), 4 if ctx.enhanced else 2, ctx.source)


@register(UNKEI.card_id)
class Unkei(CardScript):
    """Fanfare: select an enemy follower and banish it; add a Glittering Gold to your
    hand. Super-Evolve: gain Crest: Unkei, Goldbloom."""
    play_targets = ENEMY

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.banish(ctx.state, target)
        E.add_to_hand(ctx.state, ctx.controller, GLITTERING_GOLD)

    def on_super_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, UNKEI_CREST)


@register(ROUGHWATER_FIRST_MATE.card_id)
class RoughwaterFirstMate(CardScript):
    """Fanfare: select an enemy follower and deal it 3 damage; summon a Dread
    Pirate's Flag. Evolve: replicate the Fanfare. Super-Evolve: add a Gilded Blade
    and a Gilded Necklace to your hand and set their costs to 0."""
    play_targets = ENEMY
    evolve_targets = ENEMY

    def fanfare(self, ctx):
        self._raid(ctx)

    def on_evolve(self, ctx):
        self._raid(ctx)

    def on_super_evolve(self, ctx):
        for token in (GILDED_BLADE, GILDED_NECKLACE):
            card = E.add_to_hand(ctx.state, ctx.controller, token)
            if card:
                card.cost = 0

    def _raid(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 3, ctx.source)
        E.summon(ctx.state, ctx.controller, DREAD_PIRATES_FLAG)


@register(GOLDEN_KNIGHT.card_id)
class GoldenKnight(CardScript):
    """Fanfare: Mode: 1. Super-evolve this follower. 2. Deal 4 damage to all enemy
    followers. 3. Restore 4 defense to your leader. Enhance (8): all of them."""
    modes = (3, 1)
    enhance = (8,)
    modes_all_when_enhanced = True

    def fanfare(self, ctx):
        if 0 in ctx.modes and not ctx.source.evolved:
            E.evolve(ctx.state, ctx.source, super_=True)
        if 1 in ctx.modes:
            E.damage(ctx.state, list(ctx.opponent.followers), 4, ctx.source)
        if 2 in ctx.modes:
            E.heal_leader(ctx.state, ctx.controller, 4)


@register(BARBAROS.card_id)
class Barbaros(CardScript):
    """Fanfare: summon a Dread Pirate's Flag, then advance the counts of all allied
    Dread Pirate's Flags by 5. Storm."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, DREAD_PIRATES_FLAG)
        for flag in flags(ctx.me):
            E.advance_countdown(ctx.state, flag, 5)


@register(BELTEZORE.card_id)
class Beltezore(CardScript):
    """Storm, Bane, Ward, Aura. Can attack 3 times per turn."""
    attacks_per_turn = 3
