"""Abysscraft cards and the cards they generate.

Card stats come from the pool table (svsim/cards/pool.py); this module holds
the abilities. Comments give the official Simplified Chinese names.
"""
from collections import Counter

from svsim.cards import common
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.enums import Craft, Keyword
from svsim.core.script import CardScript, Target, TargetSpec, register
from svsim.core.state import leader_of

DEPARTED = E.DEPARTED

SUZY_HAND_FOLLOWER = (TargetSpec(Target.HAND_CARD, filter=lambda s, p, c: c.defn.is_follower),)
TWO_ALLIED_FOLLOWERS = (TargetSpec(Target.ALLIED_FOLLOWER, 2),)

# --- tokens ---
SKELETON = card(90051110)  # 骸骨士兵 (vanilla)
BAT = card(90051120)  # 蝙蝠 (Drain only)
GHOST = card(90051130)  # 怨灵
ROTTING_ZOMBIE = card(90051140)  # 腐臭的僵尸
DEPTHS_OF_THE_ELD_SIGHT = card(90054330)  # 天眼深渊

# --- leader area / alternate forms ---
ISTYNDET_CREST = card(10954112)  # 纹章：伊斯坦戴德 对 玛尔奇盖特
RIGOR_CREST = card(10553312)  # 纹章：严酷的奥夜花
MILTEO_CREST = card(10554112)  # 纹章：充实的《恋人与节制》·米路缇欧&卢泽
VALIANT_EDGE_CREST = card(10451312)  # 纹章：妖异利刃
CORRUPTION_CREST = card(10453312)  # 纹章：堕落
BELIAL_CREST = card(10454122)  # 纹章：狡诈的堕天司·彼列
VOID_COLONEL_CRYSTALLIZE = card(10952112)  # 渊底上校（结晶）

# --- set 10009 ---
RUTHLESS_BLITZER = card(10951110)  # 强袭的特攻队长
NETHERWORLD_LIEUTENANT = card(10951120)  # 幽冥中尉
SPOOKY_SURPRISE = card(10951310)  # 恐怖惊遇
VOID_COLONEL = card(10952110)  # 渊底上校
SPARKLY_DEMONESS = card(10952120)  # 闪烁恶魔
CHAINS_OF_THE_PAST = card(10952310)  # 锁链相连
RAMPAGING_COMMANDER = card(10953110)  # 激烈的副总长
REAPERS_DUE = card(10953310)  # 驱逐死神
ISTYNDET_VS_MITILYKKET = card(10954110)  # 伊斯坦戴德 对 玛尔奇盖特
GARODETH_VS_ZETH = card(10954120)  # 伽罗塔德 对 泽特

# --- set 10008 ---
ANISAGE = card(10851110)  # 通透的信念·安瑟珠
LILITH_DEVILISH_CUTIE = card(10851120)  # 可爱恶魔·莉莉姆
LIMIL = card(10851130)  # 兔耳恶魔·莉蜜儿
FIOLE = card(10852110)  # 母爱恶魔·菲欧蕾
MARSHA = card(10852120)  # 黑暗骑士·玛莎
BITTERSWEET_DEPARTURES = card(10852310)  # 启程的退场
SUZY = card(10853110)  # 诚实的诅咒师·丝姬
EBB_AND_FLOW = card(10853310)  # 改变的流向
ITSURUGI_AND_TAKETSUMI = card(10854110)  # 出发的憧憬·苇剑&武津御
CERES = card(10854120)  # 日月的蔷薇·赛蕾丝

# --- set 10007 ---
LULUMI = card(10751110)  # 暗夜键盘手·露露米
RAZ = card(10751120)  # 恶魔鼓手·拉兹
SOUL_TUNING = card(10751310)  # 灵魂调律
HIGHWIRE_FELINE = card(10752110)  # 猫咪走绳师
JUGGLER_CORVID = card(10752120)  # 乌鸦杂耍师
HARMONY_OF_YOUTH = card(10752310)  # 讴歌青春
BEASTMASTER_BONES = card(10753110)  # 骸骨驯兽师
HARK_TO_THE_NIGHT_SONG = card(10753310)  # 夜之歌的演唱会
ADAHIME = card(10754110)  # 傍死的安纳提玛·徒姬
MACMILLAN = card(10754120)  # 死亡主持人·马克米朗

# --- set 10006 ---
REVERENT_DEMON = card(10651110)  # 渴望的恶魔
GHOST_DODGER = card(10651120)  # 逃避幽灵者
ADVENT_OF_THE_ELD_SIGHT = card(10651310)  # 天眼授予
YEARNFUL_NECROMANCER = card(10652110)  # 渴欲的唤灵师
DEVILISH_HEARTBREAKER = card(10652120)  # 失恋恶魔
ALLURE_OF_THE_MIGHTIEST = card(10652310)  # “最强”的诱惑
DEPRIVED_DESTROYER = card(10653110)  # 渴命的破坏者
DEPLETIVE_ELD_SIGHT = card(10653310)  # 枯渴的天眼
ARMES = card(10654110)  # 枯渴的魔神·阿尔弭斯
BIBATII = card(10654120)  # 古旧天眼·比芭提

# --- set 10005 ---
SUPPORT_WOLF = card(10551110)  # 鼓舞之狼
CRIMSON_SOULMANCER = card(10551120)  # 红符的魂魄道士
VALOR_OF_THE_NIGHTBLOSSOM = card(10551310)  # 奥夜花的开战
FICKLE_NECROMANCER = card(10552110)  # 制造麻烦的唤灵师
FRIENDLY_BLUE_OGRE = card(10552120)  # 牵线搭桥的青鬼
TYRANNICAL_FISTS = card(10552310)  # 残虐的炸裂
LIFESTEALER = card(10553110)  # 致命掠夺者
RIGOR_OF_THE_NIGHTBLOSSOM = card(10553310)  # 严酷的奥夜花
MILTEO_AND_LUZEN = card(10554110)  # 充实的《恋人与节制》·米路缇欧&卢泽
SHAKDOH = card(10554120)  # 奥夜花·释藤

# --- set 10000 (Basic) ---
MISTRESS_OF_THE_FANGED = card(10051110)  # 魔狼首领 (Storm, Bane only)
NIGHT_FIEND = card(10051120)  # 黑夜鬼人
DEVIOUS_LESSER_MUMMY = card(10051130)  # 恶毒的小木乃伊
CHAOS_CYCLONE = card(10051310)  # 混沌诅咒
LILITH_ENCHANTING_SUCCUBUS = card(10052110)  # 魅惑的魅魔·莉莉姆
AMOROUS_NECROMANCER = card(10052120)  # 多情的唤灵师
SOUL_PREDATION = card(10052310)  # 捕食灵魂

# --- set 10004 ---
ALMEIDA = card(10451110)  # 憧憬的铁锤·阿尔梅达
VASERAGA = card(10451120)  # 不屈利刃·巴萨拉卡
VALIANT_EDGE = card(10451310)  # 妖异利刃
NEZHA = card(10452110)  # 霸空武神·哪吒
SATYR = card(10452120)  # 爱的旅人·萨堤洛斯
BAAL = card(10452130)  # 元素共鸣·巴尔
NEHAN = card(10453110)  # 生与死之技·涅槃
CORRUPTION = card(10453310)  # 堕落
FEDIEL = card(10454110)  # 暗之法则·菲迪埃尔
BELIAL = card(10454120)  # 狡诈的堕天司·彼列

TOKENS = [SKELETON, BAT, GHOST, ROTTING_ZOMBIE, DEPTHS_OF_THE_ELD_SIGHT]
LEADER_AREA = [ISTYNDET_CREST, RIGOR_CREST, MILTEO_CREST, VALIANT_EDGE_CREST, CORRUPTION_CREST,
               BELIAL_CREST]
ALTERNATE_FORMS = [VOID_COLONEL_CRYSTALLIZE]
KEYWORD_ONLY = [MISTRESS_OF_THE_FANGED, SKELETON, BAT]   # no script needed
BLOCKED: list = []


# --- helpers -----------------------------------------------------------------------------

def hit_both_leaders(ctx, amount: int) -> None:
    """Deal damage to both leaders (turn player's first, so they lose a double KO)."""
    E.damage(ctx.state, E.leaders_turn_order(ctx.state), amount, ctx.source)


def hit_own_leader(ctx, amount: int) -> None:
    E.damage(ctx.state, [common.own_leader(ctx)], amount, ctx.source)


def hit_enemy_leader(ctx, amount: int) -> None:
    E.damage(ctx.state, [common.enemy_leader(ctx)], amount, ctx.source)


def random_enemy_follower(ctx) -> list:
    """A random enemy follower (random effects can hit Aura / Ambush followers)."""
    return E.random_sample(ctx.state, ctx.opponent.followers, 1)


def buff_each(state, followers, atk: int, life: int) -> None:
    """Give +X/+Y (or -X/-Y) to each follower still on the field (earlier ones may
    have died to an earlier -X/-Y of the same effect)."""
    for f in list(followers):
        if state.on_field(f.uid) is f:
            E.buff(state, f, atk, life)


def evolve_on_field(state, inst) -> None:
    """Evolve a follower by an effect, if it's still on the field and unevolved."""
    if inst is not None and not inst.evolved and state.on_field(inst.uid) is inst:
        E.evolve(state, inst)


def four_of_a_cost(player_state) -> bool:
    """"If you have at least 4 cards with the same cost in your hand"."""
    costs = Counter(c.cost for c in player_state.hand)
    return bool(costs) and max(costs.values()) >= 4


def is_departed(inst) -> bool:
    return inst.defn.is_follower and E.has_trait(inst, DEPARTED)


remove_last_words = E.remove_last_words
has_last_words = E.has_last_words


def in_hand(ctx) -> bool:
    return any(c is ctx.source for c in ctx.me.hand)


class CantAttack(CardScript):
    """Granted: "Can't attack followers or leaders"."""
    cant_attack = True


class AttackThreeTimes(CardScript):
    """Granted: "Can attack 3 times per turn"."""
    attacks_per_turn = 3


class SummonCopyLastWords(CardScript):
    """Granted by Reaper's Due: "Last Words: Summon a copy of this card"."""

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, ctx.source.defn)


CANT_ATTACK = CantAttack()
ATTACK_THREE_TIMES = AttackThreeTimes()
SUMMON_COPY_LAST_WORDS = SummonCopyLastWords()


# --- tokens ------------------------------------------------------------------------------

@register(GHOST.card_id)
class Ghost(CardScript):
    """Storm. When this card leaves the field, banish it. At the end of your turn,
    banish this card."""
    banish_on_leave = True

    def on_turn_end(self, ctx):
        E.banish(ctx.state, ctx.source)


@register(ROTTING_ZOMBIE.card_id)
class RottingZombie(CardScript):
    """Last Words: summon a Rotting Zombie and remove Last Words from it."""

    def last_words(self, ctx):
        zombie = E.summon(ctx.state, ctx.controller, ROTTING_ZOMBIE)
        if zombie:
            remove_last_words(zombie)


@register(DEPTHS_OF_THE_ELD_SIGHT.card_id)
class DepthsOfTheEldSight(CardScript):
    """Draw 2 cards."""

    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)


# --- leader area / alternate forms -------------------------------------------------------

@register(ISTYNDET_CREST.card_id)
class IstyndetCrest(CardScript):
    """At the end of your turn, if an allied card on the field has Last Words, destroy
    a random allied card with Last Words and a random enemy follower."""

    # UNSURE: if the random allied card can't be destroyed (e.g. "Can't be destroyed by
    # abilities"), is the enemy follower still destroyed? Implemented: yes, and such
    # cards stay among the random candidates.

    def on_turn_end(self, ctx):
        with_lw = [c for c in ctx.me.field if has_last_words(c)]
        if not with_lw:
            return
        for target in E.random_sample(ctx.state, with_lw, 1):
            E.destroy(ctx.state, target)
        for target in random_enemy_follower(ctx):
            E.destroy(ctx.state, target)


@register(RIGOR_CREST.card_id)
class RigorCrest(CardScript):
    """Countdown (2). At the end of your turn, draw a card; then, if you have at least
    4 cards with the same cost in hand, summon a Skeleton and give it Ward."""

    def on_turn_end(self, ctx):
        E.draw(ctx.state, ctx.controller)
        if four_of_a_cost(ctx.me):
            skeleton = E.summon(ctx.state, ctx.controller, SKELETON)
            if skeleton:
                E.give_keywords(skeleton, Keyword.WARD)


@register(MILTEO_CREST.card_id)
class MilteoCrest(CardScript):
    """Allied followers' Fanfare and Enhance abilities don't activate. Whenever you
    play a follower, evolve it."""
    suppresses_fanfare = True

    def on_play(self, ctx):
        played = ctx.other
        if played is not None and played.defn.is_follower and not ctx.as_spell:
            evolve_on_field(ctx.state, played)


@register(VALIANT_EDGE_CREST.card_id)
class ValiantEdgeCrest(CardScript):
    """Countdown (2). At the end of your turn, deal 2 damage to a random enemy
    follower and restore 1 defense to your leader."""

    def on_turn_end(self, ctx):
        E.damage(ctx.state, random_enemy_follower(ctx), 2, ctx.source)
        E.heal_leader(ctx.state, ctx.controller, 1)


@register(CORRUPTION_CREST.card_id)
class CorruptionCrest(CardScript):
    """Countdown (4). At the end of your turn, deal 2 damage to your leader."""

    def on_turn_end(self, ctx):
        hit_own_leader(ctx, 2)


@register(BELIAL_CREST.card_id)
class BelialCrest(CardScript):
    """Countdown (4). Last Words: deal 20 damage to the enemy leader."""

    def last_words(self, ctx):
        hit_enemy_leader(ctx, 20)


@register(VOID_COLONEL_CRYSTALLIZE.card_id)
class VoidColonelCrystallize(CardScript):
    """Crystallize (2): Countdown (4). Last Words: summon a Void Colonel."""

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, VOID_COLONEL)


# --- set 10009 ---------------------------------------------------------------------------

@register(RUTHLESS_BLITZER.card_id)
class RuthlessBlitzer(CardScript):
    """Fanfare: deal 2 damage to both leaders."""

    def fanfare(self, ctx):
        hit_both_leaders(ctx, 2)


@register(NETHERWORLD_LIEUTENANT.card_id)
class NetherworldLieutenant(CardScript):
    """Last Words: summon a Netherworld Lieutenant, give it +1/+0 and Rush, and remove
    Last Words from it."""

    def last_words(self, ctx):
        lieutenant = E.summon(ctx.state, ctx.controller, NETHERWORLD_LIEUTENANT)
        if lieutenant:
            E.buff(ctx.state, lieutenant, 1, 0)
            E.give_keywords(lieutenant, Keyword.RUSH)
            remove_last_words(lieutenant)


@register(SPOOKY_SURPRISE.card_id)
class SpookySurprise(CardScript):
    """Summon a Ghost and a Rotting Zombie."""

    def cast(self, ctx):
        E.summon(ctx.state, ctx.controller, GHOST)
        E.summon(ctx.state, ctx.controller, ROTTING_ZOMBIE)


@register(VOID_COLONEL.card_id)
class VoidColonel(CardScript):
    """Ward. Last Words: destroy a random enemy follower; restore 2 defense to your
    leader. Crystallize (2): see VoidColonelCrystallize."""

    def last_words(self, ctx):
        for target in random_enemy_follower(ctx):
            E.destroy(ctx.state, target)
        E.heal_leader(ctx.state, ctx.controller, 2)


@register(SPARKLY_DEMONESS.card_id)
class SparklyDemoness(CardScript):
    """Fanfare: select an enemy follower and destroy it. Deal 2 damage to the enemy leader."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        hit_enemy_leader(ctx, 2)


@register(CHAINS_OF_THE_PAST.card_id)
class ChainsOfThePast(CardScript):
    """Once (Enhance (4): twice): deal 3 damage to a random enemy follower and 1
    damage to both leaders."""
    enhance = (4,)

    def cast(self, ctx):
        for _ in range(2 if ctx.enhanced else 1):
            if ctx.state.winner is not None:
                return
            E.damage(ctx.state, random_enemy_follower(ctx), 3, ctx.source)
            hit_both_leaders(ctx, 1)


@register(RAMPAGING_COMMANDER.card_id)
class RampagingCommander(CardScript):
    """Fanfare: deal 3 damage to all enemy followers, then 3 damage to both leaders.
    Super-Evolve: draw 2 cards; deal 1 damage to both leaders."""

    def fanfare(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 3, ctx.source)
        hit_both_leaders(ctx, 3)

    def on_super_evolve(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)
        hit_both_leaders(ctx, 1)


@register(REAPERS_DUE.card_id)
class ReapersDue(CardScript):
    """Select an allied follower and give it "Last Words: summon a copy of this card"."""
    play_targets = common.ALLIED_FOLLOWER

    def cast(self, ctx):
        for target in ctx.chosen():
            E.grant(target, SUMMON_COPY_LAST_WORDS)


@register(ISTYNDET_VS_MITILYKKET.card_id)
class IstyndetVsMitilykket(CardScript):
    """Fanfare: Reanimate (2) three times, then deal 2 damage to all enemy followers.
    Super-Evolve: gain Crest: Istyndet vs. Mitilykket."""

    def fanfare(self, ctx):
        for _ in range(3):
            E.reanimate(ctx.state, ctx.controller, 2)
        E.damage(ctx.state, list(ctx.opponent.followers), 2, ctx.source)

    def on_super_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, ISTYNDET_CREST)


@register(GARODETH_VS_ZETH.card_id)
class GarodethVsZeth(CardScript):
    """Activates in hand: at the end of your turn, if your leader has 12 defense or
    less, reduce this card's cost by 1. Fanfare: Mode: 1. Gain Storm; deal 2 damage
    to your leader. 2. Gain Ward; deal 8 damage to all enemy followers."""
    listen_in_hand = True
    modes = (2, 1)

    def on_turn_end(self, ctx):
        if in_hand(ctx) and ctx.me.leader_hp <= 12:
            E.add_cost(ctx.source, -1)

    def fanfare(self, ctx):
        if 0 in ctx.modes:
            E.give_keywords(ctx.source, Keyword.STORM)
            hit_own_leader(ctx, 2)
        if 1 in ctx.modes:
            E.give_keywords(ctx.source, Keyword.WARD)
            E.damage(ctx.state, list(ctx.opponent.followers), 8, ctx.source)


# --- set 10008 ---------------------------------------------------------------------------
@register(ANISAGE.card_id)
class Anisage(CardScript):
    """Storm. Ignores Ward."""
    ignores_ward = True


@register(LILITH_DEVILISH_CUTIE.card_id)
class LilithDevilishCutie(CardScript):
    """Strike: deal 1 damage to both leaders. Last Words: add a Bat to your hand."""

    def strike(self, ctx):
        hit_both_leaders(ctx, 1)

    def last_words(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, BAT)


@register(LIMIL.card_id)
class Limil(CardScript):
    """Fanfare: if your leader has more defense than the enemy leader, summon 2 Bats.
    Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        self._bats(ctx)

    def on_evolve(self, ctx):
        self._bats(ctx)

    def _bats(self, ctx):
        if ctx.me.leader_hp > ctx.opponent.leader_hp:
            for _ in range(2):
                E.summon(ctx.state, ctx.controller, BAT)


@register(FIOLE.card_id)
class Fiole(CardScript):
    """Fanfare: summon 3 Bats. Whenever an allied Bat enters the field, give it Rush."""

    def fanfare(self, ctx):
        for _ in range(3):
            E.summon(ctx.state, ctx.controller, BAT)

    def on_ally_enter(self, ctx):
        if ctx.other.defn.name == BAT.name:
            E.give_keywords(ctx.other, Keyword.RUSH)


@register(MARSHA.card_id)
class Marsha(CardScript):
    """Fanfare: deal 1 damage to all enemy followers and both leaders. Evolve:
    replicate the Fanfare."""

    def fanfare(self, ctx):
        self._sweep(ctx)

    def on_evolve(self, ctx):
        self._sweep(ctx)

    def _sweep(self, ctx):
        targets = list(ctx.opponent.followers) + E.leaders_turn_order(ctx.state)
        E.damage(ctx.state, targets, 1, ctx.source)


@register(BITTERSWEET_DEPARTURES.card_id)
class BittersweetDepartures(CardScript):
    """Mode (pick 2): 1. Deal 1 damage to the enemy leader. 2. Restore 2 defense to
    your leader. 3. Deal 3 damage to a random enemy follower. 4. Gain 4 shadows."""
    modes = (4, 2)

    def cast(self, ctx):
        if 0 in ctx.modes:
            hit_enemy_leader(ctx, 1)
        if 1 in ctx.modes:
            E.heal_leader(ctx.state, ctx.controller, 2)
        if 2 in ctx.modes:
            E.damage(ctx.state, random_enemy_follower(ctx), 3, ctx.source)
        if 3 in ctx.modes:
            ctx.me.shadows += 4


@register(SUZY.card_id)
class Suzy(CardScript):
    """Fanfare: select an enemy follower and give it -0/-3. Evolve: select a follower
    in your hand and give it +3/+0."""
    play_targets = common.ENEMY_FOLLOWER
    evolve_targets = SUZY_HAND_FOLLOWER

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.buff(ctx.state, target, 0, -3)

    def on_evolve(self, ctx):
        for target in ctx.chosen_hand():
            E.buff(ctx.state, target, 3, 0)


@register(EBB_AND_FLOW.card_id)
class EbbAndFlow(CardScript):
    """Select a card in your hand and return it to your deck. Draw 2 cards. If you've
    unlocked super-evolution, reduce their costs by 1."""
    play_targets = common.HAND_CARD

    def cast(self, ctx):
        for c in ctx.chosen_hand():
            E.return_to_deck(ctx.state, c)
        drawn = E.draw(ctx.state, ctx.controller, 2)
        if E.super_evolution_unlocked(ctx.state, ctx.controller):
            for c in drawn:
                E.add_cost(c, -1)


@register(ITSURUGI_AND_TAKETSUMI.card_id)
class ItsurugiAndTaketsumi(CardScript):
    """Fanfare: Mode: 1. Deal 4 damage to the enemy leader; restore 4 defense to your
    leader. 2. Deal 5 damage to all enemy followers; recover 1 evolution point.
    Evolve: Mode: 1. Draw 2 cards. 2. Recover 2 play points."""
    modes = (2, 1)
    evolve_modes = (2, 1)

    def fanfare(self, ctx):
        if 0 in ctx.modes:
            hit_enemy_leader(ctx, 4)
            E.heal_leader(ctx.state, ctx.controller, 4)
        if 1 in ctx.modes:
            E.damage(ctx.state, list(ctx.opponent.followers), 5, ctx.source)
            E.recover_ep(ctx.state, ctx.controller, 1)

    def on_evolve(self, ctx):
        if 0 in ctx.modes:
            E.draw(ctx.state, ctx.controller, 2)
        if 1 in ctx.modes:
            E.recover_pp(ctx.state, ctx.controller, 2)


@register(CERES.card_id)
class Ceres(CardScript):
    """Fanfare: Necromancy (20) - reduce the cost of all Abysscraft cards in your hand
    by 2. Clash: deal 4 damage to the opposing follower. At the end of your turn,
    restore 4 defense to your leader."""

    def fanfare(self, ctx):
        if E.necromancy(ctx.state, ctx.controller, 20):
            for c in list(ctx.me.hand):
                if c.defn.craft == Craft.ABYSS:
                    E.add_cost(c, -2)

    def clash(self, ctx):
        E.damage(ctx.state, [ctx.other], 4, ctx.source)

    def on_turn_end(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 4)


# --- set 10007 ---------------------------------------------------------------------------

@register(LULUMI.card_id)
class Lulumi(CardScript):
    """Rush. Last Words: add a Bat to your hand."""

    def last_words(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, BAT)


@register(RAZ.card_id)
class Raz(CardScript):
    """Last Words: summon a Skeleton. Evolve: select an enemy follower and deal it 3 damage."""
    evolve_targets = common.ENEMY_FOLLOWER

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, SKELETON)

    def on_evolve(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 3, ctx.source)


@register(SOUL_TUNING.card_id)
class SoulTuning(CardScript):
    """Select 2 allied followers and give them +0/+1. Draw a card."""
    play_targets = TWO_ALLIED_FOLLOWERS

    def cast(self, ctx):
        for target in ctx.chosen():
            E.buff(ctx.state, target, 0, 1)
        E.draw(ctx.state, ctx.controller)


@register(HIGHWIRE_FELINE.card_id)
class HighwireFeline(CardScript):
    """Fanfare: select an enemy follower and deal it 3 damage; summon a Skeleton.
    Evolve: replicate the Fanfare."""
    play_targets = common.ENEMY_FOLLOWER
    evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        self._act(ctx)

    def on_evolve(self, ctx):
        self._act(ctx)

    def _act(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 3, ctx.source)
        E.summon(ctx.state, ctx.controller, SKELETON)


@register(JUGGLER_CORVID.card_id)
class JugglerCorvid(CardScript):
    """Fanfare: select an enemy follower and destroy it. Reanimate (2)."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        E.reanimate(ctx.state, ctx.controller, 2)


@register(HARMONY_OF_YOUTH.card_id)
class HarmonyOfYouth(CardScript):
    """Summon a Ghost, a Bat, and a Skeleton, and evolve them."""

    def cast(self, ctx):
        summoned = [E.summon(ctx.state, ctx.controller, token) for token in (GHOST, BAT, SKELETON)]
        for inst in summoned:
            evolve_on_field(ctx.state, inst)


@register(BEASTMASTER_BONES.card_id)
class BeastmasterBones(CardScript):
    """Fanfare: summon a Rotting Zombie and a Skeleton. Whenever an allied Departed
    follower enters the field, give it Storm. Super-Evolve: select another allied
    follower; if you did, destroy it and a random enemy follower."""
    super_evolve_targets = common.OTHER_ALLIED_FOLLOWER

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, ROTTING_ZOMBIE)
        E.summon(ctx.state, ctx.controller, SKELETON)

    def on_ally_enter(self, ctx):
        if is_departed(ctx.other):
            E.give_keywords(ctx.other, Keyword.STORM)

    def on_super_evolve(self, ctx):
        chosen = ctx.chosen()
        if not chosen:
            return
        for target in chosen:
            E.destroy(ctx.state, target)
        for target in random_enemy_follower(ctx):
            E.destroy(ctx.state, target)


@register(HARK_TO_THE_NIGHT_SONG.card_id)
class HarkToTheNightSong(CardScript):
    """Deal 6 damage split between all enemy followers. Necromancy (6) - deal 2 damage
    to the enemy leader."""

    def cast(self, ctx):
        E.split_damage(ctx.state, 1 - ctx.controller, 6, ctx.source)
        if E.necromancy(ctx.state, ctx.controller, 6):
            hit_enemy_leader(ctx, 2)


@register(ADAHIME.card_id)
class Adahime(CardScript):
    """Fanfare: summon 2 random differently named Abysscraft followers costing 2 or
    less from your deck. Whenever another allied Abysscraft follower enters the field,
    give it Rush. Super-Evolve: give all other allied Abysscraft followers +2/+2."""

    def fanfare(self, ctx):
        E.summon_from_deck(ctx.state, ctx.controller,
                           lambda c: c.defn.is_follower and c.defn.craft == Craft.ABYSS
                           and c.cost <= 2, k=2, distinct_names=True)

    def on_ally_enter(self, ctx):
        if ctx.other.defn.craft == Craft.ABYSS:
            E.give_keywords(ctx.other, Keyword.RUSH)

    def on_super_evolve(self, ctx):
        buff_each(ctx.state, [f for f in ctx.me.followers
                              if f is not ctx.source and f.defn.craft == Craft.ABYSS], 2, 2)


@register(MACMILLAN.card_id)
class Macmillan(CardScript):
    """Fanfare: Necromancy (10) - summon 3 Rotting Zombies. During your turn, whenever
    an allied Departed follower enters the field, give it +1/+0, Rush, and Ward and
    deal 1 damage to the enemy leader."""

    def fanfare(self, ctx):
        if E.necromancy(ctx.state, ctx.controller, 10):
            for _ in range(3):
                E.summon(ctx.state, ctx.controller, ROTTING_ZOMBIE)

    def on_ally_enter(self, ctx):
        if common.during_your_turn(ctx) and is_departed(ctx.other):
            E.buff(ctx.state, ctx.other, 1, 0)
            E.give_keywords(ctx.other, Keyword.RUSH | Keyword.WARD)
            hit_enemy_leader(ctx, 1)


# --- set 10006 ---------------------------------------------------------------------------

@register(REVERENT_DEMON.card_id)
class ReverentDemon(CardScript):
    """Last Words: draw a card; deal 1 damage to your leader."""

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller)
        hit_own_leader(ctx, 1)


@register(GHOST_DODGER.card_id)
class GhostDodger(CardScript):
    """Rush. Last Words: add a Ghost to your hand."""

    def last_words(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, GHOST)


@register(ADVENT_OF_THE_ELD_SIGHT.card_id)
class AdventOfTheEldSight(CardScript):
    """Draw 2 cards. Necromancy (4) - restore 2 defense to your leader."""

    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)
        if E.necromancy(ctx.state, ctx.controller, 4):
            E.heal_leader(ctx.state, ctx.controller, 2)


@register(YEARNFUL_NECROMANCER.card_id)
class YearnfulNecromancer(CardScript):
    """Enhance (8): Reanimate (9). Ward."""
    enhance = (8,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.reanimate(ctx.state, ctx.controller, 9)


@register(DEVILISH_HEARTBREAKER.card_id)
class DevilishHeartbreaker(CardScript):
    """Enhance (7): gain Storm. Evolve: select an enemy follower and deal it 4 damage."""
    enhance = (7,)
    evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.give_keywords(ctx.source, Keyword.STORM)

    def on_evolve(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4, ctx.source)


@register(ALLURE_OF_THE_MIGHTIEST.card_id)
class AllureOfTheMightiest(CardScript):
    """Select an enemy follower, banish it, and summon an exact copy of it (on your side)."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        for target in ctx.chosen():
            E.banish(ctx.state, target)
            E.summon_copy(ctx.state, ctx.controller, target)


@register(DEPRIVED_DESTROYER.card_id)
class DeprivedDestroyer(CardScript):
    """Fanfare: select another allied follower; if you did, destroy it and evolve this
    follower. When this follower evolves, summon a Bat and evolve it."""
    play_targets = common.OTHER_ALLIED_FOLLOWER

    def fanfare(self, ctx):
        chosen = ctx.chosen()
        if not chosen:
            return
        for target in chosen:
            E.destroy(ctx.state, target)
        evolve_on_field(ctx.state, ctx.source)

    def on_evolved(self, ctx):
        evolve_on_field(ctx.state, E.summon(ctx.state, ctx.controller, BAT))


@register(DEPLETIVE_ELD_SIGHT.card_id)
class DepletiveEldSight(CardScript):
    """Mode: 1. Recover 1 evolution point. 2. Deal 2 damage to all enemy followers."""
    modes = (2, 1)

    def cast(self, ctx):
        if 0 in ctx.modes:
            E.recover_ep(ctx.state, ctx.controller, 1)
        if 1 in ctx.modes:
            E.damage(ctx.state, list(ctx.opponent.followers), 2, ctx.source)


@register(ARMES.card_id)
class Armes(CardScript):
    """Aura. Can't be destroyed by abilities. Clash: destroy the opposing follower.
    Super-Evolve: gain "Can attack 3 times per turn"."""
    indestructible = True

    def clash(self, ctx):
        E.destroy(ctx.state, ctx.other)

    def on_super_evolve(self, ctx):
        E.grant(ctx.source, ATTACK_THREE_TIMES)


@register(BIBATII.card_id)
class Bibatii(CardScript):
    """Fanfare: Necromancy (4) - evolve this follower. When this follower evolves, add
    a Depths of the Eld Sight to your hand."""

    def fanfare(self, ctx):
        if E.necromancy(ctx.state, ctx.controller, 4):
            evolve_on_field(ctx.state, ctx.source)

    def on_evolved(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, DEPTHS_OF_THE_ELD_SIGHT)


# --- set 10005 ---------------------------------------------------------------------------

@register(SUPPORT_WOLF.card_id)
class SupportWolf(CardScript):
    """Enhance (6): gain +0/+6, Bane, and Barrier. Rush."""
    enhance = (6,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.buff(ctx.state, ctx.source, 0, 6)
            E.give_keywords(ctx.source, Keyword.BANE | Keyword.BARRIER)


@register(CRIMSON_SOULMANCER.card_id)
class CrimsonSoulmancer(CardScript):
    """Fanfare: Reanimate (2). Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        E.reanimate(ctx.state, ctx.controller, 2)

    def on_evolve(self, ctx):
        E.reanimate(ctx.state, ctx.controller, 2)


@register(VALOR_OF_THE_NIGHTBLOSSOM.card_id)
class ValorOfTheNightblossom(CardScript):
    """Select an enemy follower and deal it 5 damage. Add a Valor of the Nightblossom
    to your deck."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 5, ctx.source)
        E.put_into_deck(ctx.state, ctx.controller, VALOR_OF_THE_NIGHTBLOSSOM)


@register(FICKLE_NECROMANCER.card_id)
class FickleNecromancer(CardScript):
    """Fanfare: summon a Ghost and a Skeleton. Evolve: summon a Rotting Zombie."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, GHOST)
        E.summon(ctx.state, ctx.controller, SKELETON)

    def on_evolve(self, ctx):
        E.summon(ctx.state, ctx.controller, ROTTING_ZOMBIE)


@register(FRIENDLY_BLUE_OGRE.card_id)
class FriendlyBlueOgre(CardScript):
    """Fanfare: select an enemy follower and give it "Can't attack followers or leaders"
    until the end of your opponent's turn. Draw a card. Evolve: replicate the Fanfare."""
    play_targets = common.ENEMY_FOLLOWER
    evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        self._act(ctx)

    def on_evolve(self, ctx):
        self._act(ctx)

    def _act(self, ctx):
        for target in ctx.chosen():
            E.grant(target, CANT_ATTACK, until_turn=common.end_of_opponents_turn(ctx))
        E.draw(ctx.state, ctx.controller)


@register(TYRANNICAL_FISTS.card_id)
class TyrannicalFists(CardScript):
    """Deal 3 damage to every leader with the lowest defense (both on a tie: Q&A)."""

    def cast(self, ctx):
        state = ctx.state
        lowest = min(p.leader_hp for p in state.players)
        targets = [uid for uid in E.leaders_turn_order(state)
                   if state.players[leader_of(uid)].leader_hp == lowest]
        E.damage(state, targets, 3, ctx.source)


@register(LIFESTEALER.card_id)
class Lifestealer(CardScript):
    """Fanfare: transform all other followers into Skeletons. Whenever a Skeleton is
    destroyed, restore 1 defense to your leader. Evolve: deal 1 damage to all other
    followers."""

    def fanfare(self, ctx):
        for f in self._others(ctx):
            E.transform(ctx.state, f, SKELETON)

    def on_card_destroyed(self, ctx):
        if ctx.other.defn.card_id == SKELETON.card_id:
            E.heal_leader(ctx.state, ctx.controller, 1)

    def on_evolve(self, ctx):
        E.damage(ctx.state, self._others(ctx), 1, ctx.source)

    def _others(self, ctx):
        return [f for f in ctx.state.field_order() if f.defn.is_follower and f is not ctx.source]


@register(RIGOR_OF_THE_NIGHTBLOSSOM.card_id)
class RigorOfTheNightblossom(CardScript):
    """Gain Crest: Rigor of the Nightblossom."""

    def cast(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, RIGOR_CREST)


@register(MILTEO_AND_LUZEN.card_id)
class MilteoAndLuzen(CardScript):
    """Fanfare: Reanimate (4) and Reanimate (2). When this follower evolves, destroy 6
    other random followers. When it super-evolves, gain Crest: Milteo & Luzen."""

    def fanfare(self, ctx):
        E.reanimate(ctx.state, ctx.controller, 4)
        E.reanimate(ctx.state, ctx.controller, 2)

    def on_evolved(self, ctx):
        others = [f for f in ctx.state.field_order() if f.defn.is_follower and f is not ctx.source]
        for target in E.random_sample(ctx.state, others, 6):
            E.destroy(ctx.state, target)
        if ctx.super_:
            E.add_to_leader_area(ctx.state, ctx.controller, MILTEO_CREST)


@register(SHAKDOH.card_id)
class Shakdoh(CardScript):
    """Fanfare: twice: "Return your hand to your deck and draw that many cards; then,
    if you have at least 4 cards with the same cost in hand, deal 4 damage to all
    enemies." Super-Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        self._shuffle_twice(ctx)

    def on_super_evolve(self, ctx):
        self._shuffle_twice(ctx)

    def _shuffle_twice(self, ctx):
        for _ in range(2):
            if ctx.state.winner is not None:
                return
            hand = list(ctx.me.hand)
            for c in hand:
                E.return_to_deck(ctx.state, c)
            E.draw(ctx.state, ctx.controller, len(hand))
            if four_of_a_cost(ctx.me):
                E.damage(ctx.state, list(ctx.opponent.followers) + [common.enemy_leader(ctx)], 4,
                         ctx.source)


# --- set 10000 (Basic) -------------------------------------------------------------------
# Mistress of the Fanged (Storm, Bane) needs no script.

@register(NIGHT_FIEND.card_id)
class NightFiend(CardScript):
    """Fanfare: deal 1 damage to your leader."""

    def fanfare(self, ctx):
        hit_own_leader(ctx, 1)


@register(DEVIOUS_LESSER_MUMMY.card_id)
class DeviousLesserMummy(CardScript):
    """Fanfare: Necromancy (4) - gain Storm."""

    def fanfare(self, ctx):
        if E.necromancy(ctx.state, ctx.controller, 4):
            E.give_keywords(ctx.source, Keyword.STORM)


@register(CHAOS_CYCLONE.card_id)
class ChaosCyclone(CardScript):
    """Mode: 1. Draw a follower. 2. Reanimate (2) (selectable even with nothing to
    reanimate: Q&A)."""
    modes = (2, 1)

    def cast(self, ctx):
        if 0 in ctx.modes:
            E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.is_follower)
        if 1 in ctx.modes:
            E.reanimate(ctx.state, ctx.controller, 2)


@register(LILITH_ENCHANTING_SUCCUBUS.card_id)
class LilithEnchantingSuccubus(CardScript):
    """Last Words: add a Bat to your hand."""

    def last_words(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, BAT)


@register(AMOROUS_NECROMANCER.card_id)
class AmorousNecromancer(CardScript):
    """Evolve: summon 2 Ghosts. Super-Evolve: give them Drain."""

    def on_evolve(self, ctx):
        ghosts = [E.summon(ctx.state, ctx.controller, GHOST) for _ in range(2)]
        E.counters(ctx.source)["ghosts"] = [g.uid for g in ghosts if g is not None]

    def on_super_evolve(self, ctx):
        for uid in E.counters(ctx.source).pop("ghosts", []):
            ghost = ctx.state.on_field(uid)
            if ghost is not None:
                E.give_keywords(ghost, Keyword.DRAIN)


@register(SOUL_PREDATION.card_id)
class SoulPredation(CardScript):
    """Select an allied follower and destroy it. Draw 2 cards (even if it survives: Q&A)."""
    play_targets = common.ALLIED_FOLLOWER

    def cast(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        E.draw(ctx.state, ctx.controller, 2)


# --- set 10004 ---------------------------------------------------------------------------

@register(ALMEIDA.card_id)
class Almeida(CardScript):
    """Enhance (4): evolve this follower and give it +1/+1. Rush."""
    enhance = (4,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            evolve_on_field(ctx.state, ctx.source)
            E.buff(ctx.state, ctx.source, 1, 1)


@register(VASERAGA.card_id)
class Vaseraga(CardScript):
    """Intimidate. Last Words: summon a Vaseraga, Unyielding Scythe; deal 2 damage to
    your leader."""

    def last_words(self, ctx):
        E.summon(ctx.state, ctx.controller, VASERAGA)
        hit_own_leader(ctx, 2)


@register(VALIANT_EDGE.card_id)
class ValiantEdge(CardScript):
    """Deal 2 damage to your leader. Gain Crest: Valiant Edge."""

    def cast(self, ctx):
        hit_own_leader(ctx, 2)
        E.add_to_leader_area(ctx.state, ctx.controller, VALIANT_EDGE_CREST)


@register(NEZHA.card_id)
class Nezha(CardScript):
    """Rush. At the end of your turn, deal 4 damage to a random enemy follower, then 2
    damage to a random enemy follower."""

    def on_turn_end(self, ctx):
        E.damage(ctx.state, random_enemy_follower(ctx), 4, ctx.source)
        E.damage(ctx.state, random_enemy_follower(ctx), 2, ctx.source)


@register(SATYR.card_id)
class Satyr(CardScript):
    """Fanfare: if there's an evolved allied follower on the field, evolve this
    follower. Aura."""

    def fanfare(self, ctx):
        if any(f.evolved for f in ctx.me.followers if f is not ctx.source):
            evolve_on_field(ctx.state, ctx.source)


@register(BAAL.card_id)
class Baal(CardScript):
    """Fanfare: Mode: 1. Give this follower and another random allied follower +1/+1.
    2. Deal 3 damage to a random enemy follower."""
    modes = (2, 1)

    def fanfare(self, ctx):
        if 0 in ctx.modes:
            others = [f for f in ctx.me.followers if f is not ctx.source]
            buff_each(ctx.state, E.random_sample(ctx.state, others, 1) + [ctx.source], 1, 1)
        if 1 in ctx.modes:
            E.damage(ctx.state, random_enemy_follower(ctx), 3, ctx.source)


@register(NEHAN.card_id)
class Nehan(CardScript):
    """Fanfare: evolve all unevolved allied followers (this one too); deal 2 damage to
    your leader. Drain."""

    def fanfare(self, ctx):
        for f in [f for f in ctx.me.followers if not f.evolved]:
            evolve_on_field(ctx.state, f)
        hit_own_leader(ctx, 2)


@register(CORRUPTION.card_id)
class Corruption(CardScript):
    """Give all followers -2/-2. Give both players Crest: Corruption. Super Skybound
    Art - destroy your Crest: Corruption."""
    skybound = True

    def cast(self, ctx):
        buff_each(ctx.state, [f for f in ctx.state.field_order() if f.defn.is_follower], -2, -2)
        E.add_to_leader_area(ctx.state, ctx.controller, CORRUPTION_CREST)
        E.add_to_leader_area(ctx.state, 1 - ctx.controller, CORRUPTION_CREST)
        if E.super_skybound_art(ctx):
            crest = E.leader_area_card(ctx.state, ctx.controller, CORRUPTION_CREST)
            if crest is not None:
                E.destroy(ctx.state, crest)


@register(FEDIEL.card_id)
class Fediel(CardScript):
    """Fanfare: Necromancy (6) - Reanimate (2) and Reanimate (1), and evolve them. At
    the end of your turn, give all enemy followers -2/-2."""

    def fanfare(self, ctx):
        if E.necromancy(ctx.state, ctx.controller, 6):
            revived = [E.reanimate(ctx.state, ctx.controller, 2),
                       E.reanimate(ctx.state, ctx.controller, 1)]
            for inst in revived:
                evolve_on_field(ctx.state, inst)

    def on_turn_end(self, ctx):
        buff_each(ctx.state, ctx.opponent.followers, -2, -2)


@register(BELIAL.card_id)
class Belial(CardScript):
    """Fanfare: deal 10 damage to all other followers. Super Skybound Art - gain Crest:
    Belial. Super-Evolve: advance your Crest: Belial's count by 1."""
    skybound = True

    def fanfare(self, ctx):
        others = [f for f in ctx.state.field_order() if f.defn.is_follower and f is not ctx.source]
        E.damage(ctx.state, others, 10, ctx.source)
        if E.super_skybound_art(ctx):
            E.add_to_leader_area(ctx.state, ctx.controller, BELIAL_CREST)

    def on_super_evolve(self, ctx):
        crest = E.leader_area_card(ctx.state, ctx.controller, BELIAL_CREST)
        if crest is not None:
            E.advance_countdown(ctx.state, crest, 1)
