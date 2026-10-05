"""Forestcraft cards and the cards they generate.

Card stats come from the pool table (svsim/cards/pool.py); this module holds
the abilities. Comments give the official Simplified Chinese names.

Combo counts the card being played (official Q&A on May, Journey Elf). Target
filters that depend on Combo are checked when the action is listed, before the
played card is counted, hence the `+ 1` in `_combo_on_play`.
"""
from svsim.cards import common
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.enums import Keyword
from svsim.core.script import CardScript, Target, TargetSpec, register
from svsim.core.state import FIELD_LIMIT

PIXIE = "Pixie"

# --- tokens ---
FAIRY = card(90011110)  # 妖精
SPRINGBLOOM_FAIRY = card(90011120)  # 新绿的妖精
DEEPWOOD_BOUNTY = card(90011310)  # 森林的奥秘
EVE = card(90014110)  # 冰晶剑士·伊芙
DEPTHS_OF_THE_ELD_LANCE = card(90014330)  # 天枪深渊

# --- leader area ---
STARRY_SKY_CREST = card(10412312)  # 纹章：绮罗星
YUEL_CREST = card(10414122)  # 纹章：调和的舞者·尤艾尔&苏丝雅
SATHANID_FAITH = card(10614122)  # 信仰：古旧天枪·萨莎妮德
MINIMIZED_ANXIETY_CREST = card(10712312)  # 纹章：忧虑缩小
MAGNIFIED_MALICE_CREST = card(10713312)  # 纹章：恶意扩大
THESTAE_CREST = card(10714112)  # 纹章：操量的安纳提玛·达斯特迪兹
GREAT_HART_CREST = card(10714122)  # 纹章：冰界鹿王

# --- set 10009 ---
SPROUTING_INITIATE = card(10911110)  # 发芽组员
JUNGLE_YOUTH = card(10911120)  # 金刚伙伴 (Intimidate only: no script)
TRAP_IN_THE_WOODS = card(10911210)  # 森林陷阱
LEAFSHADOW_ASSASSIN = card(10912110)  # 根延潜伏者
PRIMATE_PLOTTERS = card(10912120)  # 温泉度假猴
VERDANT_RING_KINDRED = card(10912310)  # 绿伞会两大招牌
VIRID_LIEUTENANT = card(10913110)  # 枝叶大姐大
CRIMSON_INCENSE = card(10913310)  # 绯岸橙醉
MAGACHIYO = card(10914110)  # 烟管的罪人·曲千代
HIEN = card(10914120)  # 香风的变貌·飞燕

# --- set 10008 ---
MARLONE = card(10811110)  # 昔日的天秤·马龙
CITRUS = card(10811120)  # 异端隐士·西特拉斯
MOELLE = card(10811130)  # 忧郁少女·莫埃尔
RUFLET = card(10812110)  # 太古的妖精·露芙蕾
LYCORIS = card(10812120)  # 情念的毒荆·莉柯瑞丝
PEACEFUL_SOLITUDE = card(10812310)  # 宁静的孤独
MICHELLE = card(10813110)  # 温柔读心者·米榭儿
CURIOSITY_ABOUNDS = card(10813310)  # 水镜的信赖
SETUS_AND_MAISHA = card(10814110)  # 离合有终·赛德斯&梅希亚
TIA = card(10814120)  # 永恒冰晶·蒂亚

# --- set 10007 ---
MACROBEAR = card(10711110)  # 巨型熊
ELVEN_TRAPPER = card(10711120)  # 精灵陷阱师
COGNITIVE_SHIFT = card(10711310)  # 人格切换
VIREWIND_FENCER = card(10712110)  # 绿风细剑师
HAWKEYED_TACTICIAN = card(10712120)  # 弓兵指挥者
MINIMIZED_ANXIETY = card(10712310)  # 忧虑缩小
FROSTBOW_SNIPER = card(10713110)  # 冰箭射手
MAGNIFIED_MALICE = card(10713310)  # 恶意扩大
THESTAE = card(10714110)  # 操量的安纳提玛·达斯特迪兹
GREAT_HART = card(10714120)  # 冰界鹿王

# --- set 10006 ---
MOTHERLY_FORESTDWELLER = card(10611110)  # 慈育的森民
MONKEY_OF_PARADISE = card(10611120)  # 伊甸之猴
ADVENT_OF_THE_ELD_LANCE = card(10611310)  # 天枪授予
KINDLY_EXECUTOR = card(10612110)  # 慈颜的拥趸
HOWLING_WOLFMAN = card(10612120)  # 咆哮狼人 (Storm only: no script)
FLORAL_OFFERING = card(10612310)  # 向女王献花
MERCIFUL_ATTENDANT = card(10613110)  # 慈惠的心腹
NURTURING_ELD_LANCE = card(10613310)  # 慈爱的天枪
ALTHENIA = card(10614110)  # 慈爱的凛华·奥尔提雅
SATHANID = card(10614120)  # 古旧天枪·萨莎妮德

# --- set 10005 ---
PRUDENT_TANUKI = card(10511110)  # 熟虑的狸猫
BATTLEDORE_WOODSMAIDEN = card(10511120)  # 森林羽子板工匠
FLIGHT_OF_THE_SWARMPETAL = card(10511310)  # 虫风花的飞翔
FLOWERING_FRIENDSHIP = card(10512110)  # 新晋搭档
FAIRY_BEASTWHISPERER = card(10512120)  # 和气蔼蔼的妖精 (keywords only: no script)
QUIET_ENCOURAGEMENT = card(10512310)  # 寂静的助力
SPIRITED_SKIPPER = card(10513110)  # 引路船工
GRACE_OF_THE_SWARMPETAL = card(10513310)  # 优雅的虫风花
WOLFRAUD = card(10514110)  # 脚踩天穹的《倒吊人》·罗弗拉德
MIROKU = card(10514120)  # 虫风花·魅禄

# --- set 10004 ---
KOU_AND_YOU = card(10411110)  # 爱恨舞者·晧&曜
MANAMEL = card(10411120)  # 可爱如琬似花·玛娜玛尔
COMET_DRIVE = card(10411310)  # 彗星
CHLOE = card(10412110)  # 美妆少女·克洛伊
ANTHURIA = card(10412120)  # 绯焰舞姬·安苏莉娅
STARRY_SKY = card(10412310)  # 绮罗星
CUPITAN = card(10413110)  # 幻彩弓手·丘比丹
ALFHEIMR = card(10413310)  # 亚尔夫海姆
EWIYAR = card(10414110)  # 风之法则·艾云尼亚
YUEL_AND_SOCIETTE = card(10414120)  # 调和的舞者·尤艾尔&苏丝雅

# --- set 10000 (Basic) ---
FAIRY_TAMER = card(10011110)  # 妖精驯服者
STRAY_BEASTMAN = card(10011120)  # 流浪兽人
GENTLE_TREANT = card(10011130)  # 温厚的树精
WILD_PROFUSION = card(10011210)  # 缭乱之庭
MAY = card(10012110)  # 冒险精灵·小梅
SELWYN = card(10012120)  # 音速射手·塞尔文
BUG_ALERT = card(10012310)  # 昆虫的忠告

CARDS = [SPROUTING_INITIATE, JUNGLE_YOUTH, TRAP_IN_THE_WOODS, LEAFSHADOW_ASSASSIN, PRIMATE_PLOTTERS,
         VERDANT_RING_KINDRED, VIRID_LIEUTENANT, CRIMSON_INCENSE, MAGACHIYO, HIEN,
         MARLONE, CITRUS, MOELLE, RUFLET, LYCORIS, PEACEFUL_SOLITUDE, MICHELLE, CURIOSITY_ABOUNDS,
         SETUS_AND_MAISHA, TIA,
         MACROBEAR, ELVEN_TRAPPER, COGNITIVE_SHIFT, VIREWIND_FENCER, HAWKEYED_TACTICIAN,
         MINIMIZED_ANXIETY, FROSTBOW_SNIPER, MAGNIFIED_MALICE, THESTAE, GREAT_HART,
         MOTHERLY_FORESTDWELLER, MONKEY_OF_PARADISE, ADVENT_OF_THE_ELD_LANCE, KINDLY_EXECUTOR,
         HOWLING_WOLFMAN, FLORAL_OFFERING, MERCIFUL_ATTENDANT, NURTURING_ELD_LANCE, ALTHENIA, SATHANID,
         PRUDENT_TANUKI, BATTLEDORE_WOODSMAIDEN, FLIGHT_OF_THE_SWARMPETAL, FLOWERING_FRIENDSHIP,
         FAIRY_BEASTWHISPERER, QUIET_ENCOURAGEMENT, SPIRITED_SKIPPER, GRACE_OF_THE_SWARMPETAL,
         WOLFRAUD, MIROKU,
         KOU_AND_YOU, MANAMEL, COMET_DRIVE, CHLOE, ANTHURIA, STARRY_SKY, CUPITAN, ALFHEIMR, EWIYAR,
         YUEL_AND_SOCIETTE,
         FAIRY_TAMER, STRAY_BEASTMAN, GENTLE_TREANT, WILD_PROFUSION, MAY, SELWYN, BUG_ALERT]
TOKENS = [FAIRY, SPRINGBLOOM_FAIRY, DEEPWOOD_BOUNTY, EVE, DEPTHS_OF_THE_ELD_LANCE]
LEADER_AREA = [STARRY_SKY_CREST, YUEL_CREST, SATHANID_FAITH, MINIMIZED_ANXIETY_CREST,
               MAGNIFIED_MALICE_CREST, THESTAE_CREST, GREAT_HART_CREST]
# Cards whose text is only keywords: they play correctly without a script.
NO_SCRIPT_NEEDED = [JUNGLE_YOUTH, HOWLING_WOLFMAN, FAIRY_BEASTWHISPERER, FAIRY, EVE]


# --- helpers -------------------------------------------------------------------------

def _combo(ctx, n: int) -> bool:
    """Combo (n): at least n cards played this turn, counting the one being played."""
    return ctx.me.combo >= n


def _combo_on_play(n: int, met: bool = True):
    """Target filter: whether Combo (n) will (met=True) or won't be reached once the
    card being listed is played."""
    return lambda state, player, c: (state.players[player].combo + 1 >= n) == met


def _super_evolve_possible(state, player, c) -> bool:
    """Target filter for Super-Evolve-only selections: skip them when super-evolving
    isn't possible (they still show up on plain evolutions, unused)."""
    return state.players[player].sep > 0 and E.super_evolution_unlocked(state, player)


def _add(ctx, defn, n: int = 1) -> list:
    added = [E.add_to_hand(ctx.state, ctx.controller, defn) for _ in range(n)]
    return [c for c in added if c is not None]


def _summon(ctx, defn, n: int = 1) -> list:
    summoned = [E.summon(ctx.state, ctx.controller, defn) for _ in range(n)]
    return [c for c in summoned if c is not None]


def _evolve(ctx, inst) -> None:
    """Evolve a follower by an effect (no Evolve abilities, no points)."""
    if inst is not None and not inst.evolved and ctx.state.on_field(inst.uid) is inst:
        E.evolve(ctx.state, inst)


def _in_hand(ctx) -> bool:
    return any(c is ctx.source for c in ctx.me.hand)


def _random_enemy_follower(ctx) -> list:
    return E.random_sample(ctx.state, ctx.opponent.followers, 1)


def _gain_crest(ctx, crest) -> None:
    E.add_to_leader_area(ctx.state, ctx.controller, crest)


def _buff_all_allies(ctx, atk: int, life: int, exclude=None) -> None:
    for f in list(ctx.me.followers):
        if f is not exclude:
            E.buff(ctx.state, f, atk, life)


def _give_all_allies(ctx, keywords: Keyword) -> None:
    for f in list(ctx.me.followers):
        E.give_keywords(f, keywords)


def _is_pixie(inst) -> bool:
    return inst.defn.is_follower and E.has_trait(inst, PIXIE)


# --- tokens ------------------------------------------------------------------------------

@register(SPRINGBLOOM_FAIRY.card_id)
class SpringbloomFairy(CardScript):
    """Ward. At the end of your turn, evolve this follower."""

    def on_turn_end(self, ctx):
        _evolve(ctx, ctx.source)


@register(DEEPWOOD_BOUNTY.card_id)
class DeepwoodBounty(CardScript):
    """Restore 1 defense to your leader."""

    def cast(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 1)


@register(DEPTHS_OF_THE_ELD_LANCE.card_id)
class DepthsOfTheEldLance(CardScript):
    """Select an unevolved allied follower on the field and evolve it."""
    play_targets = (TargetSpec(Target.ALLIED_FOLLOWER, filter=lambda s, p, c: not c.evolved),)

    def cast(self, ctx):
        for f in ctx.chosen():
            _evolve(ctx, f)


# --- leader area ---------------------------------------------------------------------------

@register(STARRY_SKY_CREST.card_id)
class StarrySkyCrest(CardScript):
    """Countdown (1). Last Words: deal 1 damage to the enemy leader; add a Starry Sky to your hand."""

    def last_words(self, ctx):
        E.damage(ctx.state, [common.enemy_leader(ctx)], 1, ctx.source)
        _add(ctx, STARRY_SKY)


@register(YUEL_CREST.card_id)
class YuelCrest(CardScript):
    """Countdown (4). Once on each of your turns, when you play a follower, evolve it."""

    def on_play(self, ctx):
        played = ctx.other
        if ctx.as_spell or not played.defn.is_follower or not common.during_your_turn(ctx):
            return
        if E.once_per_turn(ctx, "yuel"):
            _evolve(ctx, played)


class EldLanceBlessing(CardScript):
    """Granted to Sathanid's faith: whenever an allied follower evolves, 1 damage to the enemy leader."""

    def on_ally_evolve(self, ctx):
        E.damage(ctx.state, [common.enemy_leader(ctx)], 1, ctx.source)


ELD_LANCE_BLESSING = EldLanceBlessing()


@register(SATHANID_FAITH.card_id)
class SathanidFaith(CardScript):
    """Value starts at 0; whenever an allied follower evolves, increase it by 1."""

    def on_ally_evolve(self, ctx):
        E.change_faith(ctx.state, ctx.controller, SATHANID_FAITH, 1)


@register(MINIMIZED_ANXIETY_CREST.card_id)
class MinimizedAnxietyCrest(CardScript):
    """Countdown (1). Last Words: add a Magnified Malice to your hand."""

    def last_words(self, ctx):
        _add(ctx, MAGNIFIED_MALICE)


@register(MAGNIFIED_MALICE_CREST.card_id)
class MagnifiedMaliceCrest(CardScript):
    """Countdown (1). Last Words: add a Minimized Anxiety to your hand."""

    def last_words(self, ctx):
        _add(ctx, MINIMIZED_ANXIETY)


@register(THESTAE_CREST.card_id)
class ThestaeCrest(CardScript):
    """Countdown (3). At the end of your turn, Combo (3): give all followers in your deck +1/+1."""

    def on_turn_end(self, ctx):
        if _combo(ctx, 3):
            for c in list(ctx.me.deck):
                if c.defn.is_follower:
                    E.buff(ctx.state, c, 1, 1)


@register(GREAT_HART_CREST.card_id)
class GreatHartCrest(CardScript):
    """Countdown (3). At the end of your turn, Combo (3): add a Deepwood Bounty to your hand."""

    def on_turn_end(self, ctx):
        if _combo(ctx, 3):
            _add(ctx, DEEPWOOD_BOUNTY)


# --- set 10009 -------------------------------------------------------------------------------

@register(SPROUTING_INITIATE.card_id)
class SproutingInitiate(CardScript):
    """Fanfare: Combo (3) - draw a card. Rush."""

    def fanfare(self, ctx):
        if _combo(ctx, 3):
            E.draw(ctx.state, ctx.controller)


@register(TRAP_IN_THE_WOODS.card_id)
class TrapInTheWoods(CardScript):
    """Whenever an enemy follower enters the field, destroy it and this card."""

    # Several followers entering at once: each queues a trigger, but the first one
    # destroys the trap, so the rest fizzle (official Q&A: only the first is destroyed).
    def on_enemy_enter(self, ctx):
        if ctx.state.on_field(ctx.other.uid) is ctx.other:
            E.destroy(ctx.state, ctx.other)
        # UNSURE: is the trap still destroyed when the follower already left the field
        # (or survives, e.g. "can't be destroyed by abilities")? Assumed yes.
        E.destroy(ctx.state, ctx.source)


@register(LEAFSHADOW_ASSASSIN.card_id)
class LeafshadowAssassin(CardScript):
    """Fanfare: add a Fairy to your hand. Combo (3) - give it Bane."""

    def fanfare(self, ctx):
        for fairy in _add(ctx, FAIRY):
            if _combo(ctx, 3):
                E.give_keywords(fairy, Keyword.BANE)


@register(PRIMATE_PLOTTERS.card_id)
class PrimatePlotters(CardScript):
    """Fanfare: add an exact copy of a random card in the opponent's hand to your hand. Evolve: again."""

    def fanfare(self, ctx):
        self._steal(ctx)

    def on_evolve(self, ctx):
        self._steal(ctx)

    def _steal(self, ctx):
        for c in E.random_sample(ctx.state, ctx.opponent.hand, 1):
            E.add_copy_to_hand(ctx.state, ctx.controller, c)


@register(VERDANT_RING_KINDRED.card_id)
class VerdantRingKindred(CardScript):
    """Mode: 1. 4 damage to a random enemy follower; 2. add a Deepwood Bounty and a Fairy. Combo (3): both."""
    modes = (2, 1)

    def all_modes(self, state, card, enhanced):
        return state.players[card.owner].combo + 1 >= 3

    def cast(self, ctx):
        modes = (0, 1) if _combo(ctx, 3) else ctx.modes
        if 0 in modes:
            E.damage(ctx.state, _random_enemy_follower(ctx), 4, ctx.source)
        if 1 in modes:
            _add(ctx, DEEPWOOD_BOUNTY)
            _add(ctx, FAIRY)


@register(VIRID_LIEUTENANT.card_id)
class ViridLieutenant(CardScript):
    """Fanfare: Combo (3) - draw 2 cards. Evolve: give another allied follower +1/+1 and Rush."""
    evolve_targets = common.OTHER_ALLIED_FOLLOWER

    def fanfare(self, ctx):
        if _combo(ctx, 3):
            E.draw(ctx.state, ctx.controller, 2)

    def on_evolve(self, ctx):
        for f in ctx.chosen():
            E.buff(ctx.state, f, 1, 1)
            E.give_keywords(f, Keyword.RUSH)


@register(CRIMSON_INCENSE.card_id)
class CrimsonIncense(CardScript):
    """In hand: at the end of your turn, Combo (3) - cost -1. Destroy an enemy follower; draw a card."""
    listen_in_hand = True
    play_targets = common.ENEMY_FOLLOWER

    def on_turn_end(self, ctx):
        if _combo(ctx, 3):
            E.add_cost(ctx.source, -1)

    def cast(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        E.draw(ctx.state, ctx.controller)


@register(MAGACHIYO.card_id)
class Magachiyo(CardScript):
    """Fanfare: 4 damage to an enemy follower (Combo (3): to all enemy followers). Super-Evolve: Storm."""
    # With Combo (3) the selection is irrelevant, so none is offered.
    play_targets = (TargetSpec(Target.ENEMY_FOLLOWER, filter=_combo_on_play(3, met=False)),)

    def fanfare(self, ctx):
        if _combo(ctx, 3):
            E.damage(ctx.state, list(ctx.opponent.followers), 4, ctx.source)
        else:
            E.damage(ctx.state, ctx.chosen(), 4, ctx.source)

    def on_super_evolve(self, ctx):
        E.give_keywords(ctx.source, Keyword.STORM)


@register(HIEN.card_id)
class Hien(CardScript):
    """In hand: cost -1 this turn per card you play. Fanfare: 4 damage to an enemy. Last Words: summon one."""
    listen_in_hand = True
    play_targets = common.ENEMY_FOLLOWER

    def on_play(self, ctx):
        if _in_hand(ctx):
            E.add_cost(ctx.source, -1, until_turn=common.end_of_turn(ctx))

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4, ctx.source)

    def last_words(self, ctx):
        _summon(ctx, HIEN)


# --- set 10008 -------------------------------------------------------------------------------

@register(MARLONE.card_id)
class Marlone(CardScript):
    """Fanfare: destroy X random enemy followers, X = enemy followers minus allied followers."""

    def fanfare(self, ctx):
        # Marlone itself counts (official Q&A: 5 enemy Fairies, no other allies -> X = 4).
        x = len(ctx.opponent.followers) - len(ctx.me.followers)
        if x > 0:
            for target in E.random_sample(ctx.state, ctx.opponent.followers, x):
                E.destroy(ctx.state, target)


@register(CITRUS.card_id)
class Citrus(CardScript):
    """Fanfare: summon 2 Fairies. Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        _summon(ctx, FAIRY, 2)

    def on_evolve(self, ctx):
        _summon(ctx, FAIRY, 2)


@register(MOELLE.card_id)
class Moelle(CardScript):
    """Fanfare: return a card in your hand to your deck; draw a card. Ward."""
    play_targets = common.HAND_CARD

    def fanfare(self, ctx):
        for c in ctx.chosen_hand():
            E.return_to_deck(ctx.state, c)
        E.draw(ctx.state, ctx.controller)


@register(RUFLET.card_id)
class Ruflet(CardScript):
    """Once per own turn, when buffed on the field, summon a Fairy. Last Words: add a Fairy to your hand."""

    # UNSURE: does the +2/+2 (+3/+3) from evolving count as being "given + attack or
    # defense"? The engine treats evolution bonuses as buffs, so it does here.
    def on_buffed(self, ctx):
        if common.during_your_turn(ctx) and E.once_per_turn(ctx, "ruflet"):
            _summon(ctx, FAIRY)

    def last_words(self, ctx):
        _add(ctx, FAIRY)


@register(LYCORIS.card_id)
class Lycoris(CardScript):
    """Fanfare: summon a Michelle, Kind Mindreader. Rush, Bane."""

    def fanfare(self, ctx):
        _summon(ctx, MICHELLE)


@register(PEACEFUL_SOLITUDE.card_id)
class PeacefulSolitude(CardScript):
    """Destroy an enemy follower. Restore 2 defense to your leader."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        E.heal_leader(ctx.state, ctx.controller, 2)


@register(MICHELLE.card_id)
class Michelle(CardScript):
    """Fanfare: summon a Lycoris, Barbs of Passion; give all allied followers Barrier. Ward."""

    def fanfare(self, ctx):
        _summon(ctx, LYCORIS)
        _give_all_allies(ctx, Keyword.BARRIER)


@register(CURIOSITY_ABOUNDS.card_id)
class CuriosityAbounds(CardScript):
    """Summon 2 differently named followers costing 2 or less from your deck; all allied followers +1/+1."""

    def cast(self, ctx):
        E.summon_from_deck(ctx.state, ctx.controller, lambda c: c.defn.is_follower and c.cost <= 2,
                           k=2, distinct_names=True)
        _buff_all_allies(ctx, 1, 1)


@register(SETUS_AND_MAISHA.card_id)
class SetusAndMaisha(CardScript):
    """Fanfare: destroy an enemy follower; give all other allied followers +1/+1. Storm, Ward."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        _buff_all_allies(ctx, 1, 1, exclude=ctx.source)


@register(TIA.card_id)
class Tia(CardScript):
    """Enhance (4): allied followers +1/+1. Rush. Once per own turn, when buffed on the field, add an Eve."""
    enhance = (4,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            _buff_all_allies(ctx, 1, 1)

    # UNSURE: as for Ruflet, evolving counts as being given + attack / defense here.
    def on_buffed(self, ctx):
        if common.during_your_turn(ctx) and E.once_per_turn(ctx, "tia"):
            _add(ctx, EVE)


# --- set 10007 -------------------------------------------------------------------------------

@register(MACROBEAR.card_id)
class Macrobear(CardScript):
    """Fanfare: summon an exact copy of this card. Rush, Ward. Can't take more than 3 damage at a time."""
    damage_cap = 3

    def fanfare(self, ctx):
        E.summon_copy(ctx.state, ctx.controller, ctx.source)


@register(ELVEN_TRAPPER.card_id)
class ElvenTrapper(CardScript):
    """Fanfare: return a card in your hand to your deck; add 2 Fairies to your hand."""
    play_targets = common.HAND_CARD

    def fanfare(self, ctx):
        for c in ctx.chosen_hand():
            E.return_to_deck(ctx.state, c)
        _add(ctx, FAIRY, 2)


@register(COGNITIVE_SHIFT.card_id)
class CognitiveShift(CardScript):
    """Return 2 cards in your hand to your deck. Draw 2 cards."""
    play_targets = (TargetSpec(Target.HAND_CARD, 2),)

    def cast(self, ctx):
        for c in ctx.chosen_hand():
            E.return_to_deck(ctx.state, c)
        E.draw(ctx.state, ctx.controller, 2)


@register(VIREWIND_FENCER.card_id)
class VirewindFencer(CardScript):
    """Fanfare: Combo (3) - give this follower Storm."""

    def fanfare(self, ctx):
        if _combo(ctx, 3):
            E.give_keywords(ctx.source, Keyword.STORM)


@register(HAWKEYED_TACTICIAN.card_id)
class HawkeyedTactician(CardScript):
    """Fanfare: 4 damage to an enemy follower; Combo +1. Evolve: replicate the Fanfare."""
    play_targets = common.ENEMY_FOLLOWER
    evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        self._volley(ctx)

    def on_evolve(self, ctx):
        self._volley(ctx)

    def _volley(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4, ctx.source)
        ctx.me.combo += 1


@register(MINIMIZED_ANXIETY.card_id)
class MinimizedAnxiety(CardScript):
    """Restore 1 defense to your leader. Combo (3) - gain Crest: Minimized Anxiety."""

    def cast(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 1)
        if _combo(ctx, 3):
            _gain_crest(ctx, MINIMIZED_ANXIETY_CREST)


@register(FROSTBOW_SNIPER.card_id)
class FrostbowSniper(CardScript):
    """Fanfare: deal this follower's attack to an enemy follower. Turn end: Combo (3) - draw a card."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), ctx.source.atk, ctx.source)

    def on_turn_end(self, ctx):
        if _combo(ctx, 3):
            E.draw(ctx.state, ctx.controller)


@register(MAGNIFIED_MALICE.card_id)
class MagnifiedMalice(CardScript):
    """Deal 2 damage to a random enemy follower. Combo (3) - gain Crest: Magnified Malice."""

    def cast(self, ctx):
        E.damage(ctx.state, _random_enemy_follower(ctx), 2, ctx.source)
        if _combo(ctx, 3):
            _gain_crest(ctx, MAGNIFIED_MALICE_CREST)


@register(THESTAE.card_id)
class Thestae(CardScript):
    """Fanfare: an enemy follower gets -0/-X (X = this attack); Combo +1. Evolve: gain Crest: Thestae."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.buff(ctx.state, target, 0, -ctx.source.atk)
        ctx.me.combo += 1

    def on_evolve(self, ctx):
        _gain_crest(ctx, THESTAE_CREST)


@register(GREAT_HART.card_id)
class GreatHart(CardScript):
    """Fanfare: add 2 Deepwood Bounty. Turn end: split X (its attack) damage. Super-Evolve: gain its crest."""

    def fanfare(self, ctx):
        _add(ctx, DEEPWOOD_BOUNTY, 2)

    def on_turn_end(self, ctx):
        E.split_damage(ctx.state, 1 - ctx.controller, ctx.source.atk, ctx.source)

    def on_super_evolve(self, ctx):
        _gain_crest(ctx, GREAT_HART_CREST)


# --- set 10006 -------------------------------------------------------------------------------

@register(MOTHERLY_FORESTDWELLER.card_id)
class MotherlyForestdweller(CardScript):
    """Fanfare: add a Springbloom Fairy to your hand. Evolve: summon a Springbloom Fairy."""

    def fanfare(self, ctx):
        _add(ctx, SPRINGBLOOM_FAIRY)

    def on_evolve(self, ctx):
        _summon(ctx, SPRINGBLOOM_FAIRY)


@register(MONKEY_OF_PARADISE.card_id)
class MonkeyOfParadise(CardScript):
    """Fanfare: Combo (3) - evolve this follower."""

    def fanfare(self, ctx):
        if _combo(ctx, 3):
            _evolve(ctx, ctx.source)


@register(ADVENT_OF_THE_ELD_LANCE.card_id)
class AdventOfTheEldLance(CardScript):
    """Deal 4 damage to all enemy followers. Summon 2 Springbloom Fairies."""

    def cast(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 4, ctx.source)
        _summon(ctx, SPRINGBLOOM_FAIRY, 2)


@register(KINDLY_EXECUTOR.card_id)
class KindlyExecutor(CardScript):
    """Fanfare: add a Springbloom Fairy to your hand."""

    def fanfare(self, ctx):
        _add(ctx, SPRINGBLOOM_FAIRY)


@register(FLORAL_OFFERING.card_id)
class FloralOffering(CardScript):
    """In hand: whenever an allied follower evolves, cost -1. Draw 2 cards."""
    listen_in_hand = True

    def on_ally_evolve(self, ctx):
        if _in_hand(ctx):
            E.add_cost(ctx.source, -1)

    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)


@register(MERCIFUL_ATTENDANT.card_id)
class MercifulAttendant(CardScript):
    """Fanfare: summon a Springbloom Fairy. Whenever an allied follower evolves, restore 1 to your leader."""

    def fanfare(self, ctx):
        _summon(ctx, SPRINGBLOOM_FAIRY)

    def on_ally_evolve(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 1)

    # UNSURE: "an allied follower" is read as including this follower itself.
    def on_evolved(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 1)


@register(NURTURING_ELD_LANCE.card_id)
class NurturingEldLance(CardScript):
    """Mode: 1. destroy a random enemy follower with the highest attack; 2. summon a Springbloom Fairy."""
    modes = (2, 1)

    def cast(self, ctx):
        if 0 in ctx.modes:
            enemies = ctx.opponent.followers
            if enemies:
                top = max(f.atk for f in enemies)
                for target in E.random_sample(ctx.state, [f for f in enemies if f.atk == top], 1):
                    E.destroy(ctx.state, target)
        if 1 in ctx.modes:
            _summon(ctx, SPRINGBLOOM_FAIRY)


@register(ALTHENIA.card_id)
class Althenia(CardScript):
    """Fanfare: summon 3 Springbloom Fairies. Attacks twice a turn. Super-Evolve: destroy an enemy."""
    attacks_per_turn = 2
    evolve_targets = (TargetSpec(Target.ENEMY_FOLLOWER, filter=_super_evolve_possible),)

    def fanfare(self, ctx):
        _summon(ctx, SPRINGBLOOM_FAIRY, 3)

    def on_super_evolve(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)


@register(SATHANID.card_id)
class Sathanid(CardScript):
    """Fanfare: spend 10 faith to add a Depths of the Eld Lance and give the faith an evolve ping. Drain."""

    def fanfare(self, ctx):
        if E.spend_faith(ctx.state, ctx.controller, SATHANID_FAITH, 10):
            _add(ctx, DEPTHS_OF_THE_ELD_LANCE)
            faith = E.leader_area_card(ctx.state, ctx.controller, SATHANID_FAITH)
            E.grant(faith, ELD_LANCE_BLESSING)


# --- set 10005 -------------------------------------------------------------------------------

@register(PRUDENT_TANUKI.card_id)
class PrudentTanuki(CardScript):
    """Ambush. Evolve: draw a card."""

    def on_evolve(self, ctx):
        E.draw(ctx.state, ctx.controller)


@register(BATTLEDORE_WOODSMAIDEN.card_id)
class BattledoreWoodsmaiden(CardScript):
    """Fanfare and Evolve: summon a Fairy. Whenever an allied Pixie enters, 1 damage to the enemy leader."""

    def fanfare(self, ctx):
        _summon(ctx, FAIRY)

    def on_evolve(self, ctx):
        _summon(ctx, FAIRY)

    def on_ally_enter(self, ctx):
        if _is_pixie(ctx.other):
            E.damage(ctx.state, [common.enemy_leader(ctx)], 1, ctx.source)


@register(FLIGHT_OF_THE_SWARMPETAL.card_id)
class FlightOfTheSwarmpetal(CardScript):
    """Deal 3 damage split between all enemy followers. Add a Fairy to your hand."""

    def cast(self, ctx):
        E.split_damage(ctx.state, 1 - ctx.controller, 3, ctx.source)
        _add(ctx, FAIRY)


@register(FLOWERING_FRIENDSHIP.card_id)
class FloweringFriendship(CardScript):
    """Fanfare: Combo (5) - summon a Flowering Friendship and evolve it and this follower."""

    def fanfare(self, ctx):
        if _combo(ctx, 5):
            for friend in _summon(ctx, FLOWERING_FRIENDSHIP):
                _evolve(ctx, friend)
            _evolve(ctx, ctx.source)


@register(QUIET_ENCOURAGEMENT.card_id)
class QuietEncouragement(CardScript):
    """Deal 1 damage to all enemies. Combo (3) - 2 instead."""

    def cast(self, ctx):
        targets = list(ctx.opponent.followers) + [common.enemy_leader(ctx)]
        E.damage(ctx.state, targets, 2 if _combo(ctx, 3) else 1, ctx.source)


@register(SPIRITED_SKIPPER.card_id)
class SpiritedSkipper(CardScript):
    """Fanfare: summon 3 Fairies. Evolve: replicate the Fanfare. Super-Evolve: allied Pixies gain Bane."""

    def fanfare(self, ctx):
        _summon(ctx, FAIRY, 3)

    def on_evolve(self, ctx):
        _summon(ctx, FAIRY, 3)

    def on_super_evolve(self, ctx):
        for f in list(ctx.me.followers):
            if _is_pixie(f):
                E.give_keywords(f, Keyword.BANE)


@register(GRACE_OF_THE_SWARMPETAL.card_id)
class GraceOfTheSwarmpetal(CardScript):
    """Draw X cards, X = your Combo."""

    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller, ctx.me.combo)


@register(WOLFRAUD.card_id)
class Wolfraud(CardScript):
    """Fanfare: +X/+X (X = Combo). Evolve: discard your hand; copy 5 random enemy deck cards to your hand."""

    def fanfare(self, ctx):
        E.buff(ctx.state, ctx.source, ctx.me.combo, ctx.me.combo)

    def on_evolve(self, ctx):
        for c in list(ctx.me.hand):
            E.discard(ctx.state, c)
        for c in E.random_sample(ctx.state, ctx.opponent.deck, 5):
            E.add_copy_to_hand(ctx.state, ctx.controller, c)


@register(MIROKU.card_id)
class Miroku(CardScript):
    """Fanfare and Evolve: Mode - add 2 Fairies / recover 2 PP / 3 damage split between enemy followers."""
    modes = (3, 1)
    evolve_modes = (3, 1)

    def fanfare(self, ctx):
        self._choice(ctx)

    def on_evolve(self, ctx):
        self._choice(ctx)

    def _choice(self, ctx):
        if 0 in ctx.modes:
            _add(ctx, FAIRY, 2)
        if 1 in ctx.modes:
            E.recover_pp(ctx.state, ctx.controller, 2)
        if 2 in ctx.modes:
            E.split_damage(ctx.state, 1 - ctx.controller, 3, ctx.source)


# --- set 10004 -------------------------------------------------------------------------------

@register(KOU_AND_YOU.card_id)
class KouAndYou(CardScript):
    """Can attack 2 times per turn. Strike: restore 3 defense to all allies."""
    attacks_per_turn = 2

    def strike(self, ctx):
        for f in list(ctx.me.followers):
            E.heal(f, 3)
        E.heal_leader(ctx.state, ctx.controller, 3)


@register(MANAMEL.card_id)
class Manamel(CardScript):
    """At the end of your turn, evolve this follower. When it evolves, 1 damage to all enemy followers."""

    def on_turn_end(self, ctx):
        _evolve(ctx, ctx.source)

    def on_evolved(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 1, ctx.source)


@register(COMET_DRIVE.card_id)
class CometDrive(CardScript):
    """Deal 4 damage to an enemy follower. If an allied follower is evolved, draw a card."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4, ctx.source)
        if any(f.evolved for f in ctx.me.followers):
            E.draw(ctx.state, ctx.controller)


@register(CHLOE.card_id)
class Chloe(CardScript):
    """Enhance (8): summon a follower from your hand, then return this card to your hand."""
    enhance = (8,)
    # The selection only matters when Enhanced, which is forced whenever 8 PP are available.
    play_targets = (TargetSpec(Target.HAND_CARD,
                               filter=lambda s, p, c: c.defn.is_follower and s.players[p].pp >= 8),)

    def fanfare(self, ctx):
        if not ctx.enhanced:
            return
        p = ctx.me
        for c in ctx.chosen_hand():
            # Official Q&A: with a full field the follower stays in hand; Chloe still returns.
            if c.defn.is_follower and len(p.field) < FIELD_LIMIT:
                p.hand.remove(c)
                E.enter_field(ctx.state, c)
        if ctx.state.on_field(ctx.source.uid) is ctx.source:
            E.return_to_hand(ctx.state, ctx.source)


@register(ANTHURIA.card_id)
class Anthuria(CardScript):
    """Fanfare: give all allied followers Barrier."""

    def fanfare(self, ctx):
        _give_all_allies(ctx, Keyword.BARRIER)


@register(STARRY_SKY.card_id)
class StarrySky(CardScript):
    """Deal 2 damage to a random enemy follower. Combo (5) - gain Crest: Starry Sky."""

    def cast(self, ctx):
        E.damage(ctx.state, _random_enemy_follower(ctx), 2, ctx.source)
        if _combo(ctx, 5):
            _gain_crest(ctx, STARRY_SKY_CREST)


@register(CUPITAN.card_id)
class Cupitan(CardScript):
    """Fanfare: Skybound Art - evolve; Super Skybound Art - 3 to the enemy leader. Evolves: 7 random pings."""
    skybound = True

    # UNSURE: at 15+ both the Skybound Art and the Super Skybound Art effects activate.
    def fanfare(self, ctx):
        if E.skybound_art(ctx):
            _evolve(ctx, ctx.source)
        if E.super_skybound_art(ctx):
            E.damage(ctx.state, [common.enemy_leader(ctx)], 3, ctx.source)

    def on_evolved(self, ctx):
        for _ in range(7):
            E.damage(ctx.state, _random_enemy_follower(ctx), 1, ctx.source)


@register(ALFHEIMR.card_id)
class Alfheimr(CardScript):
    """Mode: draw and heal 1 / allies +1/+0 and Rush / allies +0/+1 and Ward. Super Skybound Art: all."""
    modes = (3, 1)
    skybound = True

    def all_modes(self, state, card, enhanced):
        return E.skybound_gauge(state, card) >= 15

    def cast(self, ctx):
        modes = (0, 1, 2) if E.super_skybound_art(ctx) else ctx.modes
        if 0 in modes:
            E.draw(ctx.state, ctx.controller)
            E.heal_leader(ctx.state, ctx.controller, 1)
        if 1 in modes:
            for f in list(ctx.me.followers):
                E.buff(ctx.state, f, 1, 0)
                E.give_keywords(f, Keyword.RUSH)
        if 2 in modes:
            for f in list(ctx.me.followers):
                E.buff(ctx.state, f, 0, 1)
                E.give_keywords(f, Keyword.WARD)


@register(EWIYAR.card_id)
class Ewiyar(CardScript):
    """Fanfare: Skybound Art - recover 1 evolution point. Rush."""
    skybound = True

    def fanfare(self, ctx):
        if E.skybound_art(ctx):
            E.recover_ep(ctx.state, ctx.controller, 1)


@register(YUEL_AND_SOCIETTE.card_id)
class YuelAndSociette(CardScript):
    """Fanfare: twice, 4 damage to a random enemy follower. Super-Evolve: gain Crest: Yuel & Societte."""

    def fanfare(self, ctx):
        for _ in range(2):
            E.damage(ctx.state, _random_enemy_follower(ctx), 4, ctx.source)

    def on_super_evolve(self, ctx):
        _gain_crest(ctx, YUEL_CREST)


# --- set 10000 (Basic) -------------------------------------------------------------------------

@register(FAIRY_TAMER.card_id)
class FairyTamer(CardScript):
    """Fanfare: add 2 Fairies to your hand."""

    def fanfare(self, ctx):
        _add(ctx, FAIRY, 2)


@register(STRAY_BEASTMAN.card_id)
class StrayBeastman(CardScript):
    """Fanfare: increase your Combo by 1."""

    def fanfare(self, ctx):
        ctx.me.combo += 1


@register(GENTLE_TREANT.card_id)
class GentleTreant(CardScript):
    """Fanfare: Combo (3) - evolve this follower. Strike: restore 2 defense to your leader."""

    def fanfare(self, ctx):
        if _combo(ctx, 3):
            _evolve(ctx, ctx.source)

    def strike(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 2)


@register(WILD_PROFUSION.card_id)
class WildProfusion(CardScript):
    """Fanfare: add a Fairy. Countdown (2). Whenever an allied Pixie enters, 1 damage to a random enemy."""

    def fanfare(self, ctx):
        _add(ctx, FAIRY)

    def on_ally_enter(self, ctx):
        if _is_pixie(ctx.other):
            E.damage(ctx.state, _random_enemy_follower(ctx), 1, ctx.source)


@register(MAY.card_id)
class May(CardScript):
    """Fanfare: Combo (3) - deal 3 damage to an enemy follower."""
    play_targets = (TargetSpec(Target.ENEMY_FOLLOWER, filter=_combo_on_play(3)),)

    def fanfare(self, ctx):
        if _combo(ctx, 3):
            E.damage(ctx.state, ctx.chosen(), 3, ctx.source)


@register(SELWYN.card_id)
class Selwyn(CardScript):
    """Storm. Super-Evolve: return an enemy follower to its owner's hand."""
    evolve_targets = (TargetSpec(Target.ENEMY_FOLLOWER, filter=_super_evolve_possible),)

    def on_super_evolve(self, ctx):
        for target in ctx.chosen():
            E.return_to_hand(ctx.state, target)


@register(BUG_ALERT.card_id)
class BugAlert(CardScript):
    """Return an allied card on the field to your hand. Deal 2 damage to a random enemy follower."""
    play_targets = (TargetSpec(Target.ALLIED_CARD),)

    def cast(self, ctx):
        for target in ctx.chosen():
            E.return_to_hand(ctx.state, target)
        E.damage(ctx.state, _random_enemy_follower(ctx), 2, ctx.source)
