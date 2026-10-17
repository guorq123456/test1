"""Tournament deck audit: 机锋 / 宇宙鱼 (nemesis-t), first half of the card list.

One regression test per audited card, asserting the official behaviour. Each
comment paraphrases the card; tokens and crests a card creates are checked in
that card's test.
"""
from svsim.cards import demo, neutral as N, portal as P
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Engage, Evolve, Fuse, PlayCard
from svsim.core.engine import apply, legal_actions, resolve_queue
from svsim.core.enums import CardType, Keyword
from svsim.core.state import BANISHED, DESTROYED, IN_PLAY, leader_uid

from helpers import count, give, pass_turns, plays, put, set_pp, start, unlock_evolution


# --- helpers ------------------------------------------------------------------------------

def hand_only(state, player, *defns):
    """Empty a player's hand, then give them these cards."""
    state.players[player].hand.clear()
    return [give(state, player, d) for d in defns]


def deck_of(state, player, defns):
    """Replace a player's deck (the last card listed is drawn first)."""
    state.players[player].deck = [state.new_instance(d, player) for d in defns]
    return state.players[player].deck


def do(state, action):
    """Apply an action after checking that it is legal."""
    assert action in legal_actions(state), action
    apply(state, action)


def play(state, inst, targets=(), modes=()):
    do(state, PlayCard(inst.uid, tuple(targets), tuple(modes)))


def can_attack(state, attacker, target_uid):
    return Attack(attacker.uid, target_uid) in legal_actions(state)


def defns(cards):
    return [c.defn for c in cards]


# --- core cards ---------------------------------------------------------------------------

def test_sincerity_of_the_dewdrop():
    # 选择战场上的 1 张卡（双方的随从或护符均可），使其变身为伊鞠的小鬼（2 费 3/3 突进）。
    state = start()
    p, opp = state.players
    theater = put(state, 0, P.PUPPET_THEATER)              # an allied amulet can be selected
    shade = put(state, 1, demo.SHADE)                      # enemy Ambush: can't be selected
    giant = put(state, 1, demo.GIANT)
    E.buff(state, giant, 2, 2)
    spell, = hand_only(state, 0, P.SINCERITY_OF_THE_DEWDROP)
    set_pp(state, 0, 1)
    assert {a.targets for a in plays(state, spell.uid)} == {(theater.uid,), (giant.uid,)}
    play(state, spell, (giant.uid,))
    assert giant.defn == P.IMARIS_LITTLE_BUDDIES and opp.field == [shade, giant]
    assert (giant.cost, giant.atk, giant.life) == (2, 3, 3) and giant.has(Keyword.RUSH)

    spell, = hand_only(state, 0, P.SINCERITY_OF_THE_DEWDROP)
    set_pp(state, 0, 1)
    play(state, spell, (theater.uid,))
    assert theater.defn == P.IMARIS_LITTLE_BUDDIES and theater.defn.type == CardType.FOLLOWER
    assert theater.countdown is None and p.field == [theater]
    assert not can_attack(state, theater, leader_uid(1))  # transformed: no leader attack this turn

    state = start()                                        # nothing selectable: can't be played
    put(state, 1, demo.SHADE)
    spell, = hand_only(state, 0, P.SINCERITY_OF_THE_DEWDROP)
    set_pp(state, 0, 1)
    assert plays(state, spell.uid) == []


def test_freerunning():
    # 模式：选 1 个发动（解析的创造物 / 古老的创造物加入手牌）；本局进入过己方战场的
    # 创造物·随从有 3 种或以上名字时，改为全部发动。
    state = start()
    p = state.players[0]
    spell, = hand_only(state, 0, P.FREERUNNING)
    for defn in (P.ANALYZING_ARTIFACT, P.ANALYZING_ARTIFACT, P.ANCIENT_ARTIFACT):
        put(state, 0, defn)                                # 3 entries, but only 2 names
    for defn in (P.MYSTIC_ARTIFACT, P.RADIANT_ARTIFACT):
        put(state, 1, defn)                                # enemy artifacts don't count
    resolve_queue(state)
    set_pp(state, 0, 1)
    assert {a.modes for a in plays(state, spell.uid)} == {(0,), (1,)}
    E.banish(state, p.field[0])                            # having left the field still counts
    P.summon(state, 0, P.MYSTIC_ARTIFACT)                  # a summoned one counts: 3 names
    resolve_queue(state)
    assert [a.modes for a in plays(state, spell.uid)] == [(0, 1)]
    before = len(p.hand)
    play(state, spell, modes=(0, 1))
    assert len(p.hand) == before + 1                       # the spell left, two artifacts came
    assert count(p.hand, P.ANALYZING_ARTIFACT) == 1 and count(p.hand, P.ANCIENT_ARTIFACT) == 1


def test_bluerust_underling():
    # 入场曲：若牌组中没有重复卡牌，选择对手的 1 个随从造成 5 点伤害。突进。
    state = start()
    deck_of(state, 0, demo.ALL)                            # no duplicates
    giant = put(state, 1, demo.GIANT)
    E.buff(state, giant, 0, 1)                             # 5/6
    shade = put(state, 1, demo.SHADE)
    underling, = hand_only(state, 0, P.BLUERUST_UNDERLING)
    set_pp(state, 0, 1)
    assert {a.targets for a in plays(state, underling.uid)} == {(giant.uid,)}
    play(state, underling, (giant.uid,))
    assert giant.life == 1 and shade.life == 2
    assert can_attack(state, underling, giant.uid) and not can_attack(state, underling, leader_uid(1))

    state = start()                                        # 40 Footmen: duplicates
    giant = put(state, 1, demo.GIANT)
    underling, = hand_only(state, 0, P.BLUERUST_UNDERLING)
    set_pp(state, 0, 1)
    assert plays(state, underling.uid) == [PlayCard(underling.uid)]
    play(state, underling)
    assert giant.life == 5


def test_disgraceful_banishment():
    # 舍弃 1 张手牌；抽 1 张有毁灭的超越者随从；之后若牌组中没有重复卡牌，再抽 2 张。
    state = start()
    p = state.players[0]
    deck_of(state, 0, [P.CUTTHROAT, P.CUTTHROAT, demo.ASSASSIN, P.ISAAC, demo.GIANT])
    spell, junk = hand_only(state, 0, P.DISGRACEFUL_BANISHMENT, demo.FOOTMAN)
    set_pp(state, 0, 1)
    play(state, spell, (junk.uid,))
    # Only Cutthroat is a Portalcraft follower with Bane (Assassin is Neutral, Isaac has no
    # Bane). After drawing it the deck has no duplicates, so 2 more cards are drawn.
    assert defns(p.hand) == [P.CUTTHROAT, demo.GIANT, P.ISAAC]
    assert defns(p.deck) == [P.CUTTHROAT, demo.ASSASSIN]
    assert junk not in p.hand and p.shadows == 2           # the discard and the spell

    state = start()
    p = state.players[0]
    deck_of(state, 0, [demo.FOOTMAN, demo.FOOTMAN, demo.ASSASSIN, P.MECHANIZED_BEAST])
    spell, junk = hand_only(state, 0, P.DISGRACEFUL_BANISHMENT, demo.FOOTMAN)
    set_pp(state, 0, 1)
    play(state, spell, (junk.uid,))
    assert defns(p.hand) == [P.MECHANIZED_BEAST]           # duplicates left: no extra draw

    spell, = hand_only(state, 0, P.DISGRACEFUL_BANISHMENT)
    set_pp(state, 0, 1)
    assert plays(state, spell.uid) == []                   # a spell needs its hand card to select


def test_cutthroat_fluxblade_convict():
    # 毁灭。进化时：抽 1 张有毁灭的超越者随从；之后若牌组中没有重复卡牌，获得纹章。
    # 纹章：自己使用随从时（每个自己的回合 1 次），使其进化。
    state = start(first=0)
    p = state.players[0]
    unlock_evolution(state, 0)
    deck_of(state, 0, [P.CUTTHROAT, P.CUTTHROAT, demo.ASSASSIN, demo.FOOTMAN])
    cutthroat = put(state, 0, P.CUTTHROAT)
    assert (cutthroat.cost, cutthroat.atk, cutthroat.life) == (1, 1, 1) and cutthroat.has(Keyword.BANE)
    p.hand.clear()
    do(state, Evolve(cutthroat.uid, super_=True))          # Evolve abilities also fire on super-evolve
    assert defns(p.hand) == [P.CUTTHROAT]
    assert defns(p.leader_area) == [P.CUTTHROAT_CREST]

    light, a, b = hand_only(state, 0, P.LIGHT_OF_THE_DEWDROP, demo.FOOTMAN, demo.FOOTMAN)
    set_pp(state, 0, 3)
    play(state, light)                                     # a spell doesn't use it
    play(state, a)
    play(state, b)
    assert a.evolved and not a.super_evolved and (a.atk, a.life) == (3, 4)
    assert not b.evolved and p.ep == 2                     # once per turn; no evolution point spent
    pass_turns(state, 2)
    c, = hand_only(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 1)
    play(state, c)
    assert c.evolved

    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    deck_of(state, 0, [P.CUTTHROAT, P.CUTTHROAT, P.CUTTHROAT, demo.FOOTMAN])
    cutthroat = put(state, 0, P.CUTTHROAT)
    p.hand.clear()
    do(state, Evolve(cutthroat.uid))
    assert defns(p.hand) == [P.CUTTHROAT] and p.leader_area == []   # 2 copies left: no crest


def test_puppet_lancer():
    # 入场曲：将 1 张改良型·悬丝傀儡（1 费 3/3 突进，对手回合结束时破坏）加入手牌。
    state = start(first=0)
    p = state.players[0]
    lancer, = hand_only(state, 0, P.PUPPET_LANCER)
    set_pp(state, 0, 2)
    play(state, lancer)
    assert (lancer.atk, lancer.life) == (2, 1)
    puppet, = p.hand
    assert puppet.defn == P.ENHANCED_PUPPET and (puppet.cost, puppet.atk, puppet.life) == (1, 3, 3)
    assert P.PUPPETRY in puppet.defn.traits
    enemy = put(state, 1, demo.FOOTMAN)
    set_pp(state, 0, 1)
    play(state, puppet)
    assert can_attack(state, puppet, enemy.uid) and not can_attack(state, puppet, leader_uid(1))
    apply(state, EndTurn())
    assert puppet.fate == IN_PLAY
    apply(state, EndTurn())                                # end of the opponent's turn
    assert puppet.fate == DESTROYED and lancer.fate == IN_PLAY


def test_puppet_theater():
    # 入场曲：将 1 张悬丝傀儡加入手牌。吟唱 2。自己的回合结束时，将 1 张悬丝傀儡加入手牌。
    state = start(first=0)
    p = state.players[0]
    theater, = hand_only(state, 0, P.PUPPET_THEATER)
    set_pp(state, 0, 2)
    play(state, theater)
    assert theater.countdown == 2 and defns(p.hand) == [P.PUPPET]
    puppet = p.hand[0]
    assert (puppet.cost, puppet.atk, puppet.life) == (0, 1, 1) and puppet.has(Keyword.RUSH)
    apply(state, EndTurn())
    assert count(p.hand, P.PUPPET) == 2
    apply(state, EndTurn())                                # my turn 2: countdown 1
    assert theater.countdown == 1 and theater.fate == IN_PLAY
    apply(state, EndTurn())
    assert count(p.hand, P.PUPPET) == 3
    apply(state, EndTurn())                                # my turn 3: countdown 0, destroyed
    assert theater.fate == DESTROYED
    apply(state, EndTurn())
    assert count(p.hand, P.PUPPET) == 3


def test_lyria_skydestined():
    # 爆能强化 8：抽 1 张费用 7 或以上的随从，回复 7 点 PP。屏障。
    state = start()
    p = state.players[0]
    deck = deck_of(state, 0, [P.KRATOS, demo.FOOTMAN, P.BLADE_PUPPETEER, P.CHAOS_LEGION])
    E.add_cost(deck[-1], 2)                                # an 8-cost spell: not a follower
    lyria, = hand_only(state, 0, N.LYRIA)
    set_pp(state, 0, 10)
    play(state, lyria)
    assert defns(p.hand) == [P.KRATOS]                     # not the 6-cost follower or the spell
    assert p.pp == 9 and lyria.has(Keyword.BARRIER)        # 10 - 8, then +7 up to the maximum

    state = start()
    p = state.players[0]
    deck_of(state, 0, [P.KRATOS, demo.FOOTMAN])
    lyria, = hand_only(state, 0, N.LYRIA)
    set_pp(state, 0, 7)
    play(state, lyria)
    assert p.hand == [] and p.pp == 5                      # not enhanced


def test_isaac_congenial_engineer():
    # 谢幕曲：将 1 张攻击创造物（3 费 5/1 突进；融合创造物卡，按融合费用合计
    # 1/2/3+ 变身为毁灭创造物 α/β/γ）加入手牌。
    state = start()
    p = state.players[0]
    isaac = put(state, 0, P.ISAAC)
    giant = put(state, 1, demo.GIANT)
    p.hand.clear()
    do(state, Attack(isaac.uid, giant.uid))
    assert isaac.fate == DESTROYED
    striker, = p.hand
    assert striker.defn == P.STRIKER_ARTIFACT and (striker.cost, striker.atk, striker.life) == (3, 5, 1)
    assert striker.has(Keyword.RUSH)
    one = give(state, 0, P.ANALYZING_ARTIFACT)
    give(state, 0, demo.FOOTMAN)
    assert {a.cards for a in legal_actions(state) if isinstance(a, Fuse)} == {(one.uid,)}
    do(state, Fuse(striker.uid, (one.uid,)))
    assert striker.defn == P.OMINOUS_ARTIFACT_ALPHA

    for fodder, result in (((P.ANALYZING_ARTIFACT, P.ANCIENT_ARTIFACT), P.OMINOUS_ARTIFACT_BETA),
                           ((P.MYSTIC_ARTIFACT,), P.OMINOUS_ARTIFACT_GAMMA)):
        striker, *rest = hand_only(state, 0, P.STRIKER_ARTIFACT, *fodder)
        do(state, Fuse(striker.uid, tuple(c.uid for c in rest)))
        assert striker.defn == result and p.hand == [striker]


def test_imari_dewdrop():
    # 入场曲：舍弃 1 张手牌，抽 1 张法术。自己使用法术时，若本随从已进化，召唤伊鞠的小鬼。
    # 超进化时：抽 2 张不同名的 1 费法术。
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    deck_of(state, 0, [demo.FOOTMAN, demo.FOOTMAN, P.SOULFORGE, demo.FOOTMAN])
    imari, junk = hand_only(state, 0, P.IMARI, demo.FOOTMAN)
    set_pp(state, 0, 2)
    play(state, imari, (junk.uid,))
    assert defns(p.hand) == [P.SOULFORGE] and p.shadows == 1
    light, follower = give(state, 0, P.LIGHT_OF_THE_DEWDROP), give(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 1)
    play(state, light)
    assert count(p.field, P.IMARIS_LITTLE_BUDDIES) == 0    # not evolved yet
    hand_before = len(p.hand)
    do(state, Evolve(imari.uid))
    assert len(p.hand) == hand_before                      # a plain evolution draws nothing
    set_pp(state, 0, 2)
    play(state, follower)
    assert count(p.field, P.IMARIS_LITTLE_BUDDIES) == 0    # a follower is not a spell
    light = give(state, 0, P.LIGHT_OF_THE_DEWDROP)
    play(state, light)
    buddies, = [f for f in p.field if f.defn == P.IMARIS_LITTLE_BUDDIES]
    assert (buddies.atk, buddies.life) == (3, 3) and buddies.has(Keyword.RUSH)

    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    deck_of(state, 0, [P.LIGHT_OF_THE_DEWDROP] * 3 + [P.SOULFORGE, P.PUPPET_LANCER, P.FREERUNNING,
                                                      P.DISGRACEFUL_BANISHMENT, P.SOULFORGE])
    imari = put(state, 0, P.IMARI)
    p.hand.clear()
    do(state, Evolve(imari.uid, super_=True))
    names = [c.defn.name for c in p.hand]
    assert len(names) == 2 and len(set(names)) == 2
    assert all(c.defn.is_spell and c.cost == 1 for c in p.hand)


def test_yog_zentha_eld_axe():
    # 入场曲：若己方战场上有原始费用 5 或以上的随从，将 1 张天斧深渊加入手牌。突进。
    # 天斧深渊（0 费法术）：选择己方原始费用 5 以上的随从，将同名卡加入手牌并使其费用 -3。
    state = start()
    p = state.players[0]
    put(state, 0, demo.CAPTAIN)                            # base cost 4
    enemy = put(state, 1, demo.FOOTMAN)
    yog, = hand_only(state, 0, P.YOG_ZENTHA)
    set_pp(state, 0, 2)
    play(state, yog)
    assert p.hand == []
    assert can_attack(state, yog, enemy.uid) and not can_attack(state, yog, leader_uid(1))

    state = start()
    p = state.players[0]
    giant = put(state, 0, demo.GIANT)                      # base cost 5
    yog, = hand_only(state, 0, P.YOG_ZENTHA)
    set_pp(state, 0, 2)
    play(state, yog)
    depths, = p.hand
    assert depths.defn == P.DEPTHS_OF_THE_ELD_AXE and depths.cost == 0
    assert {a.targets for a in plays(state, depths.uid)} == {(giant.uid,)}
    play(state, depths, (giant.uid,))
    copy, = p.hand
    assert copy.defn == demo.GIANT and copy.cost == 2


def test_cool_courier():
    # 入场曲：将 1 张古老的创造物（1 费 3/1 突进）加入手牌。进化时：发动与入场曲相同的能力。
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    courier, = hand_only(state, 0, P.COOL_COURIER)
    set_pp(state, 0, 2)
    play(state, courier)
    ancient, = p.hand
    assert ancient.defn == P.ANCIENT_ARTIFACT and (ancient.cost, ancient.atk, ancient.life) == (1, 3, 1)
    assert ancient.has(Keyword.RUSH) and P.ARTIFACT in ancient.defn.traits
    do(state, Evolve(courier.uid, super_=True))
    assert count(p.hand, P.ANCIENT_ARTIFACT) == 2


def test_eudie_your_dependable_mentor():
    # 入场曲：将 1 张解析的创造物加入手牌。进化时：选择己方 1 个进化前的其他随从，使其进化。
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    eudie, = hand_only(state, 0, P.EUDIE)
    set_pp(state, 0, 2)
    play(state, eudie)
    analyzing, = p.hand
    assert analyzing.defn == P.ANALYZING_ARTIFACT and (analyzing.cost, analyzing.atk, analyzing.life) == (1, 1, 1)
    p.hand.clear()
    done = put(state, 0, demo.FOOTMAN)
    E.evolve(state, done)
    courier = put(state, 0, P.COOL_COURIER)
    resolve_queue(state)
    evolves = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.uid == eudie.uid]
    assert {a.targets for a in evolves} == {(courier.uid,)}
    do(state, Evolve(eudie.uid, False, (courier.uid,)))
    assert courier.evolved and not courier.super_evolved and (courier.atk, courier.life) == (4, 3)
    # Q&A (Olivia): Evolve abilities only activate for evolutions paid with points.
    assert count(p.hand, P.ANCIENT_ARTIFACT) == 0 and p.ep == 1


def test_sho_reborn_night_king():
    # 入场曲：若超进化已解禁，本随从获得屏障。疾驰。
    state = start(first=0)
    state.players[0].turns_taken = 6                       # going first: unlocks on turn 7
    sho, = hand_only(state, 0, P.SHO)
    set_pp(state, 0, 3)
    play(state, sho)
    assert not sho.has(Keyword.BARRIER) and can_attack(state, sho, leader_uid(1))

    state = start(first=1)
    apply(state, EndTurn())                                # player 0 goes second
    state.players[0].turns_taken = 6                       # going second: unlocks on turn 6
    sho, = hand_only(state, 0, P.SHO)
    set_pp(state, 0, 3)
    play(state, sho)
    assert sho.has(Keyword.BARRIER) and sho.has(Keyword.STORM)
    assert can_attack(state, sho, leader_uid(1))


def test_slaus_revolving_wheel_of_fortune():
    # 潜行。自己回合开始时，从未发动过的能力中随机发动 1 个：手牌本回合费用 -1 / 己方随从 +2/+2 /
    # 主战者回复 3。自己回合结束时若本随从已进化，使对手获得纹章并使本随从消失。
    # 纹章：吟唱 3；回合开始时随机发动 1 个未发动的：手牌本回合 +1 / 己方随从 -2/-2 / 对自己主战者 3 伤害。
    state = start(first=0)
    p, opp = state.players
    p.leader_hp = 10
    slaus = put(state, 0, P.SLAUS)
    ally = put(state, 0, demo.FOOTMAN)
    assert (slaus.cost, slaus.atk, slaus.life) == (3, 0, 2) and slaus.has(Keyword.AMBUSH)
    p.hand.clear()                                         # keep the hand from filling up
    seen, discounted = [], []
    for _ in range(3):
        apply(state, EndTurn())
        assert all(c.cost == c.defn.cost for c in discounted)   # the discount ended with my turn
        apply(state, EndTurn())                                 # my turn starts, then I draw
        pick = slaus.counters["wheel"][-1]
        seen.append(pick)
        if pick == 0:
            *discounted, drawn = p.hand
            assert all(c.cost == c.defn.cost - 1 for c in discounted) and drawn.cost == drawn.defn.cost
    assert sorted(seen) == [0, 1, 2]
    assert (ally.atk, ally.life) == (3, 4) and (slaus.atk, slaus.life) == (2, 4) and p.leader_hp == 13
    pass_turns(state, 2)                                   # nothing left to activate
    assert (ally.atk, ally.life) == (3, 4) and p.leader_hp == 13 and len(slaus.counters["wheel"]) == 3
    apply(state, EndTurn())
    assert slaus.fate == IN_PLAY and opp.leader_area == []  # not evolved: stays

    apply(state, EndTurn())
    unlock_evolution(state, 0)
    giant = put(state, 1, demo.GIANT)
    do(state, Evolve(slaus.uid))
    opp.hand.clear()                                       # keep the opponent's hand from filling up
    shadows = p.shadows
    apply(state, EndTurn())
    assert slaus.fate == BANISHED and p.shadows == shadows
    crest, = opp.leader_area
    assert crest.defn == P.SLAUS_CREST
    seen = []
    for _ in range(3):                                     # the opponent's next three turns
        pick = crest.counters["wheel"][-1]
        seen.append(pick)
        if pick == 0:
            *raised, drawn = opp.hand
            assert all(c.cost == c.defn.cost + 1 for c in raised) and drawn.cost == drawn.defn.cost
        pass_turns(state, 2)
    assert sorted(seen) == [0, 1, 2]
    assert crest.fate == DESTROYED and opp.leader_area == []
    assert opp.leader_hp == 17 and (giant.atk, giant.life) == (3, 3)


def test_encroached_world():
    # 启动：选择 1 张手牌，使其变身为对手牌组中随机 1 张卡的复制卡牌（手牌为 0 也能启动：Q&A）。
    state = start()
    p, opp = state.players
    world = put(state, 0, N.ENCROACHED_WORLD)
    assert world.defn.type == CardType.AMULET and world.countdown is None
    original = state.new_instance(demo.GIANT, 1)
    E.add_cost(original, -2)
    opp.deck = [original]
    target, = hand_only(state, 0, demo.FOOTMAN)
    set_pp(state, 0, 0)
    do(state, Engage(world.uid, (target.uid,)))
    assert p.hand == [target] and target.defn == demo.GIANT and target.cost == 3 and target.owner == 0
    assert opp.deck == [original]
    assert not any(isinstance(a, Engage) for a in legal_actions(state))   # once per turn
    pass_turns(state, 2)
    p.hand.clear()
    assert Engage(world.uid, ()) in legal_actions(state)
    do(state, Engage(world.uid, ()))
    assert world.fate == IN_PLAY and p.hand == []

    # Engage costs nothing and works on the turn it was played (cf. Q&A on Witch's New Brew).
    state = start()
    p, opp = state.players
    opp.deck = [state.new_instance(P.MYSTIC_ARTIFACT, 1)]
    world, target = hand_only(state, 0, N.ENCROACHED_WORLD, demo.FOOTMAN)
    set_pp(state, 0, 3)
    play(state, world)
    do(state, Engage(world.uid, (target.uid,)))
    assert target.defn == P.MYSTIC_ARTIFACT and p.pp == 0


def test_intrepid_newshound():
    # 谢幕曲：抽 1 张牌。超进化时：召唤 2 个神话记者。
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    hound = put(state, 0, N.INTREPID_NEWSHOUND)
    do(state, Evolve(hound.uid))
    assert count(p.field, N.INTREPID_NEWSHOUND) == 1       # a plain evolution summons nothing

    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    hound = put(state, 0, N.INTREPID_NEWSHOUND)
    do(state, Evolve(hound.uid, super_=True))
    copies = [f for f in p.field if f is not hound]
    assert defns(copies) == [N.INTREPID_NEWSHOUND] * 2
    assert all((f.atk, f.life) == (3, 2) and not f.evolved for f in copies)
    p.hand.clear()
    E.destroy(state, copies[0])
    resolve_queue(state)
    assert len(p.hand) == 1


def test_brazen_broadcaster():
    # 入场曲：召唤解析的创造物；爆能强化 5：召唤神秘的创造物。己方创造物·随从进场时获得突进。
    state = start()
    p = state.players[0]
    enemy = put(state, 1, demo.FOOTMAN)
    broadcaster, analyzing, footman = hand_only(state, 0, P.BRAZEN_BROADCASTER,
                                                P.ANALYZING_ARTIFACT, demo.FOOTMAN)
    set_pp(state, 0, 7)
    play(state, broadcaster)
    assert p.pp == 2
    tokens = p.field[1:]
    assert defns(tokens) == [P.ANALYZING_ARTIFACT, P.MYSTIC_ARTIFACT]
    assert all(t.has(Keyword.RUSH) for t in tokens) and tokens[1].has(Keyword.WARD)
    assert len(p.hand) == 3                                # the summoned Analyzing Artifact drew
    play(state, analyzing)
    play(state, footman)
    assert analyzing.has(Keyword.RUSH) and can_attack(state, analyzing, enemy.uid)
    assert not footman.has(Keyword.RUSH)

    state = start()
    p = state.players[0]
    broadcaster, = hand_only(state, 0, P.BRAZEN_BROADCASTER)
    set_pp(state, 0, 4)
    play(state, broadcaster)
    assert defns(p.field) == [P.BRAZEN_BROADCASTER, P.ANALYZING_ARTIFACT] and p.pp == 1


def test_lazuli_gateway_connector():
    # 入场曲：将 1 张绚烂的创造物（3 费 2/2 疾驰）加入手牌。
    state = start()
    p = state.players[0]
    lazuli, = hand_only(state, 0, P.LAZULI)
    set_pp(state, 0, 6)
    play(state, lazuli)
    radiant, = p.hand
    assert radiant.defn == P.RADIANT_ARTIFACT and (radiant.cost, radiant.atk, radiant.life) == (3, 2, 2)
    play(state, radiant)
    assert can_attack(state, radiant, leader_uid(1))


def test_soulforge():
    # 选择对手的 1 个随从破坏；若牌组中没有重复卡牌，改为破坏对手的所有随从。
    state = start()
    deck_of(state, 0, demo.ALL)
    giant, shade, footman = put(state, 1, demo.GIANT), put(state, 1, demo.SHADE), put(state, 1, demo.FOOTMAN)
    spell, = hand_only(state, 0, P.SOULFORGE)
    set_pp(state, 0, 3)
    assert {a.targets for a in plays(state, spell.uid)} == {(giant.uid,), (footman.uid,)}
    play(state, spell, (giant.uid,))
    assert giant.fate == shade.fate == footman.fate == DESTROYED   # Ambush included

    state = start()
    giant, footman = put(state, 1, demo.GIANT), put(state, 1, demo.FOOTMAN)
    spell, = hand_only(state, 0, P.SOULFORGE)
    set_pp(state, 0, 3)
    play(state, spell, (giant.uid,))
    assert giant.fate == DESTROYED and footman.fate == IN_PLAY


def test_gran_and_djeeta_valiant_skyfarers():
    # 入场曲：模式选 1（随机 1 个敌方随从 5 伤害 / 抽 2 张随从）。奥义（计量 ≥ 10）：本随从进化。
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)                             # 8 turns taken
    enemy = put(state, 1, demo.GIANT)
    gd = give(state, 0, N.GRAN_AND_DJEETA)
    footman = put(state, 0, demo.FOOTMAN)
    do(state, Evolve(footman.uid))                         # gauge 9
    set_pp(state, 0, 4)
    assert {a.modes for a in plays(state, gd.uid)} == {(0,), (1,)}
    play(state, gd, modes=(0,))
    assert enemy.fate == DESTROYED and not gd.evolved

    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    deck_of(state, 0, [demo.GIANT, P.SOULFORGE, demo.LANCER, P.FREERUNNING])
    gd, = hand_only(state, 0, N.GRAN_AND_DJEETA)
    eudie, footman = put(state, 0, P.EUDIE), put(state, 0, demo.FOOTMAN)
    do(state, Evolve(eudie.uid, False, (footman.uid,)))    # two evolutions while it's in hand: gauge 10
    set_pp(state, 0, 4)
    play(state, gd, modes=(1,))
    assert sorted(c.defn.name for c in p.hand) == ["Giant", "Lancer"]
    assert gd.evolved and not gd.super_evolved and (gd.atk, gd.life) == (5, 4) and p.ep == 1


def test_marionette_master():
    # 入场曲：召唤改良型·悬丝傀儡和悬丝傀儡；爆能强化 7：使它们获得疾驰。
    for pp, storm in ((6, False), (7, True)):
        state = start()
        p = state.players[0]
        master, = hand_only(state, 0, P.MARIONETTE_MASTER)
        set_pp(state, 0, pp)
        play(state, master)
        assert p.pp == pp - (7 if storm else 4)
        puppets = p.field[1:]
        assert defns(puppets) == [P.ENHANCED_PUPPET, P.PUPPET]
        assert all(f.has(Keyword.RUSH) and f.has(Keyword.STORM) == storm for f in puppets)
        assert all(can_attack(state, f, leader_uid(1)) == storm for f in puppets)
        assert not master.has(Keyword.STORM)


def test_card_stats_and_keywords():
    # 费用 / 攻击 / 生命 / 卡牌类型 / 静态关键词与官方数据一致（含衍生卡）。
    F, A, CA, S = CardType.FOLLOWER, CardType.AMULET, CardType.COUNTDOWN_AMULET, CardType.SPELL
    K = Keyword
    table = [
        (P.SINCERITY_OF_THE_DEWDROP, S, 1, 0, 0, K.NONE),
        (P.FREERUNNING, S, 1, 0, 0, K.NONE),
        (P.BLUERUST_UNDERLING, F, 1, 1, 1, K.RUSH),
        (P.DISGRACEFUL_BANISHMENT, S, 1, 0, 0, K.NONE),
        (P.CUTTHROAT, F, 1, 1, 1, K.BANE),
        (P.PUPPET_LANCER, F, 2, 2, 1, K.NONE),
        (P.PUPPET_THEATER, CA, 2, 0, 0, K.NONE),
        (N.LYRIA, F, 2, 1, 1, K.BARRIER),
        (P.ISAAC, F, 2, 2, 2, K.NONE),
        (P.IMARI, F, 2, 2, 2, K.NONE),
        (P.YOG_ZENTHA, F, 2, 2, 1, K.RUSH),
        (P.COOL_COURIER, F, 2, 2, 1, K.NONE),
        (P.EUDIE, F, 2, 2, 2, K.NONE),
        (P.SHO, F, 3, 2, 1, K.STORM),
        (P.SLAUS, F, 3, 0, 2, K.AMBUSH),
        (N.ENCROACHED_WORLD, A, 3, 0, 0, K.NONE),
        (N.INTREPID_NEWSHOUND, F, 3, 3, 2, K.NONE),
        (P.BRAZEN_BROADCASTER, F, 3, 1, 1, K.NONE),
        (P.LAZULI, F, 3, 3, 3, K.NONE),
        (P.SOULFORGE, S, 3, 0, 0, K.NONE),
        (N.GRAN_AND_DJEETA, F, 4, 3, 2, K.NONE),
        (P.MARIONETTE_MASTER, F, 4, 3, 3, K.NONE),
        # tokens
        (P.PUPPET, F, 0, 1, 1, K.RUSH),
        (P.ENHANCED_PUPPET, F, 1, 3, 3, K.RUSH),
        (P.ANALYZING_ARTIFACT, F, 1, 1, 1, K.NONE),
        (P.ANCIENT_ARTIFACT, F, 1, 3, 1, K.RUSH),
        (P.MYSTIC_ARTIFACT, F, 3, 4, 5, K.WARD),
        (P.RADIANT_ARTIFACT, F, 3, 2, 2, K.STORM),
        (P.STRIKER_ARTIFACT, F, 3, 5, 1, K.RUSH),
        (P.IMARIS_LITTLE_BUDDIES, F, 2, 3, 3, K.RUSH),
        (P.DEPTHS_OF_THE_ELD_AXE, S, 0, 0, 0, K.NONE),
    ]
    for defn, kind, cost, atk, life, keywords in table:
        assert (defn.type, defn.cost, defn.atk, defn.life, defn.keywords) == \
            (kind, cost, atk, life, keywords), defn.name
    assert P.PUPPET_THEATER.countdown == 2 and P.SLAUS_CREST.countdown == 3
    assert P.CUTTHROAT_CREST.countdown is None
