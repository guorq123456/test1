"""Neutral cards: every Neutral card in the Rotation pool, with the tokens,
crests and Accelerate forms they produce.

Card stats come from the pool table (svsim/cards/pool.py); this module holds
the abilities. Comments give the official Simplified Chinese names.
"""
from svsim.cards import common
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.enums import CardType, Craft, Keyword
from svsim.core.script import CardScript, Target, TargetSpec, register
from svsim.core.state import leader_uid

LYRIA = card(10403120)  # 掌握天空命运的少女·露莉亚
FATE_OF_THE_WORLD = card(10503310)  # 《世界》的呈现

# --- set 10009 ---
JAILOR_OF_ANTIQUITY = card(10901110)  # 最古老的狱卒
INITIATION_OF_REBIRTH = card(10901310)  # 轮回转冲
BLADE_ANGEL = card(10902110)  # 圣剑天使
WARDEN_OF_SELFLESSNESS = card(10903110)  # 无我看守
AZVALDT = card(10903210)  # 混沌监狱·阿兹弗特
ZERAEL = card(10904110)  # 断绝的轮回·泽勒尔
# --- set 10008 ---
HAMSA = card(10801110)  # 自律的圣鸟·汉萨
REINA = card(10801120)  # 无尽旅途·蕾娜
ALFIED = card(10802110)  # 激动的欢喜·阿尔菲德
LEGACY_OF_THE_BRAVE = card(10802310)  # 救世的英姿
AIKA = card(10803110)  # 遗忘的纯真·爱卡
WILLS_UNITED = card(10803310)  # 传承的意志
ALABASTER_BAHAMUT = card(10804110)  # 阿尔比昂巴哈姆特
OLIVIA = card(10804120)  # 高洁的黑翼·奥莉薇
# --- set 10007 ---
ALTARO_SUPERFAN = card(10701110)  # 纯真孩童
TEARS_OF_DEGRADATION = card(10701310)  # 颓废之泪
INTREPID_NEWSHOUND = card(10702110)  # 神话记者
HEDONISTIC_SOCIALITE = card(10703110)  # 享乐的上级市民
CITY_OF_BABELON = card(10703210)  # 巴别隆城
ILLAMRITA = card(10704110)  # 特殊目标·海雷姆哈妮
ALTARO_MAYOR = card(10704120)  # 巴别隆市长·埃尔塔罗
# --- set 10006 ---
MUDDLED_ONLOOKER = card(10601110)  # 浑浊之民
DISRUPTED_COMMONER = card(10601120)  # 匍匐的异类
ENCROACHED_WORLD = card(10602210)  # 被侵略的世界
BEAST_LOST_TO_THE_DARK = card(10603110)  # 彷徨于黑暗之兽
DARK_DIMENSIONS = card(10603210)  # 黑暗次元
OMEGOTEP = card(10604110)  # 恐惧的象征·欧米伽奥提普
# --- set 10005 ---
MONSTER_LITTERATEUR = card(10501110)  # 挥毫的怪物
GODDESS_OF_STARLIGHT = card(10502110)  # 星辉女神
BEHEMOTH_GENERAL = card(10502120)  # 手持军配团扇的伟丈夫
WORLD_OF_GAMES = card(10503210)  # 大游戏世界
GETENOU = card(10504110)  # 八界花·下天央
# --- set 10000 (Basic) ---
INDOMITABLE_FIGHTER = card(10001110)  # 不屈的剑斗士
LEAH = card(10001120)  # 叮当天使·莉亚
QUAKE_GOLIATH = card(10001130)  # 激震的歌利亚 (Ward only: no script)
DETECTIVES_LENS = card(10001210)  # 侦探的放大镜
ARRIET = card(10002110)  # 煌响使者·亨莉雅妲
CARAVAN_MAMMOTH = card(10002120)  # 商队猛犸象 (vanilla: no script)
ADVENTURERS_GUILD = card(10002210)  # 冒险者公会
# --- set 10004 ---
KATALINA = card(10401110)  # 驰骋天空的守护者·卡塔莉娜
VYRN = card(10401120)  # 亲爱的搭档·碧
YUNI = card(10402110)  # 宙域使者·尤妮
GRAN_AND_DJEETA = card(10403110)  # 征服苍空的骑空士·古兰&姬塔
SANDALPHON = card(10404110)  # 天司长的继承者·圣德芬

# --- leader area / alternate forms ---
JAILOR_ACCELERATE = card(10901112)  # 最古老的狱卒 (激奏)
ILLAMRITA_CREST = card(10704112)  # 纹章：特殊目标·海雷姆哈妮
SANDALPHON_CREST = card(10404112)  # 纹章：天司长的继承者·圣德芬

CARDS = [LYRIA, FATE_OF_THE_WORLD,
         JAILOR_OF_ANTIQUITY, INITIATION_OF_REBIRTH, BLADE_ANGEL, WARDEN_OF_SELFLESSNESS, AZVALDT,
         ZERAEL,
         HAMSA, REINA, ALFIED, LEGACY_OF_THE_BRAVE, AIKA, WILLS_UNITED, ALABASTER_BAHAMUT, OLIVIA,
         ALTARO_SUPERFAN, TEARS_OF_DEGRADATION, INTREPID_NEWSHOUND, HEDONISTIC_SOCIALITE,
         CITY_OF_BABELON, ILLAMRITA, ALTARO_MAYOR,
         MUDDLED_ONLOOKER, DISRUPTED_COMMONER, ENCROACHED_WORLD, BEAST_LOST_TO_THE_DARK,
         DARK_DIMENSIONS, OMEGOTEP,
         MONSTER_LITTERATEUR, GODDESS_OF_STARLIGHT, BEHEMOTH_GENERAL, WORLD_OF_GAMES, GETENOU,
         INDOMITABLE_FIGHTER, LEAH, QUAKE_GOLIATH, DETECTIVES_LENS, ARRIET, CARAVAN_MAMMOTH,
         ADVENTURERS_GUILD,
         KATALINA, VYRN, YUNI, GRAN_AND_DJEETA, SANDALPHON]
LEADER_AREA = [ILLAMRITA_CREST, SANDALPHON_CREST]
ALTERNATE_FORMS = [JAILOR_ACCELERATE]

HAND = (TargetSpec(Target.HAND_CARD),)
ENCROACHER = "Encroacher"
ONE_TO_EIGHT = frozenset(range(1, 9))


# --- shared helpers -------------------------------------------------------------------

def _random_enemy_follower(ctx, k: int = 1) -> list:
    """Random effects can hit followers that can't be selected (Aura, Ambush)."""
    return E.random_sample(ctx.state, ctx.opponent.followers, k)


def _played_one_to_eight(p) -> bool:
    """You've played cards with base costs of 1, 2, ..., 8 this match."""
    return ONE_TO_EIGHT <= p.played_base_costs


def _heal_all_allies(ctx, amount: int) -> None:
    """Restore defense to all allied followers on the field and to your leader."""
    for f in list(ctx.me.followers):
        E.heal(f, amount)
    E.heal_leader(ctx.state, ctx.controller, amount)


def _played_base_cost(played, as_spell: bool) -> int:
    """Base cost of a card as it was played: an accelerated card's base cost is its
    Accelerate cost (official Q&A on Zerael); a crystallized one has already turned
    into its Crystallize form."""
    if as_spell and not played.defn.is_spell and played.defn.accelerate is not None:
        return played.defn.accelerate.cost
    return played.defn.cost


def _become_exact_copy(state, target, original) -> None:
    """Transform `target` (it keeps its place and uid) into an exact copy of `original`."""
    clone = original.copy()
    E.transform(state, target, original.defn)
    for name in ("cost", "atk", "life", "max_life", "keywords", "countdown", "evolved",
                 "super_evolved", "max_attacks", "counters", "grants", "cost_mods"):
        setattr(target, name, getattr(clone, name))


# --- existing starter-deck cards --------------------------------------------------------

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


# --- set 10009 ----------------------------------------------------------------------------

@register(JAILOR_OF_ANTIQUITY.card_id)
class JailorOfAntiquity(CardScript):
    """Fanfare: select an enemy follower and deal it 6 damage; deal 2 damage to a
    random enemy follower that wasn't selected. Ward. Accelerate (1): see below."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 6, ctx.source)
        # The second part happens even when nothing could be selected (official Q&A).
        unselected = [f for f in ctx.opponent.followers if f.uid not in ctx.targets]
        E.damage(ctx.state, E.random_sample(ctx.state, unselected, 1), 2, ctx.source)


@register(JAILOR_ACCELERATE.card_id)
class JailorAccelerate(CardScript):
    """Accelerate (1): deal 2 damage to a random enemy follower."""

    def cast(self, ctx):
        E.damage(ctx.state, _random_enemy_follower(ctx), 2, ctx.source)


@register(INITIATION_OF_REBIRTH.card_id)
class InitiationOfRebirth(CardScript):
    """Put a copy of a random allied follower destroyed this match with the highest
    base cost into your deck. Draw a card."""

    def cast(self, ctx):
        destroyed = ctx.me.destroyed
        if destroyed:
            top = max(d.cost for d in destroyed)
            # UNSURE: weighted by how often each was destroyed (like Reanimate), or uniform by name?
            defn = ctx.state.rng.choice([d for d in destroyed if d.cost == top])
            E.put_into_deck(ctx.state, ctx.controller, defn)
        E.draw(ctx.state, ctx.controller)


@register(BLADE_ANGEL.card_id)
class BladeAngel(CardScript):
    """Fanfare: select 2 other allied followers and give them +3/+3."""
    play_targets = (TargetSpec(Target.ALLIED_FOLLOWER, 2, other=True),)

    def fanfare(self, ctx):
        for f in ctx.chosen():
            E.buff(ctx.state, f, 3, 3)


@register(WARDEN_OF_SELFLESSNESS.card_id)
class WardenOfSelflessness(CardScript):
    """Fanfare: add a Jailor of Antiquity to your hand; deal X damage to 2 random
    enemy followers, X = Neutral cards in your hand. Evolve: recover 1 play point."""

    def fanfare(self, ctx):
        E.add_to_hand(ctx.state, ctx.controller, JAILOR_OF_ANTIQUITY)
        x = sum(c.defn.craft == Craft.NEUTRAL for c in ctx.me.hand)
        if x > 0:
            E.damage(ctx.state, _random_enemy_follower(ctx, 2), x, ctx.source)

    def on_evolve(self, ctx):
        E.recover_pp(ctx.state, ctx.controller, 1)


@register(AZVALDT.card_id)
class Azvaldt(CardScript):
    """At the end of your turn, if you've played cards with base costs 1 to 8 this
    match, destroy this card. Last Words: summon a copy each of 4 random differently
    named allied followers destroyed this match; give all allied followers +3/+3."""

    def on_turn_end(self, ctx):
        # Official Q&A with Zerael: Azvaldt is destroyed, then Zerael is invoked, then this
        # Last Words resolves. APPROX: the engine checks end-of-turn Invokes before turn-end
        # abilities resolve, so on a full field (Azvaldt + 4 followers) Zerael isn't invoked.
        if _played_one_to_eight(ctx.me):
            E.destroy(ctx.state, ctx.source)

    def last_words(self, ctx):
        by_name = {}
        for defn in ctx.me.destroyed:
            by_name.setdefault(defn.name, defn)
        # UNSURE: are the 4 names picked uniformly, or weighted by how often each was destroyed?
        for defn in E.random_sample(ctx.state, list(by_name.values()), 4):
            E.summon(ctx.state, ctx.controller, defn)
        for f in list(ctx.me.followers):
            E.buff(ctx.state, f, 3, 3)


@register(ZERAEL.card_id)
class Zerael(CardScript):
    """Activates in deck: at the end of your turn, if you've played cards with base
    costs 1 to 8 this match, Invoke this card. Fanfare: select an enemy follower and
    deal it 9 damage. Intimidate."""
    invoke_at = "turn_end"
    play_targets = common.ENEMY_FOLLOWER

    def can_invoke(self, state, card):
        return _played_one_to_eight(state.players[card.owner])

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 9, ctx.source)


# --- set 10008 ----------------------------------------------------------------------------

@register(HAMSA.card_id)
class Hamsa(CardScript):
    """Evolve: give this follower +5/+5."""

    def on_evolve(self, ctx):
        E.buff(ctx.state, ctx.source, 5, 5)


@register(REINA.card_id)
class Reina(CardScript):
    """Fanfare: recover 1 evolution point."""

    def fanfare(self, ctx):
        E.recover_ep(ctx.state, ctx.controller, 1)


@register(ALFIED.card_id)
class Alfied(CardScript):
    """Fanfare: select an enemy follower and deal it 4 damage. Evolve: gain Storm."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        E.damage(ctx.state, ctx.chosen(), 4, ctx.source)

    def on_evolve(self, ctx):
        E.give_keywords(ctx.source, Keyword.STORM)


@register(LEGACY_OF_THE_BRAVE.card_id)
class LegacyOfTheBrave(CardScript):
    """Add an exact copy of a random card in your opponent's hand to your hand and
    reduce its cost by 1. Draw a card."""

    def cast(self, ctx):
        for original in E.random_sample(ctx.state, ctx.opponent.hand, 1):
            copy = E.add_copy_to_hand(ctx.state, ctx.controller, original)
            if copy is not None:
                E.add_cost(copy, -1)
        E.draw(ctx.state, ctx.controller)


@register(AIKA.card_id)
class Aika(CardScript):
    """Fanfare: add a copy of a random allied follower destroyed this match to your
    hand. Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        self._recall(ctx)

    def on_evolve(self, ctx):
        self._recall(ctx)

    def _recall(self, ctx):
        # UNSURE: weighted by how often each was destroyed (like Reanimate), or uniform by name?
        if ctx.me.destroyed:
            E.add_to_hand(ctx.state, ctx.controller, ctx.state.rng.choice(ctx.me.destroyed))


@register(WILLS_UNITED.card_id)
class WillsUnited(CardScript):
    """Mode: 1. Deal 3 damage to a random enemy follower. 2. Reanimate (2).
    3. Give all allied followers +1/+0."""
    modes = (3, 1)

    def cast(self, ctx):
        if 0 in ctx.modes:
            E.damage(ctx.state, _random_enemy_follower(ctx), 3, ctx.source)
        if 1 in ctx.modes:
            E.reanimate(ctx.state, ctx.controller, 2)
        if 2 in ctx.modes:
            for f in list(ctx.me.followers):
                E.buff(ctx.state, f, 1, 0)


@register(ALABASTER_BAHAMUT.card_id)
class AlabasterBahamut(CardScript):
    """Fanfare: Mode: 1. Banish all other followers. 2. Banish all amulets.
    3. Banish all crests (not faiths: official Q&A)."""
    modes = (3, 1)

    def fanfare(self, ctx):
        state = ctx.state
        if 0 in ctx.modes:
            for f in [c for c in state.field_order() if c.defn.is_follower and c is not ctx.source]:
                E.banish(state, f)
        if 1 in ctx.modes:
            for a in [c for c in state.field_order() if c.defn.is_amulet]:
                E.banish(state, a)
        if 2 in ctx.modes:
            for p in state.players:
                for crest in [c for c in p.leader_area if c.defn.type == CardType.CREST]:
                    E.banish(state, crest)


@register(OLIVIA.card_id)
class Olivia(CardScript):
    """Fanfare: recover 2 super-evolution points. Ward."""

    def fanfare(self, ctx):
        E.recover_sep(ctx.state, ctx.controller, 2)


# --- set 10007 ----------------------------------------------------------------------------

@register(ALTARO_SUPERFAN.card_id)
class AltaroSuperfan(CardScript):
    """Evolve: draw a Neutral card."""

    def on_evolve(self, ctx):
        E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.craft == Craft.NEUTRAL)


@register(TEARS_OF_DEGRADATION.card_id)
class TearsOfDegradation(CardScript):
    """Select an enemy card on the field and banish it."""
    play_targets = (TargetSpec(Target.ENEMY_CARD),)

    def cast(self, ctx):
        for target in ctx.chosen():
            E.banish(ctx.state, target)


@register(INTREPID_NEWSHOUND.card_id)
class IntrepidNewshound(CardScript):
    """Last Words: draw a card. Super-Evolve: summon 2 Intrepid Newshounds."""

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller)

    def on_super_evolve(self, ctx):
        for _ in range(2):
            E.summon(ctx.state, ctx.controller, INTREPID_NEWSHOUND)


@register(HEDONISTIC_SOCIALITE.card_id)
class HedonisticSocialite(CardScript):
    """Fanfare: select a card in your hand and discard it. Deal 2 damage to all
    enemy followers."""
    play_targets = HAND

    def fanfare(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        E.damage(ctx.state, list(ctx.opponent.followers), 2, ctx.source)


@register(CITY_OF_BABELON.card_id)
class CityOfBabelon(CardScript):
    """Countdown (1). At the end of your turn, activate the next of: 1. Deal 2 damage
    to a random enemy follower. 2. Restore 2 defense to your leader. 3. Deal 2 damage
    to the enemy leader and destroy this card. Engage (1): select a card in your hand
    and discard it; delay this amulet's count by 1."""
    engage_cost = 1
    engage_targets = HAND

    def on_turn_end(self, ctx):
        counters = E.counters(ctx.source)
        step = counters.get("step", 0)
        counters["step"] = step + 1
        if step == 0:
            E.damage(ctx.state, _random_enemy_follower(ctx), 2, ctx.source)
        elif step == 1:
            E.heal_leader(ctx.state, ctx.controller, 2)
        else:
            E.damage(ctx.state, [common.enemy_leader(ctx)], 2, ctx.source)
            E.destroy(ctx.state, ctx.source)

    def engage(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        # UNSURE: does the delay still happen when no card could be discarded (empty hand)?
        E.advance_countdown(ctx.state, ctx.source, -1)


class _DesignatedTarget(CardScript):
    """Given by Illamrita: can't attack followers or leaders; at the end of your
    turn, banish this card."""
    cant_attack = True

    def on_turn_end(self, ctx):
        E.banish(ctx.state, ctx.source)


DESIGNATED_TARGET = _DesignatedTarget()


@register(ILLAMRITA.card_id)
class Illamrita(CardScript):
    """Follower Strike: gain Barrier; give the opposing follower "Can't attack
    followers or leaders" and "At the end of your turn, banish this card".
    Last Words: gain Crest: Illamrita, Designated Target."""

    def follower_strike(self, ctx):
        E.give_keywords(ctx.source, Keyword.BARRIER)
        if ctx.other is not None and ctx.state.on_field(ctx.other.uid) is ctx.other:
            E.grant(ctx.other, DESIGNATED_TARGET)

    def last_words(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, ILLAMRITA_CREST)


@register(ILLAMRITA_CREST.card_id)
class IllamritaCrest(CardScript):
    """Countdown (2). Last Words: summon an Illamrita, Designated Target and evolve it."""

    def last_words(self, ctx):
        summoned = E.summon(ctx.state, ctx.controller, ILLAMRITA)
        if summoned is not None:
            E.evolve(ctx.state, summoned)


@register(ALTARO_MAYOR.card_id)
class AltaroMayor(CardScript):
    """Ambush. At the end of your turn, draw a card."""

    def on_turn_end(self, ctx):
        E.draw(ctx.state, ctx.controller)


# --- set 10006 ----------------------------------------------------------------------------

@register(MUDDLED_ONLOOKER.card_id)
class MuddledOnlooker(CardScript):
    """Last Words: deal 1 damage to the enemy leader."""

    def last_words(self, ctx):
        E.damage(ctx.state, [common.enemy_leader(ctx)], 1, ctx.source)


@register(DISRUPTED_COMMONER.card_id)
class DisruptedCommoner(CardScript):
    """Fanfare: select an enemy follower and destroy it. Bane."""
    play_targets = common.ENEMY_FOLLOWER

    def fanfare(self, ctx):
        for target in ctx.chosen():
            E.destroy(ctx.state, target)


@register(ENCROACHED_WORLD.card_id)
class EncroachedWorld(CardScript):
    """Engage: select a card in your hand and transform it into an exact copy of a
    random card in your opponent's deck (nothing happens with an empty hand: Q&A)."""
    engage_cost = 0
    engage_targets = HAND

    def engage(self, ctx):
        for c in ctx.chosen_hand():
            for original in E.random_sample(ctx.state, ctx.opponent.deck, 1):
                _become_exact_copy(ctx.state, c, original)


BEAST_ABILITIES = (Keyword.STORM, Keyword.BANE, Keyword.INTIMIDATE, Keyword.DRAIN, Keyword.AURA,
                   Keyword.BARRIER)


@register(BEAST_LOST_TO_THE_DARK.card_id)
class BeastLostToTheDark(CardScript):
    """Fanfare: gain 3 random abilities out of Storm, Bane, Intimidate, Drain, Aura, Barrier."""

    def fanfare(self, ctx):
        for keyword in E.random_sample(ctx.state, BEAST_ABILITIES, 3):
            E.give_keywords(ctx.source, keyword)


@register(DARK_DIMENSIONS.card_id)
class DarkDimensions(CardScript):
    """Countdown (2). At the end of your turn, deal 2 damage to all non-Encroacher followers."""

    def on_turn_end(self, ctx):
        targets = [c for c in ctx.state.field_order()
                   if c.defn.is_follower and not E.has_trait(c, ENCROACHER)]
        E.damage(ctx.state, targets, 2, ctx.source)


@register(OMEGOTEP.card_id)
class Omegotep(CardScript):
    """Fanfare: activate 2 random abilities out of: 1. Destroy a random enemy
    follower. 2. Deal 2 damage to the enemy leader. 3. Recover 2 play points.
    4. Gain +4/+4 and activate this card's Fanfare. Super-Evolve: replicate the Fanfare."""

    def fanfare(self, ctx):
        self._dread(ctx)

    def on_super_evolve(self, ctx):
        self._dread(ctx)

    def _dread(self, ctx):
        state = ctx.state
        for option in sorted(E.random_sample(state, range(4), 2)):   # in printed order
            if option == 0:
                for target in _random_enemy_follower(ctx):
                    E.destroy(state, target)
            elif option == 1:
                E.damage(state, [common.enemy_leader(ctx)], 2, ctx.source)
            elif option == 2:
                E.recover_pp(state, ctx.controller, 2)
            else:
                E.buff(state, ctx.source, 4, 4)
                # Queued like any other trigger: it fizzles if this follower has left the field.
                E.enqueue(state, "fanfare", ctx.source, ctx.controller, script=self)


# --- set 10005 ----------------------------------------------------------------------------

@register(MONSTER_LITTERATEUR.card_id)
class MonsterLitterateur(CardScript):
    """Fanfare: if there's another card with base cost 1 on the field (either side),
    gain +1/+1."""

    def fanfare(self, ctx):
        if any(c is not ctx.source and c.defn.cost == 1 for c in ctx.state.field_order()):
            E.buff(ctx.state, ctx.source, 1, 1)


@register(GODDESS_OF_STARLIGHT.card_id)
class GoddessOfStarlight(CardScript):
    """Evolve: select 3 cards in your hand and discard them. Add an exact copy each
    of the 3 leftmost cards in your hand to your hand."""
    evolve_targets = (TargetSpec(Target.HAND_CARD, 3),)

    def on_evolve(self, ctx):
        for c in ctx.chosen_hand():
            E.discard(ctx.state, c)
        for original in list(ctx.me.hand[:3]):
            E.add_copy_to_hand(ctx.state, ctx.controller, original)


@register(BEHEMOTH_GENERAL.card_id)
class BehemothGeneral(CardScript):
    """Evolve: if the 3 highest base costs in your hand add up to more than those in
    your opponent's hand, destroy all enemy followers."""

    def on_evolve(self, ctx):
        if _top_three_base_costs(ctx.me.hand) > _top_three_base_costs(ctx.opponent.hand):
            for f in list(ctx.opponent.followers):
                E.destroy(ctx.state, f)


def _top_three_base_costs(hand) -> int:
    return sum(sorted((c.defn.cost for c in hand), reverse=True)[:3])


@register(WORLD_OF_GAMES.card_id)
class WorldOfGames(CardScript):
    """Countdown (5). Whenever you play another card, if there's a card on the field
    other than it with the same base cost, advance this amulet's count by 1.
    Last Words: draw 2 cards."""

    def on_play(self, ctx):
        played = ctx.other
        cost = _played_base_cost(played, ctx.as_spell)
        # The condition is checked as the card is played (official Q&A: a Divine Thunder
        # that destroys the only 4-cost follower still advances the count), but this
        # trigger resolves after the card's own effect. Cards destroyed since the play
        # are recovered from this amulet's pending on_card_destroyed triggers, and cards
        # that entered since a follower was played are ignored.
        # APPROX: a card banished, transformed or returned to hand by the played card's own
        # effect no longer counts, and cards summoned by a played spell do count.
        gone = [t.ctx.other for t in ctx.state.queue
                if t.hook == "on_card_destroyed" and t.ctx.source is ctx.source]
        newer = None if ctx.as_spell else played.order
        on_field = [c for c in ctx.state.field_order() if newer is None or c.order <= newer]
        # UNSURE: does this amulet itself count as "a card on the field other than it"
        # (so playing any 1-base-cost card advances it)? Implemented: yes.
        if any(c is not played and c.defn.cost == cost for c in on_field + gone):
            E.advance_countdown(ctx.state, ctx.source, 1)

    def on_card_destroyed(self, ctx):
        """Bookkeeping only: on_play reads these pending triggers (see above)."""

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller, 2)


@register(GETENOU.card_id)
class Getenou(CardScript):
    """Fanfare: discard your hand. Mode: 1. Draw 8 cards. 2. Draw 2 cards and reduce
    their costs by 8."""
    modes = (2, 1)

    def fanfare(self, ctx):
        for c in list(ctx.me.hand):
            E.discard(ctx.state, c)
        if 0 in ctx.modes:
            E.draw(ctx.state, ctx.controller, 8)
        if 1 in ctx.modes:
            for drawn in E.draw(ctx.state, ctx.controller, 2):
                E.add_cost(drawn, -8)


# --- set 10000 (Basic) ----------------------------------------------------------------------

@register(INDOMITABLE_FIGHTER.card_id)
class IndomitableFighter(CardScript):
    """Enhance (4): gain +3/+3."""
    enhance = (4,)

    def fanfare(self, ctx):
        if ctx.enhanced:
            E.buff(ctx.state, ctx.source, 3, 3)


@register(LEAH.card_id)
class Leah(CardScript):
    """Ward. Last Words: draw a card. Evolve: draw a card."""

    def last_words(self, ctx):
        E.draw(ctx.state, ctx.controller)

    def on_evolve(self, ctx):
        E.draw(ctx.state, ctx.controller)


@register(DETECTIVES_LENS.card_id)
class DetectivesLens(CardScript):
    """Engage: destroy this card; select an enemy follower and remove its Ward. (It
    can be engaged with no Ward follower around: it's just destroyed. Only Ward
    followers are offered, as selecting another one does nothing.)"""
    engage_cost = 0
    engage_targets = (TargetSpec(Target.ENEMY_FOLLOWER,
                                 filter=lambda state, player, c: c.has(Keyword.WARD)),)

    def engage(self, ctx):
        E.destroy(ctx.state, ctx.source)
        for target in ctx.chosen():
            E.remove_keywords(target, Keyword.WARD)


@register(ARRIET.card_id)
class Arriet(CardScript):
    """Evolve: restore 2 defense to your leader. Super-Evolve: restore 4 instead."""

    def on_evolve(self, ctx):
        E.heal_leader(ctx.state, ctx.controller, 4 if ctx.super_ else 2)


@register(ADVENTURERS_GUILD.card_id)
class AdventurersGuild(CardScript):
    """Fanfare: draw a follower. Engage: destroy this card; select an allied
    follower and give it Rush."""
    engage_cost = 0
    engage_targets = common.ALLIED_FOLLOWER

    def fanfare(self, ctx):
        E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.is_follower)

    def engage(self, ctx):
        E.destroy(ctx.state, ctx.source)
        for f in ctx.chosen():
            E.give_keywords(f, Keyword.RUSH)


# --- set 10004 ----------------------------------------------------------------------------

@register(KATALINA.card_id)
class Katalina(CardScript):
    """Fanfare: Skybound Art - deal 5 damage to 2 random enemy followers. Ward.
    Can't take more than 3 damage at a time."""
    skybound = True
    damage_cap = 3

    def fanfare(self, ctx):
        if E.skybound_art(ctx):
            E.damage(ctx.state, _random_enemy_follower(ctx, 2), 5, ctx.source)


@register(VYRN.card_id)
class Vyrn(CardScript):
    """Fanfare: if you've unlocked super-evolution, evolve this follower."""

    def fanfare(self, ctx):
        if E.super_evolution_unlocked(ctx.state, ctx.controller) and not ctx.source.evolved:
            E.evolve(ctx.state, ctx.source)


@register(YUNI.card_id)
class Yuni(CardScript):
    """Aura. At the end of your turn, restore 1 defense to all allies."""

    def on_turn_end(self, ctx):
        _heal_all_allies(ctx, 1)


@register(GRAN_AND_DJEETA.card_id)
class GranAndDjeeta(CardScript):
    """Fanfare: Mode: 1. Deal 5 damage to a random enemy follower. 2. Draw 2
    followers. Skybound Art - evolve this follower."""
    modes = (2, 1)
    skybound = True

    def fanfare(self, ctx):
        if 0 in ctx.modes:
            E.damage(ctx.state, _random_enemy_follower(ctx), 5, ctx.source)
        if 1 in ctx.modes:
            for _ in range(2):
                E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.is_follower)
        if E.skybound_art(ctx) and not ctx.source.evolved:
            E.evolve(ctx.state, ctx.source)


@register(SANDALPHON.card_id)
class Sandalphon(CardScript):
    """Activates in deck: at the start of your turn, if allied followers have evolved
    6+ times this match, Invoke this card. When Invoked, gain Crest: Sandalphon and
    return this card to your hand. Fanfare: Super Skybound Art - 5 times, deal 2
    damage to a random enemy (re-rolled each time: official Q&A)."""
    invoke_at = "turn_start"
    skybound = True

    def can_invoke(self, state, card):
        return state.players[card.owner].evolutions >= 6

    def on_invoked(self, ctx):
        E.add_to_leader_area(ctx.state, ctx.controller, SANDALPHON_CREST)
        E.return_to_hand(ctx.state, ctx.source)    # a fresh card: cost changes are gone (Q&A)

    def fanfare(self, ctx):
        if not E.super_skybound_art(ctx):
            return
        for _ in range(5):
            enemies = list(ctx.opponent.followers) + [common.enemy_leader(ctx)]
            E.damage(ctx.state, E.random_sample(ctx.state, enemies, 1), 2, ctx.source)


@register(SANDALPHON_CREST.card_id)
class SandalphonCrest(CardScript):
    """Countdown (2). At the end of your turn, restore 1 defense to all allies."""

    def on_turn_end(self, ctx):
        _heal_all_allies(ctx, 1)
