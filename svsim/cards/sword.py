"""Swordcraft: every Rotation card, its tokens, crests and faith.

The Pirate Sword starter deck comes first, then the rest of the pool set by
set, newest first. Card stats come from the pool table (svsim/cards/pool.py);
this module holds the abilities. Comments give the official Simplified
Chinese names.
"""
from svsim.cards import common
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.enums import Craft, Keyword
from svsim.core.script import CardScript, Target, TargetSpec, register
from svsim.core.state import leader_uid

ENEMY = (TargetSpec(Target.ENEMY_FOLLOWER),)
ALLY = (TargetSpec(Target.ALLIED_FOLLOWER),)

# --- tokens ---
STEELCLAD_KNIGHT = card(90021120)  # 铁甲骑士
DEPTHS_OF_THE_ELD_SWORD = card(90024320)  # 天剑深渊
DREAD_PIRATES_FLAG = card(90021210)  # 令人战栗的海盗旗
GILDED_BLADE = card(90021310)  # 黄金短剑
GILDED_GOBLET = card(90021320)  # 黄金之杯
GILDED_BOOTS = card(90021330)  # 黄金之靴
GILDED_NECKLACE = card(90021340)  # 黄金项链
GLITTERING_GOLD = card(90021350)  # 闪耀的金币

# --- leader area ---
ELD_SWORD_FAITH = card(10624122)  # 古旧天剑·伊德梅塔 (faith)
UNKEI_CREST = card(10524122)  # 纹章：丽金花·云庆

# --- deck cards ---
FLASHSTEP_QUICKBLADER = card(10021110)  # 须臾剑士
ORCHESTRATED_SILENCE = card(10722310)  # 无音的包围
YIDMETRA = card(10624120)  # 古旧天剑·伊德梅塔
OPEN_SEA_SCOUT = card(10921110)  # 海域斥候
WHIRLPOOL_GUNNER = card(10922110)  # 漩涡炮手
SPLENDOR_OF_THE_GOLDBLOOM = card(10523310)  # 荣耀的丽金花
SEVERED_TIES = card(10922310)  # 燃尽之缘
ZETA_AND_BEA = card(10424110)  # 真红与群青·塞达&贝阿朵丽丝
LAGE_DOR = card(10923310)  # 黄金时代
UNKEI = card(10524120)  # 丽金花·云庆
ROUGHWATER_FIRST_MATE = card(10923110)  # 波涛副船长
GOLDEN_KNIGHT = card(10423110)  # 真王之刃·黄金骑士
BARBAROS = card(10924110)  # 逆行的罪人·巴巴洛丝
BELTEZORE = card(10924120)  # 武皇的变貌·贝尔铁佐

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
    the field +1/+1" (counted in counters["buffs"]; grants stack, and the Enhanced
    follower that triggered it is buffed too: both confirmed by a player)."""

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
        if counters.get("value", 0) >= 5:      # below 5 nothing happens (confirmed)
            counters["value"] -= 5
            counters["buffs"] = counters.get("buffs", 0) + 1


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
                E.set_cost(copy, 1)


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
            added = E.add_to_hand(ctx.state, ctx.controller, token)
            if added:
                E.set_cost(added, 0)

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


# =====================================================================================
# The rest of the Rotation pool
# =====================================================================================

OFFICER = "Officer"

# --- tokens ---
KNIGHT = card(90021110)  # 骑士 (vanilla)
NAHTS_HENCHMAN = card(90021130)  # 娜哈特的私兵 (vanilla)
WRETCH = card(90022110)  # 异形 (Rush only)
DESPERADOS_SHOT = card(90024330)  # 亡命者的枪击

# --- crests ---
GILDARIA_CREST = card(10724112)  # 纹章：统音的安纳提玛·吉尔达利娅
MAJESTIC_CONQUEST_CREST = card(10622312)  # 纹章：威风的行军

# --- set 10009 ---
KINDRED_CAVALRYWOMAN = card(10921120)  # 团结骑兵 (keywords only)
PHALANX = card(10921310)  # 方阵
FEROCIOUS_COMMANDER = card(10922120)  # 凶猛指挥官

# --- set 10008 ---
NAHT_AND_VINCE = card(10821110)  # 武力与治安·娜哈特·娜哈特&宾森特
SHAILI = card(10821120)  # 寡言的刺客·夏伊莉
SASHA = card(10821130)  # 悠久的骑士·莎夏
KATZE = card(10822110)  # 越狱者·卡婕
ODA_NOBUNAGA = card(10822120)  # 织田信长
SHARED_EXISTENCE = card(10822310)  # 重历新生
OKITA_SOUJI = card(10823110)  # 冲田总司
SLICE_OF_DOMESTICITY = card(10823310)  # 相伴相随的日常
BUNNY_AND_BARON = card(10824110)  # 天命的子弹·巴妮&巴隆
MARS = card(10824120)  # 焦灼炎将·玛尔斯

# --- set 10007 ---
BOMBASTIC_BOMBARDIER = card(10721110)  # 曲行工兵
HIGH_STRUNG_LIAISON = card(10721120)  # 传调联络兵
MEASURED_ATTUNEMENT = card(10721310)  # 敌我的调律
SHARP_EARED_OPERATIVE = card(10722110)  # 听略谍报兵
METRONOMIC_MEDIC = card(10722120)  # 斩奏医护兵
KNELLCLAW_LIEUTENANT = card(10723110)  # 响爪分队长
CAESURA_AL_FINE = card(10723310)  # 带来静寂的拔刀
GILDARIA = card(10724110)  # 统音的安纳提玛·吉尔达利娅
CESAR = card(10724120)  # 宽严的音帅·塞扎尔

# --- set 10006 ---
FEARLESS_SOLDIER = card(10621110)  # 勇烈的士兵
IDLE_MAID = card(10621120)  # 懒惰女仆
ADVENT_OF_THE_ELD_SWORD = card(10621310)  # 天剑授予
LOYAL_GUARD = card(10622110)  # 忠烈的近卫兵
NAVY_CAT = card(10622120)  # 猫人水手
MAJESTIC_CONQUEST = card(10622310)  # 威风的行军
HEARTLESS_STRATEGIST = card(10623110)  # 暴烈的参谋
RUTHLESS_ELD_SWORD = card(10623310)  # 惨烈的天剑
NOEL_IV = card(10624110)  # 惨烈的剑王·罗德诺艾尔四世

# --- set 10005 ---
ALTRUISTIC_ARISTOCRAT = card(10521110)  # 好施的名人
SMOKE_SHROUDED_BEAUTY = card(10521120)  # 烟管美玉
EXTRAVAGANCE_OF_THE_GOLDBLOOM = card(10521310)  # 丽金花的挥霍
SWIFT_STAFFMASTER = card(10522110)  # 迅猛的武术家
AMPHIBIAN_GOLDMUNCHER = card(10522120)  # 吉祥蛙
SERENITYS_SHIELD = card(10522310)  # 温柔援军
UNMOVING_TACTICIAN = card(10523110)  # 不动如山的将校
OLUON = card(10524110)  # 威猛的《战车》·奥辂昂

# --- set 10000 (Basic) ---
ARMS_PEDDLER = card(10021120)  # 战斗商贩
CENTAUR_CENTURION = card(10021130)  # 人马骑士 (keywords only)
WAY_OF_THE_MAID = card(10021310)  # 女仆的礼仪
ROYAL_COACHWOMAN = card(10022110)  # 王室御用车夫
RUSTY = card(10022120)  # 魔煌的诡谲者·拉斯提
ANCESTRAL_CROWN = card(10022210)  # 昭示正统的王冠

# --- set 10004 ---
RANDALL = card(10421110)  # 信念腿法·兰德尔
ARTHUR = card(10421120)  # 决心之辉龙·亚瑟
MORDRED = card(10421130)  # 迷茫的狮子·莫德雷德
AGLOVALE = card(10422110)  # 冰心霸王·艾格罗瓦尔
FEATHER = card(10422120)  # 如火斗志·菲泽 (vanilla)
FIORITO = card(10422130)  # 绽放的肌肉·菲奥莉托 (keywords only)
KNIGHTLY_ARDOR = card(10423310)  # 骁勇骑士
SEOFON = card(10424120)  # 十天众统领·希耶提

# Cards that need no script: vanilla or keywords only.
NO_SCRIPT = [FLASHSTEP_QUICKBLADER, KINDRED_CAVALRYWOMAN, CENTAUR_CENTURION, FEATHER, FIORITO,
             KNIGHT, STEELCLAD_KNIGHT, NAHTS_HENCHMAN, WRETCH]


# --- helpers -------------------------------------------------------------------------

class CantAttack(CardScript):
    """Granted: "Can't attack followers or leaders"."""
    cant_attack = True


class AttackTwice(CardScript):
    """Granted: "Can attack 2 times per turn"."""
    attacks_per_turn = 2


CANT_ATTACK = CantAttack()
ATTACK_TWICE = AttackTwice()


def _summon(ctx, defn, n: int = 1, keywords: Keyword = Keyword.NONE) -> list:
    """Summon n copies of a card (as many as fit), giving each `keywords`."""
    summoned = []
    for _ in range(n):
        inst = E.summon(ctx.state, ctx.controller, defn)
        if inst is None:
            break
        if keywords:
            E.give_keywords(inst, keywords)
        summoned.append(inst)
    return summoned


def _on_field(ctx, inst) -> bool:
    return ctx.state.on_field(inst.uid) is inst


def _hit_selected(ctx, amount: int) -> None:
    E.damage(ctx.state, ctx.chosen(), amount, ctx.source)


def _hit_random_enemy(ctx, amount: int, times: int = 1) -> None:
    """`times` times: deal `amount` damage to a random enemy follower (Aura included)."""
    for _ in range(times):
        E.damage(ctx.state, E.random_sample(ctx.state, ctx.opponent.followers, 1), amount,
                 ctx.source)


def _hit_all_enemies(ctx, amount: int) -> None:
    E.damage(ctx.state, list(ctx.opponent.followers), amount, ctx.source)


def _buff_others(ctx, atk: int, life: int, keywords: Keyword = Keyword.NONE,
                 only=lambda f: True) -> None:
    """Give all other allied followers on the field +atk/+life (and keywords)."""
    for f in [f for f in ctx.me.followers if f is not ctx.source and only(f)]:
        E.buff(ctx.state, f, atk, life)
        if keywords:
            E.give_keywords(f, keywords)


def _add(ctx, defn, n: int = 1) -> None:
    for _ in range(n):
        E.add_to_hand(ctx.state, ctx.controller, defn)


def is_sword_follower(inst) -> bool:
    return inst.defn.is_follower and inst.defn.craft == Craft.SWORD


def _spells_in_hand(p) -> int:
    return sum(c.defn.is_spell for c in p.hand)


def _return_and_draw_sword_followers(ctx) -> None:
    """Return the selected hand card to the deck, then draw 2 Swordcraft followers."""
    for c in ctx.chosen_hand():
        E.return_to_deck(ctx.state, c)
    for _ in range(2):
        E.draw_matching(ctx.state, ctx.controller, is_sword_follower)


# --- tokens and crests -----------------------------------------------------------------

@register(DESPERADOS_SHOT.card_id)
class DesperadosShot(CardScript):
    """Twice: deal 4 damage to a random enemy follower."""

    def cast(self, ctx):
        _hit_random_enemy(ctx, 4, times=2)


@register(GILDARIA_CREST.card_id)
class GildariaCrest(CardScript):
    """Countdown (1). On your turn, allied followers entering deal 1 damage to the enemy leader."""

    def on_ally_enter(self, ctx):
        if common.during_your_turn(ctx):
            E.damage(ctx.state, [common.enemy_leader(ctx)], 1, ctx.source)


@register(MAJESTIC_CONQUEST_CREST.card_id)
class MajesticConquestCrest(CardScript):
    """Countdown (2). Whenever you play an Enhanced card, summon a Fearless Soldier."""

    def on_play(self, ctx):
        if ctx.enhanced:
            E.summon(ctx.state, ctx.controller, FEARLESS_SOLDIER)


# --- set 10009 ---------------------------------------------------------------------------

@register(PHALANX.card_id)
class Phalanx(CardScript):
    """Summon a Steelclad Knight and give it Ward. Enhance (6): summon 5 instead."""
    enhance = (6,)

    def cast(self, ctx):
        _summon(ctx, STEELCLAD_KNIGHT, 5 if ctx.enhanced else 1, Keyword.WARD)


@register(FEROCIOUS_COMMANDER.card_id)
class FerociousCommander(CardScript):
    """Fanfare: summon 2 Steelclad Knights. Enhance (7): they and this follower get +3/+0 and Rush."""
    enhance = (7,)

    def fanfare(self, ctx):
        knights = _summon(ctx, STEELCLAD_KNIGHT, 2)
        if ctx.enhanced:
            for f in knights + [ctx.source]:
                if _on_field(ctx, f):
                    E.buff(ctx.state, f, 3, 0)
                    E.give_keywords(f, Keyword.RUSH)


# --- set 10008 ---------------------------------------------------------------------------

@register(NAHT_AND_VINCE.card_id)
class NahtAndVince(CardScript):
    """Fanfare: summon a Naht's Henchman, 3 damage to all enemy followers. Super-Evolve: do it again."""

    def fanfare(self, ctx):
        self._crackdown(ctx)

    def on_super_evolve(self, ctx):
        self._crackdown(ctx)

    def _crackdown(self, ctx):
        E.summon(ctx.state, ctx.controller, NAHTS_HENCHMAN)
        _hit_all_enemies(ctx, 3)


@register(SHAILI.card_id)
class Shaili(CardScript):
    """Ambush. Evolve: an enemy follower can't attack until the end of your opponent's turn."""
    evolve_targets = common.ENEMY_FOLLOWER

    def on_evolve(self, ctx):
        for f in ctx.chosen():
            E.grant(f, CANT_ATTACK, common.end_of_opponents_turn(ctx))


@register(SASHA.card_id)
class Sasha(CardScript):
    """Fanfare: summon a Steelclad Knight with Rush. Evolve: summon one with Ward."""

    def fanfare(self, ctx):
        _summon(ctx, STEELCLAD_KNIGHT, 1, Keyword.RUSH)

    def on_evolve(self, ctx):
        _summon(ctx, STEELCLAD_KNIGHT, 1, Keyword.WARD)


@register(KATZE.card_id)
class Katze(CardScript):
    """Once on each of your turns, a spell you play deals 2 to a random enemy. Evolve: add a Gold."""

    def on_play(self, ctx):
        # Confirmed by the player: the once-per-turn use is spent even with no enemy follower.
        if ctx.as_spell and common.during_your_turn(ctx) and E.once_per_turn(ctx, "katze"):
            _hit_random_enemy(ctx, 2)

    def on_evolve(self, ctx):
        _add(ctx, GLITTERING_GOLD)


@register(ODA_NOBUNAGA.card_id)
class OdaNobunaga(CardScript):
    """Fanfare: deal 6 damage to all enemy followers. Intimidate."""

    def fanfare(self, ctx):
        _hit_all_enemies(ctx, 6)


@register(SHARED_EXISTENCE.card_id)
class SharedExistence(CardScript):
    """A random highest-attack enemy follower gets -10/-10. Enhance (6): also summon 3 Wretches."""
    enhance = (6,)

    def cast(self, ctx):
        enemies = ctx.opponent.followers
        if enemies:
            top = max(f.atk for f in enemies)
            for f in E.random_sample(ctx.state, [f for f in enemies if f.atk == top], 1):
                E.buff(ctx.state, f, -10, -10)
        if ctx.enhanced:
            _summon(ctx, WRETCH, 3)


@register(OKITA_SOUJI.card_id)
class OkitaSouji(CardScript):
    """Fanfare: evolve if super-evolution is unlocked. Follower Strike: 3 damage (x3 if evolved)."""

    def fanfare(self, ctx):
        if E.super_evolution_unlocked(ctx.state, ctx.controller) and not ctx.source.evolved:
            E.evolve(ctx.state, ctx.source)

    def follower_strike(self, ctx):
        for _ in range(3 if ctx.source.evolved else 1):
            E.damage(ctx.state, [ctx.other], 3, ctx.source)


@register(SLICE_OF_DOMESTICITY.card_id)
class SliceOfDomesticity(CardScript):
    """Mode: 4 damage to a random enemy follower / heal 2; both if 2+ allied cards on the field."""
    modes = (2, 1)

    def all_modes(self, state, card, enhanced):
        return len(state.players[card.owner].field) >= 2

    def cast(self, ctx):
        if 0 in ctx.modes:
            _hit_random_enemy(ctx, 4)
        if 1 in ctx.modes:
            E.heal_leader(ctx.state, ctx.controller, 2)


@register(BUNNY_AND_BARON.card_id)
class BunnyAndBaron(CardScript):
    """Fanfare: summon a copy; Rally (20): 4 to the enemy leader. Rush. Evolve: add Desperados' Shot."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, BUNNY_AND_BARON)    # counts toward the Rally
        if ctx.me.rally >= 20:
            E.damage(ctx.state, [common.enemy_leader(ctx)], 4, ctx.source)

    def on_evolve(self, ctx):
        _add(ctx, DESPERADOS_SHOT)


@register(MARS.card_id)
class Mars(CardScript):
    """Fanfare: 3 Knights. Entering Officer allies: +2/+0, Rush; this +1/+0. Super-Evolve: a Knight."""

    def fanfare(self, ctx):
        _summon(ctx, KNIGHT, 3)

    def on_ally_enter(self, ctx):
        officer = ctx.other
        if not (officer.defn.is_follower and E.has_trait(officer, OFFICER)):
            return
        if _on_field(ctx, officer):
            E.buff(ctx.state, officer, 2, 0)
            E.give_keywords(officer, Keyword.RUSH)
        E.buff(ctx.state, ctx.source, 1, 0)

    def on_super_evolve(self, ctx):
        E.summon(ctx.state, ctx.controller, KNIGHT)


# --- set 10007 ---------------------------------------------------------------------------

@register(BOMBASTIC_BOMBARDIER.card_id)
class BombasticBombardier(CardScript):
    """In hand: an allied super-evolution sets its cost to 1. Fanfare: 3 damage to an enemy follower."""
    listen_in_hand = True
    play_targets = common.ENEMY_FOLLOWER

    def on_ally_evolve(self, ctx):
        if ctx.super_ and ctx.state.in_hand(ctx.controller, ctx.source.uid) is ctx.source:
            E.set_cost(ctx.source, 1)

    def fanfare(self, ctx):
        _hit_selected(ctx, 3)


@register(HIGH_STRUNG_LIAISON.card_id)
class HighStrungLiaison(CardScript):
    """Fanfare: summon a Knight and add a Steelclad Knight to your hand."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, KNIGHT)
        _add(ctx, STEELCLAD_KNIGHT)


@register(MEASURED_ATTUNEMENT.card_id)
class MeasuredAttunement(CardScript):
    """3 damage to an enemy follower. Rally (10): it can't attack until the opponent's turn ends."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        _hit_selected(ctx, 3)
        if ctx.me.rally >= 10:
            for f in ctx.chosen():
                E.grant(f, CANT_ATTACK, common.end_of_opponents_turn(ctx))


@register(SHARP_EARED_OPERATIVE.card_id)
class SharpEaredOperative(CardScript):
    """Last Words: summon a Knight. Evolve: select an enemy follower and deal it 3 damage."""
    evolve_targets = common.ENEMY_FOLLOWER

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, KNIGHT)

    def on_evolve(self, ctx):
        _hit_selected(ctx, 3)


@register(METRONOMIC_MEDIC.card_id)
class MetronomicMedic(CardScript):
    """Fanfare: draw 2 cards, summon 2 Knights. Evolve: 3 damage to an enemy follower."""
    evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)
        _summon(ctx, KNIGHT, 2)

    def on_evolve(self, ctx):
        _hit_selected(ctx, 3)


@register(KNELLCLAW_LIEUTENANT.card_id)
class KnellclawLieutenant(CardScript):
    """Fanfare: summon 3 Knights, then Mode: other allies +1/+0 and Rush, or +0/+1 and Ward."""
    modes = (2, 1)

    def fanfare(self, ctx):
        _summon(ctx, KNIGHT, 3)
        if 0 in ctx.modes:
            _buff_others(ctx, 1, 0, Keyword.RUSH)
        if 1 in ctx.modes:
            _buff_others(ctx, 0, 1, Keyword.WARD)


@register(CAESURA_AL_FINE.card_id)
class CaesuraAlFine(CardScript):
    """6 damage to an enemy follower. Rally (10): X to all enemy followers, X = allied followers."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        _hit_selected(ctx, 6)
        if ctx.me.rally >= 10:
            _hit_all_enemies(ctx, len(ctx.me.followers))


@register(GILDARIA.card_id)
class Gildaria(CardScript):
    """Fanfare: Rally (20): crest, evolve. Your turn: entering allies get Rush. Evolves: 2 Steelclads."""

    def fanfare(self, ctx):
        if ctx.me.rally >= 20:
            E.add_to_leader_area(ctx.state, ctx.controller, GILDARIA_CREST)
            if not ctx.source.evolved:
                E.evolve(ctx.state, ctx.source)

    def on_ally_enter(self, ctx):
        if common.during_your_turn(ctx) and _on_field(ctx, ctx.other):
            E.give_keywords(ctx.other, Keyword.RUSH)

    def on_evolved(self, ctx):
        _summon(ctx, STEELCLAD_KNIGHT, 2)


@register(CESAR.card_id)
class Cesar(CardScript):
    """Fanfare: 2 Steelclads; other Swordcraft allies +1/+3, Ward. Super-Evolve: destroy an enemy."""
    super_evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        _summon(ctx, STEELCLAD_KNIGHT, 2)
        _buff_others(ctx, 1, 3, Keyword.WARD, only=is_sword_follower)

    def on_super_evolve(self, ctx):
        for f in ctx.chosen():
            E.destroy(ctx.state, f)


# --- set 10006 ---------------------------------------------------------------------------

@register(FEARLESS_SOLDIER.card_id)
class FearlessSoldier(CardScript):
    """Enhance (3): give this follower +1/+1. Rush."""
    enhance = (3,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.buff(ctx.state, ctx.source, 1, 1)


@register(IDLE_MAID.card_id)
class IdleMaid(CardScript):
    """Fanfare: return a card in your hand to the deck, then draw 2 Swordcraft followers."""
    play_targets = common.HAND_CARD

    def fanfare(self, ctx):
        _return_and_draw_sword_followers(ctx)


@register(ADVENT_OF_THE_ELD_SWORD.card_id)
class AdventOfTheEldSword(CardScript):
    """Summon 3 Fearless Soldiers. Enhance (7): give them +2/+2."""
    enhance = (7,)

    def cast(self, ctx):
        for soldier in _summon(ctx, FEARLESS_SOLDIER, 3):
            if ctx.enhanced and _on_field(ctx, soldier):
                E.buff(ctx.state, soldier, 2, 2)


@register(LOYAL_GUARD.card_id)
class LoyalGuard(CardScript):
    """Enhance (4): +2/+2. Ward. Evolve: 3 damage to an enemy follower."""
    enhance = (4,)
    evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.buff(ctx.state, ctx.source, 2, 2)

    def on_evolve(self, ctx):
        _hit_selected(ctx, 3)


@register(NAVY_CAT.card_id)
class NavyCat(CardScript):
    """Fanfare: destroy all enemy followers with 1 defense. Storm."""

    def fanfare(self, ctx):
        for f in [f for f in ctx.opponent.followers if f.life == 1]:
            E.destroy(ctx.state, f)


@register(MAJESTIC_CONQUEST.card_id)
class MajesticConquest(CardScript):
    """Gain Crest: Majestic Conquest. Enhance (3): delay its count by 2."""
    enhance = (3,)

    def cast(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, MAJESTIC_CONQUEST_CREST)
        if ctx.enhanced:
            crest = E.leader_area_card(ctx.state, ctx.controller, MAJESTIC_CONQUEST_CREST)
            if crest is not None:
                E.advance_countdown(ctx.state, crest, -2)


@register(HEARTLESS_STRATEGIST.card_id)
class HeartlessStrategist(CardScript):
    """Fanfare: destroy an enemy follower. Enhance (6): also recover 3 PP, add a Fearless Soldier."""
    play_targets = common.ENEMY_FOLLOWER
    enhance = (6,)

    def fanfare(self, ctx):
        for f in ctx.chosen():
            E.destroy(ctx.state, f)
        if ctx.enhanced:
            E.recover_pp(ctx.state, ctx.controller, 3)
            _add(ctx, FEARLESS_SOLDIER)


@register(RUTHLESS_ELD_SWORD.card_id)
class RuthlessEldSword(CardScript):
    """Mode: draw a card / 3 damage to a random enemy follower. Enhance (3): both."""
    modes = (2, 1)
    enhance = (3,)
    modes_all_when_enhanced = True

    def cast(self, ctx):
        if 0 in ctx.modes:
            E.draw(ctx.state, ctx.controller)
        if 1 in ctx.modes:
            _hit_random_enemy(ctx, 3)


@register(NOEL_IV.card_id)
class NoelIV(CardScript):
    """Fanfare: Bane soldier; Enhance (7): +Drain one; (8): +Storm one. Super-Evolve: others +1/+1."""
    enhance = (7, 8)     # tiers stack: paying 8 meets both (neither says "instead")

    def fanfare(self, ctx):
        _summon(ctx, FEARLESS_SOLDIER, 1, Keyword.BANE)
        if ctx.enhanced >= 7:
            _summon(ctx, FEARLESS_SOLDIER, 1, Keyword.DRAIN)
        if ctx.enhanced >= 8:
            _summon(ctx, FEARLESS_SOLDIER, 1, Keyword.STORM)

    def on_super_evolve(self, ctx):
        _buff_others(ctx, 1, 1)


# --- set 10005 ---------------------------------------------------------------------------

@register(ALTRUISTIC_ARISTOCRAT.card_id)
class AltruisticAristocrat(CardScript):
    """Fanfare: discard a card in your hand; heal your leader 3, or 6 if it was a spell."""
    play_targets = common.HAND_CARD

    def fanfare(self, ctx):
        chosen = ctx.chosen_hand()
        spell = any(c.defn.is_spell for c in chosen)
        for c in chosen:
            E.discard(ctx.state, c)
        E.heal_leader(ctx.state, ctx.controller, 6 if spell else 3)


@register(SMOKE_SHROUDED_BEAUTY.card_id)
class SmokeShroudedBeauty(CardScript):
    """Fanfare: with 2+ spells in hand, +1/+1 and Ward. Evolve: add a Glittering Gold."""

    def fanfare(self, ctx):
        if _spells_in_hand(ctx.me) >= 2:
            E.buff(ctx.state, ctx.source, 1, 1)
            E.give_keywords(ctx.source, Keyword.WARD)

    def on_evolve(self, ctx):
        _add(ctx, GLITTERING_GOLD)


@register(EXTRAVAGANCE_OF_THE_GOLDBLOOM.card_id)
class ExtravaganceOfTheGoldbloom(CardScript):
    """Discard a spell in your hand, then twice: 3 damage to a random enemy follower."""
    play_targets = (TargetSpec(Target.HAND_CARD, filter=lambda state, player, c: c.defn.is_spell),)

    def cast(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        _hit_random_enemy(ctx, 3, times=2)


@register(SWIFT_STAFFMASTER.card_id)
class SwiftStaffmaster(CardScript):
    """When drawn, costs 3 until the end of the turn. Fanfare: draw a card, heal your leader 3. Rush."""

    def on_drawn(self, ctx):
        E.set_cost(ctx.source, 3, until_turn=common.end_of_turn(ctx))

    def fanfare(self, ctx):
        E.draw(ctx.state, ctx.controller)
        E.heal_leader(ctx.state, ctx.controller, 3)


@register(AMPHIBIAN_GOLDMUNCHER.card_id)
class AmphibianGoldmuncher(CardScript):
    """Your turn end: with 2+ spells in hand, 5 damage to all enemy followers. Evolve: add 2 Golds."""
    queue_checks = ("on_turn_end",)

    def queue_condition(self, hook, ctx):
        # Checked as the turn ends: a Gold that Crest: Unkei adds then doesn't count (Q&A).
        return sum(c.defn.is_spell for c in ctx.me.hand) >= 2

    def on_turn_end(self, ctx):
        _hit_all_enemies(ctx, 5)

    def on_evolve(self, ctx):
        _add(ctx, GLITTERING_GOLD, 2)


@register(SERENITYS_SHIELD.card_id)
class SerenitysShield(CardScript):
    """Summon 2 Knights. Enhance (4): summon 4 instead."""
    enhance = (4,)

    def cast(self, ctx):
        _summon(ctx, KNIGHT, 4 if ctx.enhanced else 2)


@register(UNMOVING_TACTICIAN.card_id)
class UnmovingTactician(CardScript):
    """Can't attack. Your turn end: summon a Steelclad Knight. Super-Evolve: other allies +3/+3."""
    cant_attack = True

    def on_turn_end(self, ctx):
        E.summon(ctx.state, ctx.controller, STEELCLAD_KNIGHT)

    def on_super_evolve(self, ctx):
        _buff_others(ctx, 3, 3)


@register(OLUON.card_id)
class Oluon(CardScript):
    """Turn end: unevolved, 7 to all enemy followers; evolved, 3 times 7 to another random target."""

    def on_turn_end(self, ctx):
        if not ctx.source.evolved:
            _hit_all_enemies(ctx, 7)
            return
        for _ in range(3):      # each time picks again among what is left (Q&A)
            if ctx.state.winner is not None:
                break
            others = [f for f in ctx.me.followers + ctx.opponent.followers if f is not ctx.source]
            pool = others + [common.own_leader(ctx), common.enemy_leader(ctx)]
            E.damage(ctx.state, E.random_sample(ctx.state, pool, 1), 7, ctx.source)


# --- set 10000 (Basic) -------------------------------------------------------------------

@register(ARMS_PEDDLER.card_id)
class ArmsPeddler(CardScript):
    """Rush. Last Words: draw a card."""

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller)


@register(WAY_OF_THE_MAID.card_id)
class WayOfTheMaid(CardScript):
    """Select a card in your hand and return it to the deck; draw 2 Swordcraft followers."""
    play_targets = common.HAND_CARD

    def cast(self, ctx):
        _return_and_draw_sword_followers(ctx)


@register(ROYAL_COACHWOMAN.card_id)
class RoyalCoachwoman(CardScript):
    """Last Words: summon a Knight."""

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, KNIGHT)


def _is_rusty(inst) -> bool:
    return inst.defn.card_id == RUSTY.card_id


@register(RUSTY.card_id)
class Rusty(CardScript):
    """Super-Evolve: draw every Rusty, Luxcard Trickster in your deck and give them Storm."""

    def on_super_evolve(self, ctx):
        for _ in range(sum(_is_rusty(c) for c in ctx.me.deck)):
            drawn = E.draw_matching(ctx.state, ctx.controller, _is_rusty)
            if drawn is not None:
                E.give_keywords(drawn, Keyword.STORM)


@register(ANCESTRAL_CROWN.card_id)
class AncestralCrown(CardScript):
    """Countdown (4). Whenever an allied follower enters the field, give it +1/+1."""

    def on_ally_enter(self, ctx):
        if _on_field(ctx, ctx.other):
            E.buff(ctx.state, ctx.other, 1, 1)


# --- set 10004 ---------------------------------------------------------------------------

@register(RANDALL.card_id)
class Randall(CardScript):
    """Enhance (5): give this follower Storm."""
    enhance = (5,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.give_keywords(ctx.source, Keyword.STORM)


@register(ARTHUR.card_id)
class Arthur(CardScript):
    """Ward. Evolve: summon a Mordred, Illusory Lion."""

    def on_evolve(self, ctx):
        E.summon(ctx.state, ctx.controller, MORDRED)


@register(MORDRED.card_id)
class Mordred(CardScript):
    """Storm. Evolve: summon an Arthur, Staunch Dragon."""

    def on_evolve(self, ctx):
        E.summon(ctx.state, ctx.controller, ARTHUR)


@register(AGLOVALE.card_id)
class Aglovale(CardScript):
    """Fanfare: deal 3 damage to all enemy followers. Intimidate."""

    def fanfare(self, ctx):
        _hit_all_enemies(ctx, 3)


@register(KNIGHTLY_ARDOR.card_id)
class KnightlyArdor(CardScript):
    """Mode: leftmost Sword ally attacks twice / Sword allies +1/+1, Barrier / 2 PP, 1 EP / heal 6."""
    modes = (4, 1)

    def cast(self, ctx):
        swords = [f for f in ctx.me.followers if is_sword_follower(f)]   # oldest = leftmost
        if 0 in ctx.modes and swords:
            E.grant(swords[0], ATTACK_TWICE)
        if 1 in ctx.modes:
            for f in swords:
                E.buff(ctx.state, f, 1, 1)
                E.give_keywords(f, Keyword.BARRIER)
        if 2 in ctx.modes:
            E.recover_pp(ctx.state, ctx.controller, 2)
            E.recover_ep(ctx.state, ctx.controller, 1)
        if 3 in ctx.modes:
            E.heal_leader(ctx.state, ctx.controller, 6)


@register(SEOFON.card_id)
class Seofon(CardScript):
    """Fanfare: Skybound Art: evolve all unevolved allies (itself too); Super: super-evolve them."""
    skybound = True

    def fanfare(self, ctx):
        if not E.skybound_art(ctx):
            return
        super_ = E.super_skybound_art(ctx)
        for f in [f for f in ctx.me.followers if not f.evolved]:
            E.evolve(ctx.state, f, super_=super_)


ALL_CARDS = CARDS + [
    KINDRED_CAVALRYWOMAN, PHALANX, FEROCIOUS_COMMANDER,
    NAHT_AND_VINCE, SHAILI, SASHA, KATZE, ODA_NOBUNAGA, SHARED_EXISTENCE, OKITA_SOUJI,
    SLICE_OF_DOMESTICITY, BUNNY_AND_BARON, MARS,
    BOMBASTIC_BOMBARDIER, HIGH_STRUNG_LIAISON, MEASURED_ATTUNEMENT, SHARP_EARED_OPERATIVE,
    METRONOMIC_MEDIC, KNELLCLAW_LIEUTENANT, CAESURA_AL_FINE, GILDARIA, CESAR,
    FEARLESS_SOLDIER, IDLE_MAID, ADVENT_OF_THE_ELD_SWORD, LOYAL_GUARD, NAVY_CAT,
    MAJESTIC_CONQUEST, HEARTLESS_STRATEGIST, RUTHLESS_ELD_SWORD, NOEL_IV,
    ALTRUISTIC_ARISTOCRAT, SMOKE_SHROUDED_BEAUTY, EXTRAVAGANCE_OF_THE_GOLDBLOOM,
    SWIFT_STAFFMASTER, AMPHIBIAN_GOLDMUNCHER, SERENITYS_SHIELD, UNMOVING_TACTICIAN, OLUON,
    ARMS_PEDDLER, CENTAUR_CENTURION, WAY_OF_THE_MAID, ROYAL_COACHWOMAN, RUSTY, ANCESTRAL_CROWN,
    RANDALL, ARTHUR, MORDRED, AGLOVALE, FEATHER, FIORITO, KNIGHTLY_ARDOR, SEOFON,
]
ALL_TOKENS = TOKENS + [KNIGHT, NAHTS_HENCHMAN, WRETCH, DESPERADOS_SHOT]
ALL_LEADER_AREA = LEADER_AREA + [GILDARIA_CREST, MAJESTIC_CONQUEST_CREST]
