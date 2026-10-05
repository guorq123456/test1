"""Dragoncraft: every Rotation card, its tokens, crests and alternate forms.

The Ramp Dragon starter deck came first (the first half of the module); the
rest of the Rotation pool follows, set by set, newest first. Card stats come
from the pool table (svsim/cards/pool.py); this module holds the abilities.
Comments give the official Simplified Chinese names.
"""
from svsim.cards import common
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

# --- the rest of the Rotation pool ---------------------------------------------------

# generated cards (keyword-only: no scripts)
FIRE_DRAKE_WHELP = card(90041110)  # 炽炎幼龙
VASTWING_DRAGON = card(90041120)  # 巨翼飞龙
MAJESTIC_MEGALORCA = card(90041130)  # 大海虎鲸

# crests
SPIRIT_OF_WADATSUMI_CREST = card(10841132)  # 纹章：沧海之精
DRACHE_AND_ALUZARD_CREST = card(10844112)  # 纹章：反照的赤红·德莱克&亚瑞札特
DRAGONS_VALE_ELDER_CREST = card(10744122)  # 纹章：龙峪的古龙
YUBE_CREST = card(10544122)  # 纹章：波摇花·夕夜
CRESCENT_TUBE_RIDE_CREST = card(10441312)  # 纹章：破浪新月

# set 10009: Revenants of Azvaldt
RIPPER_CLAWED_THIEF = card(10941110)  # 碎裂的盗匪
CAVE_DRAGON = card(10941120)  # 洞窟龙
DRAKE_WHELPS_TANTRUM = card(10941310)  # 幼龙闹脾气
HIGH_SPIRITED_MARAUDER = card(10942110)  # 绝倒的袭击者
DRAGONFOLK_BUTLER = card(10942120)  # 龙人管家
PARTING_JAWS = card(10942310)  # 颚口之别
BARREN_EARTH_TYRANT = card(10943110)  # 尘土的不法者
ARTIGLIO = card(10943310)  # 利牙
ANTEMARIA = card(10944110)  # 穿孔的罪人·安缇马丽亚

# set 10008: Chronicle of Destiny
GIDO = card(10841110)  # 狼人族首领·契特
SANDSTORM_WATCHDRAGON = card(10841120)  # 沙尘守宝龙
SPIRIT_OF_WADATSUMI = card(10841130)  # 沧海之精
REEF_AND_LOLO = card(10842110)  # 闪耀旋律·莉芙&萝萝
ART_OF_DECAY = card(10842310)  # 末世死化妆
GIADA = card(10843110)  # 穹顶的战火·杰亚达
EPHEMERAL_FOXFIRE = card(10843310)  # 狐火蜃景
DRACHE_AND_ALUZARD = card(10844110)  # 反照的赤红·德莱克&亚瑞札特

# set 10007: Anathema's Gambit
CARRIER_WYVERN = card(10741120)  # 载运飞龙
APATHETIC_GAZE = card(10741310)  # 百无聊赖的睥睨
GALLANT_GATEKEEPER = card(10742110)  # 豪龙守门人
DRACONIC_PART_TIMER = card(10742120)  # 龙族侍者
DRAGONEWT_PATHFINDER = card(10743110)  # 龙人先驱者
BLACKFLAME_DELUGE = card(10743310)  # 黑炎的奔流
DRAGONS_VALE_ELDER = card(10744120)  # 龙峪的古龙

# set 10006: Apocalypse Pact
RESOLUTE_DRAGONEWT = card(10641110)  # 决断的龙人
FRUITFISH = card(10641120)  # 熟透的海鱼
ADVENT_OF_THE_ELD_BLADES = card(10641310)  # 天刀授予
DECISIVE_SWORDMASTER = card(10642110)  # 果断的剑圣
SPIKED_DRAGON = card(10642120)  # 尖刺龙
IMPEDING_PUGILIST = card(10643110)  # 隔断的龙斗士
BEHEADING_ELD_BLADES = card(10643310)  # 断头的天刀

# set 10005: Blossoming Fate
SPRINGWELL_STEWARD = card(10541110)  # 涌泉打水人
STORMY_SHAMISEN_SHREDDER = card(10541120)  # 水滴打拍者
BLADE_OF_THE_CRESTPETAL = card(10541310)  # 波摇花的裁决
IRONMACE_DRAGOON = card(10542110)  # 铁锤龙骑士
JELLYFISH_DANCER = card(10542120)  # 水母舞姬
RUINBRINGER = card(10543110)  # 破灭屠戮者
YUBE = card(10544120)  # 波摇花·夕夜

# set 10000: Basic
SEARING_FIRENEWT = card(10041110)  # 烈焰火蜥蜴
AXE_WIELDING_DRAGONSLAYER = card(10041120)  # 战斧屠龙者 (Ward only: no script)
WARRIOR_OF_THE_DEEP = card(10041130)  # 凶鲨战士
STRIKE_OF_THE_DRAGONEWT = card(10041310)  # 龙人碎击
DRACONIC_BERSERKER = card(10042110)  # 猛攻的龙战士
BATTLEFORGED_DRAGON_KEEPER = card(10042120)  # 咆哮的驭龙使

# set 10004: Skybound Dragons
JOEL = card(10441110)  # 逐海之人·乔尔 (Ward, Aura only: no script)
MARI = card(10441120)  # 梅格的挚友·玛丽亲
CRESCENT_TUBE_RIDE = card(10441310)  # 破浪新月
IZMIR = card(10442110)  # 冰封的命运·伊什米尔
MUGEN = card(10442120)  # 淳朴的钢铁之躯·无限
MAXIMUM_LOVE_BOMB = card(10442310)  # 至爱狂轰
MEG = card(10443110)  # 平平无奇的女孩·梅格
PRIMAL_BEAST_ABSORPTION = card(10443310)  # 星晶兽吸收之力
WILNAS = card(10444110)  # 炎之法则·威尔纳斯

CARDS += [RIPPER_CLAWED_THIEF, CAVE_DRAGON, DRAKE_WHELPS_TANTRUM, HIGH_SPIRITED_MARAUDER,
          DRAGONFOLK_BUTLER, PARTING_JAWS, BARREN_EARTH_TYRANT, ARTIGLIO, ANTEMARIA,
          GIDO, SANDSTORM_WATCHDRAGON, SPIRIT_OF_WADATSUMI, REEF_AND_LOLO, ART_OF_DECAY, GIADA,
          EPHEMERAL_FOXFIRE, DRACHE_AND_ALUZARD,
          CARRIER_WYVERN, APATHETIC_GAZE, GALLANT_GATEKEEPER, DRACONIC_PART_TIMER,
          DRAGONEWT_PATHFINDER, BLACKFLAME_DELUGE, DRAGONS_VALE_ELDER,
          RESOLUTE_DRAGONEWT, FRUITFISH, ADVENT_OF_THE_ELD_BLADES, DECISIVE_SWORDMASTER,
          SPIKED_DRAGON, IMPEDING_PUGILIST, BEHEADING_ELD_BLADES,
          SPRINGWELL_STEWARD, STORMY_SHAMISEN_SHREDDER, BLADE_OF_THE_CRESTPETAL, IRONMACE_DRAGOON,
          JELLYFISH_DANCER, RUINBRINGER, YUBE,
          SEARING_FIRENEWT, AXE_WIELDING_DRAGONSLAYER, WARRIOR_OF_THE_DEEP,
          STRIKE_OF_THE_DRAGONEWT, DRACONIC_BERSERKER, BATTLEFORGED_DRAGON_KEEPER,
          JOEL, MARI, CRESCENT_TUBE_RIDE, IZMIR, MUGEN, MAXIMUM_LOVE_BOMB, MEG,
          PRIMAL_BEAST_ABSORPTION, WILNAS]
TOKENS += [FIRE_DRAKE_WHELP, VASTWING_DRAGON, MAJESTIC_MEGALORCA]
LEADER_AREA += [SPIRIT_OF_WADATSUMI_CREST, DRACHE_AND_ALUZARD_CREST, DRAGONS_VALE_ELDER_CREST,
                YUBE_CREST, CRESCENT_TUBE_RIDE_CREST]
# Cards with only keywords (or nothing) on them: they need no script.
KEYWORD_ONLY = [AXE_WIELDING_DRAGONSLAYER, JOEL, FIRE_DRAKE_WHELP, VASTWING_DRAGON,
                MAJESTIC_MEGALORCA]

MARINE = "Marine"
NO_LAST_WORDS = "no_last_words"   # counters flag: this card's Last Words were removed


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


# =====================================================================================
# The rest of the Rotation pool
# =====================================================================================

def _on_field(state, inst) -> bool:
    return state.on_field(inst.uid) is inst


def _random_enemy_follower(ctx) -> list:
    """A random enemy follower (random effects can hit Aura), as a 0- or 1-item list."""
    return E.random_sample(ctx.state, ctx.opponent.followers, 1)


def _discard_chosen(ctx) -> None:
    for c in ctx.chosen_hand():
        E.discard(ctx.state, c)


def _evolve_self(ctx, super_: bool = False) -> None:
    """"Evolve / Super-evolve this follower": an effect, so no points are spent
    and the follower's own Evolve / Super-Evolve abilities don't fire."""
    if not ctx.source.evolved and _on_field(ctx.state, ctx.source):
        E.evolve(ctx.state, ctx.source, super_=super_)


def _attacked_leader_last_turn(ctx) -> bool:
    """"If an allied follower attacked a leader on your last turn"."""
    return ctx.me.attacked_leader_last_turn


def _ten_max_pp(ctx) -> bool:
    return ctx.me.max_pp >= 10


def _add_to_hand_with_cost(ctx, defn, cost: int):
    added = E.add_to_hand(ctx.state, ctx.controller, defn)
    if added:
        E.set_cost(added, cost)
    return added


def _buff_in_hand(state, inst, atk: int, life: int) -> None:
    """Buff a card in hand. The new stats are also noted in its counters: the
    engine tells identical hand cards apart by id, cost, keywords and counters
    only, so without this a buffed copy would be merged with unbuffed ones."""
    E.buff(state, inst, atk, life)
    E.counters(inst)["hand_stats"] = (inst.atk, inst.life)


def _destroy_strongest_enemy(ctx) -> None:
    """Destroy a random enemy follower with the highest attack."""
    enemies = ctx.opponent.followers
    if enemies:
        top = max(f.atk for f in enemies)
        for f in E.random_sample(ctx.state, [f for f in enemies if f.atk == top], 1):
            E.destroy(ctx.state, f)


class _AttackTwice(CardScript):
    """Granted: "Can attack 2 times per turn"."""
    attacks_per_turn = 2


class _CantAttack(CardScript):
    """Granted: "Can't attack followers or leaders"."""
    cant_attack = True


ATTACK_TWICE = _AttackTwice()
CANT_ATTACK = _CantAttack()


# --- crests ------------------------------------------------------------------------------

@register(SPIRIT_OF_WADATSUMI_CREST.card_id)
class SpiritOfWadatsumiCrest(CardScript):
    """Whenever an allied Marine follower enters the field, give it +1/+1."""

    def on_ally_enter(self, ctx):
        if E.has_trait(ctx.other, MARINE) and _on_field(ctx.state, ctx.other):
            E.buff(ctx.state, ctx.other, 1, 1)


@register(DRACHE_AND_ALUZARD_CREST.card_id)
class DracheAndAluzardCrest(CardScript):
    """Countdown (2). Last Words: add a Drache & Aluzard to your hand and set its cost to 2."""

    def last_words(self, ctx):
        _add_to_hand_with_cost(ctx, DRACHE_AND_ALUZARD, 2)


@register(DRAGONS_VALE_ELDER_CREST.card_id)
class DragonsValeElderCrest(CardScript):
    """Countdown (2). At the end of your turn, summon a Vastwing Dragon."""

    def on_turn_end(self, ctx):
        E.summon(ctx.state, ctx.controller, VASTWING_DRAGON)


@register(YUBE_CREST.card_id)
class YubeCrest(CardScript):
    """Whenever an allied Marine follower attacks, give it +1/+0 until the end of the
    turn and, once on each of your turns, add a Majestic Megalorca to your hand."""

    def on_attack(self, ctx):
        attacker = ctx.other
        if attacker.owner != ctx.controller or not E.has_trait(attacker, MARINE):
            return
        if _on_field(ctx.state, attacker):
            E.buff(ctx.state, attacker, 1, 0, until_turn=common.end_of_turn(ctx))
        if common.during_your_turn(ctx) and E.once_per_turn(ctx, "megalorca"):
            E.add_to_hand(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)


@register(CRESCENT_TUBE_RIDE_CREST.card_id)
class CrescentTubeRideCrest(CardScript):
    """Countdown (4). At the end of your turn, give a random allied follower +1/+1."""

    def on_turn_end(self, ctx):
        for f in E.random_sample(ctx.state, ctx.me.followers, 1):
            E.buff(ctx.state, f, 1, 1)


# --- set 10009: Revenants of Azvaldt -------------------------------------------------------

@register(RIPPER_CLAWED_THIEF.card_id)
class RipperClawedThief(CardScript):
    """Fanfare: if an allied follower attacked a leader on your last turn, gain Storm.
    Last Words: add a Ripper-Clawed Thief to your hand and remove its Last Words."""

    def fanfare(self, ctx):
        if _attacked_leader_last_turn(ctx):
            E.give_keywords(ctx.source, Keyword.STORM)

    def last_words(self, ctx):
        if (ctx.source.counters or {}).get(NO_LAST_WORDS):
            return
        thief = E.add_to_hand(ctx.state, ctx.controller, RIPPER_CLAWED_THIEF)
        if thief:
            E.counters(thief)[NO_LAST_WORDS] = True


@register(CAVE_DRAGON.card_id)
class CaveDragon(CardScript):
    """Fanfare: if you're in Overflow, evolve this follower. Ambush."""

    def fanfare(self, ctx):
        if E.overflow(ctx.state, ctx.controller):
            _evolve_self(ctx)


@register(DRAKE_WHELPS_TANTRUM.card_id)
class DrakeWhelpsTantrum(CardScript):
    """Summon a Fire Drake Whelp. Enhance (3): also deal 3 damage to a random enemy follower."""
    enhance = (3,)

    def cast(self, ctx):
        E.summon(ctx.state, ctx.controller, FIRE_DRAKE_WHELP)
        if ctx.enhanced:
            E.damage(ctx.state, _random_enemy_follower(ctx), 3, ctx.source)


@register(HIGH_SPIRITED_MARAUDER.card_id)
class HighSpiritedMarauder(CardScript):
    """Storm. Strike: if an allied follower attacked a leader on your last turn, gain
    +1/+0 until the end of the turn."""

    def strike(self, ctx):
        if _attacked_leader_last_turn(ctx):
            E.buff(ctx.state, ctx.source, 1, 0, until_turn=common.end_of_turn(ctx))


@register(DRAGONFOLK_BUTLER.card_id)
class DragonfolkButler(CardScript):
    """Fanfare: restore 3 defense to your leader and recover 3 play points. Evolve:
    select another allied follower and give it +3/+3."""
    evolve_targets = common.OTHER_ALLIED_FOLLOWER

    def fanfare(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 3)
        E.recover_pp(ctx.state, ctx.controller, 3)

    def on_evolve(self, ctx):
        for f in ctx.chosen():
            E.buff(ctx.state, f, 3, 3)


@register(PARTING_JAWS.card_id)
class PartingJaws(CardScript):
    """Select 2 cards in your hand and discard them. Deal 3 damage to a random enemy
    follower and the enemy leader."""
    play_targets = (TargetSpec(Target.HAND_CARD, 2),)

    def cast(self, ctx):
        _discard_chosen(ctx)
        E.damage(ctx.state, _random_enemy_follower(ctx) + [common.enemy_leader(ctx)], 3,
                 ctx.source)


@register(BARREN_EARTH_TYRANT.card_id)
class BarrenEarthTyrant(CardScript):
    """Fanfare: deal 4 damage to a random enemy follower, twice if an allied follower
    attacked a leader on your last turn. Evolve: summon a High-Spirited Marauder."""

    def fanfare(self, ctx):
        for _ in range(2 if _attacked_leader_last_turn(ctx) else 1):
            E.damage(ctx.state, _random_enemy_follower(ctx), 4, ctx.source)

    def on_evolve(self, ctx):
        E.summon(ctx.state, ctx.controller, HIGH_SPIRITED_MARAUDER)


@register(ARTIGLIO.card_id)
class Artiglio(CardScript):
    """Deal 3 damage split between all enemy followers, 6 if an allied follower
    attacked a leader on your last turn."""

    def cast(self, ctx):
        amount = 6 if _attacked_leader_last_turn(ctx) else 3
        E.split_damage(ctx.state, 1 - ctx.controller, amount, ctx.source)


@register(ANTEMARIA.card_id)
class Antemaria(CardScript):
    """Fanfare: if an allied follower attacked a leader on your last turn, gain Storm.
    Rush. Ignores Ward."""
    # APPROX: the engine has no "Ignores Ward" (engine._attack_actions always
    # enforces Ward), so enemy Ward followers still restrict this follower's
    # attacks. The flag below documents the property for when it is supported.
    ignores_ward = True

    def fanfare(self, ctx):
        if _attacked_leader_last_turn(ctx):
            E.give_keywords(ctx.source, Keyword.STORM)


# --- set 10008: Chronicle of Destiny --------------------------------------------------------

@register(GIDO.card_id)
class Gido(CardScript):
    """Fanfare: if your leader's defense is 10 or less, evolve this follower. Bane. Ward."""

    def fanfare(self, ctx):
        if ctx.me.leader_hp <= 10:
            _evolve_self(ctx)


@register(SANDSTORM_WATCHDRAGON.card_id)
class SandstormWatchdragon(CardScript):
    """Ward. Last Words: draw 3 cards."""

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller, 3)


@register(SPIRIT_OF_WADATSUMI.card_id)
class SpiritOfWadatsumi(CardScript):
    """Fanfare: add a Majestic Megalorca to your hand. Evolve: gain Crest: Spirit of
    Wadatsumi."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)

    def on_evolve(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, SPIRIT_OF_WADATSUMI_CREST)


@register(REEF_AND_LOLO.card_id)
class ReefAndLolo(CardScript):
    """Fanfare: summon a Reef & Lolo. Rush. At the end of your turn, add a Majestic
    Megalorca to your hand."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, REEF_AND_LOLO)

    def on_turn_end(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)


@register(ART_OF_DECAY.card_id)
class ArtOfDecay(CardScript):
    """Deal 4 damage to a random enemy follower. Deal 4 damage to the enemy leader."""

    def cast(self, ctx):
        E.damage(ctx.state, _random_enemy_follower(ctx), 4, ctx.source)
        E.damage(ctx.state, [common.enemy_leader(ctx)], 4, ctx.source)


@register(GIADA.card_id)
class Giada(CardScript):
    """Rush. Intimidate. Strike: gain Barrier; if attacking a follower, also gain
    "Can attack 2 times per turn" until the end of the turn."""

    def strike(self, ctx):
        E.give_keywords(ctx.source, Keyword.BARRIER)
        if ctx.other is not None and not any(g.script is ATTACK_TWICE
                                             for g in ctx.source.grants or ()):
            E.grant(ctx.source, ATTACK_TWICE, until_turn=common.end_of_turn(ctx))


@register(EPHEMERAL_FOXFIRE.card_id)
class EphemeralFoxfire(CardScript):
    """Select an enemy follower or the enemy leader and deal it 1 damage. Put an
    Ephemeral Foxfire into your deck. If you're in Overflow, draw a card."""
    play_targets = common.ENEMY_FOLLOWER_OR_LEADER

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 1, ctx.source)
        E.put_into_deck(ctx.state, ctx.controller, EPHEMERAL_FOXFIRE)
        if E.overflow(ctx.state, ctx.controller):
            E.draw(ctx.state, ctx.controller)


def _other_drache_entries(ctx) -> int:
    """Other allied Drache & Aluzards that entered the field this match."""
    # APPROX: the engine keeps no per-name log of field entries, so this counts
    # the allied copies destroyed this match plus the other copies on the field
    # now. Copies that left the field by being banished, returned to hand or
    # transformed are missed.
    me, cid = ctx.me, DRACHE_AND_ALUZARD.card_id
    destroyed = sum(d.card_id == cid for d in me.destroyed)
    on_field = sum(c.defn.card_id == cid and c is not ctx.source for c in me.field)
    return destroyed + on_field


@register(DRACHE_AND_ALUZARD.card_id)
class DracheAndAluzard(CardScript):
    """Fanfare: gain +X/+X, X = other allied Drache & Aluzards that entered the field
    this match; if X is at least 2, evolve this follower. Ward. Last Words: gain
    Crest: Drache & Aluzard."""

    def fanfare(self, ctx):
        x = _other_drache_entries(ctx)
        if x:
            E.buff(ctx.state, ctx.source, x, x)
        if x >= 2:
            _evolve_self(ctx)

    def last_words(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, DRACHE_AND_ALUZARD_CREST)


# --- set 10007: Anathema's Gambit -------------------------------------------------------------

@register(CARRIER_WYVERN.card_id)
class CarrierWyvern(CardScript):
    """Fanfare: select another allied follower and give it +2/+2. Evolve: select a
    follower in your hand and give it +2/+2."""
    play_targets = common.OTHER_ALLIED_FOLLOWER
    evolve_targets = (TargetSpec(Target.HAND_CARD,
                                 filter=lambda state, player, card: card.defn.is_follower),)

    def fanfare(self, ctx):
        for f in ctx.chosen():
            E.buff(ctx.state, f, 2, 2)

    def on_evolve(self, ctx):
        for c in ctx.chosen_hand():
            _buff_in_hand(ctx.state, c, 2, 2)


@register(APATHETIC_GAZE.card_id)
class ApatheticGaze(CardScript):
    """Gain 1 max play point. Transform every Apathetic Gaze in your hand and deck into
    a Lazing Flame."""

    def cast(self, ctx):
        E.gain_max_pp(ctx.state, ctx.controller)
        for c in [c for c in ctx.me.hand + ctx.me.deck if c.defn.card_id == APATHETIC_GAZE.card_id]:
            E.transform(ctx.state, c, LAZING_FLAME)


@register(GALLANT_GATEKEEPER.card_id)
class GallantGatekeeper(CardScript):
    """Fanfare: select an enemy follower and destroy it. Ward."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        for f in ctx.chosen():
            E.destroy(ctx.state, f)


@register(DRACONIC_PART_TIMER.card_id)
class DraconicPartTimer(CardScript):
    """Fanfare: if you have 10 max play points, evolve this follower. At the end of
    your turn, restore 1 defense to your leader (2 if this follower is evolved)."""

    def fanfare(self, ctx):
        if _ten_max_pp(ctx):
            _evolve_self(ctx)

    def on_turn_end(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 2 if ctx.source.evolved else 1)


@register(DRAGONEWT_PATHFINDER.card_id)
class DragonewtPathfinder(CardScript):
    """Fanfare: destroy a random enemy follower with the highest attack, and Mode:
    1. evolve this follower; 2. give this follower Ambush."""
    modes = (2, 1)

    def fanfare(self, ctx):
        _destroy_strongest_enemy(ctx)
        if 0 in ctx.modes:
            _evolve_self(ctx)
        if 1 in ctx.modes:
            E.give_keywords(ctx.source, Keyword.AMBUSH)


@register(BLACKFLAME_DELUGE.card_id)
class BlackflameDeluge(CardScript):
    """Deal 5 damage to all enemy followers. Deal 3 damage to the enemy leader."""

    def cast(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 5, ctx.source)
        E.damage(ctx.state, [common.enemy_leader(ctx)], 3, ctx.source)


@register(DRAGONS_VALE_ELDER.card_id)
class DragonsValeElder(CardScript):
    """Fanfare: summon a Vastwing Dragon and gain Crest: Dragon's Vale Elder. Ward.
    Super-Evolve: delay the count of that crest by 2."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, VASTWING_DRAGON)
        E.add_to_leader_area(ctx.state, ctx.controller, DRAGONS_VALE_ELDER_CREST)

    def on_super_evolve(self, ctx):
        crest = E.leader_area_card(ctx.state, ctx.controller, DRAGONS_VALE_ELDER_CREST)
        if crest is not None:
            E.advance_countdown(ctx.state, crest, -2)


# --- set 10006: Apocalypse Pact -----------------------------------------------------------------

@register(RESOLUTE_DRAGONEWT.card_id)
class ResoluteDragonewt(CardScript):
    """Fanfare: select a card in your hand and discard it. Last Words: draw 2 cards."""
    play_targets = common.HAND_CARD

    def fanfare(self, ctx):
        _discard_chosen(ctx)

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)


@register(FRUITFISH.card_id)
class Fruitfish(CardScript):
    """Enhance (6): summon 2 Fruitfish. Last Words: restore 1 defense to your leader."""
    enhance = (6,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            for _ in range(2):
                E.summon(ctx.state, ctx.controller, FRUITFISH)

    def last_words(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 1)


@register(ADVENT_OF_THE_ELD_BLADES.card_id)
class AdventOfTheEldBlades(CardScript):
    """Select an allied follower and give it +2/+2. When discarded, if its cost is 4,
    add an Advent of the Eld Blades to your hand and set its cost to 2."""
    play_targets = common.ALLIED_FOLLOWER

    def cast(self, ctx):
        for f in ctx.chosen():
            E.buff(ctx.state, f, 2, 2)

    def on_discard(self, ctx):
        if ctx.source.cost == 4:
            _add_to_hand_with_cost(ctx, ADVENT_OF_THE_ELD_BLADES, 2)


@register(DECISIVE_SWORDMASTER.card_id)
class DecisiveSwordmaster(CardScript):
    """Fanfare: select a card in your hand and discard it. Rush. Barrier."""
    play_targets = common.HAND_CARD

    def fanfare(self, ctx):
        _discard_chosen(ctx)


@register(SPIKED_DRAGON.card_id)
class SpikedDragon(CardScript):
    """At the end of your turn, evolve this follower. When this follower evolves (any
    way), deal 3 damage to all enemies."""

    def on_turn_end(self, ctx):
        _evolve_self(ctx)

    def on_evolved(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers) + [common.enemy_leader(ctx)], 3,
                 ctx.source)


@register(IMPEDING_PUGILIST.card_id)
class ImpedingPugilist(CardScript):
    """Fanfare: select a card in your hand and discard it; deal 6 damage to a random
    enemy follower. Ward. Barrier. Evolve: replicate the Fanfare."""
    play_targets = common.HAND_CARD
    evolve_targets = common.HAND_CARD

    def fanfare(self, ctx):
        self._impede(ctx)

    def on_evolve(self, ctx):
        self._impede(ctx)

    def _impede(self, ctx):
        _discard_chosen(ctx)
        E.damage(ctx.state, _random_enemy_follower(ctx), 6, ctx.source)


@register(BEHEADING_ELD_BLADES.card_id)
class BeheadingEldBlades(CardScript):
    """Deal X damage to all enemy followers, X = this card's cost. When discarded, if
    its cost is 7, add a Beheading Eld Blades costing 5 to your hand; if 5, one
    costing 3."""

    def cast(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), ctx.source.cost, ctx.source)

    def on_discard(self, ctx):
        new_cost = {7: 5, 5: 3}.get(ctx.source.cost)
        if new_cost is not None:
            _add_to_hand_with_cost(ctx, BEHEADING_ELD_BLADES, new_cost)


# --- set 10005: Blossoming Fate -------------------------------------------------------------------

@register(SPRINGWELL_STEWARD.card_id)
class SpringwellSteward(CardScript):
    """Evolve: select an enemy follower and deal it 5 damage. Super-Evolve: select 2
    enemy followers instead."""
    # APPROX: the engine offers one target list for both kinds of evolution, so two
    # picks are always offered. A normal evolve hits only the first pick; a
    # super-evolve hits both (picking the same follower twice hits it once).
    evolve_targets = (TargetSpec(Target.ENEMY_FOLLOWER), TargetSpec(Target.ENEMY_FOLLOWER))

    def on_evolve(self, ctx):
        uids = ctx.targets if ctx.super_ else ctx.targets[:1]
        victims = [f for f in (ctx.state.on_field(uid) for uid in dict.fromkeys(uids))
                   if f is not None]
        E.damage(ctx.state, victims, 5, ctx.source)


@register(STORMY_SHAMISEN_SHREDDER.card_id)
class StormyShamisenShredder(CardScript):
    """Fanfare: summon a Majestic Megalorca. Whenever an allied Marine follower enters
    the field, restore 2 defense to your leader."""

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)

    def on_ally_enter(self, ctx):
        if E.has_trait(ctx.other, MARINE):
            E.heal_leader(ctx.state, ctx.controller, 2)


@register(BLADE_OF_THE_CRESTPETAL.card_id)
class BladeOfTheCrestpetal(CardScript):
    """Draw a follower. Deal X damage to a random enemy follower, X = the cost of the
    card drawn."""

    def cast(self, ctx):
        followers = [c for c in ctx.me.deck if c.defn.is_follower]
        E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.is_follower)
        left = {id(c) for c in ctx.me.deck}
        drawn = [c for c in followers if id(c) not in left]
        if drawn:
            # UNSURE: with a full hand the drawn card is destroyed; X still uses its cost.
            E.damage(ctx.state, _random_enemy_follower(ctx), drawn[0].cost, ctx.source)


@register(IRONMACE_DRAGOON.card_id)
class IronmaceDragoon(CardScript):
    """Fanfare: select an enemy follower and deal it 7 damage. Summon a Vastwing Dragon."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 7, ctx.source)
        E.summon(ctx.state, ctx.controller, VASTWING_DRAGON)


@register(JELLYFISH_DANCER.card_id)
class JellyfishDancer(CardScript):
    """Fanfare: add a Majestic Megalorca to your hand. Whenever an allied Marine
    follower enters the field, give this follower Rush and Bane."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)

    def on_ally_enter(self, ctx):
        if E.has_trait(ctx.other, MARINE):
            E.give_keywords(ctx.source, Keyword.RUSH | Keyword.BANE)


@register(RUINBRINGER.card_id)
class Ruinbringer(CardScript):
    """Super-Evolve: banish every 1-, 3-, 5-, 7- and 9-cost card in your deck, then deal
    X damage split between all enemy followers, X = the number banished."""

    def on_super_evolve(self, ctx):
        doomed = [c for c in ctx.me.deck if c.cost in (1, 3, 5, 7, 9)]
        for c in doomed:
            E.banish(ctx.state, c)
        E.split_damage(ctx.state, 1 - ctx.controller, len(doomed), ctx.source)


@register(YUBE.card_id)
class Yube(CardScript):
    """Fanfare: summon a Majestic Megalorca. Evolve: select a card in your hand and
    discard it; gain Crest: Yube, Crestpetal."""
    evolve_targets = common.HAND_CARD

    def fanfare(self, ctx):
        E.summon(ctx.state, ctx.controller, MAJESTIC_MEGALORCA)

    def on_evolve(self, ctx):
        _discard_chosen(ctx)
        E.add_to_leader_area(ctx.state, ctx.controller, YUBE_CREST)


# --- set 10000: Basic ---------------------------------------------------------------------------

@register(SEARING_FIRENEWT.card_id)
class SearingFirenewt(CardScript):
    """Fanfare: select an enemy follower and deal it 1 damage."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 1, ctx.source)


@register(WARRIOR_OF_THE_DEEP.card_id)
class WarriorOfTheDeep(CardScript):
    """Fanfare: deal 6 damage to the enemy leader."""

    def fanfare(self, ctx):
        E.damage(ctx.state, [common.enemy_leader(ctx)], 6, ctx.source)


@register(STRIKE_OF_THE_DRAGONEWT.card_id)
class StrikeOfTheDragonewt(CardScript):
    """Select an enemy follower and deal it 2 damage, 4 if you're in Overflow."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4 if E.overflow(ctx.state, ctx.controller) else 2,
                 ctx.source)


@register(DRACONIC_BERSERKER.card_id)
class DraconicBerserker(CardScript):
    """Evolve: select an enemy follower and deal it 4 damage. Super-Evolve: deal the
    damage to all enemy followers instead."""
    evolve_targets = common.ENEMY_FOLLOWER

    def on_evolve(self, ctx):
        targets = list(ctx.opponent.followers) if ctx.super_ else ctx.chosen()
        E.damage(ctx.state, targets, 4, ctx.source)


@register(BATTLEFORGED_DRAGON_KEEPER.card_id)
class BattleforgedDragonKeeper(CardScript):
    """Enhance (7): summon a Vastwing Dragon."""
    enhance = (7,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.summon(ctx.state, ctx.controller, VASTWING_DRAGON)


# --- set 10004: Skybound Dragons ------------------------------------------------------------------

@register(MARI.card_id)
class Mari(CardScript):
    """Activates in hand: whenever a 3-base-cost allied follower super-evolves, set this
    card's cost to 0 until the end of the turn. At the end of your turn, give a random
    super-evolved allied follower +1/+1."""
    listen_in_hand = True

    def on_ally_evolve(self, ctx):
        if (ctx.super_ and ctx.other.defn.cost == 3
                and ctx.state.in_hand(ctx.controller, ctx.source.uid) is ctx.source):
            E.set_cost(ctx.source, 0, until_turn=common.end_of_turn(ctx))

    def on_turn_end(self, ctx):
        if not _on_field(ctx.state, ctx.source):     # turn hooks also fire in hand
            return
        supers = [f for f in ctx.me.followers if f.super_evolved]
        for f in E.random_sample(ctx.state, supers, 1):
            E.buff(ctx.state, f, 1, 1)


@register(CRESCENT_TUBE_RIDE.card_id)
class CrescentTubeRide(CardScript):
    """Gain Crest: Crescent Tube Ride."""

    def cast(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, CRESCENT_TUBE_RIDE_CREST)


@register(IZMIR.card_id)
class Izmir(CardScript):
    """Fanfare: if you have 10 max play points, evolve this follower. When this
    follower evolves (any way), deal 3 damage to all enemy followers."""

    def fanfare(self, ctx):
        if _ten_max_pp(ctx):
            _evolve_self(ctx)

    def on_evolved(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 3, ctx.source)


@register(MUGEN.card_id)
class Mugen(CardScript):
    """Fanfare: Super Skybound Art - gain Storm. Super-Evolve: select 2 enemy followers
    and destroy them."""
    skybound = True
    evolve_targets = (TargetSpec(Target.ENEMY_FOLLOWER, 2),)

    def fanfare(self, ctx):
        if E.super_skybound_art(ctx):
            E.give_keywords(ctx.source, Keyword.STORM)

    def on_super_evolve(self, ctx):
        for f in ctx.chosen():
            E.destroy(ctx.state, f)


@register(MAXIMUM_LOVE_BOMB.card_id)
class MaximumLoveBomb(CardScript):
    """Select an enemy follower, deal it 3 damage, and give it "Can't attack followers
    or leaders" until the end of your opponent's turn."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        for f in ctx.chosen():
            E.damage(ctx.state, [f], 3, ctx.source)
            if _on_field(ctx.state, f):
                E.grant(f, CANT_ATTACK, until_turn=common.end_of_opponents_turn(ctx))


@register(MEG.card_id)
class Meg(CardScript):
    """Fanfare: Skybound Art - super-evolve this follower. Whenever a 2-base-cost
    allied follower enters the field, give this follower Ward."""
    skybound = True

    def fanfare(self, ctx):
        if E.skybound_art(ctx):
            _evolve_self(ctx, super_=True)

    def on_ally_enter(self, ctx):
        if ctx.other.defn.cost == 2:
            E.give_keywords(ctx.source, Keyword.WARD)


@register(PRIMAL_BEAST_ABSORPTION.card_id)
class PrimalBeastAbsorption(CardScript):
    """Select an enemy card on the field, banish it, and add a copy of it (a fresh card
    of the same name) to your hand."""
    play_targets = (TargetSpec(Target.ENEMY_CARD),)

    def cast(self, ctx):
        for target in ctx.chosen():
            if E.banish(ctx.state, target):
                E.add_to_hand(ctx.state, ctx.controller, target.defn)


@register(WILNAS.card_id)
class Wilnas(CardScript):
    """Fanfare: select an enemy follower and deal it 8 damage. Intimidate. Evolve:
    replicate the Fanfare."""
    play_targets = common.ENEMY_FOLLOWER
    evolve_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 8, ctx.source)

    def on_evolve(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 8, ctx.source)
