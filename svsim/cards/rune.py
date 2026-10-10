"""Runecraft cards and the cards they generate.

Card stats come from the pool table (svsim/cards/pool.py); this module holds
the abilities. Comments give the official Simplified Chinese names.
"""
from svsim.cards import common
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.enums import Keyword
from svsim.core.script import CardScript, Target, TargetSpec, prop, register, scripts_of

MYSTERIA = "Mysteria"
GOLEM = "Golem"

# --- generated cards ---
CLAY_GOLEM = card(90031110)  # 泥尘巨像
GUARDIAN_GOLEM = card(90031120)  # 守护者巨像
MAGIC_SEDIMENT = card(90031210)  # 大地之魔片
MYSTERIAN_MISSILE = card(90031310)  # 玛纳利亚魔弹
ARS_MAGNA = card(90034320)  # 伟大之术
DEPTHS_OF_THE_ELD_CRYSTALS = card(90034330)  # 天晶深渊
DELTA_CANNON = card(90034340)  # 苍奏之四
SEND_EM_PACKING = card(90034350)  # 宏大的回归
CARAVAN_MAMMOTH = card(10002120)  # 商队猛犸象 (Neutral; no abilities)
REGAL_FALCON = card(90061130)  # 壮丽大神隼 (Havencraft token; Storm only)

# --- leader area ---
ELMOTT_CREST = card(10433112)  # 纹章：缅怀之火·埃尔默特
CAGLIOSTRO_CREST = card(10434122)  # 纹章：天才美少女炼金术士·卡莉奥丝特罗
INSOMNIAC_WITCH_CREST = card(10532112)  # 纹章：失眠女巫
LHYNKAL_CREST = card(10534112)  # 纹章：漫步的《愚者》·琳库露
SHYMM_CREST = card(10634112)  # 纹章：魔恋的爱慕·希姆
ELD_CRYSTALS_FAITH = card(10634122)  # 信仰：天晶深渊
LILANTHIM_CREST = card(10734112)  # 纹章：万食的安纳提玛·拉拉安瑟姆
TICO_CREST = card(10833112)  # 纹章：玛纳利亚文书官·琪可
SEPHIE_CREST = card(10934112)  # 纹章：万术的罪人·赛菲

# --- set 9 ---
OBSESSED_TEST_SUBJECT = card(10931110)  # 沉溺的实验体
KEY_SPIRIT = card(10931120)  # 钥灵
MISCALCULATED_EXPERIMENT = card(10931310)  # 过度反应
ENAMORED_RESEARCHER = card(10932110)  # 心醉的研究者
NOBLE_PHILOSOPHER = card(10932120)  # 高洁哲学家
HUMANE_LOVE = card(10932310)  # 人性的爱
ECSTATIC_SCHOLAR = card(10933110)  # 陶醉的才女
OBSIDIAN_RAVEN = card(10933310)  # 乌涅
SEPHIE = card(10934110)  # 万术的罪人·赛菲
PHYLENE = card(10934120)  # 破式的变貌·菲绫

# --- set 8 ---
MEOWSKERS = card(10831110)  # 森绿的恩惠·喵鲁&圆滚滚2号&吉娜
POPPY = card(10831120)  # 玛纳利亚书记官·波比
STORMY_BLAST_REPRINT = card(10831310)  # 暴风破 (set 8 reprint)
SAMMY_AND_MARIE = card(10832110)  # 快乐绽花·萨米&玛莉
HARMONIOUS_MEAL = card(10832310)  # 其乐融融的团聚
EARTH_SHATTERING_BOLT = card(10832320)  # 伏地雷击
TICO = card(10833110)  # 玛纳利亚文书官·琪可
AMETHYSTS_NAPTIME = card(10833310)  # 钢铁的小憩
TETRA_AND_LADICA = card(10834110)  # 恩爱的大地·坦忒拉&拉缇卡
GINGER = card(10834120)  # 灾难言灵·洋荷

# --- set 7 ---
DAINTY_HORROR = card(10731110)  # 小巧捕食者
LITTLE_BEASTIE = card(10731120)  # 小型怪兽
HEEL_MY_DEARIE = card(10731310)  # 召唤仆从
CHARMING_MONSTER = card(10732110)  # 迷人怪兽
PRETTY_PREDATOR = card(10732120)  # 甜蜜猎食者
HAPHAZARD_SNACKING = card(10732310)  # 暴食的零嘴
SWEET_ABOMINATION = card(10733110)  # 甜美存在
BOTTOMLESS_GLUTTONY = card(10733310)  # 饕餮魔咒
LILANTHIM = card(10734110)  # 万食的安纳提玛·拉拉安瑟姆
BELOVED_MASTERPIECE = card(10734120)  # 可爱杰作

# --- set 6 ---
CRYSTALSPAWN = card(10631110)  # 天晶魔手 (Rush only: no script)
DAYDREAM_LIBRARIAN = card(10631120)  # 空想的图书管理员
ADVENT_OF_THE_ELD_CRYSTALS = card(10631310)  # 天晶授予
ENRAPTURED_STUDENT = card(10632110)  # 魔境的学生
ADVENTUROUS_GRIMOIRE = card(10632120)  # 冒险魔导书
REAVED_ORDER = card(10632310)  # 正常的侵蚀
SPELLBOUND_PROFESSOR = card(10633110)  # 魔醉的教师
BEWITCHING_ELD_CRYSTALS = card(10633310)  # 魔恋的天晶
SHYMM = card(10634110)  # 魔恋的爱慕·希姆
CALGE_DANTHLA = card(10634120)  # 古旧天晶·卡卢基典瑟拉

# --- set 5 ---
TERRAFORMING_WIZARD = card(10531110)  # 创造魔法师
WATERBENDING_CHARMWIELDER = card(10531120)  # 流动控符师
METAMORPHOSIS_OF_THE_DAWNBLOSSOM = card(10531310)  # 明越花的转变
INSOMNIAC_WITCH = card(10532110)  # 失眠女巫
WOODSONG_HAIKUMASTER = card(10532120)  # 余韵俳谐师
KITTY_CUNNING = card(10532310)  # 魔猫戏法
EMPEROR_OF_ELEMENTS = card(10533110)  # 元素支配者
GRANDEUR_OF_THE_DAWNBLOSSOM = card(10533310)  # 壮美的明越花
LHYNKAL = card(10534110)  # 漫步的《愚者》·琳库露
ARA = card(10534120)  # 明越花·阿罗

# --- set 4 ---
PHILOSOPHIA = card(10431110)  # 不可思议的哲学家·菲拉索佩娅
SUFRAMARE = card(10431120)  # 流浪的家庭教师·斯芙拉玛尔
RUNE_PORTAL = card(10431310)  # 符文秘术
EZECRAIN = card(10432110)  # 报仇的占卜师·艾塞克莱因
MIREILLE_AND_RISETTE = card(10432120)  # 荆棘旅途·米蕾耶&莉赛特
UNLEASHED = card(10432310)  # 能量外溢
ELMOTT = card(10433110)  # 缅怀之火·埃尔默特
ALCHEMIC_FLARE = card(10433310)  # 炼金炎爆
WAMDUS = card(10434110)  # 水之法则·瓦姆杜斯
CAGLIOSTRO = card(10434120)  # 天才美少女炼金术士·卡莉奥丝特罗

# --- set 1 ---
STORMY_BLAST = card(10131320)  # 暴风破

# --- Basic ---
DAZZLING_RUNEKNIGHT = card(10031110)  # 闪光魔法剑士
WITCHS_NEW_BREW = card(10031210)  # 魔女的炼金炉
FORESIGHT = card(10031310)  # 智慧光辉
TRUTH_SUMMONS = card(10031320)  # 召唤真理
REMI_AND_RAMI = card(10032110)  # 双面魔女·蕾米拉米
BLAZE_DESTROYER = card(10032120)  # 魔焰毁灭者
ARCANE_ERUPTION = card(10032310)  # 魔爆

CARDS = [OBSESSED_TEST_SUBJECT, KEY_SPIRIT, MISCALCULATED_EXPERIMENT, ENAMORED_RESEARCHER,
         NOBLE_PHILOSOPHER, HUMANE_LOVE, ECSTATIC_SCHOLAR, OBSIDIAN_RAVEN, SEPHIE, PHYLENE,
         MEOWSKERS, POPPY, STORMY_BLAST_REPRINT, SAMMY_AND_MARIE, HARMONIOUS_MEAL,
         EARTH_SHATTERING_BOLT, TICO, AMETHYSTS_NAPTIME, TETRA_AND_LADICA, GINGER,
         DAINTY_HORROR, LITTLE_BEASTIE, HEEL_MY_DEARIE, CHARMING_MONSTER, PRETTY_PREDATOR,
         HAPHAZARD_SNACKING, SWEET_ABOMINATION, BOTTOMLESS_GLUTTONY, LILANTHIM,
         BELOVED_MASTERPIECE, CRYSTALSPAWN, DAYDREAM_LIBRARIAN, ADVENT_OF_THE_ELD_CRYSTALS,
         ENRAPTURED_STUDENT, ADVENTUROUS_GRIMOIRE, REAVED_ORDER, SPELLBOUND_PROFESSOR,
         BEWITCHING_ELD_CRYSTALS, SHYMM, CALGE_DANTHLA, TERRAFORMING_WIZARD,
         WATERBENDING_CHARMWIELDER, METAMORPHOSIS_OF_THE_DAWNBLOSSOM, INSOMNIAC_WITCH,
         WOODSONG_HAIKUMASTER, KITTY_CUNNING, EMPEROR_OF_ELEMENTS, GRANDEUR_OF_THE_DAWNBLOSSOM,
         LHYNKAL, ARA, PHILOSOPHIA, SUFRAMARE, RUNE_PORTAL, EZECRAIN, MIREILLE_AND_RISETTE,
         UNLEASHED, ELMOTT, ALCHEMIC_FLARE, WAMDUS, CAGLIOSTRO, STORMY_BLAST,
         DAZZLING_RUNEKNIGHT, WITCHS_NEW_BREW, FORESIGHT, TRUTH_SUMMONS, REMI_AND_RAMI,
         BLAZE_DESTROYER, ARCANE_ERUPTION]
TOKENS = [CLAY_GOLEM, GUARDIAN_GOLEM, MAGIC_SEDIMENT, MYSTERIAN_MISSILE, ARS_MAGNA,
          DEPTHS_OF_THE_ELD_CRYSTALS, DELTA_CANNON, SEND_EM_PACKING]
LEADER_AREA = [ELMOTT_CREST, CAGLIOSTRO_CREST, INSOMNIAC_WITCH_CREST, LHYNKAL_CREST,
               SHYMM_CREST, ELD_CRYSTALS_FAITH, LILANTHIM_CREST, TICO_CREST, SEPHIE_CREST]


# --- helpers -------------------------------------------------------------------------

def _is(defn):
    """Target filter: the card is a copy of `defn`."""
    return lambda state, player, c: c.defn.card_id == defn.card_id


def _is_golem(state, player, c) -> bool:
    return E.has_trait(c, GOLEM)


def _has_on_spellboost(state, player, c) -> bool:
    return any(s.on_spellboost is not None for s in scripts_of(c))


def _enemy_leader(ctx) -> list:
    return [common.enemy_leader(ctx)]


def _all_followers(ctx) -> list:
    """Every follower on the field, turn player's side first, oldest first."""
    return [c for c in ctx.state.field_order() if c.defn.is_follower]


def _random_enemy(ctx, k: int = 1) -> list:
    return E.random_sample(ctx.state, ctx.opponent.followers, k)


def _spellboost(ctx, times: int = 1) -> None:
    E.spellboost(ctx.state, ctx.controller, times)


def _on_field(ctx, inst) -> bool:
    return inst is not None and ctx.state.on_field(inst.uid) is inst


def _summon(ctx, defn, n: int = 1) -> list:
    summoned = []
    for _ in range(n):
        inst = E.summon(ctx.state, ctx.controller, defn)
        if inst is not None:
            summoned.append(inst)
    return summoned


def _evolve_if_able(ctx, inst) -> None:
    if _on_field(ctx, inst) and not inst.evolved:
        E.evolve(ctx.state, inst)


def entered_test_subjects(state, player: int) -> int:
    """Allied Obsessed Test Subjects that entered the field this match."""
    return state.players[player].entered.get(OBSESSED_TEST_SUBJECT.card_id, 0)


def summon_test_subjects(ctx, n: int = 1) -> list:
    return _summon(ctx, OBSESSED_TEST_SUBJECT, n)


class _CantAttack(CardScript):
    """Granted: "Can't attack followers or leaders." """
    cant_attack = True


class _TwoAttacks(CardScript):
    """Granted: "Can attack 2 times per turn." """
    attacks_per_turn = 2


CANT_ATTACK = _CantAttack()
TWO_ATTACKS = _TwoAttacks()


class _CostDownOnSpellboost(CardScript):
    """On Spellboost: reduce the cost of this card by 1."""

    def on_spellboost(self, ctx):
        E.add_cost(ctx.source, -1)


class _XOnSpellboost(CardScript):
    """X starts at `x_start`; On Spellboost: increase X by 1 (kept in counters["x"])."""
    x_start = 0

    def on_spellboost(self, ctx):
        c = E.counters(ctx.source)
        c["x"] = c.get("x", self.x_start) + 1

    def x(self, inst) -> int:
        return (inst.counters or {}).get("x", self.x_start)


class _CostDownOnEarthRite(CardScript):
    """Activates in hand. Whenever you perform Earth Rite, reduce this card's cost by 1."""
    listen_in_hand = True

    def on_earth_rite(self, ctx):
        E.add_cost(ctx.source, -1)


remove_abilities = E.silence   # "remove all abilities"


# --- generated cards -------------------------------------------------------------------

@register(MAGIC_SEDIMENT.card_id)
class MagicSediment(CardScript):
    """Earth Sigil. Engage (1): gain an earth sigil."""
    engage_cost = 1

    def engage(self, ctx):
        common.gain_earth_sigils(ctx, 1)


@register(MYSTERIAN_MISSILE.card_id)
class MysterianMissile(CardScript):
    """Deal 3 damage to a random enemy follower."""

    def cast(self, ctx):
        E.damage(ctx.state, _random_enemy(ctx), 3, ctx.source)


@register(ARS_MAGNA.card_id)
class ArsMagna(CardScript):
    """Select an enemy (follower or leader) and deal it 2 damage. Restore 1 defense to your leader."""
    play_targets = common.ENEMY_FOLLOWER_OR_LEADER

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 2, ctx.source)
        E.heal_leader(ctx.state, ctx.controller, 1)


@register(DEPTHS_OF_THE_ELD_CRYSTALS.card_id)
class DepthsOfTheEldCrystals(CardScript):
    """Summon a Crystalspawn and give it +X/+X; restore Y defense to your leader; deal
    Z damage to the enemy leader. X + Y + Z = your faith's value, each point going to
    X, Y or Z with equal chance (official Q&A)."""

    def cast(self, ctx):
        split = [0, 0, 0]
        for _ in range(E.faith_value(ctx.state, ctx.controller, ELD_CRYSTALS_FAITH)):
            split[ctx.state.rng.randrange(3)] += 1
        x, y, z = split
        for spawn in _summon(ctx, CRYSTALSPAWN):
            E.buff(ctx.state, spawn, x, x)
        E.heal_leader(ctx.state, ctx.controller, y)
        E.damage(ctx.state, _enemy_leader(ctx), z, ctx.source)


@register(DELTA_CANNON.card_id)
class DeltaCannon(CardScript):
    """Deal 5 damage to all enemy followers."""

    def cast(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 5, ctx.source)


@register(SEND_EM_PACKING.card_id)
class SendEmPacking(CardScript):
    """Select an allied follower and give it "Can attack 2 times per turn." (A follower
    that can already attack 3 times keeps 3: official Q&A.)"""
    play_targets = common.ALLIED_FOLLOWER

    def cast(self, ctx):
        for f in ctx.chosen():
            E.grant(f, TWO_ATTACKS)


# --- leader area ---------------------------------------------------------------------------

@register(ELMOTT_CREST.card_id)
class ElmottCrest(CardScript):
    """At the start of your turn, deal 1 damage to the enemy leader."""

    def on_turn_start(self, ctx):
        E.damage(ctx.state, _enemy_leader(ctx), 1, ctx.source)


@register(CAGLIOSTRO_CREST.card_id)
class CagliostroCrest(CardScript):
    """At the start of your turn, Earth Rite (1): add an Ars Magna to your hand."""

    def on_turn_start(self, ctx):
        if E.earth_rite(ctx.state, ctx.controller, 1):
            E.add_to_hand(ctx.state, ctx.controller, ARS_MAGNA)


@register(INSOMNIAC_WITCH_CREST.card_id)
class InsomniacWitchCrest(CardScript):
    """Countdown (2). Last Words: deal 3 damage to all followers."""

    def last_words(self, ctx):
        E.damage(ctx.state, _all_followers(ctx), 3, ctx.source)


@register(LHYNKAL_CREST.card_id)
class LhynkalCrest(CardScript):
    """Whenever an allied Lhynkal, Wandering Fool enters the field, reduce the enemy
    leader's max defense by 2."""

    def on_ally_enter(self, ctx):
        if ctx.other.defn.card_id != LHYNKAL.card_id:
            return
        foe = 1 - ctx.controller
        enemy = ctx.state.players[foe]
        # Confirmed by the player: max defense can drop to 0, and the leader then loses.
        E.set_leader_max_hp(ctx.state, foe, max(0, enemy.leader_max_hp - 2))
        if enemy.leader_hp <= 0 and ctx.state.winner is None:
            ctx.state.winner = ctx.controller


@register(SHYMM_CREST.card_id)
class ShymmCrest(CardScript):
    """Whenever an allied Crystalspawn attacks, give it +1/+0."""

    def on_attack(self, ctx):
        attacker = ctx.other
        if attacker.owner == ctx.controller and attacker.defn.card_id == CRYSTALSPAWN.card_id:
            E.buff(ctx.state, attacker, 1, 0)


@register(ELD_CRYSTALS_FAITH.card_id)
class EldCrystalsFaith(CardScript):
    """Faith (starts in the leader area with Calge-Danthla in the deck). Value starts at
    0; whenever an allied Crystalspawn enters the field, increase it by 1."""

    def on_ally_enter(self, ctx):
        if ctx.other.defn.card_id == CRYSTALSPAWN.card_id:
            c = E.counters(ctx.source)
            c["value"] = c.get("value", 0) + 1


@register(LILANTHIM_CREST.card_id)
class LilanthimCrest(CardScript):
    """Countdown (1). At the end of your opponent's turn, summon a Lilanthim, Anathema
    of Predation and evolve it."""

    def on_opponent_turn_end(self, ctx):
        for inst in _summon(ctx, LILANTHIM):
            E.evolve(ctx.state, inst)


@register(TICO_CREST.card_id)
class TicoCrest(CardScript):
    """Whenever you play a Mysteria spell, deal 1 damage to the enemy leader."""

    def on_play(self, ctx):
        if ctx.as_spell and E.has_trait(ctx.other, MYSTERIA):
            E.damage(ctx.state, _enemy_leader(ctx), 1, ctx.source)


@register(SEPHIE_CREST.card_id)
class SephieCrest(CardScript):
    """Once on each of your turns, when an allied Obsessed Test Subject enters the
    field, give it Storm."""

    def on_ally_enter(self, ctx):
        f = ctx.other
        if (f.defn.card_id == OBSESSED_TEST_SUBJECT.card_id and common.during_your_turn(ctx)
                and _on_field(ctx, f) and E.once_per_turn(ctx, "sephie")):
            E.give_keywords(f, Keyword.STORM)


# --- set 9 -------------------------------------------------------------------------------------

@register(OBSESSED_TEST_SUBJECT.card_id)
class ObsessedTestSubject(CardScript):
    """When this follower enters the field, if at least 5 other allied Obsessed Test
    Subjects entered the field this match, give it +3/+3. Rush.
    The count is checked as it enters (official Q&A: of two summoned together after
    four, the first stays 2/2 and the second gets +3/+3)."""
    queue_checks = ("on_enter",)

    def queue_condition(self, hook, ctx):
        return entered_test_subjects(ctx.state, ctx.controller) - 1 >= 5

    def on_enter(self, ctx):
        E.buff(ctx.state, ctx.source, 3, 3)


@register(KEY_SPIRIT.card_id)
class KeySpirit(CardScript):
    """Fanfare: select an enemy follower and deal it 7 damage; deal 4 damage to the enemy
    leader. Evolve: select a card in your hand with On Spellboost and spellboost it 4 times."""
    play_targets = common.ENEMY_FOLLOWER
    evolve_targets = (TargetSpec(Target.HAND_CARD, filter=_has_on_spellboost),)

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 7, ctx.source)
        E.damage(ctx.state, _enemy_leader(ctx), 4, ctx.source)

    def on_evolve(self, ctx):
        E.spellboost(ctx.state, ctx.controller, 4, cards=ctx.chosen_hand())


@register(MISCALCULATED_EXPERIMENT.card_id)
class MiscalculatedExperiment(CardScript):
    """Add 3 Truth Summons to your hand."""

    def cast(self, ctx):
        for _ in range(3):
            E.add_to_hand(ctx.state, ctx.controller, TRUTH_SUMMONS)


@register(ENAMORED_RESEARCHER.card_id)
class EnamoredResearcher(CardScript):
    """Fanfare: summon 2 Obsessed Test Subjects. Enhance (8): summon 3 instead and give
    them Ward. Evolve: select an allied Obsessed Test Subject and give it Bane."""
    enhance = (8,)
    evolve_targets = (TargetSpec(Target.ALLIED_FOLLOWER, filter=_is(OBSESSED_TEST_SUBJECT)),)

    def fanfare(self, ctx):
        for f in summon_test_subjects(ctx, 3 if ctx.enhanced else 2):
            if ctx.enhanced and _on_field(ctx, f):
                E.give_keywords(f, Keyword.WARD)

    def on_evolve(self, ctx):
        for f in ctx.chosen():
            E.give_keywords(f, Keyword.BANE)


@register(NOBLE_PHILOSOPHER.card_id)
class NoblePhilosopher(CardScript):
    """Fanfare: return your hand to your deck, then draw as many cards as you returned."""

    def fanfare(self, ctx):
        returned = list(ctx.me.hand)
        for c in returned:
            E.return_to_deck(ctx.state, c)
        E.draw(ctx.state, ctx.controller, len(returned))


@register(HUMANE_LOVE.card_id)
class HumaneLove(CardScript):
    """Summon an Obsessed Test Subject and give it +1/+0. Add an Obsessed Test Subject
    to your hand and give it +1/+0."""

    def cast(self, ctx):
        for f in summon_test_subjects(ctx):
            E.buff(ctx.state, f, 1, 0)
        added = E.add_to_hand(ctx.state, ctx.controller, OBSESSED_TEST_SUBJECT)
        if added is not None:
            E.buff(ctx.state, added, 1, 0)


@register(ECSTATIC_SCHOLAR.card_id)
class EcstaticScholar(CardScript):
    """Fuse: any cards. Fanfare: draw 2 cards; summon an Obsessed Test Subject.
    Super-Evolve: if a card was fused to this card, select an allied Obsessed Test
    Subject and give it Drain."""
    fuse_filter = staticmethod(lambda c: True)
    super_evolve_targets = (TargetSpec(Target.ALLIED_FOLLOWER, filter=_is(OBSESSED_TEST_SUBJECT)),)

    def fanfare(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)
        summon_test_subjects(ctx)

    def on_super_evolve(self, ctx):
        if (ctx.source.counters or {}).get("fused"):
            for f in ctx.chosen():
                E.give_keywords(f, Keyword.DRAIN)


@register(OBSIDIAN_RAVEN.card_id)
class ObsidianRaven(CardScript):
    """Summon an Obsessed Test Subject. Twice: deal 7 damage to a random enemy follower."""

    def cast(self, ctx):
        summon_test_subjects(ctx)
        for _ in range(2):
            E.damage(ctx.state, _random_enemy(ctx), 7, ctx.source)


@register(SEPHIE.card_id)
class Sephie(CardScript):
    """Fuse: any cards. Whenever you fuse to this card, spend 2 play points to summon an
    Obsessed Test Subject. Fanfare: summon 2 Obsessed Test Subjects. Super-Evolve: gain
    Crest: Sephie, Maven Convict."""
    fuse_filter = staticmethod(lambda c: True)

    def on_fuse(self, ctx):
        # "Spend 2 play points to ...": nothing happens with fewer than 2.
        # Confirmed by the player: with a full field the 2 play points are still spent.
        if ctx.me.pp >= 2:
            ctx.me.pp -= 2
            summon_test_subjects(ctx)

    def fanfare(self, ctx):
        summon_test_subjects(ctx, 2)

    def on_super_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, SEPHIE_CREST)


@register(PHYLENE.card_id)
class Phylene(_CostDownOnSpellboost):
    """On Spellboost: reduce the cost of this card by 1. Bane, Ward, Aura."""


# --- set 8 ---------------------------------------------------------------------------------------

@register(MEOWSKERS.card_id)
class Meowskers(CardScript):
    """Fanfare: select an enemy follower and deal it 1 damage; spellboost your hand.
    Evolve: replicate the Fanfare."""
    play_targets = common.ENEMY_FOLLOWER
    evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        self._effect(ctx)

    def on_evolve(self, ctx):
        self._effect(ctx)

    def _effect(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 1, ctx.source)
        _spellboost(ctx)


@register(POPPY.card_id)
class Poppy(CardScript):
    """Fanfare: add a Mysterian Missile to your hand."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, MYSTERIAN_MISSILE)


@register(STORMY_BLAST.card_id, STORMY_BLAST_REPRINT.card_id)
class StormyBlast(_XOnSpellboost):
    """X starts at 2; On Spellboost: X + 1. Select an enemy follower and deal it X damage."""
    x_start = 2
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), self.x(ctx.source), ctx.source)


@register(SAMMY_AND_MARIE.card_id)
class SammyAndMarie(_CostDownOnSpellboost):
    """On Spellboost: reduce the cost of this card by 1. Fanfare: draw 2 cards; your
    opponent draws a card."""

    def fanfare(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)
        E.draw(ctx.state, 1 - ctx.controller, 1)


@register(HARMONIOUS_MEAL.card_id)
class HarmoniousMeal(CardScript):
    """Restore 2 defense to your leader. Spellboost your hand (and the spell itself
    spellboosts it again afterwards)."""

    def cast(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 2)
        _spellboost(ctx)


@register(EARTH_SHATTERING_BOLT.card_id)
class EarthShatteringBolt(CardScript):
    """Deal 8 damage to a random enemy follower with the highest attack; deal 2 damage to
    the enemy leader. Earth Rite (2): add an Earth-Shattering Bolt to your hand."""

    def cast(self, ctx):
        enemies = ctx.opponent.followers
        if enemies:
            top = max(f.atk for f in enemies)
            E.damage(ctx.state, E.random_sample(ctx.state, [f for f in enemies if f.atk == top], 1),
                     8, ctx.source)
        E.damage(ctx.state, _enemy_leader(ctx), 2, ctx.source)
        if E.earth_rite(ctx.state, ctx.controller, 2):
            E.add_to_hand(ctx.state, ctx.controller, EARTH_SHATTERING_BOLT)


@register(TICO.card_id)
class Tico(CardScript):
    """Fanfare: add 2 Mysterian Missiles to your hand. Evolve: reduce the cost of all
    Mysteria spells in your hand by 1. Super-Evolve: gain Crest: Tico."""

    def fanfare(self, ctx):
        for _ in range(2):
            E.add_to_hand(ctx.state, ctx.controller, MYSTERIAN_MISSILE)

    def on_evolve(self, ctx):
        for c in ctx.me.hand:
            if c.defn.is_spell and E.has_trait(c, MYSTERIA):
                E.add_cost(c, -1)

    def on_super_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, TICO_CREST)


@register(AMETHYSTS_NAPTIME.card_id)
class AmethystsNaptime(_XOnSpellboost):
    """X starts at 0; On Spellboost: X + 1. Draw 2 cards. If X is at least 5, restore 2
    defense to your leader and recover 2 play points."""

    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)
        if self.x(ctx.source) >= 5:
            E.heal_leader(ctx.state, ctx.controller, 2)
            E.recover_pp(ctx.state, ctx.controller, 2)


@register(TETRA_AND_LADICA.card_id)
class TetraAndLadica(_XOnSpellboost):
    """X starts at 0; On Spellboost: X + 1. Fanfare: if X is at least 10, add a Delta
    Cannon to your hand; if at least 20, add a Send 'Em Packing too. Storm."""

    def fanfare(self, ctx):
        x = self.x(ctx.source)
        if x >= 10:
            E.add_to_hand(ctx.state, ctx.controller, DELTA_CANNON)
        if x >= 20:
            E.add_to_hand(ctx.state, ctx.controller, SEND_EM_PACKING)


@register(GINGER.card_id)
class Ginger(CardScript):
    """Fanfare: summon 2 Guardian Golems. Whenever another allied follower enters the
    field, give it Rush and spellboost your hand. Evolve: summon a Guardian Golem."""

    def fanfare(self, ctx):
        _summon(ctx, GUARDIAN_GOLEM, 2)

    def on_ally_enter(self, ctx):
        if _on_field(ctx, ctx.other):
            E.give_keywords(ctx.other, Keyword.RUSH)
        _spellboost(ctx)

    def on_evolve(self, ctx):
        _summon(ctx, GUARDIAN_GOLEM)


# --- set 7 ---------------------------------------------------------------------------------------

@register(DAINTY_HORROR.card_id)
class DaintyHorror(CardScript):
    """Fanfare: Earth Rite (1): evolve this follower. Ward."""

    def fanfare(self, ctx):
        if not ctx.source.evolved and E.earth_rite(ctx.state, ctx.controller, 1):
            _evolve_if_able(ctx, ctx.source)


@register(LITTLE_BEASTIE.card_id)
class LittleBeastie(CardScript):
    """Fanfare: select an enemy follower and deal it 1 damage; gain an earth sigil.
    Evolve: replicate the Fanfare."""
    play_targets = common.ENEMY_FOLLOWER
    evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        self._effect(ctx)

    def on_evolve(self, ctx):
        self._effect(ctx)

    def _effect(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 1, ctx.source)
        common.gain_earth_sigils(ctx, 1)


@register(HEEL_MY_DEARIE.card_id)
class HeelMyDearie(_CostDownOnEarthRite):
    """Activates in hand: whenever you perform Earth Rite, reduce this card's cost by 1.
    Draw 2 cards. Gain an earth sigil."""

    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)
        common.gain_earth_sigils(ctx, 1)


@register(CHARMING_MONSTER.card_id)
class CharmingMonster(CardScript):
    """Rush. Last Words: gain 2 earth sigils. Super-Evolve: Earth Rite (2): summon 2
    Charming Monsters."""

    def last_words(self, ctx):
        common.gain_earth_sigils(ctx, 2)

    def on_super_evolve(self, ctx):
        if E.earth_rite(ctx.state, ctx.controller, 2):
            _summon(ctx, CHARMING_MONSTER, 2)


@register(PRETTY_PREDATOR.card_id)
class PrettyPredator(CardScript):
    """Fanfare: gain 2 earth sigils. Ward."""

    def fanfare(self, ctx):
        common.gain_earth_sigils(ctx, 2)


@register(HAPHAZARD_SNACKING.card_id)
class HaphazardSnacking(CardScript):
    """Mode: 1. Gain 4 earth sigils. 2. Earth Rite (2): deal 2 damage to all enemy followers."""
    modes = (2, 1)

    def cast(self, ctx):
        if 0 in ctx.modes:
            common.gain_earth_sigils(ctx, 4)
        if 1 in ctx.modes and E.earth_rite(ctx.state, ctx.controller, 2):
            E.damage(ctx.state, list(ctx.opponent.followers), 2, ctx.source)


@register(SWEET_ABOMINATION.card_id)
class SweetAbomination(CardScript):
    """Fanfare: Earth Rite (1): Mode: 1. Deal 3 damage to all enemy followers. 2. Draw 2
    cards. Evolve: replicate the Fanfare (choose again)."""
    modes = (2, 1)
    evolve_modes = (2, 1)

    def fanfare(self, ctx):
        self._effect(ctx)

    def on_evolve(self, ctx):
        self._effect(ctx)

    def _effect(self, ctx):
        if not E.earth_rite(ctx.state, ctx.controller, 1):
            return
        if 0 in ctx.modes:
            E.damage(ctx.state, list(ctx.opponent.followers), 3, ctx.source)
        if 1 in ctx.modes:
            E.draw(ctx.state, ctx.controller, 2)


@register(BOTTOMLESS_GLUTTONY.card_id)
class BottomlessGluttony(_CostDownOnEarthRite):
    """Activates in hand: whenever you perform Earth Rite, reduce this card's cost by 1.
    Select an enemy follower and destroy it. Gain 2 earth sigils."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        common.gain_earth_sigils(ctx, 2)


@register(LILANTHIM.card_id)
class Lilanthim(CardScript):
    """Fanfare: Earth Rite (1): gain Crest: Lilanthim. Aura. Evolve: Earth Rite (1):
    select an enemy follower and destroy it."""
    evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        if E.earth_rite(ctx.state, ctx.controller, 1):
            E.add_to_leader_area(ctx.state, ctx.controller, LILANTHIM_CREST)

    def on_evolve(self, ctx):
        # Confirmed by the player: the Earth Rite is performed even with no enemy
        # follower to select.
        if E.earth_rite(ctx.state, ctx.controller, 1):
            for target in ctx.chosen():
                E.destroy(ctx.state, target)


@register(BELOVED_MASTERPIECE.card_id)
class BelovedMasterpiece(CardScript):
    """Fanfare: deal 6 damage to all enemy followers. Ward. Last Words: Earth Rite (2):
    deal 3 damage to the enemy leader. Super-Evolve: summon a Beloved Masterpiece."""

    def fanfare(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 6, ctx.source)

    def last_words(self, ctx):
        if E.earth_rite(ctx.state, ctx.controller, 2):
            E.damage(ctx.state, _enemy_leader(ctx), 3, ctx.source)

    def on_super_evolve(self, ctx):
        _summon(ctx, BELOVED_MASTERPIECE)


# --- set 6 ---------------------------------------------------------------------------------------

@register(DAYDREAM_LIBRARIAN.card_id)
class DaydreamLibrarian(CardScript):
    """Fanfare: summon a Caravan Mammoth. Super-Evolve: give all other allied followers Rush."""

    def fanfare(self, ctx):
        _summon(ctx, CARAVAN_MAMMOTH)

    def on_super_evolve(self, ctx):
        for f in ctx.me.followers:
            if f is not ctx.source:
                E.give_keywords(f, Keyword.RUSH)


@register(ADVENT_OF_THE_ELD_CRYSTALS.card_id)
class AdventOfTheEldCrystals(CardScript):
    """Summon 2 Crystalspawns."""

    def cast(self, ctx):
        _summon(ctx, CRYSTALSPAWN, 2)


@register(ENRAPTURED_STUDENT.card_id)
class EnrapturedStudent(CardScript):
    """Fanfare: summon 2 Crystalspawns. Whenever an allied Crystalspawn enters the field,
    restore 1 defense to your leader."""

    def fanfare(self, ctx):
        _summon(ctx, CRYSTALSPAWN, 2)

    def on_ally_enter(self, ctx):
        if ctx.other.defn.card_id == CRYSTALSPAWN.card_id:
            E.heal_leader(ctx.state, ctx.controller, 1)


@register(ADVENTUROUS_GRIMOIRE.card_id)
class AdventurousGrimoire(CardScript):
    """Enhance (6): summon 2 Adventurous Grimoires. Rush. Last Words: spellboost your hand."""
    enhance = (6,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            _summon(ctx, ADVENTUROUS_GRIMOIRE, 2)

    def last_words(self, ctx):
        _spellboost(ctx)


@register(REAVED_ORDER.card_id)
class ReavedOrder(CardScript):
    """Select an allied Crystalspawn and destroy it. Draw 2 cards."""
    play_targets = (TargetSpec(Target.ALLIED_FOLLOWER, filter=_is(CRYSTALSPAWN)),)

    def cast(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        E.draw(ctx.state, ctx.controller, 2)


@register(SPELLBOUND_PROFESSOR.card_id)
class SpellboundProfessor(CardScript):
    """Fanfare: summon 2 Crystalspawns. Evolve: give all allied Crystalspawns +1/+0."""

    def fanfare(self, ctx):
        _summon(ctx, CRYSTALSPAWN, 2)

    def on_evolve(self, ctx):
        for f in list(ctx.me.followers):
            if f.defn.card_id == CRYSTALSPAWN.card_id:
                E.buff(ctx.state, f, 1, 0)


@register(BEWITCHING_ELD_CRYSTALS.card_id)
class BewitchingEldCrystals(CardScript):
    """Mode: 1. Summon a Crystalspawn and give it +1/+0 and Storm. 2. Summon 2
    Crystalspawns and give them +1/+0. Enhance (6): activate both."""
    modes = (2, 1)
    enhance = (6,)
    modes_all_when_enhanced = True

    def cast(self, ctx):
        if 0 in ctx.modes:
            for f in _summon(ctx, CRYSTALSPAWN):
                E.buff(ctx.state, f, 1, 0)
                E.give_keywords(f, Keyword.STORM)
        if 1 in ctx.modes:
            for f in _summon(ctx, CRYSTALSPAWN, 2):
                E.buff(ctx.state, f, 1, 0)


@register(SHYMM.card_id)
class Shymm(CardScript):
    """Fanfare: summon 2 Crystalspawns. Drain. Super-Evolve: gain Crest: Shymm."""

    def fanfare(self, ctx):
        _summon(ctx, CRYSTALSPAWN, 2)

    def on_super_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, SHYMM_CREST)


@register(CALGE_DANTHLA.card_id)
class CalgeDanthla(CardScript):
    """Activates in hand: whenever an allied Crystalspawn enters the field, reduce this
    card's cost by 1. Fanfare: summon 2 Crystalspawns and give them Storm. Evolve: add a
    Depths of the Eld Crystals to your hand. (Its faith starts in the leader area.)"""
    listen_in_hand = True

    def on_ally_enter(self, ctx):
        if (ctx.other.defn.card_id == CRYSTALSPAWN.card_id
                and ctx.state.in_zone(ctx.source, "hand")):
            E.add_cost(ctx.source, -1)

    def fanfare(self, ctx):
        for f in _summon(ctx, CRYSTALSPAWN, 2):
            E.give_keywords(f, Keyword.STORM)

    def on_evolve(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, DEPTHS_OF_THE_ELD_CRYSTALS)


# --- set 5 ---------------------------------------------------------------------------------------

@register(TERRAFORMING_WIZARD.card_id)
class TerraformingWizard(CardScript):
    """Fanfare: gain 2 earth sigils. Super-Evolve: summon 2 Guardian Golems."""

    def fanfare(self, ctx):
        common.gain_earth_sigils(ctx, 2)

    def on_super_evolve(self, ctx):
        _summon(ctx, GUARDIAN_GOLEM, 2)


@register(WATERBENDING_CHARMWIELDER.card_id)
class WaterbendingCharmwielder(CardScript):
    """Fanfare: deal 3 damage to 3 random enemy followers. Spellboost your hand 3 times."""

    def fanfare(self, ctx):
        E.damage(ctx.state, _random_enemy(ctx, 3), 3, ctx.source)
        _spellboost(ctx, 3)


@register(METAMORPHOSIS_OF_THE_DAWNBLOSSOM.card_id)
class MetamorphosisOfTheDawnblossom(CardScript):
    """Select a card in your hand and discard it. Draw 2 cards."""
    play_targets = common.HAND_CARD

    def cast(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        E.draw(ctx.state, ctx.controller, 2)


@register(INSOMNIAC_WITCH.card_id)
class InsomniacWitch(CardScript):
    """Fanfare: gain Crest: Insomniac Witch. Evolve: destroy your Crest: Insomniac Witch."""

    def fanfare(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, INSOMNIAC_WITCH_CREST)

    def on_evolve(self, ctx):
        crest = E.leader_area_card(ctx.state, ctx.controller, INSOMNIAC_WITCH_CREST)
        if crest is not None:
            E.destroy(ctx.state, crest)


@register(WOODSONG_HAIKUMASTER.card_id)
class WoodsongHaikumaster(_CostDownOnSpellboost):
    """On Spellboost: reduce the cost of this card by 1. Fanfare: draw a card. Last
    Words: spellboost your hand."""

    def fanfare(self, ctx):
        E.draw(ctx.state, ctx.controller)

    def last_words(self, ctx):
        _spellboost(ctx)


@register(KITTY_CUNNING.card_id)
class KittyCunning(CardScript):
    """Earth Rite (2): activate 2 different random abilities of: 1. Summon a Clay Golem.
    2. Restore 2 defense to your leader. 3. Gain 3 earth sigils."""

    def cast(self, ctx):
        if not E.earth_rite(ctx.state, ctx.controller, 2):
            return
        picks = sorted(E.random_sample(ctx.state, [0, 1, 2], 2))
        if 0 in picks:
            _summon(ctx, CLAY_GOLEM)
        if 1 in picks:
            E.heal_leader(ctx.state, ctx.controller, 2)
        if 2 in picks:
            common.gain_earth_sigils(ctx, 3)


@register(EMPEROR_OF_ELEMENTS.card_id)
class EmperorOfElements(CardScript):
    """Fanfare: summon 2 Guardian Golems. Whenever an allied Golem follower enters the
    field, Earth Rite (1): evolve it."""

    def fanfare(self, ctx):
        _summon(ctx, GUARDIAN_GOLEM, 2)

    def on_ally_enter(self, ctx):
        f = ctx.other
        if (f.defn.is_follower and E.has_trait(f, GOLEM) and _on_field(ctx, f) and not f.evolved
                and E.earth_rite(ctx.state, ctx.controller, 1)):
            E.evolve(ctx.state, f)


def _become_exact_copy(state, inst, model) -> None:
    """Transform `inst` into an exact copy of `model` (stats, keywords, counters,
    granted abilities and cost changes included)."""
    E.transform(state, inst, model.defn)
    clone = model.copy()
    inst.cost, inst.atk, inst.life, inst.max_life = clone.cost, clone.atk, clone.life, clone.max_life
    inst.keywords = clone.keywords
    inst.counters, inst.grants, inst.cost_mods = clone.counters, clone.grants, clone.cost_mods
    inst.max_attacks = prop(inst, "attacks_per_turn")


@register(GRANDEUR_OF_THE_DAWNBLOSSOM.card_id)
class GrandeurOfTheDawnblossom(CardScript):
    """Transform each allied follower into an exact copy of a random follower in your
    deck (chosen independently for each: official Q&A)."""

    def cast(self, ctx):
        pool = [c for c in ctx.me.deck if c.defn.is_follower]
        if not pool:
            return
        for f in list(ctx.me.followers):
            _become_exact_copy(ctx.state, f, ctx.state.rng.choice(pool))


@register(LHYNKAL.card_id)
class Lhynkal(CardScript):
    """Fanfare: gain Crest: Lhynkal, Wandering Fool. Rush. Super-Evolve: put 10 Lhynkal,
    Wandering Fool into your deck."""

    def fanfare(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, LHYNKAL_CREST)

    def on_super_evolve(self, ctx):
        for _ in range(10):
            E.put_into_deck(ctx.state, ctx.controller, LHYNKAL)


@register(ARA.card_id)
class Ara(_CostDownOnSpellboost):
    """On Spellboost: reduce the cost of this card by 1. Fanfare: select an enemy follower
    and deal it 10 damage. Evolve: select another follower and transform it into a Regal
    Falcon."""
    play_targets = common.ENEMY_FOLLOWER
    evolve_targets = (TargetSpec(Target.ANY_FOLLOWER, other=True),)

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 10, ctx.source)

    def on_evolve(self, ctx):
        for target in ctx.chosen():
            E.transform(ctx.state, target, REGAL_FALCON)


# --- set 4 ---------------------------------------------------------------------------------------

@register(PHILOSOPHIA.card_id)
class Philosophia(CardScript):
    """Fanfare: draw a spell."""

    def fanfare(self, ctx):
        E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.is_spell)


@register(SUFRAMARE.card_id)
class Suframare(CardScript):
    """At the end of your turn, spellboost your hand X times (X = this follower's attack).
    Evolve: this follower gains "Can't attack followers or leaders." """

    def on_turn_end(self, ctx):
        _spellboost(ctx, ctx.source.atk)

    def on_evolve(self, ctx):
        E.grant(ctx.source, CANT_ATTACK)


@register(RUNE_PORTAL.card_id)
class RunePortal(CardScript):
    """Deal 6 damage to all enemy followers. Restore 3 defense to your leader."""

    def cast(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 6, ctx.source)
        E.heal_leader(ctx.state, ctx.controller, 3)


@register(EZECRAIN.card_id)
class Ezecrain(CardScript):
    """Fanfare: select 2 enemy followers and deal them 4 damage. Gain 2 earth sigils."""
    play_targets = (TargetSpec(Target.ENEMY_FOLLOWER, 2),)

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4, ctx.source)
        common.gain_earth_sigils(ctx, 2)


@register(MIREILLE_AND_RISETTE.card_id)
class MireilleAndRisette(CardScript):
    """Fanfare: summon a Mireille & Risette. Earth Rite (2): evolve it and this follower
    (two evolutions: Skybound Art gauges go up by 2, official Q&A)."""

    def fanfare(self, ctx):
        twins = _summon(ctx, MIREILLE_AND_RISETTE)
        if E.earth_rite(ctx.state, ctx.controller, 2):
            for f in twins + [ctx.source]:
                _evolve_if_able(ctx, f)


@register(UNLEASHED.card_id)
class Unleashed(CardScript):
    """Mode: 1. Draw a card; deal 4 damage to a random enemy follower. 2. Draw 2 cards;
    deal 4 damage to 2 random enemy followers and 2 damage to your leader."""
    modes = (2, 1)

    def cast(self, ctx):
        if 0 in ctx.modes:
            E.draw(ctx.state, ctx.controller)
            E.damage(ctx.state, _random_enemy(ctx), 4, ctx.source)
        if 1 in ctx.modes:
            E.draw(ctx.state, ctx.controller, 2)
            E.damage(ctx.state, _random_enemy(ctx, 2), 4, ctx.source)
            E.damage(ctx.state, [common.own_leader(ctx)], 2, ctx.source)


@register(ELMOTT.card_id)
class Elmott(CardScript):
    """Fanfare: select an enemy follower, remove all its abilities, and deal it 3 damage.
    Super-Evolve: gain Crest: Elmott."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        for target in ctx.chosen():
            remove_abilities(target)
        E.damage(ctx.state, ctx.chosen(), 3, ctx.source)

    def on_super_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, ELMOTT_CREST)


@register(ALCHEMIC_FLARE.card_id)
class AlchemicFlare(CardScript):
    """Select an enemy follower and deal it 4 damage. Gain an earth sigil. Skybound Art:
    deal 2 damage to the enemy leader."""
    play_targets = common.ENEMY_FOLLOWER
    skybound = True

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4, ctx.source)
        common.gain_earth_sigils(ctx, 1)
        if E.skybound_art(ctx):
            E.damage(ctx.state, _enemy_leader(ctx), 2, ctx.source)


@register(WAMDUS.card_id)
class Wamdus(CardScript):
    """On Spellboost: give this card +1/+1. Fanfare: spellboost your hand. Super-Evolve:
    Mode: 1. Give all other allied followers Barrier. 2. Deal X damage split between all
    enemy followers (X = this follower's attack)."""
    super_evolve_modes = (2, 1)

    def on_spellboost(self, ctx):
        E.buff(ctx.state, ctx.source, 1, 1)

    def fanfare(self, ctx):
        _spellboost(ctx)

    def on_super_evolve(self, ctx):
        if 0 in ctx.modes:
            for f in ctx.me.followers:
                if f is not ctx.source:
                    E.give_keywords(f, Keyword.BARRIER)
        if 1 in ctx.modes:
            E.split_damage(ctx.state, 1 - ctx.controller, ctx.source.atk, ctx.source)


@register(CAGLIOSTRO.card_id)
class Cagliostro(CardScript):
    """Fanfare: gain 2 earth sigils; add an Ars Magna to your hand. Skybound Art: evolve
    this follower. Super Skybound Art: gain Crest: Cagliostro."""
    skybound = True

    def fanfare(self, ctx):
        common.gain_earth_sigils(ctx, 2)
        E.add_to_hand(ctx.state, ctx.controller, ARS_MAGNA)
        if E.skybound_art(ctx):
            _evolve_if_able(ctx, ctx.source)
        if E.super_skybound_art(ctx):
            E.add_to_leader_area(ctx.state, ctx.controller, CAGLIOSTRO_CREST)


# --- Basic -----------------------------------------------------------------------------------------

@register(DAZZLING_RUNEKNIGHT.card_id)
class DazzlingRuneknight(CardScript):
    """Fanfare: Mode: 1. Spellboost your hand twice. 2. Earth Rite (1): give this follower
    +2/+2 and Ward (selectable without sigils; then nothing happens: official Q&A)."""
    modes = (2, 1)

    def fanfare(self, ctx):
        if 0 in ctx.modes:
            _spellboost(ctx, 2)
        if 1 in ctx.modes and E.earth_rite(ctx.state, ctx.controller, 1):
            E.buff(ctx.state, ctx.source, 2, 2)
            E.give_keywords(ctx.source, Keyword.WARD)


@register(WITCHS_NEW_BREW.card_id)
class WitchsNewBrew(CardScript):
    """Fanfare: draw a card. Earth Sigil. Engage (1): gain an earth sigil."""
    engage_cost = 1

    def fanfare(self, ctx):
        E.draw(ctx.state, ctx.controller)

    def engage(self, ctx):
        common.gain_earth_sigils(ctx, 1)


@register(FORESIGHT.card_id)
class Foresight(CardScript):
    """Draw a card."""

    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller)


@register(TRUTH_SUMMONS.card_id)
class TruthSummons(CardScript):
    """Summon a Clay Golem."""

    def cast(self, ctx):
        _summon(ctx, CLAY_GOLEM)


@register(REMI_AND_RAMI.card_id)
class RemiAndRami(CardScript):
    """Fanfare: Earth Rite (1): summon a Guardian Golem. Super-Evolve: select an allied
    Golem follower, evolve it, and give it +3/+3."""
    super_evolve_targets = (TargetSpec(Target.ALLIED_FOLLOWER, filter=_is_golem),)

    def fanfare(self, ctx):
        if E.earth_rite(ctx.state, ctx.controller, 1):
            _summon(ctx, GUARDIAN_GOLEM)

    def on_super_evolve(self, ctx):
        for f in ctx.chosen():
            _evolve_if_able(ctx, f)
            if _on_field(ctx, f):
                E.buff(ctx.state, f, 3, 3)


@register(BLAZE_DESTROYER.card_id)
class BlazeDestroyer(_CostDownOnSpellboost):
    """On Spellboost: reduce the cost of this card by 1."""


@register(ARCANE_ERUPTION.card_id)
class ArcaneEruption(CardScript):
    """Deal 2 damage to all followers. Earth Rite (1): draw a card."""

    def cast(self, ctx):
        E.damage(ctx.state, _all_followers(ctx), 2, ctx.source)
        if E.earth_rite(ctx.state, ctx.controller, 1):
            E.draw(ctx.state, ctx.controller)
