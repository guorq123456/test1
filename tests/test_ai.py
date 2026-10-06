"""Evaluation, the greedy agent and ISMCTS. Synthetic cards use ids 7151+."""
import random

from svsim.agents.greedy_agent import GreedyAgent, mulligan
from svsim.agents.mcts_agent import MCTSAgent, full_game_agent
from svsim.cards import demo, dragon
from svsim.core import effects as E
from svsim.core.actions import Attack, EndTurn, Mulligan, PlayCard
from svsim.core.carddef import CardDef
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import CardType, Craft
from svsim.core.script import CardScript, register
from svsim.core.state import leader_uid
from svsim.core.view import determinize
from svsim.search.evaluate import WIN, after_end_of_turn, evaluate, threat
from svsim.search.lethal import state_key
from svsim.search.mcts import ISMCTS, action_key

from helpers import give, put, set_pp, start

BEACON = CardDef(7151, "Beacon", Craft.NEUTRAL, CardType.AMULET, 2)   # end of turn: 3 to the enemy leader


@register(BEACON.card_id)
class Beacon(CardScript):
    def on_turn_end(self, ctx):
        E.damage(ctx.state, [leader_uid(1 - ctx.controller)], 3, ctx.source)


def position(pp: int = 0):
    state = start(first=0)
    for p in state.players:
        p.hand.clear()
    set_pp(state, 0, pp)
    return state


def test_evaluation_prefers_more_board_and_fears_lethal():
    state = position()
    base = evaluate(state, 0)
    put(state, 0, demo.GIANT)
    assert evaluate(state, 0) > base and evaluate(state, 1) < evaluate(state, 0)
    calm = evaluate(state, 0)
    state.players[0].leader_hp = 4
    put(state, 1, demo.GIANT)                               # 5 attack next turn: lethal
    assert threat(state, 1) >= 4
    assert evaluate(state, 0) < calm - 10
    state.winner = 0
    assert evaluate(state, 0) == WIN and evaluate(state, 1) == -WIN


def test_end_of_turn_preview_stops_before_the_opponent_turn():
    state = position()
    put(state, 0, BEACON)
    hand = len(state.players[1].hand)
    after = after_end_of_turn(state)
    assert after.players[1].leader_hp == 17 and not after.over
    assert len(after.players[1].hand) == hand              # the opponent hasn't drawn
    assert state.players[1].leader_hp == 20                # the original is untouched


def test_greedy_takes_a_winning_attack_and_otherwise_ends_the_turn():
    state = position()
    state.players[1].leader_hp = 3
    lancer = put(state, 0, demo.LANCER)
    agent = GreedyAgent()
    assert agent.act(state, legal_actions(state)) == Attack(lancer.uid, leader_uid(1))
    state = position()
    assert agent.act(state, legal_actions(state)) == EndTurn()


def test_greedy_trades_into_a_threat():
    state = position()
    state.players[0].leader_hp = 5
    giant = put(state, 1, demo.GIANT)                       # would kill next turn
    assassin = put(state, 0, demo.ASSASSIN)                 # 1/1 Bane
    agent = GreedyAgent()
    assert agent.act(state, legal_actions(state)) == Attack(assassin.uid, giant.uid)


def test_mulligan_redraws_expensive_cards():
    state = new_game([demo.FOOTMAN] * 20 + [demo.GIANT] * 20, [demo.FOOTMAN] * 40, seed=1, first=0)
    action = mulligan(state)
    hand = state.players[0].hand
    assert isinstance(action, Mulligan)
    assert [hand[i].defn for i in action.indices] == [c.defn for c in hand if c.cost >= 5]


def test_a_ramp_deck_keeps_its_ramp_and_redraws_the_rest():
    # The player: Ramp Dragon's opening hand is about ramp, often a full redraw to find it.
    from svsim.cards import decks
    from svsim.search.race import ramps
    ramp, rhino = decks.build(decks.RAMP_DRAGON), decks.build(decks.RHINO_FOREST)
    for seed in range(6):
        state = new_game(ramp, rhino, seed=seed, first=0)
        hand = state.players[0].hand
        action = mulligan(state)
        assert sorted(action.indices) == [i for i, c in enumerate(hand) if not ramps(c.defn)]
        state = new_game(rhino, ramp, seed=seed, first=0)                # no ramp in the deck: by cost
        hand = state.players[0].hand
        assert [hand[i] for i in mulligan(state).indices] == [c for c in hand if c.cost >= 5]
    assert ramps(dragon.DRAGONSIGN) and ramps(dragon.LUMIORE_AND_ARGENTE) and ramps(dragon.ZOOEY)
    assert not ramps(dragon.SAGATSUMATSU) and not ramps(demo.FOOTMAN)


def test_action_keys_match_across_determinizations():
    state = position(pp=3)
    card = give(state, 0, demo.FIREBOLT)
    enemy = put(state, 1, demo.GIANT)
    action = PlayCard(card.uid, (enemy.uid,))
    rng = random.Random(0)
    keys = {action_key(determinize(state, 0, rng), action) for _ in range(5)}
    assert len(keys) == 1


def test_ismcts_finds_the_kill_and_leaves_the_state_alone():
    state = position()
    state.players[1].leader_hp = 2
    wall = put(state, 1, demo.SHIELDBEARER)                 # 1/3 Ward: the Giant clears it
    giant, raider = put(state, 0, demo.GIANT), put(state, 0, demo.RAIDER)
    before = state_key(state)
    first = ISMCTS(iterations=300, seed=1).choose(state)
    assert state_key(state) == before
    assert first == Attack(giant.uid, wall.uid)             # then the Raider wins
    assert raider.uid in (a.attacker for a in legal_actions(state) if isinstance(a, Attack))


def test_ismcts_prefers_removing_a_lethal_threat():
    state = position(pp=2)
    state.players[0].leader_hp = 5
    giant = put(state, 1, demo.GIANT)
    firebolt = give(state, 0, demo.FIREBOLT)                # 3 damage: not enough alone
    assassin = put(state, 0, demo.ASSASSIN)                 # Bane kills it
    choice = ISMCTS(iterations=300, seed=2).choose(state)
    assert choice == Attack(assassin.uid, giant.uid) or (
        isinstance(choice, PlayCard) and choice.uid == firebolt.uid)


def test_full_game_agent_plays_legal_moves_to_the_end():
    state = new_game([demo.FOOTMAN, demo.LANCER, demo.GIANT, demo.FIREBOLT] * 10,
                     [demo.FOOTMAN, demo.RAIDER, demo.SHIELDBEARER, demo.ARCHER] * 10, seed=4)
    agents = [full_game_agent(iterations=20, seed=0), MCTSAgent(iterations=20, seed=1)]
    from svsim.core.engine import apply
    while not state.over:
        actions = legal_actions(state)
        action = agents[state.active].act(state, actions)
        assert action in actions
        apply(state, action)
    assert state.winner in (0, 1, -1)


def test_play_tool_runs_a_scripted_game():
    from svsim.tools.play import load_deck, run
    replies = iter(["0 1", "h", "l", "x"] + ["e"] * 200)
    out = []
    winner = run(load_deck("pirate"), load_deck("ramp"), ai_spec="greedy", seed=3, you_first=True,
                 ask=lambda prompt: next(replies), say=out.append, record_to=None)
    assert winner == 1                                      # ending every turn loses
    text = "\n".join(out)
    assert "AI 会这样走" in text and "AI：" in text and "AI 赢了" in text


def test_reply_mode_plays_out_the_opponent_turn():
    state = position()
    put(state, 0, demo.GIANT)
    put(state, 1, demo.LANCER)
    search = ISMCTS(iterations=30, seed=3, reply=True)
    s = determinize(state, 0, random.Random(0))
    search._step(s, EndTurn())
    assert s.active == 1 and not s.over and s.max_turns == state.max_turns
    root = search.last_root
    choice = search.choose(state)
    assert choice in legal_actions(state) and search.last_root is not root
    assert search.last_root.visits == 30


def test_play_tool_with_the_rhinoceroach_deck():
    from svsim.tools.play import load_deck, run
    replies = iter(["", "l", "e", "l", "e", "l"] + ["e"] * 200)
    out = []
    run(load_deck("rhino"), load_deck("ramp"), ai_spec="greedy", seed=1, you_first=True,
        ask=lambda prompt: next(replies), say=out.append, record_to=None)
    text = "\n".join(out)
    assert "这回合杀不了" in text or "有必杀" in text
    assert "速算" in text                                   # some turn had a Rhinoceroach in hand


def test_games_are_recorded_and_can_be_reviewed(tmp_path):
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply
    from svsim.tools import records
    from svsim.tools.play import load_deck, run
    from svsim.tools.review import review
    replies = iter(["0", "# 先垫一张", "0", "e", "0", "e"] + ["e"] * 200)
    out = []
    winner = run(load_deck("rhino"), load_deck("ramp"), ai_spec="greedy", seed=7, you_first=True,
                 ask=lambda prompt: next(replies), say=out.append, record_to=str(tmp_path))
    saved = records.decode(str(next(tmp_path.iterdir())))
    assert records.decode(out[-1].split("\n")[-1]) == saved     # the replay code is the same record
    # Replaying follows the game exactly: every action is legal where it was taken,
    # and the game ends with the same result.
    for state, action in records.steps(saved):
        assert action in legal_actions(state)
    state = records.start(saved)
    for data in saved["actions"]:
        apply(state, from_dict(data))
    assert state.over and state.winner == winner == saved["winner"]
    text = []
    stats = review(saved, "greedy", say=text.append)
    assert stats["decisions"] > 0 and stats["same"] <= stats["decisions"]
    joined = "\n".join(text)
    assert "你：" in joined and "结果：AI 赢了" in joined and "AI 选得一样的" in joined
    # The note is kept before the first action of the turn (after both mulligans).
    assert saved["notes"] == [{"at": 2, "text": "先垫一张"}] and "【你的备注】先垫一张" in joined


def test_a_replayable_follower_counts_as_a_card_for_a_deck_that_returns_its_cards():
    # The player: against Rhinoceroach Forest, Sprouting Initiate (Combo 3: draw) is the 1/1 to
    # destroy first; Baby Carbuncle returns it to hand and it draws again when replayed.
    from svsim.cards import decks, forest
    from svsim.core import effects as E
    from svsim.learn.model import Learned
    from svsim.search.evaluate import evaluate, latent_cards
    ramp, rhino = decks.build(decks.RAMP_DRAGON), decks.build(decks.RHINO_FOREST)
    state = new_game(ramp, rhino, seed=3, first=0)
    apply(state, Mulligan(()))
    apply(state, Mulligan(()))
    sprout = put(state, 1, forest.SPROUTING_INITIATE)
    fairy = put(state, 1, forest.FAIRY)
    put(state, 1, forest.SATHANID)
    assert latent_cards(state.players[1]) == 1 and latent_cards(state.players[0]) == 0
    for weights in (None, Learned()):
        kept_sprout, kept_fairy = state.clone(), state.clone()
        E.destroy(kept_sprout, kept_sprout.on_field(fairy.uid))
        E.destroy(kept_fairy, kept_fairy.on_field(sprout.uid))
        args = () if weights is None else (weights,)
        assert evaluate(kept_fairy, 0, *args) > evaluate(kept_sprout, 0, *args)
    plain = new_game(ramp, [demo.FOOTMAN] * 40, seed=3, first=0)          # nobody to return it: just a 1/1
    put(plain, 1, forest.SPROUTING_INITIATE)
    assert latent_cards(plain.players[1]) == 0
