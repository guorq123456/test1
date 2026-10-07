"""Portalcraft cards and the cards they generate.

Card stats come from the pool table (svsim/cards/pool.py); this module holds
the abilities. Comments give the official Simplified Chinese names.
"""
from svsim.cards import common
from svsim.cards.pool import POOL, card
from svsim.core import effects as E
from svsim.core.enums import Craft, Keyword
from svsim.core.script import CardScript, Target, TargetSpec, prop, register

ARTIFACT = "Artifact"
PUPPETRY = "Puppetry"

# --- tokens ---
PUPPET = card(90071110)  # 悬丝傀儡
ENHANCED_PUPPET = card(90071120)  # 改良型·悬丝傀儡
ANALYZING_ARTIFACT = card(90071130)  # 解析的创造物
ANCIENT_ARTIFACT = card(90071140)  # 古老的创造物 (keywords only)
MYSTIC_ARTIFACT = card(90071150)  # 神秘的创造物 (keywords only)
RADIANT_ARTIFACT = card(90071160)  # 绚烂的创造物 (keywords only)
GEAR_OF_AMBITION = card(90071210)  # 未来核心
GEAR_OF_REMEMBRANCE = card(90071220)  # 过往核心
STRIKER_ARTIFACT = card(90072110)  # 攻击创造物
FORTIFIER_ARTIFACT = card(90072120)  # 城堡创造物
OMINOUS_ARTIFACT_ALPHA = card(90073110)  # 毁灭创造物α
OMINOUS_ARTIFACT_BETA = card(90073120)  # 毁灭创造物β
OMINOUS_ARTIFACT_GAMMA = card(90073130)  # 毁灭创造物γ
MASTERWORK_ARTIFACT_OMEGA = card(90074110)  # 卓越创造物Ω
IMARIS_LITTLE_BUDDIES = card(90074140)  # 伊鞠的小鬼 (keywords only)
WARDEN_OF_THE_TRIGGER = card(90074150)  # 击针看守
DEPTHS_OF_THE_ELD_AXE = card(90074320)  # 天斧深渊

# --- leader area / alternate forms ---
LU_WOH_CREST = card(10474112)  # 纹章：光之法则·龙敖
SLAUS_CREST = card(10574112)  # 纹章：转动的《命运之轮》·斯洛士
CUTTHROAT_CREST = card(10974112)  # 纹章：束刃的罪人·卡特斯罗特
SHODDY_PLAYTHING_ACCELERATE = card(10671112)  # 低劣的玩具（激奏）
SUBSTANDARD_PUPPET_ACCELERATE = card(10672112)  # 拙劣的人偶（激奏）
LUDICROUS_ORDNANCE_ACCELERATE = card(10673112)  # 愚劣的兵器（激奏）

# --- set 10009 ---
BLUERUST_UNDERLING = card(10971110)  # 青锈小卒
TWINDRONE_ENGINEER = card(10971120)  # 双子无人机少女
DIMENSIONAL_SELECTION = card(10971310)  # 次元选定
IRONWORK_BODYGUARD = card(10972110)  # 锻磨保镖
BLADE_PUPPETEER = card(10972120)  # 刀线客
DISGRACEFUL_BANISHMENT = card(10972310)  # 屈辱流放
STEELFORGED_RIGHT_HAND = card(10973110)  # 铸铁亲信
SOULFORGE = card(10973310)  # 白牙燐敛
CUTTHROAT = card(10974110)  # 束刃的罪人·卡特斯罗特
AIZEDEN = card(10974120)  # 弹哭的变貌·艾兹伊甸

# --- set 10008 ---
KRATOS = card(10871110)  # 满溢的幸福·库伦特司
LEONA = card(10871120)  # 过度守护者·莉欧娜
ZERK = card(10871130)  # 器械操纵者·吉尔克
LAYLA = card(10872110)  # 人造的馈赠·蕾拉
LAZULI = card(10872120)  # 门扉接续者·拉姿莉
UNSULLIED_DAYS = card(10872310)  # 纯净无垢的日常
MIRIAM = card(10873110)  # 知恩图报·米莉亚姆
THE_JOURNEY_AHEAD = card(10873310)  # 开辟未来
ASHER_AND_LYDIA = card(10874110)  # 决断的交错·亚修雷&莉缇雅
EUDIE = card(10874120)  # 你的前辈·欧丝

# --- set 10007 ---
BRUSQUE_BARKEEP = card(10771110)  # 个性店主
BEAT_BREAKER = card(10771120)  # 炫酷舞者
FREERUNNING = card(10771310)  # 跑酷
COOL_COURIER = card(10772110)  # 悠然的滑手
AUDACIOUS_ARTIST = card(10772120)  # 大胆的涂鸦师
BLINK_STEP = card(10772310)  # 闪光一瞬
BRAZEN_BROADCASTER = card(10773110)  # 狂野播报员
WARP_SLASH = card(10773310)  # 瞬移斩击
SCARLET = card(10774110)  # 虚刻的安纳提玛·斯卡雷特
MYUU = card(10774120)  # 奋厉追赶·米乌

# --- set 10006 ---
SHODDY_PLAYTHING = card(10671110)  # 低劣的玩具
BRILLIANT_INVENTOR = card(10671120)  # 聪明的创造者
ADVENT_OF_THE_ELD_AXE = card(10671310)  # 天斧授予
SUBSTANDARD_PUPPET = card(10672110)  # 拙劣的人偶
TIMID_PIONEER = card(10672120)  # 胆小鬼先锋
MYRIAD_DESIGNS = card(10672310)  # 平庸的制图
LUDICROUS_ORDNANCE = card(10673110)  # 愚劣的兵器
UNFEELING_ELD_AXE = card(10673310)  # 恶劣的天斧
CAMISCILLA = card(10674110)  # 恶劣的纯心·卡密希拉
YOG_ZENTHA = card(10674120)  # 古旧天斧·尤泽塔

# --- set 10005 ---
MARIONETTE_MASTER = card(10571110)  # 舞台缔造者
FLOWERING_ARTISAN = card(10571120)  # 繁花技师
LIGHT_OF_THE_DEWDROP = card(10571310)  # 尽小花的临照
NEW_AGE_CARTOGRAPHER = card(10572110)  # 新时代地理学者
LUNAR_BUNNY = card(10572120)  # 清宵玉兔
RESURRECTION_TUNER = card(10572310)  # 苏生调律
NEURON_DISRUPTER = card(10573110)  # 神经遮蔽者
SINCERITY_OF_THE_DEWDROP = card(10573310)  # 诚心的尽小花
SLAUS = card(10574110)  # 转动的《命运之轮》·斯洛士
IMARI = card(10574120)  # 尽小花·伊鞠

# --- set 10000 (Basic) ---
KITTY_CANNONEER = card(10071110)  # 炮击猫兽人
PUPPET_LANCER = card(10071120)  # 人偶长矛手
MECHANIZED_BEAST = card(10071130)  # 兽性铁人 (keywords only)
BULLET_FROM_BEYOND = card(10071310)  # 来自异次元的枪击
ELECTRIC_WHIP_LASS = card(10072110)  # 电鞭手
MECHA_CAVALIER = card(10072120)  # 魔钢骑兵
PUPPET_THEATER = card(10072210)  # 人偶剧场

# --- set 10004 ---
SHO = card(10471110)  # 夜王再起·翔
TSUBASA = card(10471120)  # 爆燃老大·翼
ISAAC = card(10471130)  # 报恩工匠·艾萨克
EUSTACE = card(10472110)  # 轰雷闪狼·尤斯提斯
ILSA = card(10472120)  # 严厉的教官·伊尔莎
STONE_BREAKER = card(10472310)  # 身无长物唯有石
CASSIUS = card(10473110)  # 向往天空的回归者·卡西乌斯
CHAOS_LEGION = card(10473310)  # 混沌军势
LU_WOH = card(10474110)  # 光之法则·龙敖
BEELZEBUB = card(10474120)  # 唯一王者·别西卜

CARDS = [
    BLUERUST_UNDERLING, TWINDRONE_ENGINEER, DIMENSIONAL_SELECTION, IRONWORK_BODYGUARD,
    BLADE_PUPPETEER, DISGRACEFUL_BANISHMENT, STEELFORGED_RIGHT_HAND, SOULFORGE, CUTTHROAT,
    AIZEDEN,
    KRATOS, LEONA, ZERK, LAYLA, LAZULI, UNSULLIED_DAYS, MIRIAM, THE_JOURNEY_AHEAD,
    ASHER_AND_LYDIA, EUDIE,
    BRUSQUE_BARKEEP, BEAT_BREAKER, FREERUNNING, COOL_COURIER, AUDACIOUS_ARTIST, BLINK_STEP,
    BRAZEN_BROADCASTER, WARP_SLASH, SCARLET, MYUU,
    SHODDY_PLAYTHING, BRILLIANT_INVENTOR, ADVENT_OF_THE_ELD_AXE, SUBSTANDARD_PUPPET,
    TIMID_PIONEER, MYRIAD_DESIGNS, LUDICROUS_ORDNANCE, UNFEELING_ELD_AXE, CAMISCILLA,
    YOG_ZENTHA,
    MARIONETTE_MASTER, FLOWERING_ARTISAN, LIGHT_OF_THE_DEWDROP, NEW_AGE_CARTOGRAPHER,
    LUNAR_BUNNY, RESURRECTION_TUNER, NEURON_DISRUPTER, SINCERITY_OF_THE_DEWDROP, SLAUS, IMARI,
    KITTY_CANNONEER, PUPPET_LANCER, MECHANIZED_BEAST, BULLET_FROM_BEYOND, ELECTRIC_WHIP_LASS,
    MECHA_CAVALIER, PUPPET_THEATER,
    SHO, TSUBASA, ISAAC, EUSTACE, ILSA, STONE_BREAKER, CASSIUS, CHAOS_LEGION, LU_WOH,
    BEELZEBUB,
]
TOKENS = [PUPPET, ENHANCED_PUPPET, ANALYZING_ARTIFACT, ANCIENT_ARTIFACT, MYSTIC_ARTIFACT,
          RADIANT_ARTIFACT, GEAR_OF_AMBITION, GEAR_OF_REMEMBRANCE, STRIKER_ARTIFACT,
          FORTIFIER_ARTIFACT, OMINOUS_ARTIFACT_ALPHA, OMINOUS_ARTIFACT_BETA,
          OMINOUS_ARTIFACT_GAMMA, MASTERWORK_ARTIFACT_OMEGA, IMARIS_LITTLE_BUDDIES,
          WARDEN_OF_THE_TRIGGER, DEPTHS_OF_THE_ELD_AXE]
LEADER_AREA = [LU_WOH_CREST, SLAUS_CREST, CUTTHROAT_CREST]
ALTERNATE_FORMS = [SHODDY_PLAYTHING_ACCELERATE, SUBSTANDARD_PUPPET_ACCELERATE,
                   LUDICROUS_ORDNANCE_ACCELERATE]
# Cards with only keywords (or nothing) on them: they need no script.
VANILLA = [MECHANIZED_BEAST, ANCIENT_ARTIFACT, MYSTIC_ARTIFACT, RADIANT_ARTIFACT,
           IMARIS_LITTLE_BUDDIES]


# --- helpers ---------------------------------------------------------------------------

def is_artifact_follower(c) -> bool:
    return c.defn.is_follower and E.has_trait(c, ARTIFACT)


def base_cost_5_plus(c) -> bool:
    return c.defn.cost >= 5


def no_duplicates(state, player: int) -> bool:
    return E.no_duplicates_in_deck(state.players[player])


def unevolved(state, player, c) -> bool:
    return not c.evolved


def on_field(ctx) -> bool:
    return ctx.state.in_play(ctx.source.uid) is ctx.source


summon = E.summon
summon_copy = E.summon_copy


def damage_random_enemy_followers(ctx, amount: int, times: int) -> None:
    """Do this `times` times: deal `amount` damage to a random enemy follower."""
    for _ in range(times):
        E.damage(ctx.state, E.random_sample(ctx.state, ctx.opponent.followers, 1), amount,
                 ctx.source)


def draw_bane_follower(ctx) -> None:
    """Draw a Portalcraft follower with Bane."""
    E.draw_matching(ctx.state, ctx.controller,
                    lambda c: c.defn.craft == Craft.PORTAL and c.defn.is_follower
                    and c.has(Keyword.BANE))


def draw_distinct(state, player: int, predicate, k: int) -> None:
    """Draw k differently named cards matching `predicate`."""
    p = state.players[player]
    names = set()
    for _ in range(k):
        matches = [c for c in p.deck if predicate(c) and c.defn.name not in names]
        if not matches:
            return
        chosen = state.rng.choice(matches)
        names.add(chosen.defn.name)
        E.draw_matching(state, player, lambda c, chosen=chosen: c is chosen)


def lower_attack_until(state, inst, n: int, until_turn: int) -> None:
    """-n/-0 until the end of a turn. Only the attack actually removed is given back:
    effects.buff clamps attack at 0 but restores the full amount on expiry."""
    E.buff(state, inst, -min(n, inst.atk), 0, until_turn=until_turn)


remove_all_abilities = E.silence


def artifacts_entered(state, player: int) -> int:
    """Differently named allied Artifact followers that entered the field this match."""
    names = set()
    for cid in state.players[player].entered:
        defn = POOL.get(cid)
        if defn is not None and ARTIFACT in defn.traits:
            names.add(defn.name)
    return len(names)


def three_artifacts(ctx) -> bool:
    return artifacts_entered(ctx.state, ctx.controller) >= 3


# --- tokens ------------------------------------------------------------------------------

@register(PUPPET.card_id, ENHANCED_PUPPET.card_id)
class Puppet(CardScript):
    """Rush. At the end of your opponent's turn, destroy this card."""

    def on_opponent_turn_end(self, ctx):
        E.destroy(ctx.state, ctx.source)


@register(ANALYZING_ARTIFACT.card_id)
class AnalyzingArtifact(CardScript):
    """When this card enters the field, draw a card."""

    def on_enter(self, ctx):
        E.draw(ctx.state, ctx.controller)


class Gear(CardScript):
    """Fuse: Artifact amulets. When you Fuse to this card, transform it. Can't be played."""
    unplayable = True
    fuse_filter = staticmethod(lambda c: c.defn.is_amulet and E.has_trait(c, ARTIFACT))
    becomes = None

    def on_fuse(self, ctx):
        E.transform(ctx.state, ctx.source, self.becomes)


@register(GEAR_OF_AMBITION.card_id)
class GearOfAmbition(Gear):
    """Fuse: Artifact amulets. When you Fuse to this card, transform it into a Striker
    Artifact. Can't be played."""
    becomes = STRIKER_ARTIFACT


@register(GEAR_OF_REMEMBRANCE.card_id)
class GearOfRemembrance(Gear):
    """Fuse: Artifact amulets. When you Fuse to this card, transform it into a Fortifier
    Artifact. Can't be played."""
    becomes = FORTIFIER_ARTIFACT


def ominous_for(total_cost: int):
    if total_cost >= 3:
        return OMINOUS_ARTIFACT_GAMMA
    return {1: OMINOUS_ARTIFACT_ALPHA, 2: OMINOUS_ARTIFACT_BETA}.get(total_cost)


@register(STRIKER_ARTIFACT.card_id, FORTIFIER_ARTIFACT.card_id)
class StrikerFortifierArtifact(CardScript):
    """Fuse: Artifact cards. When you Fuse to this card, transform it by the total cost
    fused: 1 = Ominous Artifact α, 2 = β, 3 or more = γ. (Rush / Ward.)"""
    fuse_filter = staticmethod(lambda c: E.has_trait(c, ARTIFACT))

    def on_fuse(self, ctx):
        target = ominous_for(sum(c.cost for c in ctx.cards))
        if target is not None:
            E.transform(ctx.state, ctx.source, target)


@register(OMINOUS_ARTIFACT_ALPHA.card_id)
class OminousArtifactAlpha(CardScript):
    """Fuse: Ominous Artifact β and γ. When both have been fused to it (over any number
    of turns), transform it into a Masterwork Artifact Ω. At the end of your turn,
    restore 3 defense to your leader."""
    fuse_filter = staticmethod(lambda c: c.defn.card_id in (OMINOUS_ARTIFACT_BETA.card_id,
                                                           OMINOUS_ARTIFACT_GAMMA.card_id))

    def on_fuse(self, ctx):
        fused = E.counters(ctx.source).get("fused", ())
        if OMINOUS_ARTIFACT_BETA.card_id in fused and OMINOUS_ARTIFACT_GAMMA.card_id in fused:
            E.transform(ctx.state, ctx.source, MASTERWORK_ARTIFACT_OMEGA)

    def on_turn_end(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 3)


@register(OMINOUS_ARTIFACT_BETA.card_id)
class OminousArtifactBeta(CardScript):
    """At the end of your turn, deal 3 damage to the enemy leader."""

    def on_turn_end(self, ctx):
        E.damage(ctx.state, [common.enemy_leader(ctx)], 3, ctx.source)


@register(OMINOUS_ARTIFACT_GAMMA.card_id)
class OminousArtifactGamma(CardScript):
    """At the end of your turn, deal 3 damage to all enemy followers."""

    def on_turn_end(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 3, ctx.source)


@register(MASTERWORK_ARTIFACT_OMEGA.card_id)
class MasterworkArtifactOmega(CardScript):
    """Fanfare: deal 5 damage to all enemy followers and restore 5 defense to your
    leader. Storm, Ward, Aura."""

    def fanfare(self, ctx):
        E.damage(ctx.state, list(ctx.opponent.followers), 5, ctx.source)
        E.heal_leader(ctx.state, ctx.controller, 5)


@register(WARDEN_OF_THE_TRIGGER.card_id)
class WardenOfTheTrigger(CardScript):
    """Ward. Last Words: restore 2 defense to your leader."""

    def last_words(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 2)


@register(DEPTHS_OF_THE_ELD_AXE.card_id)
class DepthsOfTheEldAxe(CardScript):
    """Select an allied follower with a base cost of 5 or more; add a card of the same
    name to your hand and reduce its cost by 3."""
    play_targets = (TargetSpec(Target.ALLIED_FOLLOWER,
                               filter=lambda s, p, c: base_cost_5_plus(c)),)

    def cast(self, ctx):
        for f in ctx.chosen():
            copy = E.add_to_hand(ctx.state, ctx.controller, f.defn)   # a same-name card, not an exact copy
            if copy is not None:
                E.add_cost(copy, -3)


# --- leader area / alternate forms ---------------------------------------------------------

# 玩家确认的解读（官方原文没写明，测试会话 2026-10-07 的核对标出）：机锋的纹章只在真的进化了随从时才消耗「每回合一次」。
@register(CUTTHROAT_CREST.card_id)
class CutthroatCrest(CardScript):
    """Once on each of your turns, when you play a follower, evolve it."""

    def on_play(self, ctx):
        other = ctx.other
        if ctx.as_spell or not other.defn.is_follower:
            return
        # Confirmed by the player: the once-per-turn use is only spent on an actual
        # evolution (not when the follower is already evolved, or gone).
        if ctx.state.on_field(other.uid) is other and not other.evolved \
                and E.once_per_turn(ctx, "cutthroat"):
            E.evolve(ctx.state, other)


@register(LU_WOH_CREST.card_id)
class LuWohCrest(CardScript):
    """Countdown (2). Whenever an enemy follower with Storm attacks a leader, give it
    -3/-0 until the end of the turn."""

    def on_attack(self, ctx):
        attacker = ctx.other
        if attacker.owner != ctx.controller and attacker.has(Keyword.STORM) and ctx.target < 0:
            lower_attack_until(ctx.state, attacker, 3, common.end_of_turn(ctx))


def wheel_of_fortune(ctx, options) -> None:
    """Activate a random option that this card hasn't activated yet."""
    used = E.counters(ctx.source).setdefault("wheel", [])
    left = [i for i in range(len(options)) if i not in used]
    if not left:
        return
    pick = ctx.state.rng.choice(left)
    used.append(pick)
    options[pick](ctx)


def _hand_cost(n):
    def apply(ctx):
        for c in list(ctx.me.hand):
            E.add_cost(c, n, until_turn=common.end_of_turn(ctx))
    return apply


def _all_allies(n):
    def apply(ctx):
        for f in list(ctx.me.followers):
            E.buff(ctx.state, f, n, n)
    return apply


SLAUS_GOOD = (_hand_cost(-1), _all_allies(2), lambda ctx: E.heal_leader(ctx.state, ctx.controller, 3))
SLAUS_BAD = (_hand_cost(1), _all_allies(-2),
             lambda ctx: E.damage(ctx.state, [common.own_leader(ctx)], 3, ctx.source))


# 玩家确认的解读（官方原文没写明，测试会话 2026-10-07 的核对标出）：斯洛士给对手的纹章在吟唱归零那回合仍发动第 3 项。
@register(SLAUS_CREST.card_id)
class SlausCrest(CardScript):
    """Countdown (3). At the start of your turn, activate a random one not yet activated
    of: 1. +1 cost to all cards in your hand until the end of the turn. 2. All allied
    followers -2/-2. 3. Deal 3 damage to your leader."""

    def on_turn_start(self, ctx):
        wheel_of_fortune(ctx, SLAUS_BAD)

    def last_words(self, ctx):
        # Confirmed by the player: the ability still activates on the turn the count
        # reaches 0. The engine destroys a countdown crest at 0 before its start-of-turn
        # ability would be queued, so its Last Words does it instead.
        if ctx.source.countdown is not None and ctx.source.countdown <= 0:
            wheel_of_fortune(ctx, SLAUS_BAD)


@register(SHODDY_PLAYTHING_ACCELERATE.card_id)
class ShoddyPlaythingAccelerate(CardScript):
    """Accelerate (2): summon a Shoddy Plaything."""

    def cast(self, ctx):
        summon(ctx.state, ctx.controller, SHODDY_PLAYTHING)


@register(SUBSTANDARD_PUPPET_ACCELERATE.card_id)
class SubstandardPuppetAccelerate(CardScript):
    """Accelerate (3): summon 2 Substandard Puppets."""

    def cast(self, ctx):
        for _ in range(2):
            summon(ctx.state, ctx.controller, SUBSTANDARD_PUPPET)


@register(LUDICROUS_ORDNANCE_ACCELERATE.card_id)
class LudicrousOrdnanceAccelerate(CardScript):
    """Accelerate (4): summon a Ludicrous Ordnance."""

    def cast(self, ctx):
        summon(ctx.state, ctx.controller, LUDICROUS_ORDNANCE)


# --- set 10009 -------------------------------------------------------------------------------

HIGHLANDER_ENEMY = (TargetSpec(Target.ENEMY_FOLLOWER, filter=lambda s, p, c: no_duplicates(s, p)),)


@register(BLUERUST_UNDERLING.card_id)
class BluerustUnderling(CardScript):
    """Fanfare: if there are no duplicates in your deck, select an enemy follower and
    deal it 5 damage. Rush."""
    play_targets = HIGHLANDER_ENEMY

    def fanfare(self, ctx):
        if no_duplicates(ctx.state, ctx.controller):
            E.damage(ctx.state, ctx.chosen(), 5, ctx.source)


@register(TWINDRONE_ENGINEER.card_id)
class TwindroneEngineer(CardScript):
    """Fanfare: summon an Analyzing Artifact. Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        summon(ctx.state, ctx.controller, ANALYZING_ARTIFACT)

    on_evolve = fanfare


@register(DIMENSIONAL_SELECTION.card_id)
class DimensionalSelection(CardScript):
    """Mode: 1. Deal 5 damage to all enemy followers. 2. Summon 2 Mystic Artifacts."""
    modes = (2, 1)

    def cast(self, ctx):
        if 0 in ctx.modes:
            E.damage(ctx.state, list(ctx.opponent.followers), 5, ctx.source)
        if 1 in ctx.modes:
            for _ in range(2):
                summon(ctx.state, ctx.controller, MYSTIC_ARTIFACT)


# 玩家确认的解读（官方原文没写明，测试会话 2026-10-07 的核对标出）：锻磨保镖没有可选随从时照样回复 4 点。
@register(IRONWORK_BODYGUARD.card_id)
class IronworkBodyguard(CardScript):
    """Fanfare: if there are no duplicates in your deck, select an enemy follower, deal
    it 4 damage and restore 4 defense to your leader. Ward."""
    play_targets = HIGHLANDER_ENEMY

    def fanfare(self, ctx):
        if no_duplicates(ctx.state, ctx.controller):
            E.damage(ctx.state, ctx.chosen(), 4, ctx.source)
            # Confirmed by the player: the defense is restored even with no enemy follower.
            E.heal_leader(ctx.state, ctx.controller, 4)


@register(BLADE_PUPPETEER.card_id)
class BladePuppeteer(CardScript):
    """Fanfare: summon an Enhanced Puppet and a Puppet. Whenever an allied Puppetry
    follower enters the field, deal 1 damage to the enemy leader."""

    def fanfare(self, ctx):
        summon(ctx.state, ctx.controller, ENHANCED_PUPPET)
        summon(ctx.state, ctx.controller, PUPPET)

    def on_ally_enter(self, ctx):
        if E.has_trait(ctx.other, PUPPETRY):
            E.damage(ctx.state, [common.enemy_leader(ctx)], 1, ctx.source)


@register(DISGRACEFUL_BANISHMENT.card_id)
class DisgracefulBanishment(CardScript):
    """Select a card in your hand and discard it. Draw a Portalcraft follower with Bane.
    Then, if there are no duplicates in your deck, draw 2 cards."""
    play_targets = common.HAND_CARD

    def cast(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        draw_bane_follower(ctx)
        if no_duplicates(ctx.state, ctx.controller):
            E.draw(ctx.state, ctx.controller, 2)


@register(STEELFORGED_RIGHT_HAND.card_id)
class SteelforgedRightHand(CardScript):
    """Fanfare: select an enemy follower and destroy it. If there are no duplicates in
    your deck, give this follower Storm."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        if no_duplicates(ctx.state, ctx.controller):
            E.give_keywords(ctx.source, Keyword.STORM)


@register(SOULFORGE.card_id)
class Soulforge(CardScript):
    """Select an enemy follower and destroy it. If there are no duplicates in your deck,
    destroy all enemy followers instead."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        targets = list(ctx.opponent.followers) if no_duplicates(ctx.state, ctx.controller) \
            else ctx.chosen()
        for target in targets:
            E.destroy(ctx.state, target)


@register(CUTTHROAT.card_id)
class Cutthroat(CardScript):
    """Bane. Evolve: draw a Portalcraft follower with Bane. Then, if there are no
    duplicates in your deck, gain Crest: Cutthroat, Fluxblade Convict."""

    def on_evolve(self, ctx):
        draw_bane_follower(ctx)
        if no_duplicates(ctx.state, ctx.controller):
            E.add_to_leader_area(ctx.state, ctx.controller, CUTTHROAT_CREST)


@register(AIZEDEN.card_id)
class Aizeden(CardScript):
    """Fanfare: summon a Warden of the Trigger. Whenever an allied Artifact follower
    enters the field, destroy a random enemy follower. Super-Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        summon(ctx.state, ctx.controller, WARDEN_OF_THE_TRIGGER)

    on_super_evolve = fanfare

    def on_ally_enter(self, ctx):
        if is_artifact_follower(ctx.other):
            for target in E.random_sample(ctx.state, ctx.opponent.followers, 1):
                E.destroy(ctx.state, target)


# --- set 10008 -------------------------------------------------------------------------------

@register(KRATOS.card_id)
class Kratos(CardScript):
    """Ward. Last Words: summon a Kratos, Everyday Joy and remove Last Words from it."""

    def last_words(self, ctx):
        kratos = summon(ctx.state, ctx.controller, KRATOS)
        if kratos is not None:
            E.remove_last_words(kratos)


@register(LEONA.card_id)
class Leona(CardScript):
    """Ward. Super-Evolve: select another allied follower and give it Ambush."""
    evolve_targets = common.OTHER_ALLIED_FOLLOWER

    def on_super_evolve(self, ctx):
        for f in ctx.chosen():
            E.give_keywords(f, Keyword.AMBUSH)


# 玩家确认的解读（官方原文没写明，测试会话 2026-10-07 的核对标出）：随机加入手牌时按被破坏的次数加权。
@register(ZERK.card_id)
class Zerk(CardScript):
    """Fanfare: add a card named like a random allied Artifact follower destroyed this
    match to your hand."""

    def fanfare(self, ctx):
        # Confirmed by the player: random over destroyed cards, weighted by how often each
        # was destroyed, like Reanimate.
        destroyed = [d for d in ctx.me.destroyed if ARTIFACT in d.traits]
        if destroyed:
            E.add_to_hand(ctx.state, ctx.controller, ctx.state.rng.choice(destroyed))


@register(LAYLA.card_id)
class Layla(CardScript):
    """Rush. Last Words: add an Ancient Artifact to your hand."""

    def last_words(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, ANCIENT_ARTIFACT)


@register(LAZULI.card_id)
class Lazuli(CardScript):
    """Fanfare: add a Radiant Artifact to your hand."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, RADIANT_ARTIFACT)


@register(UNSULLIED_DAYS.card_id)
class UnsulliedDays(CardScript):
    """Draw 2 cards. If you've unlocked super-evolution, restore 2 defense to your leader."""

    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)
        if E.super_evolution_unlocked(ctx.state, ctx.controller):
            E.heal_leader(ctx.state, ctx.controller, 2)


@register(MIRIAM.card_id)
class Miriam(CardScript):
    """Fanfare: select an enemy follower and destroy it. Summon a Radiant Artifact."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        summon(ctx.state, ctx.controller, RADIANT_ARTIFACT)


@register(THE_JOURNEY_AHEAD.card_id)
class TheJourneyAhead(CardScript):
    """Select an enemy follower and deal it 6 damage. If at least 3 differently named
    allied Artifact followers have entered the field this match, recover 1 evolution point."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 6, ctx.source)
        if three_artifacts(ctx):
            E.recover_ep(ctx.state, ctx.controller, 1)


@register(ASHER_AND_LYDIA.card_id)
class AsherAndLydia(CardScript):
    """Fanfare: select an enemy follower and give it Ward. Enhance (9): evolve this
    follower and give it Storm. When this follower evolves, destroy 2 random enemy
    followers with Ward."""
    play_targets = common.ENEMY_FOLLOWER
    enhance = (9,)

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.give_keywords(target, Keyword.WARD)
        if ctx.enhanced:
            if not ctx.source.evolved:
                E.evolve(ctx.state, ctx.source)
            E.give_keywords(ctx.source, Keyword.STORM)

    def on_evolved(self, ctx):
        wards = [f for f in ctx.opponent.followers if f.has(Keyword.WARD)]
        for target in E.random_sample(ctx.state, wards, 2):
            E.destroy(ctx.state, target)


@register(EUDIE.card_id)
class Eudie(CardScript):
    """Fanfare: add an Analyzing Artifact to your hand. Evolve: select another unevolved
    allied follower and evolve it."""
    evolve_targets = (TargetSpec(Target.ALLIED_FOLLOWER, other=True, filter=unevolved),)

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, ANALYZING_ARTIFACT)

    def on_evolve(self, ctx):
        for f in ctx.chosen():
            if not f.evolved:
                E.evolve(ctx.state, f)


# --- set 10007 -------------------------------------------------------------------------------

@register(BRUSQUE_BARKEEP.card_id)
class BrusqueBarkeep(CardScript):
    """Whenever an allied Artifact follower enters the field, restore 1 defense to your
    leader. Evolve: summon a Mystic Artifact."""

    def on_ally_enter(self, ctx):
        if is_artifact_follower(ctx.other):
            E.heal_leader(ctx.state, ctx.controller, 1)

    def on_evolve(self, ctx):
        summon(ctx.state, ctx.controller, MYSTIC_ARTIFACT)


@register(BEAT_BREAKER.card_id)
class BeatBreaker(CardScript):
    """Fanfare: summon a Beat Breaker; if at least 3 differently named allied Artifact
    followers have entered the field this match, summon 2 instead. Rush."""

    def fanfare(self, ctx):
        for _ in range(2 if three_artifacts(ctx) else 1):
            summon(ctx.state, ctx.controller, BEAT_BREAKER)


@register(FREERUNNING.card_id)
class Freerunning(CardScript):
    """Mode: 1. Add an Analyzing Artifact to your hand. 2. Add an Ancient Artifact to
    your hand. If at least 3 differently named allied Artifact followers have entered
    the field this match, activate both instead."""
    modes = (2, 1)

    def all_modes(self, state, card, enhanced):
        return artifacts_entered(state, card.owner) >= 3

    def cast(self, ctx):
        if 0 in ctx.modes:
            E.add_to_hand(ctx.state, ctx.controller, ANALYZING_ARTIFACT)
        if 1 in ctx.modes:
            E.add_to_hand(ctx.state, ctx.controller, ANCIENT_ARTIFACT)


@register(COOL_COURIER.card_id)
class CoolCourier(CardScript):
    """Fanfare: add an Ancient Artifact to your hand. Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, ANCIENT_ARTIFACT)

    on_evolve = fanfare


@register(AUDACIOUS_ARTIST.card_id)
class AudaciousArtist(CardScript):
    """Fanfare: select an enemy follower and destroy it. If at least 3 differently named
    allied Artifact followers have entered the field this match, summon an Ancient
    Artifact and a Mystic Artifact."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        if three_artifacts(ctx):
            summon(ctx.state, ctx.controller, ANCIENT_ARTIFACT)
            summon(ctx.state, ctx.controller, MYSTIC_ARTIFACT)


@register(BLINK_STEP.card_id)
class BlinkStep(CardScript):
    """Give all allied followers +1/+0. If you've unlocked super-evolution, give all
    followers in your hand +1/+0."""

    def cast(self, ctx):
        for f in list(ctx.me.followers):
            E.buff(ctx.state, f, 1, 0)
        if E.super_evolution_unlocked(ctx.state, ctx.controller):
            for c in [c for c in ctx.me.hand if c.defn.is_follower]:
                E.buff(ctx.state, c, 1, 0)


@register(BRAZEN_BROADCASTER.card_id)
class BrazenBroadcaster(CardScript):
    """Fanfare: summon an Analyzing Artifact. Enhance (5): also summon a Mystic Artifact.
    Whenever an allied Artifact follower enters the field, give it Rush."""
    enhance = (5,)

    def fanfare(self, ctx):
        summon(ctx.state, ctx.controller, ANALYZING_ARTIFACT)
        if ctx.enhanced:
            summon(ctx.state, ctx.controller, MYSTIC_ARTIFACT)

    def on_ally_enter(self, ctx):
        if is_artifact_follower(ctx.other):
            E.give_keywords(ctx.other, Keyword.RUSH)


@register(WARP_SLASH.card_id)
class WarpSlash(CardScript):
    """Deal X damage to all enemy followers, X = differently named allied Artifact
    followers that entered the field this match. Deal 1 damage to the enemy leader."""

    def cast(self, ctx):
        x = artifacts_entered(ctx.state, ctx.controller)
        E.damage(ctx.state, list(ctx.opponent.followers), x, ctx.source)
        E.damage(ctx.state, [common.enemy_leader(ctx)], 1, ctx.source)


@register(SCARLET.card_id)
class Scarlet(CardScript):
    """Fanfare: deal X damage to all enemy followers, X = differently named allied
    Artifact followers that entered the field this match. Storm, Ward."""

    def fanfare(self, ctx):
        x = artifacts_entered(ctx.state, ctx.controller)
        E.damage(ctx.state, list(ctx.opponent.followers), x, ctx.source)


@register(MYUU.card_id)
class Myuu(CardScript):
    """Whenever an allied Artifact follower enters the field, deal 3 damage to a random
    enemy follower. Evolve: summon an Ancient Artifact. Super-Evolve: then, if at least
    3 differently named allied Artifact followers have entered the field this match,
    give this follower Storm."""

    def on_ally_enter(self, ctx):
        if is_artifact_follower(ctx.other):
            damage_random_enemy_followers(ctx, 3, 1)

    def on_evolve(self, ctx):
        summon(ctx.state, ctx.controller, ANCIENT_ARTIFACT)

    def on_super_evolve(self, ctx):
        if three_artifacts(ctx):
            E.give_keywords(ctx.source, Keyword.STORM)


# --- set 10006 -------------------------------------------------------------------------------

@register(SHODDY_PLAYTHING.card_id)
class ShoddyPlaything(CardScript):
    """Fanfare: draw 3 cards. Ward. Accelerate (2): see ShoddyPlaythingAccelerate."""

    def fanfare(self, ctx):
        E.draw(ctx.state, ctx.controller, 3)


@register(BRILLIANT_INVENTOR.card_id)
class BrilliantInventor(CardScript):
    """Fanfare: summon an Ominous Artifact α and give it Bane and Ward."""

    def fanfare(self, ctx):
        alpha = summon(ctx.state, ctx.controller, OMINOUS_ARTIFACT_ALPHA)
        if alpha is not None:
            E.give_keywords(alpha, Keyword.BANE | Keyword.WARD)


def big_ally_on_field(ctx) -> bool:
    return any(base_cost_5_plus(f) for f in ctx.me.followers)


@register(ADVENT_OF_THE_ELD_AXE.card_id)
class AdventOfTheEldAxe(CardScript):
    """Select an enemy follower and deal it 4 damage. If there's an allied follower with
    a base cost of 5 or more on the field, draw a card."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4, ctx.source)
        if big_ally_on_field(ctx):
            E.draw(ctx.state, ctx.controller)


@register(SUBSTANDARD_PUPPET.card_id)
class SubstandardPuppet(CardScript):
    """Fanfare: summon a Substandard Puppet, and evolve it and this follower.
    Accelerate (3): see SubstandardPuppetAccelerate."""

    def fanfare(self, ctx):
        twin = summon(ctx.state, ctx.controller, SUBSTANDARD_PUPPET)
        for f in (twin, ctx.source):
            if f is not None and ctx.state.on_field(f.uid) is f and not f.evolved:
                E.evolve(ctx.state, f)


@register(TIMID_PIONEER.card_id)
class TimidPioneer(CardScript):
    """Fanfare: select an enemy follower with 3 defense or less and banish it. Ambush."""
    play_targets = (TargetSpec(Target.ENEMY_FOLLOWER, filter=lambda s, p, c: c.life <= 3),)

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.banish(ctx.state, target)


@register(MYRIAD_DESIGNS.card_id)
class MyriadDesigns(CardScript):
    """Summon a Ludicrous Ordnance, a Shoddy Plaything and a Substandard Puppet, and give
    them +0/+1."""

    def cast(self, ctx):
        for defn in (LUDICROUS_ORDNANCE, SHODDY_PLAYTHING, SUBSTANDARD_PUPPET):
            f = summon(ctx.state, ctx.controller, defn)
            if f is not None:
                E.buff(ctx.state, f, 0, 1)


def split_three(ctx) -> None:
    E.split_damage(ctx.state, 1 - ctx.controller, 3, ctx.source)


@register(LUDICROUS_ORDNANCE.card_id)
class LudicrousOrdnance(CardScript):
    """Fanfare: summon 2 Ludicrous Ordnances. At the end of your turn, deal 3 damage
    split between all enemy followers. Evolve: do that too. Accelerate (4): see
    LudicrousOrdnanceAccelerate."""

    def fanfare(self, ctx):
        for _ in range(2):
            summon(ctx.state, ctx.controller, LUDICROUS_ORDNANCE)

    def on_turn_end(self, ctx):
        split_three(ctx)

    def on_evolve(self, ctx):
        split_three(ctx)


@register(UNFEELING_ELD_AXE.card_id)
class UnfeelingEldAxe(CardScript):
    """Activates in hand: whenever an allied follower with a base cost of 5 or more enters
    the field, reduce this card's cost by 1 until the end of the turn. Evolve a random
    unevolved allied follower with a base cost of 5 or more; deal 6 damage to a random
    enemy follower."""
    listen_in_hand = True

    def on_ally_enter(self, ctx):
        if base_cost_5_plus(ctx.other) and ctx.state.in_hand(ctx.controller, ctx.source.uid):
            E.add_cost(ctx.source, -1, until_turn=common.end_of_turn(ctx))

    def cast(self, ctx):
        big = [f for f in ctx.me.followers if base_cost_5_plus(f) and not f.evolved]
        for f in E.random_sample(ctx.state, big, 1):
            E.evolve(ctx.state, f)
        damage_random_enemy_followers(ctx, 6, 1)


@register(CAMISCILLA.card_id)
class Camiscilla(CardScript):
    """Fanfare: summon a Shoddy Plaything and a Substandard Puppet. Whenever another
    allied follower with a base cost of 5 or more enters the field, evolve it.
    Super-Evolve: deal X damage to the enemy leader, X = allied followers on the field
    with a base cost of 5 or more."""

    def fanfare(self, ctx):
        summon(ctx.state, ctx.controller, SHODDY_PLAYTHING)
        summon(ctx.state, ctx.controller, SUBSTANDARD_PUPPET)

    def on_ally_enter(self, ctx):
        other = ctx.other
        if base_cost_5_plus(other) and ctx.state.on_field(other.uid) is other and not other.evolved:
            E.evolve(ctx.state, other)

    def on_super_evolve(self, ctx):
        x = sum(base_cost_5_plus(f) for f in ctx.me.followers)
        E.damage(ctx.state, [common.enemy_leader(ctx)], x, ctx.source)


@register(YOG_ZENTHA.card_id)
class YogZentha(CardScript):
    """Fanfare: if there's an allied follower with a base cost of 5 or more on the field,
    add a Depths of the Eld Axe to your hand. Rush."""

    def fanfare(self, ctx):
        if big_ally_on_field(ctx):
            E.add_to_hand(ctx.state, ctx.controller, DEPTHS_OF_THE_ELD_AXE)


# --- set 10005 -------------------------------------------------------------------------------

@register(MARIONETTE_MASTER.card_id)
class MarionetteMaster(CardScript):
    """Fanfare: summon an Enhanced Puppet and a Puppet. Enhance (7): give them Storm."""
    enhance = (7,)

    def fanfare(self, ctx):
        for defn in (ENHANCED_PUPPET, PUPPET):
            puppet = summon(ctx.state, ctx.controller, defn)
            if puppet is not None and ctx.enhanced:
                E.give_keywords(puppet, Keyword.STORM)


@register(FLOWERING_ARTISAN.card_id)
class FloweringArtisan(CardScript):
    """Fanfare: draw a spell. Whenever you play a spell, deal 3 damage to all enemy followers."""

    def fanfare(self, ctx):
        E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.is_spell)

    def on_play(self, ctx):
        if ctx.as_spell:
            E.damage(ctx.state, list(ctx.opponent.followers), 3, ctx.source)


@register(LIGHT_OF_THE_DEWDROP.card_id)
class LightOfTheDewdrop(CardScript):
    """Draw a card."""

    def cast(self, ctx):
        E.draw(ctx.state, ctx.controller)


@register(NEW_AGE_CARTOGRAPHER.card_id)
class NewAgeCartographer(CardScript):
    """Fanfare: add an Ominous Artifact β to your hand. Super-Evolve: select an Artifact
    follower in your hand that costs 5 or less and summon an exact copy of it."""
    evolve_targets = (TargetSpec(Target.HAND_CARD,
                                 filter=lambda s, p, c: is_artifact_follower(c) and c.cost <= 5),)

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, OMINOUS_ARTIFACT_BETA)

    def on_super_evolve(self, ctx):
        for c in ctx.chosen_hand():
            summon_copy(ctx.state, ctx.controller, c)


@register(LUNAR_BUNNY.card_id)
class LunarBunny(CardScript):
    """Ward. When you play a spell, evolve this follower."""

    def on_play(self, ctx):
        if ctx.as_spell and not ctx.source.evolved:
            E.evolve(ctx.state, ctx.source)


@register(RESURRECTION_TUNER.card_id)
class ResurrectionTuner(CardScript):
    """Select a card in your hand and discard it. Add cards named like 2 random
    differently named allied followers destroyed this match to your hand."""
    play_targets = common.HAND_CARD

    def cast(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        by_name = {}
        for d in ctx.me.destroyed:
            by_name.setdefault(d.name, d)
        for defn in E.random_sample(ctx.state, list(by_name.values()), 2):
            E.add_to_hand(ctx.state, ctx.controller, defn)


@register(NEURON_DISRUPTER.card_id)
class NeuronDisrupter(CardScript):
    """Fanfare: recover X play points, X = other allied followers on the field. Rush.
    Last Words: draw 2 cards."""

    def fanfare(self, ctx):
        x = sum(1 for f in ctx.me.followers if f is not ctx.source)
        E.recover_pp(ctx.state, ctx.controller, x)

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)


@register(SINCERITY_OF_THE_DEWDROP.card_id)
class SincerityOfTheDewdrop(CardScript):
    """Select a card on the field and transform it into an Imari's Little Buddies."""
    play_targets = (TargetSpec(Target.ANY_CARD),)

    def cast(self, ctx):
        for target in ctx.chosen():
            E.transform(ctx.state, target, IMARIS_LITTLE_BUDDIES)


@register(SLAUS.card_id)
class Slaus(CardScript):
    """Ambush. At the end of your turn, if evolved, give your opponent Crest: Slaus and
    banish this card. At the start of your turn, activate a random one not yet activated
    of: 1. -1 cost to all cards in your hand until the end of the turn. 2. All allied
    followers +2/+2. 3. Restore 3 defense to your leader."""

    def on_turn_end(self, ctx):
        if ctx.source.evolved:
            E.add_to_leader_area(ctx.state, 1 - ctx.controller, SLAUS_CREST)
            E.banish(ctx.state, ctx.source)

    def on_turn_start(self, ctx):
        wheel_of_fortune(ctx, SLAUS_GOOD)


@register(IMARI.card_id)
class Imari(CardScript):
    """Fanfare: select a card in your hand and discard it; draw a spell. Whenever you play
    a spell, if this follower is evolved, summon an Imari's Little Buddies. Super-Evolve:
    draw 2 differently named 1-cost spells."""
    play_targets = common.HAND_CARD

    def fanfare(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.is_spell)

    def on_play(self, ctx):
        if ctx.as_spell and ctx.source.evolved:
            summon(ctx.state, ctx.controller, IMARIS_LITTLE_BUDDIES)

    def on_super_evolve(self, ctx):
        draw_distinct(ctx.state, ctx.controller, lambda c: c.defn.is_spell and c.cost == 1, 2)


# --- set 10000 (Basic) -------------------------------------------------------------------------

@register(KITTY_CANNONEER.card_id)
class KittyCannoneer(CardScript):
    """Fanfare: add a Gear of Ambition to your hand. Rush."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, GEAR_OF_AMBITION)


@register(PUPPET_LANCER.card_id)
class PuppetLancer(CardScript):
    """Fanfare: add an Enhanced Puppet to your hand."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, ENHANCED_PUPPET)


@register(BULLET_FROM_BEYOND.card_id)
class BulletFromBeyond(CardScript):
    """Select an enemy follower and destroy it. Add a Gear of Ambition and a Gear of
    Remembrance to your hand."""
    play_targets = common.ENEMY_FOLLOWER

    def cast(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)
        E.add_to_hand(ctx.state, ctx.controller, GEAR_OF_AMBITION)
        E.add_to_hand(ctx.state, ctx.controller, GEAR_OF_REMEMBRANCE)


@register(ELECTRIC_WHIP_LASS.card_id)
class ElectricWhipLass(CardScript):
    """Fanfare: add a Gear of Remembrance to your hand."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, GEAR_OF_REMEMBRANCE)


@register(MECHA_CAVALIER.card_id)
class MechaCavalier(CardScript):
    """Ward. Evolve: summon a Mecha Cavalier. Super-Evolve: summon 2 instead."""

    def on_evolve(self, ctx):
        for _ in range(2 if ctx.super_ else 1):
            summon(ctx.state, ctx.controller, MECHA_CAVALIER)


@register(PUPPET_THEATER.card_id)
class PuppetTheater(CardScript):
    """Fanfare: add a Puppet to your hand. Countdown (2). At the end of your turn, add a
    Puppet to your hand."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, PUPPET)

    on_turn_end = fanfare


# --- set 10004 ---------------------------------------------------------------------------------

@register(SHO.card_id)
class Sho(CardScript):
    """Fanfare: if you've unlocked super-evolution, give this follower Barrier. Storm."""

    def fanfare(self, ctx):
        if E.super_evolution_unlocked(ctx.state, ctx.controller):
            E.give_keywords(ctx.source, Keyword.BARRIER)


@register(TSUBASA.card_id)
class Tsubasa(CardScript):
    """Fanfare: increase the Skybound Art gauges of all cards in your hand by 1. Rush."""

    def fanfare(self, ctx):
        for c in ctx.me.hand:
            if prop(c, "skybound"):
                E.counters(c)["skybound"] = E.counters(c).get("skybound", 0) + 1


@register(ISAAC.card_id)
class Isaac(CardScript):
    """Last Words: add a Striker Artifact to your hand."""

    def last_words(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, STRIKER_ARTIFACT)


@register(EUSTACE.card_id)
class Eustace(CardScript):
    """Fanfare: Skybound Art - select another unevolved allied follower and evolve it and
    this follower. Clash: deal 3 damage to the opposing follower."""
    skybound = True
    play_targets = (TargetSpec(Target.ALLIED_FOLLOWER, other=True, filter=unevolved),)

    def fanfare(self, ctx):
        if not E.skybound_art(ctx):
            return
        for f in ctx.chosen():
            if not f.evolved:
                E.evolve(ctx.state, f)
        # Confirmed by the player: it still evolves with no other follower to select.
        if on_field(ctx) and not ctx.source.evolved:
            E.evolve(ctx.state, ctx.source)

    def clash(self, ctx):
        E.damage(ctx.state, [ctx.other], 3, ctx.source)


@register(ILSA.card_id)
class Ilsa(CardScript):
    """Fanfare: Mode: 1. Three times, deal 4 damage to a random enemy follower. 2. Deal 4
    damage to the enemy leader."""
    modes = (2, 1)

    def fanfare(self, ctx):
        if 0 in ctx.modes:
            damage_random_enemy_followers(ctx, 4, 3)
        if 1 in ctx.modes:
            E.damage(ctx.state, [common.enemy_leader(ctx)], 4, ctx.source)


@register(STONE_BREAKER.card_id)
class StoneBreaker(CardScript):
    """Six times, deal 1 damage to a random enemy follower."""

    def cast(self, ctx):
        damage_random_enemy_followers(ctx, 1, 6)


@register(CASSIUS.card_id)
class Cassius(CardScript):
    """Fanfare: select an Artifact follower in your hand and deal X damage to all enemy
    followers, X = its attack (0 if none: official Q&A). Last Words: add a Fortifier
    Artifact to your hand."""
    play_targets = (TargetSpec(Target.HAND_CARD, filter=lambda s, p, c: is_artifact_follower(c)),)

    def fanfare(self, ctx):
        x = sum(c.atk for c in ctx.chosen_hand())
        E.damage(ctx.state, list(ctx.opponent.followers), x, ctx.source)

    def last_words(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, FORTIFIER_ARTIFACT)


@register(CHAOS_LEGION.card_id)
class ChaosLegion(CardScript):
    """Deal 3 damage to all enemies. Super Skybound Art - deal 6 instead."""
    skybound = True

    def cast(self, ctx):
        amount = 6 if E.super_skybound_art(ctx) else 3
        E.damage(ctx.state, list(ctx.opponent.followers) + [common.enemy_leader(ctx)], amount,
                 ctx.source)


@register(LU_WOH.card_id)
class LuWoh(CardScript):
    """Fanfare: six times, deal 1 damage to a random enemy follower. Give all followers in
    your opponent's hand +1/+0. Skybound Art - gain Crest: Lu Woh, Light Personified."""
    skybound = True

    def fanfare(self, ctx):
        damage_random_enemy_followers(ctx, 1, 6)
        for c in [c for c in ctx.opponent.hand if c.defn.is_follower]:
            E.buff(ctx.state, c, 1, 0)
        if E.skybound_art(ctx):
            E.add_to_leader_area(ctx.state, ctx.controller, LU_WOH_CREST)


@register(BEELZEBUB.card_id)
class Beelzebub(CardScript):
    """Fanfare: select 2 enemy followers, remove all abilities from them and deal them 9
    damage. Give the enemy leader "Takes 1 more damage"."""
    play_targets = (TargetSpec(Target.ENEMY_FOLLOWER, 2),)

    def fanfare(self, ctx):
        targets = ctx.chosen()
        for target in targets:
            remove_all_abilities(target)
        E.damage(ctx.state, targets, 9, ctx.source)
        ctx.opponent.extra_damage += 1      # stacks with each copy (official Q&A)
