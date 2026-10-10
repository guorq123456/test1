"""Tournament deck audit: 机锋 / 宇宙鱼 (nemesis-t), second half of the card list.

One regression test per audited card (core cards first, then the other cards of
the standard list, then the free-slot cards). Each test builds a small position
and checks the behaviour the official card text (and Q&A) asks for.
"""
from svsim.cards import demo, neutral
from svsim.cards import portal as P
from svsim.cards.pool import card
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.engine import apply, legal_actions, resolve_queue
from svsim.core.enums import CardType, Keyword
from svsim.core.state import DESTROYED, IN_PLAY, leader_uid

from helpers import count, give, pass_turns, plays, put, set_pp, start, unlock_evolution

K = Keyword


# --- helpers -------------------------------------------------------------------------------

def hand_only(state, player, *defns):
    """Empty a player's hand, then give them these cards."""
    state.players[player].hand.clear()
    return [give(state, player, d) for d in defns]


def act(state, action):
    """Apply an action, checking first that the engine offers it."""
    assert action in legal_actions(state), action
    apply(state, action)


def play(state, inst, targets=(), modes=()):
    act(state, PlayCard(inst.uid, tuple(targets), tuple(modes)))


def evolve(state, inst, super_=False, targets=()):
    act(state, Evolve(inst.uid, super_, tuple(targets)))


def highlander(state, player=0):
    """A deck with no duplicates."""
    state.players[player].deck = [state.new_instance(d, player) for d in demo.ALL]


def entered_before(state, player, *defns):
    """These followers entered the field earlier this match (and have left it since)."""
    p = state.players[player]
    for d in defns:
        p.entered[d.card_id] = p.entered.get(d.card_id, 0) + 1


def big_enemy(state, life=20):
    """An enemy 5/`life` follower that survives a few hits."""
    giant = put(state, 1, demo.GIANT)
    E.buff(state, giant, 0, life - 5)
    return giant


# --- core cards ----------------------------------------------------------------------------

def test_myuu_hot_on_his_heels():
    # 友方创造物·随从进场时随机打敌方随从3点；进化时召唤古老的创造物；
    # 超进化时之后若本局进场的友方创造物·随从≥3种则获得疾驰。
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    myuu = put(state, 0, P.MYUU)
    giant = big_enemy(state)
    put(state, 0, demo.FOOTMAN)                           # not an Artifact: nothing
    resolve_queue(state)
    assert giant.life == 20
    put(state, 0, P.MYSTIC_ARTIFACT)
    put(state, 0, P.ANALYZING_ARTIFACT)
    resolve_queue(state)
    assert giant.life == 14                               # 3 for each Artifact
    evolve(state, myuu, super_=True)
    ancient = p.field[-1]
    assert ancient.defn == P.ANCIENT_ARTIFACT and (ancient.atk, ancient.life) == (3, 1)
    assert ancient.has(K.RUSH) and Attack(ancient.uid, giant.uid) in legal_actions(state)
    assert giant.life == 11                               # its own summon triggers the 3 damage
    assert (myuu.atk, myuu.life) == (6, 8) and myuu.has(K.STORM)   # Ancient is the 3rd name

    # Only 2 names, counting the summoned Ancient Artifact: no Storm.
    state = start()
    unlock_evolution(state, 0)
    entered_before(state, 0, P.MYSTIC_ARTIFACT, P.MYSTIC_ARTIFACT)
    myuu = put(state, 0, P.MYUU)
    evolve(state, myuu, super_=True)
    assert not myuu.has(K.STORM)

    # A plain evolution summons the Ancient Artifact but never gives Storm.
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    entered_before(state, 0, P.MYSTIC_ARTIFACT, P.ANALYZING_ARTIFACT, P.RADIANT_ARTIFACT)
    myuu = put(state, 0, P.MYUU)
    giant = big_enemy(state)
    evolve(state, myuu)
    assert count(p.field, P.ANCIENT_ARTIFACT) == 1 and giant.life == 17
    assert (myuu.atk, myuu.life) == (5, 7) and not myuu.has(K.STORM)


def test_ironwork_bodyguard():
    # 入场曲：牌组无重复卡时，选择敌方随从造成4点伤害并回复主战者4点。守护。
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    highlander(state)
    giant = put(state, 1, demo.GIANT)
    guard, = hand_only(state, 0, P.IRONWORK_BODYGUARD)
    set_pp(state, 0, 4)
    play(state, guard, (giant.uid,))
    assert giant.life == 1 and p.leader_hp == 14
    assert guard.has(K.WARD) and (guard.atk, guard.life) == (4, 4)

    # No enemy follower to select: the rest still resolves.
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    highlander(state)
    guard, = hand_only(state, 0, P.IRONWORK_BODYGUARD)
    set_pp(state, 0, 4)
    play(state, guard)
    assert p.leader_hp == 14

    # Duplicates in the deck: nothing.
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    giant = put(state, 1, demo.GIANT)
    guard, = hand_only(state, 0, P.IRONWORK_BODYGUARD)
    set_pp(state, 0, 4)
    assert plays(state, guard.uid) == [PlayCard(guard.uid)]
    play(state, guard)
    assert giant.life == 5 and p.leader_hp == 10


def test_asher_and_lydia_paths_beyond():
    # 入场曲：选择敌方随从使其获得守护。爆能强化9：本随从进化并获得疾驰。
    # 本随从进化时（任何方式）：随机破坏2个拥有守护的敌方随从。
    state = start()
    footman, shield, giant = (put(state, 1, demo.FOOTMAN), put(state, 1, demo.SHIELDBEARER),
                              put(state, 1, demo.GIANT))
    asher, = hand_only(state, 0, P.ASHER_AND_LYDIA)
    set_pp(state, 0, 9)
    play(state, asher, (footman.uid,))
    assert state.players[0].pp == 0                       # Enhance cost paid
    assert asher.evolved and not asher.super_evolved and (asher.atk, asher.life) == (7, 7)
    assert asher.has(K.STORM) and state.players[0].ep == 2
    assert footman.fate == DESTROYED and shield.fate == DESTROYED and giant.fate == IN_PLAY
    assert Attack(asher.uid, leader_uid(1)) in legal_actions(state)

    # Without Enhance: only the Ward.
    state = start()
    footman = put(state, 1, demo.FOOTMAN)
    asher, = hand_only(state, 0, P.ASHER_AND_LYDIA)
    set_pp(state, 0, 8)
    play(state, asher, (footman.uid,))
    assert footman.has(K.WARD) and footman.fate == IN_PLAY and not asher.evolved
    assert not asher.has(K.STORM)

    # Super-evolving with points also counts as "this follower evolves".
    state = start()
    unlock_evolution(state, 0)
    asher = put(state, 0, P.ASHER_AND_LYDIA)
    wards = [put(state, 1, demo.SHIELDBEARER) for _ in range(3)]
    plain = put(state, 1, demo.FOOTMAN)
    evolve(state, asher, super_=True)
    assert sum(w.fate == DESTROYED for w in wards) == 2 and plain.fate == IN_PLAY


def test_steelforged_right_hand():
    # 入场曲：选择敌方随从破坏之；牌组无重复卡时本随从获得疾驰。
    for unique in (False, True):
        state = start()
        if unique:
            highlander(state)
        giant = put(state, 1, demo.GIANT)
        hand, = hand_only(state, 0, P.STEELFORGED_RIGHT_HAND)
        set_pp(state, 0, 5)
        play(state, hand, (giant.uid,))
        assert giant.fate == DESTROYED and (hand.atk, hand.life) == (3, 3)
        assert hand.has(K.STORM) == unique
        assert (Attack(hand.uid, leader_uid(1)) in legal_actions(state)) == unique


def test_sandalphon_primarch_successor():
    # 牌组中：己方随从本局进化≥6次时，回合开始瞬念召唤；被召唤时获得纹章并回到手牌。
    # Q&A（野兽公主的誓约）：吟唱归零的护符先被破坏，再瞬念召唤，然后谢幕曲（场满召唤失败），最后回手。
    state = start(first=0)
    p = state.players[0]
    totem = put(state, 0, demo.TOTEM)                     # Last Words: summon a Wisp
    totem.countdown = 1
    for _ in range(4):
        put(state, 0, demo.FOOTMAN)
    sandalphon = state.new_instance(neutral.SANDALPHON, 0)
    E.set_cost(sandalphon, 3)
    p.deck.insert(0, sandalphon)
    p.evolutions = 6
    p.hand.clear()
    pass_turns(state, 2)
    assert totem.fate == DESTROYED and count(p.field, demo.WISP) == 0
    assert count(p.field, demo.FOOTMAN) == 4 and not any(c.defn == neutral.SANDALPHON for c in p.field)
    crest = E.leader_area_card(state, 0, neutral.SANDALPHON_CREST)
    assert crest is not None and crest.countdown == 2
    back = [c for c in p.hand if c.defn == neutral.SANDALPHON]
    assert len(back) == 1 and back[0].cost == 6            # returned: cost changes gone
    assert len(p.hand) == 2                                 # plus the turn's draw

    # Crest: at the end of your turn, restore 1 defense to all allies.
    p.leader_hp = 15
    hurt = p.followers[0]
    hurt.life = 1
    apply(state, EndTurn())
    assert p.leader_hp == 16 and hurt.life == 2

    # 5 evolutions are not enough.
    state = start(first=0)
    p = state.players[0]
    sandalphon = state.new_instance(neutral.SANDALPHON, 0)
    p.deck.insert(0, sandalphon)
    p.evolutions = 5
    pass_turns(state, 2)
    assert sandalphon in p.deck and p.leader_area == []

    # Fanfare: Super Skybound Art (gauge 15) - 5 times, 2 damage to a random enemy.
    for bonus, dealt in ((13, 0), (14, 10)):
        state = start()
        giant = big_enemy(state)
        sandalphon, = hand_only(state, 0, neutral.SANDALPHON)
        E.counters(sandalphon)["skybound"] = bonus           # turn 1 + bonus
        set_pp(state, 0, 6)
        play(state, sandalphon)
        assert (20 - giant.life) + (20 - state.players[1].leader_hp) == dealt


def test_chaos_legion():
    # 对所有敌方随从与敌方主战者造成3点伤害；解放奥义（计量≥15）改为6点。
    for bonus, amount in ((4, 3), (5, 6)):
        state = start()
        state.players[0].turns_taken = 10
        giant = big_enemy(state)
        footman = put(state, 1, demo.FOOTMAN)
        spell, = hand_only(state, 0, P.CHAOS_LEGION)
        E.counters(spell)["skybound"] = bonus
        set_pp(state, 0, 6)
        play(state, spell)
        assert giant.life == 20 - amount and footman.fate == DESTROYED
        assert state.players[1].leader_hp == 20 - amount


def test_camiscilla_unfeeling_heart():
    # 入场曲：召唤低劣的玩具与拙劣的人偶。其他原始费用≥5的友方随从进场时使其进化。
    # 超进化时：对敌方主战者造成X点伤害，X为己方场上原始费用≥5的随从数。
    state = start()
    p, opp = state.players
    unlock_evolution(state, 0)
    footman = put(state, 1, demo.FOOTMAN)
    shield = put(state, 1, demo.SHIELDBEARER)
    cami, asher = hand_only(state, 0, P.CAMISCILLA, P.ASHER_AND_LYDIA)
    set_pp(state, 0, 7)
    play(state, cami)
    assert [f.defn for f in p.field] == [P.CAMISCILLA, P.SHODDY_PLAYTHING, P.SUBSTANDARD_PUPPET]
    assert [f.evolved for f in p.field] == [False, True, True]
    assert p.hand == [asher]                              # summoned: no Fanfare draws
    assert p.ep == 2
    # A played 5-cost follower is evolved after its Fanfare: Asher's own evolve trigger fires.
    set_pp(state, 0, 5)
    play(state, asher, (footman.uid,))
    assert asher.evolved and not asher.super_evolved and (asher.atk, asher.life) == (7, 7)
    assert footman.fate == DESTROYED and shield.fate == DESTROYED
    myuu = put(state, 0, P.MYUU)                          # base cost 4: not evolved
    resolve_queue(state)
    assert not myuu.evolved
    evolve(state, cami, super_=True)
    assert opp.leader_hp == 20 - 4                        # Camiscilla, Plaything, Puppet, Asher

    # A plain evolution deals no damage (Super-Evolve only).
    state = start()
    unlock_evolution(state, 0)
    cami = put(state, 0, P.CAMISCILLA)
    evolve(state, cami)
    assert state.players[1].leader_hp == 20


def test_aizeden_killshot_revenant():
    # 入场曲：召唤击针看守。友方创造物·随从进场时随机破坏1个敌方随从。超进化时：重复入场曲。
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    unlock_evolution(state, 0)
    enemies = [put(state, 1, demo.GIANT) for _ in range(3)]
    aizeden, = hand_only(state, 0, P.AIZEDEN)
    set_pp(state, 0, 7)
    play(state, aizeden)
    warden = p.field[-1]
    assert warden.defn == P.WARDEN_OF_THE_TRIGGER and (warden.atk, warden.life) == (3, 3)
    assert warden.has(K.WARD) and P.is_artifact_follower(warden)
    assert sum(e.fate == DESTROYED for e in enemies) == 1   # the Warden is an Artifact
    put(state, 0, demo.FOOTMAN)
    resolve_queue(state)
    assert sum(e.fate == DESTROYED for e in enemies) == 1
    evolve(state, aizeden, super_=True)
    assert count(p.field, P.WARDEN_OF_THE_TRIGGER) == 2
    assert sum(e.fate == DESTROYED for e in enemies) == 2
    E.destroy(state, warden)                              # Warden's Last Words
    resolve_queue(state)
    assert p.leader_hp == 12

    # A plain evolution doesn't replicate the Fanfare.
    state = start()
    unlock_evolution(state, 0)
    aizeden = put(state, 0, P.AIZEDEN)
    giant = put(state, 1, demo.GIANT)
    evolve(state, aizeden)
    assert count(state.players[0].field, P.WARDEN_OF_THE_TRIGGER) == 0 and giant.fate == IN_PLAY


def test_scarlet_anathema_of_dislocation():
    # 入场曲：对所有敌方随从造成X点伤害，X为本局进场过的友方创造物·随从种类数。疾驰、守护。
    state = start()
    p, opp = state.players
    entered_before(state, 0, P.ANCIENT_ARTIFACT, P.ANCIENT_ARTIFACT, P.MYSTIC_ARTIFACT)
    entered_before(state, 1, P.RADIANT_ARTIFACT)            # the opponent's don't count
    put(state, 0, P.ANALYZING_ARTIFACT)
    resolve_queue(state)
    giant = big_enemy(state, life=10)
    scarlet, = hand_only(state, 0, P.SCARLET)
    set_pp(state, 0, 8)
    play(state, scarlet)
    assert giant.life == 10 - 3 and opp.leader_hp == 20
    assert scarlet.has(K.STORM | K.WARD) and (scarlet.atk, scarlet.life) == (6, 6)
    assert Attack(scarlet.uid, leader_uid(1)) in legal_actions(state)


# --- other cards of the standard list --------------------------------------------------------

def test_zerk_artifact_manipulator():
    # 入场曲：随机将1张本局被破坏的友方创造物·随从的同名卡加入手牌。
    state = start()
    p = state.players[0]
    zerk, = hand_only(state, 0, P.ZERK)
    p.destroyed = [demo.FOOTMAN, demo.GIANT]               # no Artifact destroyed
    set_pp(state, 0, 1)
    play(state, zerk)
    assert p.hand == []
    for seed in range(5):
        state = start(seed=seed)
        p = state.players[0]
        zerk, = hand_only(state, 0, P.ZERK)
        p.destroyed = [demo.FOOTMAN, demo.GIANT, P.MYSTIC_ARTIFACT, demo.LANCER]
        set_pp(state, 0, 1)
        play(state, zerk)
        assert [c.defn for c in p.hand] == [P.MYSTIC_ARTIFACT]
        assert (zerk.atk, zerk.life) == (1, 1)


def test_aika_elegy_of_loss():
    # 入场曲：随机将1张本局被破坏的友方随从的同名卡加入手牌。进化时：重复入场曲（超进化也算）。
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    aika, = hand_only(state, 0, neutral.AIKA)
    set_pp(state, 0, 2)
    play(state, aika)
    assert p.hand == []
    p.destroyed = [P.WARDEN_OF_THE_TRIGGER]                 # tokens count too
    evolve(state, aika, super_=True)
    assert [c.defn for c in p.hand] == [P.WARDEN_OF_THE_TRIGGER]
    state = start()
    p = state.players[0]
    p.destroyed = [demo.GIANT]
    aika, = hand_only(state, 0, neutral.AIKA)
    set_pp(state, 0, 2)
    play(state, aika)
    assert [c.defn for c in p.hand] == [demo.GIANT] and (aika.atk, aika.life) == (2, 1)


def test_new_age_cartographer():
    # 入场曲：将毁灭创造物β加入手牌。超进化时：选择手牌中费用≤5的创造物·随从，召唤其复制。
    state = start()
    p, opp = state.players
    unlock_evolution(state, 0)
    cartographer, = hand_only(state, 0, P.NEW_AGE_CARTOGRAPHER)
    set_pp(state, 0, 4)
    play(state, cartographer)
    beta, = p.hand
    assert beta.defn == P.OMINOUS_ARTIFACT_BETA and (beta.cost, beta.atk, beta.life) == (5, 4, 4)
    alpha = give(state, 0, P.OMINOUS_ARTIFACT_ALPHA)
    E.add_cost(alpha, 1)                                   # costs 6 now: can't be selected
    give(state, 0, demo.FOOTMAN)                           # not an Artifact
    supers = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.super_]
    assert {a.targets for a in supers} == {(beta.uid,)}
    evolve(state, cartographer, super_=True, targets=(beta.uid,))
    copy = p.field[-1]
    assert copy.defn == P.OMINOUS_ARTIFACT_BETA and copy is not beta and beta in p.hand
    apply(state, EndTurn())                                # the copy's end-of-turn ability
    assert opp.leader_hp == 17

    # A plain evolution summons nothing.
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    cartographer = put(state, 0, P.NEW_AGE_CARTOGRAPHER)
    beta, = hand_only(state, 0, P.OMINOUS_ARTIFACT_BETA)
    plain = [a for a in legal_actions(state) if isinstance(a, Evolve) and not a.super_]
    assert plain
    apply(state, plain[0])
    assert p.field == [cartographer] and beta in p.hand


def test_brusque_barkeep():
    # 友方创造物·随从进场时回复主战者1点。进化时：召唤神秘的创造物（4/5 守护）。
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    unlock_evolution(state, 0)
    barkeep = put(state, 0, P.BRUSQUE_BARKEEP)
    put(state, 0, P.ANCIENT_ARTIFACT)
    put(state, 0, demo.FOOTMAN)
    resolve_queue(state)
    assert p.leader_hp == 11
    evolve(state, barkeep, super_=True)                    # super-evolving counts as evolving
    mystic = p.field[-1]
    assert mystic.defn == P.MYSTIC_ARTIFACT and (mystic.atk, mystic.life) == (4, 5)
    assert mystic.has(K.WARD) and p.leader_hp == 12


def test_twindrone_engineer():
    # 入场曲：召唤解析的创造物（进场时抽1张）。进化时：重复入场曲（超进化也算）。
    state = start()
    p = state.players[0]
    unlock_evolution(state, 0)
    engineer, = hand_only(state, 0, P.TWINDRONE_ENGINEER)
    set_pp(state, 0, 4)
    play(state, engineer)
    assert count(p.field, P.ANALYZING_ARTIFACT) == 1 and len(p.hand) == 1
    evolve(state, engineer, super_=True)
    assert count(p.field, P.ANALYZING_ARTIFACT) == 2 and len(p.hand) == 2


def test_katalina_skys_protector():
    # 入场曲：奥义（计量≥10）对随机2个敌方随从造成5点伤害。守护。一次受到的伤害最多3点。
    state = start()
    enemies = [put(state, 1, demo.GIANT) for _ in range(3)]
    katalina, = hand_only(state, 0, neutral.KATALINA)
    E.counters(katalina)["skybound"] = 9                   # turn 1 + 9
    set_pp(state, 0, 5)
    play(state, katalina)
    assert sum(e.fate == DESTROYED for e in enemies) == 2
    assert katalina.has(K.WARD)
    E.damage(state, [katalina], 5)
    assert katalina.life == 2
    state = start()
    giant = put(state, 1, demo.GIANT)
    katalina, = hand_only(state, 0, neutral.KATALINA)
    E.counters(katalina)["skybound"] = 8                   # gauge 9: no Skybound Art
    set_pp(state, 0, 5)
    play(state, katalina)
    assert giant.life == 5
    apply(state, EndTurn())
    act(state, Attack(giant.uid, katalina.uid))             # 5 attack: takes 3
    assert katalina.life == 2 and giant.fate == DESTROYED


def test_lu_woh_light_personified():
    # 入场曲：6次随机打敌方随从1点；对手手牌中的随从+1/+0；奥义：获得纹章（吟唱2：
    # 拥有疾驰的敌方随从攻击主战者时，回合结束前-3/-0）。
    state = start()
    p, opp = state.players
    p.turns_taken = 10
    giant = big_enemy(state)
    opp.hand = [state.new_instance(d, 1) for d in (demo.FOOTMAN, demo.FIREBOLT)]
    lu_woh, = hand_only(state, 0, P.LU_WOH)
    set_pp(state, 0, 5)
    play(state, lu_woh)
    assert giant.life == 14
    assert [(c.atk, c.life) for c in opp.hand] == [(2, 2), (0, 0)]
    crest = E.leader_area_card(state, 0, P.LU_WOH_CREST)
    assert crest is not None and crest.countdown == 2
    apply(state, EndTurn())
    raider = put(state, 1, demo.RAIDER)                     # 2/1 Storm
    E.buff(state, raider, 3, 0)                            # 5/1
    lancer = put(state, 1, demo.LANCER)                     # 3/2 Rush, no Storm
    act(state, Attack(raider.uid, leader_uid(0)))
    act(state, Attack(lancer.uid, leader_uid(0)))
    assert p.leader_hp == 20 - 2 - 3
    apply(state, EndTurn())
    assert raider.atk == 5
    # Without the gauge: no crest.
    state = start()
    lu_woh, = hand_only(state, 0, P.LU_WOH)
    set_pp(state, 0, 5)
    play(state, lu_woh)
    assert state.players[0].leader_area == [] and (lu_woh.atk, lu_woh.life) == (6, 6)


# --- free-slot cards -------------------------------------------------------------------------

def test_world_of_games():
    # 吟唱5。自己使用其他卡牌时，若场上有与其原始费用相同的其他卡牌则倒计数-1。谢幕曲：抽2张。
    state = start()
    p = state.players[0]
    games = put(state, 0, neutral.WORLD_OF_GAMES)
    assert games.countdown == 5
    put(state, 1, demo.LANCER)                              # base cost 3
    zerk, aika, leona, barkeep = hand_only(state, 0, P.ZERK, neutral.AIKA, P.LEONA,
                                           P.BRUSQUE_BARKEEP)
    set_pp(state, 0, 10)
    play(state, zerk)                                       # cost 1: the amulet itself matches
    assert games.countdown == 4
    play(state, aika)                                       # cost 2: nothing else costs 2
    assert games.countdown == 4
    play(state, leona)                                      # cost 2: Aika matches
    assert games.countdown == 3
    games.countdown = 1
    E.banish(state, zerk)                                   # make room on the field
    E.banish(state, aika)
    play(state, barkeep)                                    # cost 4: no match
    assert games.fate == IN_PLAY
    give(state, 0, P.TWINDRONE_ENGINEER)
    set_pp(state, 0, 4)
    play(state, p.hand[-1])                                 # cost 4: the Barkeep matches
    assert games.fate == DESTROYED
    assert len(p.hand) == 3                                 # Analyzing Artifact + 2 Last Words draws


def test_leona_overbearing_guardian():
    # 守护。超进化时：选择另1个友方随从使其获得潜行。
    state = start()
    unlock_evolution(state, 0)
    leona, footman = put(state, 0, P.LEONA), put(state, 0, demo.FOOTMAN)
    assert leona.has(K.WARD) and (leona.atk, leona.life) == (2, 2)
    supers = [a for a in legal_actions(state) if isinstance(a, Evolve) and a.super_
              and a.uid == leona.uid]
    assert {a.targets for a in supers} == {(footman.uid,)}
    evolve(state, leona, super_=True, targets=(footman.uid,))
    assert footman.has(K.AMBUSH) and not leona.has(K.AMBUSH)
    state = start()
    unlock_evolution(state, 0)
    leona, footman = put(state, 0, P.LEONA), put(state, 0, demo.FOOTMAN)
    evolve(state, leona, targets=(footman.uid,))
    assert not footman.has(K.AMBUSH)


def test_shoddy_plaything():
    # 入场曲：抽3张。守护。激奏2：召唤1个低劣的玩具。
    state = start()
    p = state.players[0]
    toy, = hand_only(state, 0, P.SHODDY_PLAYTHING)
    set_pp(state, 0, 6)
    play(state, toy)
    assert len(p.hand) == 3 and toy.has(K.WARD) and (toy.atk, toy.life) == (1, 3)
    state = start()
    p = state.players[0]
    toy, = hand_only(state, 0, P.SHODDY_PLAYTHING)
    set_pp(state, 0, 5)
    play(state, toy)
    summoned, = p.field
    assert summoned.defn == P.SHODDY_PLAYTHING and summoned is not toy
    assert p.hand == [] and p.pp == 3 and p.shadows == 1   # played as a spell for 2


def test_brilliant_inventor():
    # 入场曲：召唤毁灭创造物α并使其获得毁灭和守护。（α：回合结束时回复主战者3点。）
    state = start()
    p = state.players[0]
    p.leader_hp = 10
    inventor, = hand_only(state, 0, P.BRILLIANT_INVENTOR)
    set_pp(state, 0, 6)
    play(state, inventor)
    alpha = p.field[-1]
    assert alpha.defn == P.OMINOUS_ARTIFACT_ALPHA and (alpha.atk, alpha.life) == (3, 5)
    assert alpha.has(K.BANE | K.WARD) and (inventor.atk, inventor.life) == (1, 1)
    apply(state, EndTurn())
    assert p.leader_hp == 13
    giant = put(state, 1, demo.GIANT)
    act(state, Attack(giant.uid, alpha.uid))
    assert giant.fate == DESTROYED                           # Bane


def test_ludicrous_ordnance():
    # 入场曲：召唤2个愚劣的兵器。回合结束时与进化时：对所有敌方随从分配3点伤害。激奏4：召唤1个。
    state = start(first=0)
    p = state.players[0]
    unlock_evolution(state, 0)
    enemies = [put(state, 1, demo.SHIELDBEARER) for _ in range(4)]   # 1/3 each
    gun, = hand_only(state, 0, P.LUDICROUS_ORDNANCE)
    set_pp(state, 0, 8)
    play(state, gun)
    assert count(p.field, P.LUDICROUS_ORDNANCE) == 3 and (gun.atk, gun.life) == (3, 4)
    assert all(e.life == 3 for e in enemies)
    evolve(state, gun)
    assert enemies[0].fate == DESTROYED and all(e.life == 3 for e in enemies[1:])
    apply(state, EndTurn())                                  # 3 x 3 split, oldest first
    assert all(e.fate == DESTROYED for e in enemies)
    state = start()
    p = state.players[0]
    gun, = hand_only(state, 0, P.LUDICROUS_ORDNANCE)
    set_pp(state, 0, 7)
    play(state, gun)
    assert count(p.field, P.LUDICROUS_ORDNANCE) == 1 and gun not in p.field and p.pp == 3


def test_beelzebub_supreme_king():
    # 入场曲：选择2个敌方随从，使其失去所有能力并造成9点伤害；敌方主战者获得“受到的伤害+1”（可叠加）。
    state = start()
    opp = state.players[1]
    katalina = put(state, 1, neutral.KATALINA)              # takes at most 3: lost first
    angel = put(state, 1, demo.ANGEL)                       # Barrier: lost first
    beelzebub, = hand_only(state, 0, P.BEELZEBUB)
    set_pp(state, 0, 9)
    play(state, beelzebub, (katalina.uid, angel.uid))
    assert katalina.fate == DESTROYED and angel.fate == DESTROYED
    assert (beelzebub.atk, beelzebub.life) == (9, 9)
    E.damage(state, [leader_uid(1)], 2)
    assert opp.leader_hp == 17
    second, = hand_only(state, 0, P.BEELZEBUB)
    set_pp(state, 0, 9)
    play(state, second)
    E.damage(state, [leader_uid(1)], 1)
    assert opp.leader_hp == 14


# --- printed stats and keywords ---------------------------------------------------------------

def test_nemesis_t_b_stats_and_keywords():
    # 费用 / 攻击 / 生命 / 关键词 / 特性（含衍生物、纹章、激奏形态）与官方数据一致。
    followers = {
        10774120: (4, 3, 5, K.NONE), 10972110: (4, 4, 4, K.WARD), 10874110: (5, 5, 5, K.NONE),
        10973110: (5, 3, 3, K.NONE), 10404110: (6, 7, 6, K.NONE), 10674110: (7, 6, 6, K.NONE),
        10974120: (7, 5, 5, K.NONE), 10774110: (8, 6, 6, K.STORM | K.WARD),
        10871130: (1, 1, 1, K.NONE), 10803110: (2, 2, 1, K.NONE), 10572110: (4, 2, 2, K.NONE),
        10771110: (4, 3, 3, K.NONE), 10971120: (4, 3, 3, K.NONE), 10401110: (5, 5, 5, K.WARD),
        10474110: (5, 6, 6, K.NONE), 10871120: (2, 2, 2, K.WARD), 10671110: (6, 1, 3, K.WARD),
        10671120: (6, 1, 1, K.NONE), 10673110: (8, 3, 4, K.NONE), 10474120: (9, 9, 9, K.NONE),
        # tokens
        90071140: (1, 3, 1, K.RUSH), 90071150: (3, 4, 5, K.WARD), 90071130: (1, 1, 1, K.NONE),
        90074150: (3, 3, 3, K.WARD), 90073110: (5, 3, 5, K.NONE), 90073120: (5, 4, 4, K.NONE),
    }
    for cid, (cost, atk, life, kw) in followers.items():
        d = card(cid)
        assert d.type == CardType.FOLLOWER, cid
        assert (d.cost, d.atk, d.life, d.keywords) == (cost, atk, life, kw), cid
    for cid in (90071140, 90071150, 90071130, 90074150, 90073110, 90073120):
        assert "Artifact" in card(cid).traits and card(cid).is_token, cid
    assert card(10473310).type == CardType.SPELL and card(10473310).cost == 6
    world = card(10503210)
    assert world.type == CardType.COUNTDOWN_AMULET and (world.cost, world.countdown) == (1, 5)
    assert card(10671110).accelerate.cost == 2 and card(10673110).accelerate.cost == 4
    assert card(10404112).type == CardType.CREST and card(10404112).countdown == 2
    assert card(10474112).type == CardType.CREST and card(10474112).countdown == 2
    assert card(10404110).craft == card(10401110).craft == card(10803110).craft == 0
