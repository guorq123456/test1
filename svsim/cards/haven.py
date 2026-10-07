"""Havencraft cards and the cards they generate.

Card stats come from the pool table (svsim/cards/pool.py); this module holds
the abilities. Comments give the official Simplified Chinese names.
"""

from svsim.cards import common
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.enums import Craft, Keyword
from svsim.core.script import CardScript, Target, TargetSpec, register, script_for

ENEMY = common.ENEMY_FOLLOWER
HAND = common.HAND_CARD
ANOTHER_CARD = (TargetSpec(Target.ANY_CARD, other=True),)
SMALL_ENEMY = (TargetSpec(Target.ENEMY_FOLLOWER, filter=lambda state, player, c: c.life <= 3),)

# --- tokens ---
HOLY_FALCON = card(90061110)  # 神圣猎鹰
HOLYFLAME_TIGER = card(90061120)  # 圣炎猛虎
REGAL_FALCON = card(90061130)  # 壮丽大神隼
RINGS_OF_MOONLIGHT = card(90064210)  # 月影指环
DEPTHS_OF_THE_ELD_TOME = card(90064320)  # 天书深渊

# --- leader area / alternate forms ---
ERRALDE_CREST = card(10964112)  # 纹章：神纹的罪人·艾尔拉德
VERDILIA_CREST = card(10864112)  # 纹章：飞跃的姐妹·贝尔迪俪亚&卡诗黛儿
ZOE_CREST = card(10864122)  # 纹章：希望的光彩·莉迪耶尔
KUKISHIRO_CREST = card(10564122)  # 纹章：雾卷花·茎白
LYANTHOTH_FAITH = card(10664122)  # 古旧天书·莲妥丝 (信仰)
ALMIRAJ_CRYSTALLIZE = card(10962122)  # 奇迹独角兔 (结晶)
COWARD_CRYSTALLIZE = card(10661112)  # 崇奉的懦者 (结晶)
DYER_CRYSTALLIZE = card(10662112)  # 崇敬的涂描者 (结晶)
CRUSADER_CRYSTALLIZE = card(10663112)  # 崇拜的圣骑士 (结晶)

# --- Basic (10000) ---
SOULCURE_SISTER = card(10061110)  # 治愈的修女
FOX_OF_PURITY = card(10061120)  # 纯洁白狐
WINGED_WARRIOR = card(10061130)  # 圣翼战士
AVIAN_STATUE = card(10061210)  # 投影鸟像
IRONFIST_PRIEST = card(10062110)  # 铁拳神父
SACRED_GRIFFON = card(10062120)  # 神圣狮鹫
WINGED_STATUE = card(10062210)  # 羽翼石像

# --- set 10004 ---
TROUE = card(10461110)  # 英雄幻视·托路
LAMRETTA = card(10461120)  # 克己复礼的修女·拉姆蕾达
AWED_AND_INSPIRED = card(10461210)  # 莉莉艾的鼓舞
SARA = card(10462110)  # 沙神的巫女·莎拉
SOPHIA = card(10462120)  # 赞恩教僧侣·索菲娅
SKYFARING_VESSEL = card(10462210)  # 骑驰天空之艇
TIKOH = card(10463110)  # 魔杖傍身的外科医生·缇可
GLEAMING_GEMS = card(10463210)  # 蕾·菲耶的宝石
GALLEON = card(10464110)  # 土之法则·伽莱翁
VIRA = card(10464120)  # 威严的星晶骑士·薇拉

# --- set 10005 ---
PRESCIENT_PRIESTESS = card(10561110)  # 先见的神官
BOUQUET_BELIEVER = card(10561120)  # 连结的使徒
MALICE_OF_THE_MISTBLOOM = card(10561310)  # 雾卷花的激愤
IMMOVABLE_PALADIN = card(10562110)  # 毫不动摇的圣骑士
DESPERATE_SHRINEMOUSE = card(10562120)  # 穷途末路的巫女
PROTECTIVE_SHELL = card(10562210)  # 穹顶护甲
SAINT_OF_REHABILITATION = card(10563110)  # 至圣威仪
RESOLVE_OF_THE_MISTBLOOM = card(10563210)  # 坚固的雾卷花
SOFINA = card(10564110)  # 思念的《力量》·索菲娜
KUKISHIRO = card(10564120)  # 雾卷花·茎白

# --- set 10006 ---
PROSTRATING_COWARD = card(10661110)  # 崇奉的懦者
UNHOLY_WATER = card(10661210)  # 污浊的圣水
ADVENT_OF_THE_ELD_TOME = card(10661310)  # 天书授予
VENERATING_DYER = card(10662110)  # 崇敬的涂描者
PEGASUS_RIDER = card(10662120)  # 飞马骑手
SCRIPTURE_OF_SALVATION = card(10662210)  # 救赎的圣典
WORSHIPFUL_CRUSADER = card(10663110)  # 崇拜的圣骑士
SUBLIME_ELD_TOME = card(10663210)  # 崇高的天书
KANDIMA = card(10664110)  # 崇高的憎恶·康蒂玛
LYANTHOTH = card(10664120)  # 古旧天书·莲妥丝

# --- set 10007 ---
REVEREND_OF_FINANCE = card(10761110)  # 营利支援者
MISSIONARY_OF_RECRUITMENT = card(10761120)  # 广域传教士
EARRINGS_OF_SUNLIGHT = card(10761210)  # 阳光耳饰
SISTER_OF_STRATEGIC_DEVELOPMENT = card(10762110)  # 神圣策划人
HOLY_HAWK_OF_COMMUNICATIONS = card(10762120)  # 传言圣鸟
TIMEPIECE_OF_PERFECTION = card(10762210)  # 完美的时钟
DEACON_OF_SECURITY = card(10763110)  # 审理的守卫
TRIDENT_OF_ERODING_TIDES = card(10763210)  # 海蚀三叉戟
RODEO = card(10764110)  # 裁神的安纳提玛·罗德欧
INITIA = card(10764120)  # 崇拜经理人·伊尼西雅

# --- set 10008 ---
LILIUM = card(10861110)  # 图书室的魔女·莉莉尤姆
THERESA = card(10861120)  # 勤劳的女祭司·泰瑞莎
GRANT = card(10861130)  # 亡灵猎人·格兰特
EDETH = card(10862110)  # 天阳的使徒·艾迪特
VICHE = card(10862120)  # 深渊探究者·维切
LINGERING_THREAT = card(10862310)  # 威胁的残渣
COLETTE = card(10863110)  # 圣洁驱魔人·珂蕾特
ACADEMY_HIJINKS = card(10863210)  # 同窗好友
VERDILIA_AND_CASTELLE = card(10864110)  # 飞跃的姐妹·贝尔迪俪亚&卡诗黛儿
ZOE = card(10864120)  # 希望的光彩·莉迪耶尔

# --- set 10009 ---
FOLLOWER_OF_THE_TENETS = card(10961110)  # 条规成员
PERYTON = card(10961120)  # 鹿鹰兽
ROARING_BASILICA = card(10961210)  # 咆哮圣堂
AGENT_OF_THE_TESTAMENTS = card(10962110)  # 纪律间谍
MIRACULOUS_ALMIRAJ = card(10962120)  # 奇迹独角兔
VOW_OF_DEVOTION = card(10962310)  # 铭刻之约
EXECUTOR_OF_THE_VOW = card(10963110)  # 誓言干部
JURATIO = card(10963210)  # 神纹誓言
ERRALDE = card(10964110)  # 神纹的罪人·艾尔拉德
OMERIO = card(10964120)  # 翼天的变貌·奥梅里欧

CARDS = [
    SOULCURE_SISTER, FOX_OF_PURITY, WINGED_WARRIOR, AVIAN_STATUE, IRONFIST_PRIEST, SACRED_GRIFFON,
    WINGED_STATUE, TROUE, LAMRETTA, AWED_AND_INSPIRED, SARA, SOPHIA, SKYFARING_VESSEL, TIKOH,
    GLEAMING_GEMS, GALLEON, VIRA, PRESCIENT_PRIESTESS, BOUQUET_BELIEVER, MALICE_OF_THE_MISTBLOOM,
    IMMOVABLE_PALADIN, DESPERATE_SHRINEMOUSE, PROTECTIVE_SHELL, SAINT_OF_REHABILITATION,
    RESOLVE_OF_THE_MISTBLOOM, SOFINA, KUKISHIRO, PROSTRATING_COWARD, UNHOLY_WATER,
    ADVENT_OF_THE_ELD_TOME, VENERATING_DYER, PEGASUS_RIDER, SCRIPTURE_OF_SALVATION,
    WORSHIPFUL_CRUSADER, SUBLIME_ELD_TOME, KANDIMA, LYANTHOTH, REVEREND_OF_FINANCE,
    MISSIONARY_OF_RECRUITMENT, EARRINGS_OF_SUNLIGHT, SISTER_OF_STRATEGIC_DEVELOPMENT,
    HOLY_HAWK_OF_COMMUNICATIONS, TIMEPIECE_OF_PERFECTION, DEACON_OF_SECURITY,
    TRIDENT_OF_ERODING_TIDES, RODEO, INITIA, LILIUM, THERESA, GRANT, EDETH, VICHE, LINGERING_THREAT,
    COLETTE, ACADEMY_HIJINKS, VERDILIA_AND_CASTELLE, ZOE, FOLLOWER_OF_THE_TENETS, PERYTON,
    ROARING_BASILICA, AGENT_OF_THE_TESTAMENTS, MIRACULOUS_ALMIRAJ, VOW_OF_DEVOTION,
    EXECUTOR_OF_THE_VOW, JURATIO, ERRALDE, OMERIO,
]
TOKENS = [HOLY_FALCON, HOLYFLAME_TIGER, REGAL_FALCON, RINGS_OF_MOONLIGHT, DEPTHS_OF_THE_ELD_TOME]
LEADER_AREA = [ERRALDE_CREST, VERDILIA_CREST, ZOE_CREST, KUKISHIRO_CREST, LYANTHOTH_FAITH]
ALTERNATE_FORMS = [ALMIRAJ_CRYSTALLIZE, COWARD_CRYSTALLIZE, DYER_CRYSTALLIZE, CRUSADER_CRYSTALLIZE]
# Keyword-only cards: no script needed.
NO_SCRIPT = [FOX_OF_PURITY, VENERATING_DYER, MIRACULOUS_ALMIRAJ, HOLY_FALCON, HOLYFLAME_TIGER,
             REGAL_FALCON]


# --- helpers ---------------------------------------------------------------------------

def _heal(ctx, n: int) -> None:
    E.heal_leader(ctx.state, ctx.controller, n)


def _amulets(player_state) -> list:
    return [c for c in player_state.field if c.defn.is_amulet]


def _three_amulets(ctx) -> bool:
    """"If there are at least 3 allied amulets on the field"."""
    return len(_amulets(ctx.me)) >= 3


def _base_cost_six(player_state) -> bool:
    """"If there's an allied card on the field with a base cost of 6 or more"."""
    return any(c.defn.cost >= 6 for c in player_state.field)


def _random_enemies(ctx, k: int = 1) -> list:
    return E.random_sample(ctx.state, ctx.opponent.followers, k)


def _all_enemy_followers(ctx) -> list:
    return list(ctx.opponent.followers)


def _is_allied_amulet(ctx, inst) -> bool:
    return inst.owner == ctx.controller and inst.defn.is_amulet


def _in_hand(ctx) -> bool:
    return any(c is ctx.source for c in ctx.me.hand)


def _destroy_chosen(ctx) -> None:
    for target in ctx.chosen():
        E.destroy(ctx.state, target)


def _banish_chosen(ctx) -> None:
    for target in ctx.chosen():
        E.banish(ctx.state, target)


def _return_random_to_deck(ctx, k: int) -> None:
    for c in E.random_sample(ctx.state, ctx.me.hand, k):
        E.return_to_deck(ctx.state, c)


def _evolve_self(ctx) -> None:
    if not ctx.source.evolved:
        E.evolve(ctx.state, ctx.source)


class _IfEvolvedAtTurnEnd(CardScript):
    """"At the end of your turn, if this follower is evolved": checked when the
    ability triggers, so an evolution by an earlier end-of-turn ability (e.g.
    Galleon's) doesn't count (official Q&A on Lamretta)."""
    queue_checks = ("on_turn_end",)

    def queue_condition(self, hook, ctx):
        return ctx.source.evolved


def _destroyed_last_words_amulets(player_state) -> list:
    """Allied amulets destroyed this match that have Last Words and a base cost of 2
    or less (one entry per destruction)."""
    return [d for d in player_state.destroyed_amulets
            if d.cost <= 2 and script_for(d.card_id).last_words is not None]


remove_all_abilities = E.silence   # "remove all abilities"


class _CantAttack(CardScript):
    """Granted: "Can't attack followers or leaders"."""
    cant_attack = True


class _TwoAttacks(CardScript):
    """Granted: "Can attack 2 times per turn"."""
    attacks_per_turn = 2


CANT_ATTACK = _CantAttack()
TWO_ATTACKS = _TwoAttacks()


class _AdvanceOnEngage(CardScript):
    """Countdown amulet with "Engage (N): Advance this amulet's count by N"."""

    def engage(self, ctx):
        E.advance_countdown(ctx.state, ctx.source, self.engage_cost)


# --- tokens ------------------------------------------------------------------------------

@register(RINGS_OF_MOONLIGHT.card_id)
class RingsOfMoonlight(CardScript):
    """Countdown (1). Aura. At the end of your turn, if there are at least 3 allied
    amulets on the field, deal 3 damage to all enemies."""

    def on_turn_end(self, ctx):
        if _three_amulets(ctx):
            E.damage(ctx.state, _all_enemy_followers(ctx) + [common.enemy_leader(ctx)], 3,
                     ctx.source)


@register(DEPTHS_OF_THE_ELD_TOME.card_id)
class DepthsOfTheEldTome(CardScript):
    """Select a card on the field and destroy it. If it was an allied amulet, deal 2
    damage to the enemy leader and add a Depths of the Eld Tome to your hand."""
    play_targets = (TargetSpec(Target.ANY_CARD),)

    def cast(self, ctx):
        # Confirmed by the player: as in the English, "add a Depths" is part of the "if you
        # selected an allied amulet" clause (the Chinese text puts it in its own sentence).
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
            if _is_allied_amulet(ctx, target):
                E.damage(ctx.state, [common.enemy_leader(ctx)], 2, ctx.source)
                E.add_to_hand(ctx.state, ctx.controller, DEPTHS_OF_THE_ELD_TOME)


# --- leader area -------------------------------------------------------------------------

@register(ERRALDE_CREST.card_id)
class ErraldeCrest(CardScript):
    """At the end of your turn, if there's an allied card on the field with a base
    cost of 6 or more, deal 1 damage to the enemy leader and restore 1 defense to
    your leader."""

    def on_turn_end(self, ctx):
        # Confirmed by the player: as in the English, the heal is part of the condition
        # (the Chinese text puts it in its own sentence).
        if _base_cost_six(ctx.me):
            E.damage(ctx.state, [common.enemy_leader(ctx)], 1, ctx.source)
            _heal(ctx, 1)


@register(VERDILIA_CREST.card_id)
class VerdiliaCrest(CardScript):
    """Whenever a super-evolved allied follower attacks a follower, give it "Can
    attack 2 times per turn" until the end of the turn (no effect on one that can
    already attack more: official Q&A, 3 stays 3)."""

    def on_attack(self, ctx):
        attacker = ctx.other
        if attacker.owner == ctx.controller and attacker.super_evolved and ctx.target >= 0:
            E.grant(attacker, TWO_ATTACKS, until_turn=common.end_of_turn(ctx))


@register(ZOE_CREST.card_id)
class ZoeCrest(CardScript):
    """Countdown (1). Last Words: summon a Zoe, Dazzling Hope and evolve it."""

    def last_words(self, ctx):
        zoe = E.summon(ctx.state, ctx.controller, ZOE)
        if zoe is not None:
            E.evolve(ctx.state, zoe)


@register(KUKISHIRO_CREST.card_id)
class KukishiroCrest(CardScript):
    """During your turn, whenever you draw a card costing 1, 3 or 5, summon a Fox of
    Purity or Holy Falcon at random; costing 2, 4 or 6, summon one for the opponent."""

    def on_draw(self, ctx):
        if not common.during_your_turn(ctx):
            return
        cost = ctx.other.cost
        if cost in (1, 3, 5):
            side = ctx.controller
        elif cost in (2, 4, 6):
            side = 1 - ctx.controller
        else:
            return
        E.summon(ctx.state, side, ctx.state.rng.choice((FOX_OF_PURITY, HOLY_FALCON)))


@register(LYANTHOTH_FAITH.card_id)
class LyanthothFaith(CardScript):
    """Faith: value starts at 0; +1 whenever an allied amulet is destroyed."""

    def on_card_destroyed(self, ctx):
        if _is_allied_amulet(ctx, ctx.other):
            counters = E.counters(ctx.source)
            counters["value"] = counters.get("value", 0) + 1


# --- Crystallize forms -------------------------------------------------------------------

@register(ALMIRAJ_CRYSTALLIZE.card_id)
class AlmirajCrystallize(_AdvanceOnEngage):
    """Crystallize (1): Countdown (3). Last Words: summon a Miraculous Al-mi'raj.
    Engage (1): advance this amulet's count by 1."""
    engage_cost = 1

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, MIRACULOUS_ALMIRAJ)


@register(COWARD_CRYSTALLIZE.card_id)
class CowardCrystallize(CardScript):
    """Crystallize (2): Countdown (3). Last Words: summon a Prostrating Coward."""

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, PROSTRATING_COWARD)


@register(DYER_CRYSTALLIZE.card_id)
class DyerCrystallize(CardScript):
    """Crystallize (1): Countdown (3). Last Words: summon a Venerating Dyer."""

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, VENERATING_DYER)


@register(CRUSADER_CRYSTALLIZE.card_id)
class CrusaderCrystallize(CardScript):
    """Crystallize (1): Countdown (3). Last Words: summon a Worshipful Crusader."""

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, WORSHIPFUL_CRUSADER)


# --- set 10009 -----------------------------------------------------------------------------

@register(FOLLOWER_OF_THE_TENETS.card_id)
class FollowerOfTheTenets(CardScript):
    """Ward. During your turn, when your leader's defense is restored, evolve this follower."""

    def on_leader_healed(self, ctx):
        if common.during_your_turn(ctx):
            _evolve_self(ctx)


@register(PERYTON.card_id)
class Peryton(CardScript):
    """Fanfare: summon 2 Perytons. Rush."""

    def fanfare(self, ctx):
        for _ in range(2):
            E.summon(ctx.state, ctx.controller, PERYTON)


@register(ROARING_BASILICA.card_id)
class RoaringBasilica(_AdvanceOnEngage):
    """Countdown (3). Last Words: summon a Holyflame Tiger; deal 4 damage to a random
    enemy follower. Engage (3): advance this amulet's count by 3."""
    engage_cost = 3

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, HOLYFLAME_TIGER)
        E.damage(ctx.state, _random_enemies(ctx), 4, ctx.source)


@register(AGENT_OF_THE_TESTAMENTS.card_id)
class AgentOfTheTestaments(CardScript):
    """Fanfare: give this follower Ambush until the end of your opponent's turn. At the
    end of your turn, restore 1 defense to your leader."""

    def fanfare(self, ctx):
        E.give_keywords(ctx.source, Keyword.AMBUSH, until_turn=common.end_of_opponents_turn(ctx))

    def on_turn_end(self, ctx):
        _heal(ctx, 1)


@register(VOW_OF_DEVOTION.card_id)
class VowOfDevotion(CardScript):
    """Mode: 1. Deal 3 damage to a random enemy follower. 2. Restore 2 defense to your
    leader. If there's an allied card on the field with a base cost of 6 or more,
    activate both instead."""
    modes = (2, 1)

    def all_modes(self, state, card, enhanced):
        return _base_cost_six(state.players[card.owner])

    def cast(self, ctx):
        if 0 in ctx.modes:
            E.damage(ctx.state, _random_enemies(ctx), 3, ctx.source)
        if 1 in ctx.modes:
            _heal(ctx, 2)


@register(EXECUTOR_OF_THE_VOW.card_id)
class ExecutorOfTheVow(CardScript):
    """Fanfare: restore 2 defense to your leader. Ward. During your turn, whenever
    your leader's defense is restored, destroy a random enemy follower.
    Super-Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        _heal(ctx, 2)

    def on_super_evolve(self, ctx):
        _heal(ctx, 2)

    def on_leader_healed(self, ctx):
        if common.during_your_turn(ctx):
            for target in _random_enemies(ctx):
                E.destroy(ctx.state, target)


@register(JURATIO.card_id)
class Juratio(CardScript):
    """Fanfare: destroy all followers. Engage (1): destroy this card, draw a card and
    restore 1 defense to your leader."""
    engage_cost = 1

    def fanfare(self, ctx):
        for f in [c for c in ctx.state.field_order() if c.defn.is_follower]:
            E.destroy(ctx.state, f)

    def engage(self, ctx):
        E.destroy(ctx.state, ctx.source)
        E.draw(ctx.state, ctx.controller)
        _heal(ctx, 1)


@register(ERRALDE.card_id)
class Erralde(CardScript):
    """Fanfare: select an enemy follower and destroy it. Evolve: gain Crest: Erralde."""
    play_targets = ENEMY

    def fanfare(self, ctx):
        _destroy_chosen(ctx)

    def on_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, ERRALDE_CREST)


@register(OMERIO.card_id)
class Omerio(CardScript):
    """Whenever an allied amulet is destroyed, activate the next of these in turn
    (after 3 comes 1 again: official Q&A): 1. Deal 3 damage to 2 random enemy
    followers. 2. Restore 2 defense to your leader. 3. Summon a Holy Falcon.
    Evolve: destroy all allied amulets."""

    def on_card_destroyed(self, ctx):
        if not _is_allied_amulet(ctx, ctx.other):
            return
        counters = E.counters(ctx.source)
        step = counters.get("step", 0)
        counters["step"] = (step + 1) % 3
        if step == 0:
            E.damage(ctx.state, _random_enemies(ctx, 2), 3, ctx.source)
        elif step == 1:
            _heal(ctx, 2)
        else:
            E.summon(ctx.state, ctx.controller, HOLY_FALCON)

    def on_evolve(self, ctx):
        for amulet in _amulets(ctx.me):
            E.destroy(ctx.state, amulet)


# --- set 10008 -----------------------------------------------------------------------------

@register(LILIUM.card_id)
class Lilium(CardScript):
    """Last Words: draw a card. Evolve: select an enemy follower, remove all its
    abilities and deal it 2 damage."""
    evolve_targets = ENEMY

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller)

    def on_evolve(self, ctx):
        targets = ctx.chosen()
        for target in targets:
            remove_all_abilities(target)
        E.damage(ctx.state, targets, 2, ctx.source)


@register(THERESA.card_id)
class Theresa(CardScript):
    """Fanfare: summon a Soulcure Sister and give it +2/-2 and Storm."""

    def fanfare(self, ctx):
        sister = E.summon(ctx.state, ctx.controller, SOULCURE_SISTER)
        if sister is not None:
            E.buff(ctx.state, sister, 2, -2)
            E.give_keywords(sister, Keyword.STORM)


@register(GRANT.card_id)
class GrantHunterOfUndeath(CardScript):
    """Fanfare: select an enemy follower and destroy it. Evolve: replicate the Fanfare."""
    play_targets = ENEMY
    evolve_targets = ENEMY

    def fanfare(self, ctx):
        _destroy_chosen(ctx)

    def on_evolve(self, ctx):
        _destroy_chosen(ctx)


@register(EDETH.card_id)
class Edeth(CardScript):
    """Ward, Aura. Last Words: summon an Edeth without Last Words.
    Super-Evolve: select an enemy follower and destroy it."""
    super_evolve_targets = ENEMY

    def last_words(self, ctx):
        twin = E.summon(ctx.state, ctx.controller, EDETH)
        if twin is not None:
            E.remove_last_words(twin)

    def on_super_evolve(self, ctx):
        _destroy_chosen(ctx)


@register(VICHE.card_id)
class Viche(CardScript):
    """Activates in hand: whenever an allied follower super-evolves, reduce this
    card's cost by 3. Rush, Bane."""
    listen_in_hand = True

    def on_ally_evolve(self, ctx):
        if ctx.super_ and _in_hand(ctx):
            E.add_cost(ctx.source, -3)


@register(LINGERING_THREAT.card_id)
class LingeringThreat(CardScript):
    """Select an enemy follower with 3 defense or less and banish it. Enhance (5):
    banish all enemy followers with 3 defense or less instead."""
    # APPROX: the Enhanced form still needs a selectable target to be played.
    play_targets = SMALL_ENEMY
    enhance = (5,)

    def cast(self, ctx):
        if ctx.enhanced:
            for f in [f for f in ctx.opponent.followers if f.life <= 3]:
                E.banish(ctx.state, f)
        else:
            _banish_chosen(ctx)


@register(COLETTE.card_id)
class Colette(CardScript):
    """Fanfare: if there's an evolved allied follower on the field, evolve this
    follower. Ward. When this follower evolves, twice deal 1 damage to a random
    enemy follower."""

    def fanfare(self, ctx):
        if any(f.evolved for f in ctx.me.followers if f is not ctx.source):
            _evolve_self(ctx)

    def on_evolved(self, ctx):
        for _ in range(2):
            E.damage(ctx.state, _random_enemies(ctx), 1, ctx.source)


@register(ACADEMY_HIJINKS.card_id)
class AcademyHijinks(CardScript):
    """Countdown (2). At the end of your turn, draw a card; restore 1 defense to your
    leader if there's an evolved allied follower, 2 if there's a super-evolved one."""

    def on_turn_end(self, ctx):
        E.draw(ctx.state, ctx.controller)
        followers = ctx.me.followers
        if any(f.super_evolved for f in followers):
            _heal(ctx, 2)
        elif any(f.evolved for f in followers):
            _heal(ctx, 1)


@register(VERDILIA_AND_CASTELLE.card_id)
class VerdiliaAndCastelle(CardScript):
    """Fanfare: summon a random follower costing 2 or less from your deck and
    super-evolve it. Super-Evolve: gain Crest: Verdilia & Castelle."""

    def fanfare(self, ctx):
        for f in E.summon_from_deck(ctx.state, ctx.controller,
                                    lambda c: c.defn.is_follower and c.cost <= 2):
            E.evolve(ctx.state, f, super_=True)

    def on_super_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, VERDILIA_CREST)


@register(ZOE.card_id)
class Zoe(CardScript):
    """Fanfare: Mode: 1. Deal 3 damage to all enemy followers. 2. Deal 3 damage to the
    enemy leader. 3. Restore 3 defense to your leader. Then deal 3 damage to this
    follower. Evolve: gain Crest: Zoe, Dazzling Hope."""
    modes = (3, 1)

    def fanfare(self, ctx):
        # Confirmed by the player: the 3 self-damage comes after the chosen mode.
        if 0 in ctx.modes:
            E.damage(ctx.state, _all_enemy_followers(ctx), 3, ctx.source)
        if 1 in ctx.modes:
            E.damage(ctx.state, [common.enemy_leader(ctx)], 3, ctx.source)
        if 2 in ctx.modes:
            _heal(ctx, 3)
        E.damage(ctx.state, [ctx.source], 3, ctx.source)

    def on_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, ZOE_CREST)


# --- set 10007 -----------------------------------------------------------------------------

@register(REVEREND_OF_FINANCE.card_id)
class ReverendOfFinance(CardScript):
    """Fanfare: if there are at least 3 allied amulets, summon a Reverend of Finance.
    Rush. Last Words: draw a card."""

    def fanfare(self, ctx):
        if _three_amulets(ctx):
            E.summon(ctx.state, ctx.controller, REVEREND_OF_FINANCE)

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller)


@register(MISSIONARY_OF_RECRUITMENT.card_id)
class MissionaryOfRecruitment(CardScript):
    """Fanfare: draw 2 amulets. Evolve: deal X damage to all enemy followers, X = the
    number of amulets in your hand."""

    def fanfare(self, ctx):
        for _ in range(2):
            E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.is_amulet)

    def on_evolve(self, ctx):
        x = sum(c.defn.is_amulet for c in ctx.me.hand)
        if x:
            E.damage(ctx.state, _all_enemy_followers(ctx), x, ctx.source)


@register(EARRINGS_OF_SUNLIGHT.card_id)
class EarringsOfSunlight(CardScript):
    """Fanfare: select a card in your hand and return it to the deck; draw a card.
    Engage: destroy this card and replicate the Fanfare."""
    play_targets = HAND
    engage_targets = HAND
    engage_cost = 0

    def fanfare(self, ctx):
        self._swap(ctx)

    def engage(self, ctx):
        E.destroy(ctx.state, ctx.source)
        self._swap(ctx)

    def _swap(self, ctx):
        for c in ctx.chosen_hand():
            E.return_to_deck(ctx.state, c)
        E.draw(ctx.state, ctx.controller)


@register(SISTER_OF_STRATEGIC_DEVELOPMENT.card_id)
class SisterOfStrategicDevelopment(CardScript):
    """Fanfare: if there are at least 3 allied amulets, select an enemy follower and
    deal it 5 damage."""
    play_targets = ENEMY

    def fanfare(self, ctx):
        if _three_amulets(ctx):
            E.damage(ctx.state, ctx.chosen(), 5, ctx.source)


class _BanishAndMaybeHeal(CardScript):
    """Fanfare: select an enemy follower and banish it; if there are at least 3
    allied amulets, restore 3 defense to your leader."""
    play_targets = ENEMY

    def fanfare(self, ctx):
        self._banish(ctx)

    def _banish(self, ctx):
        _banish_chosen(ctx)
        if _three_amulets(ctx):
            _heal(ctx, 3)


@register(HOLY_HAWK_OF_COMMUNICATIONS.card_id)
class HolyHawkOfCommunications(_BanishAndMaybeHeal):
    """Fanfare: select an enemy follower and banish it; if there are at least 3
    allied amulets, restore 3 defense to your leader. Storm."""


@register(TIMEPIECE_OF_PERFECTION.card_id)
class TimepieceOfPerfection(CardScript):
    """Enhance (4): deal 1 damage to all enemy followers. Engage: destroy this card and
    deal 1 damage to all enemy followers."""
    enhance = (4,)
    engage_cost = 0

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.damage(ctx.state, _all_enemy_followers(ctx), 1, ctx.source)

    def engage(self, ctx):
        E.destroy(ctx.state, ctx.source)
        E.damage(ctx.state, _all_enemy_followers(ctx), 1, ctx.source)


@register(DEACON_OF_SECURITY.card_id)
class DeaconOfSecurity(CardScript):
    """Fanfare: if there are at least 3 allied amulets, evolve this follower and give
    it Barrier. Ward. Last Words: restore 3 defense to your leader."""

    def fanfare(self, ctx):
        # Confirmed by the player: as in the English, Barrier is part of the condition
        # ("evolve this follower and give it Barrier").
        if _three_amulets(ctx):
            _evolve_self(ctx)
            E.give_keywords(ctx.source, Keyword.BARRIER)

    def last_words(self, ctx):
        _heal(ctx, 3)


@register(TRIDENT_OF_ERODING_TIDES.card_id)
class TridentOfErodingTides(CardScript):
    """Fanfare: select an enemy follower and deal it 4 damage. Engage: destroy this
    card; select an enemy follower and deal it 2 damage."""
    play_targets = ENEMY
    engage_targets = ENEMY
    engage_cost = 0

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4, ctx.source)

    def engage(self, ctx):
        E.destroy(ctx.state, ctx.source)
        E.damage(ctx.state, ctx.chosen(), 2, ctx.source)


@register(RODEO.card_id)
class Rodeo(CardScript):
    """Fanfare: summon a Rings of Moonlight. Evolve: delay the count of a random
    allied Rings of Moonlight by 1."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, RINGS_OF_MOONLIGHT)

    def on_evolve(self, ctx):
        rings = [c for c in ctx.me.field if c.defn.card_id == RINGS_OF_MOONLIGHT.card_id]
        for ring in E.random_sample(ctx.state, rings, 1):
            E.advance_countdown(ctx.state, ring, -1)


@register(INITIA.card_id)
class Initia(_BanishAndMaybeHeal):
    """Fanfare: select an enemy follower and banish it; if there are at least 3
    allied amulets, restore 3 defense to your leader. Ward, Aura.
    Super-Evolve: replicate the Fanfare."""
    super_evolve_targets = ENEMY

    def on_super_evolve(self, ctx):
        self._banish(ctx)


# --- set 10006 -----------------------------------------------------------------------------

@register(PROSTRATING_COWARD.card_id)
class ProstratingCoward(CardScript):
    """When this follower enters the field, restore 2 defense to your leader. Bane, Ward."""

    def on_enter(self, ctx):
        _heal(ctx, 2)


@register(UNHOLY_WATER.card_id)
class UnholyWater(_AdvanceOnEngage):
    """Countdown (3). Last Words: draw a card; destroy a random enemy follower.
    Engage (1): advance this amulet's count by 1."""
    engage_cost = 1

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller)
        for target in _random_enemies(ctx):
            E.destroy(ctx.state, target)


@register(ADVENT_OF_THE_ELD_TOME.card_id)
class AdventOfTheEldTome(CardScript):
    """Draw 2 amulets."""

    def cast(self, ctx):
        for _ in range(2):
            E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.is_amulet)


@register(PEGASUS_RIDER.card_id)
class PegasusRider(CardScript):
    """Fanfare: summon a Holy Falcon. Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, HOLY_FALCON)

    def on_evolve(self, ctx):
        E.summon(ctx.state, ctx.controller, HOLY_FALCON)


@register(SCRIPTURE_OF_SALVATION.card_id)
class ScriptureOfSalvation(CardScript):
    """Countdown (4). Last Words: draw 2 cards, deal 2 damage to all enemy followers
    and restore 2 defense to your leader."""

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)
        E.damage(ctx.state, _all_enemy_followers(ctx), 2, ctx.source)
        _heal(ctx, 2)


@register(WORSHIPFUL_CRUSADER.card_id)
class WorshipfulCrusader(CardScript):
    """Fanfare: summon a Worshipful Crusader. Bane, Aura. Evolve: select an enemy
    follower and destroy it."""
    evolve_targets = ENEMY

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, WORSHIPFUL_CRUSADER)

    def on_evolve(self, ctx):
        _destroy_chosen(ctx)


@register(SUBLIME_ELD_TOME.card_id)
class SublimeEldTome(CardScript):
    """Fanfare: select another card on the field and destroy it; if it was an allied
    amulet, recover 2 play points. Countdown (2). Last Words: summon a copy of a
    random allied amulet with Last Words and a base cost of 2 or less destroyed
    this match."""
    play_targets = ANOTHER_CARD

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
            if _is_allied_amulet(ctx, target):
                E.recover_pp(ctx.state, ctx.controller, 2)

    def last_words(self, ctx):
        # Confirmed by the player: picked per destruction (an amulet destroyed twice is
        # twice as likely), like Reanimate, rather than uniformly by name.
        eligible = _destroyed_last_words_amulets(ctx.me)
        if eligible:
            E.summon(ctx.state, ctx.controller, ctx.state.rng.choice(eligible))


@register(KANDIMA.card_id)
class Kandima(CardScript):
    """Fanfare: summon a copy each of 2 random differently named allied amulets with
    Last Words and a base cost of 2 or less destroyed this match. Super-Evolve:
    select another card on the field and destroy it; if it was an allied amulet,
    deal 3 damage to all enemy followers."""
    super_evolve_targets = ANOTHER_CARD

    def fanfare(self, ctx):
        eligible = _destroyed_last_words_amulets(ctx.me)
        for _ in range(2):
            if not eligible:
                break
            defn = ctx.state.rng.choice(eligible)
            E.summon(ctx.state, ctx.controller, defn)
            eligible = [d for d in eligible if d.name != defn.name]

    def on_super_evolve(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
            if _is_allied_amulet(ctx, target):
                E.damage(ctx.state, _all_enemy_followers(ctx), 3, ctx.source)


@register(LYANTHOTH.card_id)
class Lyanthoth(CardScript):
    """Fanfare: select 3 other cards on the field and destroy them. Ward. At the end of
    your turn, reduce your faith's value by 10 to add a Depths of the Eld Tome to
    your hand."""
    play_targets = (TargetSpec(Target.ANY_CARD, 3, other=True),)

    def fanfare(self, ctx):
        _destroy_chosen(ctx)

    def on_turn_end(self, ctx):
        if E.spend_faith(ctx.state, ctx.controller, LYANTHOTH_FAITH, 10):
            E.add_to_hand(ctx.state, ctx.controller, DEPTHS_OF_THE_ELD_TOME)


# --- set 10005 -----------------------------------------------------------------------------

@register(PRESCIENT_PRIESTESS.card_id)
class PrescientPriestess(CardScript):
    """Fanfare: select an enemy follower and deal it 2 damage. Ward. Evolve: replicate
    the Fanfare."""
    play_targets = ENEMY
    evolve_targets = ENEMY

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 2, ctx.source)

    def on_evolve(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 2, ctx.source)


@register(BOUQUET_BELIEVER.card_id)
class BouquetBeliever(CardScript):
    """Enhance (4): draw a card and give this follower Bane. During your turn,
    whenever you draw a card, give this follower Rush."""
    enhance = (4,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.draw(ctx.state, ctx.controller)
            E.give_keywords(ctx.source, Keyword.BANE)

    def on_draw(self, ctx):
        if common.during_your_turn(ctx):
            E.give_keywords(ctx.source, Keyword.RUSH)


@register(MALICE_OF_THE_MISTBLOOM.card_id)
class MaliceOfTheMistbloom(CardScript):
    """Return a random card from your hand to the deck. Draw 3 cards."""

    def cast(self, ctx):
        _return_random_to_deck(ctx, 1)
        E.draw(ctx.state, ctx.controller, 3)


@register(IMMOVABLE_PALADIN.card_id)
class ImmovablePaladin(CardScript):
    """Fanfare: summon 3 Immovable Paladins. Ward."""

    def fanfare(self, ctx):
        for _ in range(3):
            E.summon(ctx.state, ctx.controller, IMMOVABLE_PALADIN)


@register(DESPERATE_SHRINEMOUSE.card_id)
class DesperateShrinemouse(CardScript):
    """Fanfare: draw a card. During your turn, whenever you draw a card, deal 1 damage
    to all enemy followers. Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        E.draw(ctx.state, ctx.controller)

    def on_evolve(self, ctx):
        E.draw(ctx.state, ctx.controller)

    def on_draw(self, ctx):
        if common.during_your_turn(ctx):
            E.damage(ctx.state, _all_enemy_followers(ctx), 1, ctx.source)


@register(PROTECTIVE_SHELL.card_id)
class ProtectiveShell(CardScript):
    """Engage: destroy this card and draw X cards, X = allied followers with Ward."""
    engage_cost = 0

    def engage(self, ctx):
        E.destroy(ctx.state, ctx.source)
        x = sum(1 for f in ctx.me.followers if f.has(Keyword.WARD))
        if x:
            E.draw(ctx.state, ctx.controller, x)


@register(SAINT_OF_REHABILITATION.card_id)
class SaintOfRehabilitation(CardScript):
    """Fanfare: restore 1 defense to your leader. Ward. During your turn, whenever your
    leader's defense is restored, summon a Fox of Purity. Evolve and Super-Evolve:
    replicate the Fanfare (super-evolving with points does both)."""

    def fanfare(self, ctx):
        _heal(ctx, 1)

    def on_evolve(self, ctx):
        _heal(ctx, 1)

    def on_super_evolve(self, ctx):
        _heal(ctx, 1)

    def on_leader_healed(self, ctx):
        if common.during_your_turn(ctx):
            E.summon(ctx.state, ctx.controller, FOX_OF_PURITY)


@register(RESOLVE_OF_THE_MISTBLOOM.card_id)
class ResolveOfTheMistbloom(CardScript):
    """Fanfare: select an enemy follower and deal it 5 damage. Engage: destroy this
    card, return 2 random cards from your hand to the deck and draw 2 cards."""
    play_targets = ENEMY
    engage_cost = 0

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 5, ctx.source)

    def engage(self, ctx):
        E.destroy(ctx.state, ctx.source)
        _return_random_to_deck(ctx, 2)
        E.draw(ctx.state, ctx.controller, 2)


@register(SOFINA.card_id)
class Sofina(_IfEvolvedAtTurnEnd):
    """Fanfare: Mode: 1. Evolve this follower. 2. Evolve another random unevolved
    allied follower with Ward and give it +1/+1. Ward. At the end of your turn, if
    this follower is evolved, give all other followers -1/-1."""
    modes = (2, 1)

    def fanfare(self, ctx):
        if 0 in ctx.modes:
            _evolve_self(ctx)
        if 1 in ctx.modes:
            candidates = [f for f in ctx.me.followers if f is not ctx.source
                          and not f.evolved and f.has(Keyword.WARD)]
            for f in E.random_sample(ctx.state, candidates, 1):
                E.evolve(ctx.state, f)
                E.buff(ctx.state, f, 1, 1)

    def on_turn_end(self, ctx):
        # Confirmed by the player: like Lamretta (official Q&A), an evolution by an earlier
        # end-of-turn ability doesn't count.
        others = [f for f in ctx.state.field_order() if f.defn.is_follower and f is not ctx.source]
        for f in others:
            E.buff(ctx.state, f, -1, -1)


@register(KUKISHIRO.card_id)
class Kukishiro(CardScript):
    """Fanfare: gain Crest: Kukishiro, Mistbloom; return 2 random cards from your hand
    to the deck; draw 2 cards. Rush."""

    def fanfare(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, KUKISHIRO_CREST)
        _return_random_to_deck(ctx, 2)
        E.draw(ctx.state, ctx.controller, 2)


# --- Basic (10000) -------------------------------------------------------------------------

@register(SOULCURE_SISTER.card_id)
class SoulcureSister(CardScript):
    """Fanfare: restore 5 defense to your leader. Ward."""

    def fanfare(self, ctx):
        _heal(ctx, 5)


@register(WINGED_WARRIOR.card_id)
class WingedWarrior(CardScript):
    """Fanfare: select another allied follower and give it +1/+1. Evolve: replicate the
    Fanfare."""
    play_targets = common.OTHER_ALLIED_FOLLOWER
    evolve_targets = common.OTHER_ALLIED_FOLLOWER

    def fanfare(self, ctx):
        self._bless(ctx)

    def on_evolve(self, ctx):
        self._bless(ctx)

    def _bless(self, ctx):
        for f in ctx.chosen():
            E.buff(ctx.state, f, 1, 1)


@register(AVIAN_STATUE.card_id)
class AvianStatue(_AdvanceOnEngage):
    """Countdown (2). Last Words: summon a Regal Falcon. Engage (2): advance this
    amulet's count by 2."""
    engage_cost = 2

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, REGAL_FALCON)


@register(IRONFIST_PRIEST.card_id)
class IronfistPriest(CardScript):
    """Evolve: select an enemy follower with 3 defense or less and banish it.
    Super-Evolve: banish all enemy followers with 3 defense or less instead."""
    evolve_targets = SMALL_ENEMY

    def on_evolve(self, ctx):
        if ctx.super_:
            for f in [f for f in ctx.opponent.followers if f.life <= 3]:
                E.banish(ctx.state, f)
        else:
            _banish_chosen(ctx)


@register(SACRED_GRIFFON.card_id)
class SacredGriffon(CardScript):
    """Ward. Whenever you Engage an amulet, give this follower Storm."""

    def on_engage(self, ctx):
        E.give_keywords(ctx.source, Keyword.STORM)


@register(WINGED_STATUE.card_id)
class WingedStatue(_AdvanceOnEngage):
    """Countdown (4). Last Words: summon a Holy Falcon. Engage (1): advance this
    amulet's count by 1."""
    engage_cost = 1

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, HOLY_FALCON)


# --- set 10004 -----------------------------------------------------------------------------

@register(TROUE.card_id)
class Troue(CardScript):
    """Storm. Whenever you Engage an amulet, give this follower Drain."""

    def on_engage(self, ctx):
        E.give_keywords(ctx.source, Keyword.DRAIN)


@register(LAMRETTA.card_id)
class Lamretta(_IfEvolvedAtTurnEnd):
    """At the end of your turn, if this follower is evolved, deal 2 damage to all
    followers (not if it was evolved by an earlier end-of-turn ability, such as
    Galleon's: official Q&A). Evolve: give this follower "Can't attack followers or
    leaders" until the end of the turn."""

    def on_turn_end(self, ctx):
        everyone = [f for f in ctx.state.field_order() if f.defn.is_follower]
        E.damage(ctx.state, everyone, 2, ctx.source)

    def on_evolve(self, ctx):
        E.grant(ctx.source, CANT_ATTACK, until_turn=common.end_of_turn(ctx))


@register(AWED_AND_INSPIRED.card_id)
class AwedAndInspired(CardScript):
    """Engage (2): destroy this card; select an allied follower and transform it into
    an Awed and Inspired; draw a card."""
    engage_cost = 2
    engage_targets = common.ALLIED_FOLLOWER

    def engage(self, ctx):
        E.destroy(ctx.state, ctx.source)
        for f in ctx.chosen():
            E.transform(ctx.state, f, AWED_AND_INSPIRED)
        E.draw(ctx.state, ctx.controller)


@register(SARA.card_id)
class Sara(CardScript):
    """Enhance (6): give this follower +0/+10. Ward. Evolve: select a damaged enemy
    follower and destroy it."""
    enhance = (6,)
    evolve_targets = (TargetSpec(Target.ENEMY_FOLLOWER,
                                 filter=lambda state, player, c: c.life < c.max_life),)

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.buff(ctx.state, ctx.source, 0, 10)

    def on_evolve(self, ctx):
        _destroy_chosen(ctx)


@register(SOPHIA.card_id)
class Sophia(CardScript):
    """Fanfare: summon a random Havencraft follower costing 2 or less from your deck.
    Super-Evolve: give all other allied followers Barrier."""

    def fanfare(self, ctx):
        E.summon_from_deck(ctx.state, ctx.controller,
                           lambda c: c.defn.is_follower and c.defn.craft == Craft.HAVEN
                           and c.cost <= 2)

    def on_super_evolve(self, ctx):
        for f in ctx.me.followers:
            if f is not ctx.source:
                E.give_keywords(f, Keyword.BARRIER)


@register(SKYFARING_VESSEL.card_id)
class SkyfaringVessel(CardScript):
    """Activates in hand: whenever you Engage an amulet, reduce this card's cost by 1.
    Engage: destroy this card; select an unevolved allied follower and evolve it."""
    listen_in_hand = True
    engage_cost = 0
    engage_targets = (TargetSpec(Target.ALLIED_FOLLOWER,
                                 filter=lambda state, player, c: not c.evolved),)

    def on_engage(self, ctx):
        if _in_hand(ctx):
            E.add_cost(ctx.source, -1)

    def engage(self, ctx):
        E.destroy(ctx.state, ctx.source)
        for f in ctx.chosen():
            if not f.evolved:
                E.evolve(ctx.state, f)


@register(TIKOH.card_id)
class Tikoh(CardScript):
    """Whenever you Engage an amulet, restore 1 defense to your leader. Evolve: select
    an enemy follower and deal it 3 damage."""
    evolve_targets = ENEMY

    def on_engage(self, ctx):
        _heal(ctx, 1)

    def on_evolve(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 3, ctx.source)


@register(GLEAMING_GEMS.card_id)
class GleamingGems(CardScript):
    """Engage: destroy this card. Mode: 1. Destroy a random enemy follower. 2. Draw 2 cards."""
    engage_cost = 0
    engage_modes = (2, 1)

    def engage(self, ctx):
        E.destroy(ctx.state, ctx.source)
        if 0 in ctx.modes:
            for target in _random_enemies(ctx):
                E.destroy(ctx.state, target)
        if 1 in ctx.modes:
            E.draw(ctx.state, ctx.controller, 2)


@register(GALLEON.card_id)
class Galleon(CardScript):
    """Ward. Can't attack. At the end of your turn, if you've unlocked
    super-evolution, evolve a random unevolved allied follower that didn't attack
    this turn."""
    cant_attack = True

    def on_turn_end(self, ctx):
        if not E.super_evolution_unlocked(ctx.state, ctx.controller):
            return
        candidates = [f for f in ctx.me.followers if not f.evolved and f.attacks_made == 0]
        for f in E.random_sample(ctx.state, candidates, 1):
            E.evolve(ctx.state, f)


@register(VIRA.card_id)
class Vira(CardScript):
    """Fanfare: select 2 enemy followers and banish them. Super Skybound Art:
    super-evolve this follower. Ward. Can't take more than 3 damage at a time."""
    play_targets = (TargetSpec(Target.ENEMY_FOLLOWER, 2),)
    skybound = True
    damage_cap = 3

    def fanfare(self, ctx):
        _banish_chosen(ctx)
        if E.super_skybound_art(ctx) and not ctx.source.evolved:
            E.evolve(ctx.state, ctx.source, super_=True)
