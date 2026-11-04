"""跳费龙比赛版（ramp-t）卡牌脚本审计：按官方效果写的回归测试。

每张卡一个测试（只有身材/关键词的卡合在 test_card_stats_and_keywords 里）。
注释里只写效果的简短转述，不抄官方原文。test_ramp_dragon.py / test_cards_dragon.py /
test_cards_neutral.py 已经覆盖的基本路径这里尽量换角度测（边界、目标限制、超进化一侧等）。
"""
import pytest

from svsim.cards import demo, dragon, neutral
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.engine import apply, legal_actions, resolve_queue, selectable
from svsim.core.enums import CardType, Craft, Keyword
from svsim.core.script import Target, TargetSpec
from svsim.core.state import BANISHED, DESTROYED, IN_PLAY, leader_uid

from helpers import count, give, plays, put, set_pp, start, unlock_evolution


def act(state, action):
    """Apply an action, checking first that the engine offers it."""
    assert action in legal_actions(state), (action, legal_actions(state))
    apply(state, action)


def evolves_of(state, uid, super_=None):
    return [a for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == uid
            and (super_ is None or a.super_ == super_)]


def attacks_by(state, uid):
    return [a for a in legal_actions(state) if isinstance(a, Attack) and a.attacker == uid]


def make_evolved(state, inst, super_=False):
    """Build a position with an already evolved follower (no Evolve abilities)."""
    E.evolve(state, inst, super_=super_)
    resolve_queue(state)
    return inst


# --- 核心卡 ---------------------------------------------------------------------------

def test_sloth_of_the_crestpetal():
    # 2 次「随机敌方随从 2 伤」；觉醒时再打敌方主战者 2。
    # 随机效果可以打到灵气随从；同一个随从可能吃两次。
    state = start()
    saga = put(state, 1, dragon.SAGATSUMATSU)            # 5/4 灵气，唯一的敌方随从
    set_pp(state, 0, 7)
    sloth = give(state, 0, dragon.SLOTH_OF_THE_CRESTPETAL)
    act(state, PlayCard(sloth.uid))
    assert saga.fate == DESTROYED                        # 2 + 2
    assert state.players[1].leader_hp == 18              # 觉醒：打脸 2
    # 第一下打死随从后，第二下在剩下的随从里重新随机
    state = start()
    a, b = put(state, 1, demo.FOOTMAN), put(state, 1, demo.FOOTMAN)   # 1/2 各一
    set_pp(state, 0, 6)
    sloth = give(state, 0, dragon.SLOTH_OF_THE_CRESTPETAL)
    act(state, PlayCard(sloth.uid))
    assert a.fate == DESTROYED and b.fate == DESTROYED
    assert state.players[1].leader_hp == 20              # 6 PP 上限：不觉醒


def test_vorlalai_eld_blades():
    # 被舍弃时召唤 1 个波菈莱；毁灭；进化时 1 张天刀深渊，超进化时改为 3 张。
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 2)
    kimika = give(state, 0, dragon.KIMIKA)
    vorlalai = give(state, 0, dragon.VORLALAI)
    act(state, PlayCard(kimika.uid, (vorlalai.uid,)))    # 琪米卡入场曲舍弃波菈莱
    summoned = [c for c in p.field if c.defn == dragon.VORLALAI]
    assert len(summoned) == 1
    v = summoned[0]
    assert (v.atk, v.life) == (0, 2) and v.has(Keyword.BANE)
    assert attacks_by(state, v.uid) == []                # 召唤当回合不能攻击
    for super_, depths, stats in ((False, 1, (2, 4)), (True, 3, (3, 5))):
        state = start()
        p = state.players[0]
        p.hand.clear()
        unlock_evolution(state, 0)
        v = put(state, 0, dragon.VORLALAI)
        act(state, evolves_of(state, v.uid, super_)[0])
        assert count(p.hand, dragon.DEPTHS_OF_THE_ELD_BLADES) == depths
        assert (v.atk, v.life) == stats


def test_depths_of_the_eld_blades():
    # 衍生：使用时打敌方主战者 1、回复自己 1；被舍弃时同样发动。
    state = start()
    p, o = state.players
    p.hand.clear()
    p.leader_hp = 10
    set_pp(state, 0, 2)
    depths = give(state, 0, dragon.DEPTHS_OF_THE_ELD_BLADES)
    act(state, PlayCard(depths.uid))
    assert (o.leader_hp, p.leader_hp) == (19, 11)
    # 被金银的入场曲舍弃：两张各发动一次
    set_pp(state, 0, 8)
    lumiore = give(state, 0, dragon.LUMIORE_AND_ARGENTE)
    d1, d2 = give(state, 0, dragon.DEPTHS_OF_THE_ELD_BLADES), give(state, 0, dragon.DEPTHS_OF_THE_ELD_BLADES)
    act(state, PlayCard(lumiore.uid, (d1.uid, d2.uid)))
    assert o.leader_hp == 19 - 4 - 2 and p.leader_hp == 13


def test_dragonewt_promoter():
    # 爆能强化 4：召唤 2 个宣扬的龙人（都有突进）。
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 4)
    promoter = give(state, 0, dragon.DRAGONEWT_PROMOTER)
    act(state, PlayCard(promoter.uid))
    assert p.pp == 0 and count(p.field, dragon.DRAGONEWT_PROMOTER) == 3
    for copy in p.field:
        assert copy.has(Keyword.RUSH)
        assert attacks_by(state, copy.uid) == [Attack(copy.uid, enemy.uid)]   # 突进：只能打随从
    # 场上只剩 1 格：只召唤得出 1 个
    state = start()
    p = state.players[0]
    for _ in range(3):
        put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 4)
    promoter = give(state, 0, dragon.DRAGONEWT_PROMOTER)
    act(state, PlayCard(promoter.uid))
    assert count(p.field, dragon.DRAGONEWT_PROMOTER) == 2 and len(p.field) == 5


def test_dragonsign():
    # PP 上限 +1；之后若上限为 10 则抽 1 张。已经是 10 时也抽。
    state = start()
    p = state.players[0]
    set_pp(state, 0, 10)
    card = give(state, 0, dragon.DRAGONSIGN)
    hand = len(p.hand)
    act(state, PlayCard(card.uid))
    assert (p.max_pp, p.pp, len(p.hand)) == (10, 7, hand)
    set_pp(state, 0, 8)
    card = give(state, 0, dragon.DRAGONSIGN)
    hand = len(p.hand)
    act(state, PlayCard(card.uid))
    assert (p.max_pp, p.pp, len(p.hand)) == (9, 5, hand - 1)   # 9：不抽，新的一点是空的


def test_zooey_ally_of_the_world():
    # 入场曲：PP 上限 +1。爆能强化 10：疾驰；主战者生命上限变为 1；
    # 到对手回合结束前，主战者受到的伤害变为 0（Q&A：对手回合结束时的伤害也挡住）。
    state = start(first=0)
    p = state.players[0]
    set_pp(state, 0, 9)
    zooey = give(state, 0, dragon.ZOOEY)
    act(state, PlayCard(zooey.uid))                      # 9 PP：不强化
    assert p.max_pp == 10 and not zooey.has(Keyword.STORM)
    assert (p.leader_hp, p.leader_max_hp) == (20, 20)

    state = start(first=0)
    p = state.players[0]
    set_pp(state, 0, 10)
    zooey = give(state, 0, dragon.ZOOEY)
    act(state, PlayCard(zooey.uid))
    assert p.max_pp == 10 and p.pp == 0
    assert (p.leader_hp, p.leader_max_hp) == (1, 1)
    assert Attack(zooey.uid, leader_uid(1)) in legal_actions(state)
    erntz = make_evolved(state, put(state, 1, dragon.ERNTZ))   # 对手回合结束时打我方主战者 8
    act(state, EndTurn())
    act(state, EndTurn())                                # 对手回合结束：伤害变为 0
    assert p.leader_hp == 1 and not state.over and erntz.fate == IN_PLAY
    assert p.damage_cap is None                          # 我方下个回合已经失效
    E.heal_leader(state, 0, 5)
    assert p.leader_hp == 1                              # 上限仍是 1


def test_sagatsumatsu_fair_beheader():
    # 入场曲：选 1 张手牌舍弃，加 2 张赤流。疾驰、毁灭、灵气。
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 7)
    saga = give(state, 0, dragon.SAGATSUMATSU)
    assert plays(state, saga.uid) == [PlayCard(saga.uid)]   # 没有别的手牌也能打
    act(state, PlayCard(saga.uid))
    assert count(p.hand, dragon.SPILLING_RED) == 2 and len(p.hand) == 2
    assert saga.has(Keyword.STORM) and saga.has(Keyword.BANE) and saga.has(Keyword.AURA)
    assert Attack(saga.uid, leader_uid(1)) in legal_actions(state)
    # 灵气：对手的能力选不到它，但可以攻击它
    assert saga.uid not in selectable(state, 1, TargetSpec(Target.ENEMY_FOLLOWER))
    act(state, EndTurn())
    raider = put(state, 1, demo.RAIDER)
    assert Attack(raider.uid, saga.uid) in legal_actions(state)
    # 有手牌时必须舍弃 1 张（只能选手牌里的牌，不能选自己）
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 7)
    saga = give(state, 0, dragon.SAGATSUMATSU)
    depths = give(state, 0, dragon.DEPTHS_OF_THE_ELD_BLADES)
    assert plays(state, saga.uid) == [PlayCard(saga.uid, (depths.uid,))]
    act(state, PlayCard(saga.uid, (depths.uid,)))
    assert count(p.hand, dragon.SPILLING_RED) == 2 and state.players[1].leader_hp == 19


def test_spilling_red():
    # 选 1 张手牌舍弃，再选 1 个敌方随从破坏；两样都选得到才能使用（Q&A）。
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 1)
    red = give(state, 0, dragon.SPILLING_RED)
    put(state, 1, demo.GIANT)
    assert plays(state, red.uid) == []                   # 没有可舍弃的手牌
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 1)
    red = give(state, 0, dragon.SPILLING_RED)
    footman = give(state, 0, demo.FOOTMAN)
    put(state, 1, dragon.SAGATSUMATSU)                   # 灵气：选不到
    assert plays(state, red.uid) == []
    giant = put(state, 1, demo.GIANT)
    assert plays(state, red.uid) == [PlayCard(red.uid, (footman.uid, giant.uid))]
    act(state, PlayCard(red.uid, (footman.uid, giant.uid)))
    assert giant.fate == DESTROYED and p.hand == [] and p.shadows == 2   # 舍弃 1 + 法术 1


def test_normagdala_ravening_revenant():
    # 入场曲【模式】：(1) 抽 1、回复 3；(2) 敌方所有随从 -0/-4。守护。进化时：再选一次模式发动。
    state = start()
    p = state.players[0]
    giant, footman = put(state, 1, demo.GIANT), put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 7)
    norma = give(state, 0, dragon.NORMAGDALA)
    assert {a.modes for a in plays(state, norma.uid)} == {(0,), (1,)}
    act(state, PlayCard(norma.uid, modes=(1,)))
    assert footman.fate == DESTROYED and (giant.atk, giant.life, giant.max_life) == (5, 1, 1)
    assert norma.has(Keyword.WARD)
    # 进化：重新选模式（Q&A：复制模式类入场曲时可以重新选择）
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    unlock_evolution(state, 0)
    norma = put(state, 0, dragon.NORMAGDALA)
    hand = len(p.hand)
    act(state, Evolve(norma.uid, False, (), (0,)))
    assert p.leader_hp == 13 and len(p.hand) == hand + 1
    # 超进化也会发动「进化时」
    state = start()
    unlock_evolution(state, 0)
    norma = put(state, 0, dragon.NORMAGDALA)
    giant = put(state, 1, demo.GIANT)
    act(state, Evolve(norma.uid, True, (), (1,)))
    assert giant.life == 1


def test_lumiore_and_argente_shining_wings():
    # 入场曲：选 2 张手牌舍弃，对所有敌人 4 伤。超进化时抽 3。激奏 3：PP 上限 +1。
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 5)
    lumiore = give(state, 0, dragon.LUMIORE_AND_ARGENTE)
    assert plays(state, lumiore.uid) == [PlayCard(lumiore.uid)]
    act(state, PlayCard(lumiore.uid))                    # PP 不够 8：激奏
    assert (p.max_pp, p.pp) == (6, 2) and p.field == [] and p.shadows == 1
    set_pp(state, 0, 2)
    lumiore = give(state, 0, dragon.LUMIORE_AND_ARGENTE)
    assert plays(state, lumiore.uid) == []               # 激奏也付不起
    # 手牌只有 1 张：舍弃这 1 张，伤害照常
    state = start()
    p = state.players[0]
    p.hand.clear()
    set_pp(state, 0, 8)
    lumiore = give(state, 0, dragon.LUMIORE_AND_ARGENTE)
    footman = give(state, 0, demo.FOOTMAN)
    saga = put(state, 1, dragon.SAGATSUMATSU)            # 灵气也会被全体伤害打到
    act(state, PlayCard(lumiore.uid, (footman.uid,)))
    assert p.hand == [] and saga.fate == DESTROYED and state.players[1].leader_hp == 16
    assert lumiore in p.field and p.max_pp == 8          # 正常使用：不涨 PP
    # 普通进化不抽牌
    state = start()
    p = state.players[0]
    p.hand.clear()
    unlock_evolution(state, 0)
    lumiore = put(state, 0, dragon.LUMIORE_AND_ARGENTE)
    act(state, evolves_of(state, lumiore.uid, False)[0])
    assert p.hand == []


def test_burnite_anathema_of_ash():
    # 入场曲：敌方所有随从 9 伤。超进化时：对手获得纹章：焦灰的安纳提玛·班德奈特。
    state = start()
    saga, giant = put(state, 1, dragon.SAGATSUMATSU), put(state, 1, demo.GIANT)
    mine = put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 9)
    burnite = give(state, 0, dragon.BURNITE)
    act(state, PlayCard(burnite.uid))
    assert saga.fate == DESTROYED and giant.fate == DESTROYED and mine.fate == IN_PLAY
    # 普通进化不给纹章，超进化才给
    state = start(first=0)
    unlock_evolution(state, 0)
    burnite = put(state, 0, dragon.BURNITE)
    act(state, evolves_of(state, burnite.uid, False)[0])
    assert state.players[1].leader_area == []
    state = start(first=0)
    unlock_evolution(state, 0)
    burnite = put(state, 0, dragon.BURNITE)
    act(state, evolves_of(state, burnite.uid, True)[0])
    assert E.leader_area_card(state, 1, dragon.BURNITE_CREST) is not None


def test_burnite_crest():
    # 纹章（在对手那边）：对手回合开始时打其主战者 2；对手自己的回合中每回合 1 次，
    # 其主战者回复时打其 1（回复 0 也算：一弹班德的同文 Q&A）。我方回合中回复不触发。
    state = start(first=0)
    enemy = state.players[1]
    E.add_to_leader_area(state, 1, dragon.BURNITE_CREST)
    enemy.leader_hp = 10
    E.heal_leader(state, 1, 3)                           # 我方回合：不触发
    resolve_queue(state)
    assert enemy.leader_hp == 13
    act(state, EndTurn())
    assert enemy.leader_hp == 11                         # 回合开始 2 伤
    E.heal_leader(state, 1, 4)
    resolve_queue(state)
    assert enemy.leader_hp == 14                         # 回复 4 后再受 1
    E.heal_leader(state, 1, 4)
    resolve_queue(state)
    assert enemy.leader_hp == 18                         # 每回合 1 次


def test_erntz_governing_justice():
    # 守护。回合结束时：进化前→随机 2 个敌方随从 8 伤并回复 8；进化后→打敌方主战者 8。
    # 进化时失去守护、获得威慑。
    state = start(first=0)
    p = state.players[0]
    put(state, 0, dragon.ERNTZ)
    lone = put(state, 1, demo.GIANT)                     # 只有 1 个敌方随从
    p.leader_hp = 15
    act(state, EndTurn())
    assert lone.fate == DESTROYED and p.leader_hp == 20  # 回复不超过上限
    assert state.players[1].leader_hp == 20
    # 超进化：同样失去守护、获得威慑，回合结束打脸、不回复
    state = start(first=0)
    p = state.players[0]
    p.leader_hp = 15
    unlock_evolution(state, 0)
    erntz = put(state, 0, dragon.ERNTZ)
    act(state, evolves_of(state, erntz.uid, True)[0])
    assert not erntz.has(Keyword.WARD) and erntz.has(Keyword.INTIMIDATE)
    act(state, EndTurn())
    assert state.players[1].leader_hp == 12 and p.leader_hp == 15
    raider = put(state, 1, demo.RAIDER)
    assert attacks_by(state, raider.uid) == [Attack(raider.uid, leader_uid(0))]   # 威慑：打不到它


# --- 标准表其余卡 -----------------------------------------------------------------------

def test_ephemeral_foxfire():
    # 选敌方随从或敌方主战者 1 伤；牌组加 1 张狐火蜃景；觉醒时抽 1。
    state = start()
    p = state.players[0]
    put(state, 1, dragon.SAGATSUMATSU)                   # 灵气：选不到
    set_pp(state, 0, 7)
    fox = give(state, 0, dragon.EPHEMERAL_FOXFIRE)
    assert plays(state, fox.uid) == [PlayCard(fox.uid, (leader_uid(1),))]
    deck, hand = len(p.deck), len(p.hand)
    act(state, PlayCard(fox.uid, (leader_uid(1),)))
    assert state.players[1].leader_hp == 19
    assert len(p.deck) == deck and len(p.hand) == hand   # +1 张进牌组，觉醒再抽 1
    assert count(p.deck, dragon.EPHEMERAL_FOXFIRE) + count(p.hand, dragon.EPHEMERAL_FOXFIRE) == 1


def test_lyria_skydestined():
    # 爆能强化 8：抽 1 张费用 7 以上的随从，回复 7 PP。屏障。
    state = start()
    p = state.players[0]
    p.deck.insert(0, state.new_instance(dragon.ERNTZ, 0))
    p.deck.insert(0, state.new_instance(dragon.BLACKFLAME_DELUGE, 0))   # 7 费法术不算
    set_pp(state, 0, 10)
    lyria = give(state, 0, neutral.LYRIA)
    act(state, PlayCard(lyria.uid))
    assert p.hand[-1].defn == dragon.ERNTZ and p.pp == 9    # 10 - 8 + 7
    assert count(p.deck, dragon.BLACKFLAME_DELUGE) == 1
    assert lyria.has(Keyword.BARRIER)
    # 7 PP：不强化，只付 2
    state = start()
    p = state.players[0]
    set_pp(state, 0, 7)
    lyria = give(state, 0, neutral.LYRIA)
    hand = len(p.hand)
    act(state, PlayCard(lyria.uid))
    assert p.pp == 5 and len(p.hand) == hand - 1


def test_kimika_cook_of_happiness():
    # 入场曲：选 1 张手牌舍弃，抽 1，回复主战者 1。进化时：同样效果（超进化也发动）。
    state = start()
    p, o = state.players
    p.hand.clear()
    p.leader_hp = 15
    set_pp(state, 0, 2)
    kimika = give(state, 0, dragon.KIMIKA)
    depths = give(state, 0, dragon.DEPTHS_OF_THE_ELD_BLADES)
    act(state, PlayCard(kimika.uid, (depths.uid,)))
    assert len(p.hand) == 1 and p.leader_hp == 17 and o.leader_hp == 19   # 深渊被舍弃也发动
    # 空手也能打：照样抽牌回复
    state = start()
    p = state.players[0]
    p.hand.clear()
    p.leader_hp = 15
    set_pp(state, 0, 2)
    kimika = give(state, 0, dragon.KIMIKA)
    act(state, PlayCard(kimika.uid))
    assert len(p.hand) == 1 and p.leader_hp == 16
    # 超进化：复制入场曲
    state = start()
    p = state.players[0]
    p.hand.clear()
    p.leader_hp = 15
    unlock_evolution(state, 0)
    kimika = put(state, 0, dragon.KIMIKA)
    footman = give(state, 0, demo.FOOTMAN)
    act(state, Evolve(kimika.uid, True, (footman.uid,)))
    assert footman not in p.hand and len(p.hand) == 1 and p.leader_hp == 16


def test_wilnas_flame_personified():
    # 入场曲：选 1 个敌方随从 8 伤。威慑。进化时：同样效果（超进化也发动）。
    state = start()
    saga, giant = put(state, 1, dragon.SAGATSUMATSU), put(state, 1, demo.GIANT)
    set_pp(state, 0, 7)
    wilnas = give(state, 0, dragon.WILNAS)
    assert plays(state, wilnas.uid) == [PlayCard(wilnas.uid, (giant.uid,))]   # 灵气选不到
    act(state, PlayCard(wilnas.uid, (giant.uid,)))
    assert giant.fate == DESTROYED and wilnas.has(Keyword.INTIMIDATE)
    state = start()
    unlock_evolution(state, 0)
    wilnas = put(state, 0, dragon.WILNAS)
    giant = put(state, 1, demo.GIANT)
    act(state, Evolve(wilnas.uid, True, (giant.uid,)))
    assert giant.fate == DESTROYED


def test_alabaster_bahamut():
    # 入场曲【模式】：(1) 其他所有随从消失；(2) 所有护符消失；(3) 所有纹章消失（不含信仰）。
    state = start()
    p = state.players[0]
    vorlalai = put(state, 0, dragon.VORLALAI)
    bomber = put(state, 1, demo.BOMBER)
    set_pp(state, 0, 9)
    bahamut = give(state, 0, neutral.ALABASTER_BAHAMUT)
    assert {a.modes for a in plays(state, bahamut.uid)} == {(0,), (1,), (2,)}
    shadows = (p.shadows, state.players[1].shadows)
    act(state, PlayCard(bahamut.uid, modes=(0,)))
    assert vorlalai.fate == BANISHED and bomber.fate == BANISHED and p.field == [bahamut]
    assert (p.shadows, state.players[1].shadows) == shadows and state.players[1].leader_hp == 20
    # 模式 3：双方的纹章都消失（包括给对手的班德纹章）
    state = start()
    crest = E.add_to_leader_area(state, 1, dragon.BURNITE_CREST)
    own = E.add_to_leader_area(state, 0, dragon.YUBE_CREST)
    set_pp(state, 0, 9)
    bahamut = give(state, 0, neutral.ALABASTER_BAHAMUT)
    act(state, PlayCard(bahamut.uid, modes=(2,)))
    assert crest.fate == BANISHED and own.fate == BANISHED
    assert state.players[0].leader_area == [] and state.players[1].leader_area == []


# --- 自由位卡 ---------------------------------------------------------------------------

def test_jellyfish_dancer():
    # 入场曲：加 1 张大海虎鲸。己方海洋随从进场时，本随从获得突进和毁灭。
    state = start()
    p = state.players[0]
    p.hand.clear()
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 2)
    dancer = give(state, 0, dragon.JELLYFISH_DANCER)
    act(state, PlayCard(dancer.uid))
    assert [c.defn for c in p.hand] == [dragon.MAJESTIC_MEGALORCA]
    assert attacks_by(state, dancer.uid) == []
    E.summon(state, 0, dragon.MAJESTIC_MEGALORCA)        # 召唤进场也算
    resolve_queue(state)
    assert dancer.has(Keyword.RUSH) and dancer.has(Keyword.BANE)
    assert attacks_by(state, dancer.uid) == [Attack(dancer.uid, enemy.uid)]


def test_roar_of_prominence():
    # 对所有随从造成 X 伤，X = 场上随从数（双方合计）。
    state = start()
    mine = put(state, 0, dragon.NORMAGDALA)              # 5/6
    other = put(state, 0, dragon.VORLALAI)               # 0/2
    giants = [put(state, 1, demo.GIANT) for _ in range(2)]
    saga = put(state, 1, dragon.SAGATSUMATSU)
    set_pp(state, 0, 4)
    roar = give(state, 0, dragon.ROAR_OF_PROMINENCE)
    act(state, PlayCard(roar.uid))                       # X = 5
    assert mine.life == 1 and other.fate == DESTROYED and saga.fate == DESTROYED
    assert all(g.fate == DESTROYED for g in giants)


def test_dark_dimensions():
    # 吟唱 2。自己回合结束时，对所有非侵蚀者随从造成 2 伤（双方）。
    state = start(first=0)
    set_pp(state, 0, 4)
    dims = give(state, 0, neutral.DARK_DIMENSIONS)
    act(state, PlayCard(dims.uid))
    mine, theirs = put(state, 0, dragon.NORMAGDALA), put(state, 1, demo.GIANT)
    vorlalai = put(state, 0, dragon.VORLALAI)            # 侵蚀者：不受伤
    act(state, EndTurn())
    assert (mine.life, theirs.life, vorlalai.life) == (4, 3, 2)
    act(state, EndTurn())                                # 对手回合结束：不发动
    assert theirs.life == 3 and dims.countdown == 1
    act(state, EndTurn())                                # 第二次发动
    assert (mine.life, theirs.life) == (2, 1)
    act(state, EndTurn())
    assert dims.fate == DESTROYED                        # 我方再下个回合开始时吟唱归零


def test_fate_of_the_world():
    # 抽 2；破坏随机 1 个攻击力最高的敌方随从（灵气也会被选中）。爆能强化 10：对所有敌人 4 伤。
    hits = set()
    for seed in range(12):
        state = start(seed=seed)
        p = state.players[0]
        saga, giant = put(state, 1, dragon.SAGATSUMATSU), put(state, 1, demo.GIANT)   # 都是 5 攻
        small = put(state, 1, demo.FOOTMAN)
        set_pp(state, 0, 5)
        card = give(state, 0, neutral.FATE_OF_THE_WORLD)
        hand = len(p.hand)
        act(state, PlayCard(card.uid))
        assert len(p.hand) == hand + 1 and small.fate == IN_PLAY
        assert (saga.fate == DESTROYED) + (giant.fate == DESTROYED) == 1
        hits.add(saga.fate == DESTROYED)
    assert hits == {True, False}
    state = start()
    giant, small = put(state, 1, demo.GIANT), put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 10)
    card = give(state, 0, neutral.FATE_OF_THE_WORLD)
    act(state, PlayCard(card.uid))
    assert giant.fate == DESTROYED and small.fate == DESTROYED
    assert state.players[1].leader_hp == 16 and state.players[0].pp == 0


def test_blackflame_deluge():
    # 敌方所有随从 5 伤，敌方主战者 3 伤；己方不受影响。
    state = start()
    saga, giant = put(state, 1, dragon.SAGATSUMATSU), put(state, 1, dragon.NORMAGDALA)
    mine = put(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 7)
    card = give(state, 0, dragon.BLACKFLAME_DELUGE)
    act(state, PlayCard(card.uid))
    assert saga.fate == DESTROYED and giant.life == 1 and mine.life == 2
    assert state.players[1].leader_hp == 17 and state.players[0].leader_hp == 20


# --- 只看身材与关键词 ---------------------------------------------------------------------

# card: (职业, 类型, 费用, 攻, 防, 关键词, 种族)；数值取自官方卡牌数据
_STATS = [
    (dragon.SLOTH_OF_THE_CRESTPETAL, Craft.DRAGON, CardType.SPELL, 2, 0, 0, Keyword.NONE, ()),
    (dragon.VORLALAI, Craft.DRAGON, CardType.FOLLOWER, 2, 0, 2, Keyword.BANE, ("Encroacher",)),
    (dragon.DRAGONEWT_PROMOTER, Craft.DRAGON, CardType.FOLLOWER, 2, 2, 1, Keyword.RUSH, ()),
    (dragon.DRAGONSIGN, Craft.DRAGON, CardType.SPELL, 3, 0, 0, Keyword.NONE, ()),
    (dragon.ZOOEY, Craft.DRAGON, CardType.FOLLOWER, 5, 5, 5, Keyword.NONE, ()),
    (dragon.SAGATSUMATSU, Craft.DRAGON, CardType.FOLLOWER, 7, 5, 4,
     Keyword.STORM | Keyword.BANE | Keyword.AURA, ()),
    (dragon.NORMAGDALA, Craft.DRAGON, CardType.FOLLOWER, 7, 5, 6, Keyword.WARD, ()),
    (dragon.LUMIORE_AND_ARGENTE, Craft.DRAGON, CardType.FOLLOWER, 8, 6, 6, Keyword.NONE, ()),
    (dragon.BURNITE, Craft.DRAGON, CardType.FOLLOWER, 9, 9, 9, Keyword.NONE, ("Anathema",)),
    (dragon.ERNTZ, Craft.DRAGON, CardType.FOLLOWER, 10, 8, 8, Keyword.WARD, ()),
    (dragon.EPHEMERAL_FOXFIRE, Craft.DRAGON, CardType.SPELL, 1, 0, 0, Keyword.NONE, ()),
    (neutral.LYRIA, Craft.NEUTRAL, CardType.FOLLOWER, 2, 1, 1, Keyword.BARRIER, ()),
    (dragon.KIMIKA, Craft.DRAGON, CardType.FOLLOWER, 2, 2, 1, Keyword.NONE, ()),
    (dragon.WILNAS, Craft.DRAGON, CardType.FOLLOWER, 7, 8, 6, Keyword.INTIMIDATE, ()),
    (neutral.ALABASTER_BAHAMUT, Craft.NEUTRAL, CardType.FOLLOWER, 9, 13, 13, Keyword.NONE, ()),
    (dragon.JELLYFISH_DANCER, Craft.DRAGON, CardType.FOLLOWER, 2, 2, 1, Keyword.NONE, ()),
    (dragon.ROAR_OF_PROMINENCE, Craft.DRAGON, CardType.SPELL, 4, 0, 0, Keyword.NONE, ()),
    (neutral.DARK_DIMENSIONS, Craft.NEUTRAL, CardType.COUNTDOWN_AMULET, 4, 0, 0, Keyword.NONE, ()),
    (neutral.FATE_OF_THE_WORLD, Craft.NEUTRAL, CardType.SPELL, 5, 0, 0, Keyword.NONE, ()),
    (dragon.BLACKFLAME_DELUGE, Craft.DRAGON, CardType.SPELL, 7, 0, 0, Keyword.NONE, ("Anathema",)),
    # 衍生 / 相关卡
    (dragon.DEPTHS_OF_THE_ELD_BLADES, Craft.DRAGON, CardType.SPELL, 2, 0, 0, Keyword.NONE,
     ("Encroacher",)),
    (dragon.SPILLING_RED, Craft.DRAGON, CardType.SPELL, 1, 0, 0, Keyword.NONE, ()),
    (dragon.MAJESTIC_MEGALORCA, Craft.DRAGON, CardType.FOLLOWER, 2, 2, 2, Keyword.RUSH, ("Marine",)),
]


def test_card_stats_and_keywords():
    for defn, craft, ctype, cost, atk, life, kw, traits in _STATS:
        assert (defn.craft, defn.type, defn.cost, defn.atk, defn.life, defn.keywords,
                defn.traits) == (craft, ctype, cost, atk, life, kw, traits), defn.name
    assert neutral.DARK_DIMENSIONS.countdown == 2
    assert dragon.DEPTHS_OF_THE_ELD_BLADES.is_token and dragon.MAJESTIC_MEGALORCA.is_token
    assert dragon.LUMIORE_AND_ARGENTE.accelerate == dragon.LUMIORE_ACCELERATE
    assert dragon.LUMIORE_ACCELERATE.cost == 3 and dragon.LUMIORE_ACCELERATE.is_spell
    assert dragon.BURNITE_CREST.type == CardType.CREST
