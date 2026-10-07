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
        pirate = decks.build(decks.PIRATE_SWORD)                         # no ramp in the deck: by cost
        state = new_game(pirate, ramp, seed=seed, first=0)
        hand = state.players[0].hand
        assert [hand[i] for i in mulligan(state).indices] == [c for c in hand if c.cost >= 5]
    assert ramps(dragon.DRAGONSIGN) and ramps(dragon.LUMIORE_AND_ARGENTE) and ramps(dragon.ZOOEY)
    assert not ramps(dragon.SAGATSUMATSU) and not ramps(demo.FOOTMAN)


def test_rhinoceroach_forest_redraws_by_the_players_rules():
    # The player: keep Glade; keep one Bayle, not two; Baby Carbuncle, Lambent Cairn, Eradicating
    # Arrow and Virid Lieutenant look cheap but are mid-game cards.
    from svsim.agents.mulligan import PLAYER_RULES, by_rules
    from svsim.cards import forest, unlimited
    rules = PLAYER_RULES["rhino"]
    hand = [type("C", (), {"defn": d, "cost": d.cost})() for d in (
        unlimited.BAYLE, unlimited.GLADE, unlimited.BAYLE, unlimited.BABY_CARBUNCLE, forest.SPROUTING_INITIATE)]
    assert by_rules(hand, rules) == (2, 3)
    hand = [type("C", (), {"defn": d, "cost": d.cost})() for d in (
        unlimited.LAMBENT_CAIRN, unlimited.ERADICATING_ARROW, forest.VIRID_LIEUTENANT, unlimited.KILLER_RHINOCEROACH)]
    assert by_rules(hand, rules) == (0, 1, 2)


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


def test_a_crest_that_hurts_its_holder_counts_against_it():
    # The player's Ramp mirror games: super-evolving Burnite gives the opponent a crest that
    # burns 2 a turn; the evaluation used to count it as a crest in the opponent's favour.
    from svsim.cards import dragon
    from svsim.core import effects as E
    from svsim.learn.features import features
    from svsim.search import evaluate as EV
    from helpers import start
    assert EV.crest_burn(dragon.BURNITE_CREST) == 2
    state = start()
    before = EV.evaluate(state, 0)
    feats = features(state, 0, potential=False)
    E.add_to_leader_area(state, 1, dragon.BURNITE_CREST)
    assert EV.burn(state.players[1]) == 2
    assert EV.effective_hp(state.players[1]) == state.players[1].leader_hp - 2 * EV.BURN_TURNS
    assert EV.evaluate(state, 0) > before                     # good for the player who gave it
    after = features(state, 0, potential=False)
    assert after != feats and after[-1] == feats[-1]
    EV.CREST_EFFECTS = False
    try:
        assert EV.evaluate(state, 0) < before                 # the old way: a crest for the opponent
    finally:
        EV.CREST_EFFECTS = True


def test_a_matchup_model_is_used_where_there_is_one(tmp_path):
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.core.enums import Craft
    from svsim.learn.features import names
    from svsim.learn.model import SCALE, Learned, LinearValue, load_all

    def constant(bias):
        n = len(names(False, 2))
        return LinearValue([0.0] * (n - 1) + [bias], [0.0] * n, [1.0] * n, False, version=2)

    constant(1.0).save(tmp_path / "dragon.json")
    constant(2.0).save(tmp_path / "dragon-dragon.json")
    models = load_all(tmp_path)
    assert set(models) == {Craft.DRAGON, (Craft.DRAGON, Craft.DRAGON)}
    learned = Learned(models=models)
    ramp, rhino = decks.build(decks.RAMP_DRAGON), decks.build(decks.RHINO_FOREST)
    mirror = new_game(ramp, ramp, seed=1, first=0)
    other = new_game(ramp, rhino, seed=1, first=0)
    assert learned.score(mirror, 0) == SCALE * 2.0
    assert learned.score(other, 0) == SCALE * 1.0


def test_a_hidden_layer_adds_to_the_linear_score(tmp_path):
    import math
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.learn.features import features, names
    from svsim.learn.model import LinearValue
    n = len(names(False, 2))
    hidden = {"W1": [[0.0, 0.0] for _ in range(n - 1)] + [[0.5, -1.0]], "b1": [0.25, 0.0], "w2": [2.0, 1.0]}
    model = LinearValue([0.0] * (n - 1) + [0.5], [0.0] * n, [1.0] * n, False, version=2, hidden=hidden)
    model.save(tmp_path / "m.json")
    loaded = LinearValue.load(tmp_path / "m.json")
    ramp = decks.build(decks.RAMP_DRAGON)
    state = new_game(ramp, ramp, seed=1, first=0)
    assert features(state, 0, False, 2)[-1] == 1.0                  # the bias feature drives the hidden units
    want = 0.5 + 2.0 * math.tanh(0.75) + 1.0 * math.tanh(-1.0)
    assert abs(loaded.logit(state, 0) - want) < 1e-9


def test_the_gate_pairs_seats_and_tests_sequentially():
    from svsim.tools import gate
    lo, hi = gate.bounds(0.05, 0.05)
    assert round(hi, 3) == 2.944 and round(lo, 3) == -2.944
    assert gate.llr([0.5] * 10 + [0.75, 0.25] * 10, 0.5, 0.55) < 0          # an even score leans to H0
    assert gate.llr([0.75] * 30 + [0.5] * 10, 0.5, 0.55) > hi               # a clear edge is accepted
    mean, margin = gate.summary([0.5, 1.0, 0.5, 0.0])
    assert mean == 0.5 and margin > 0
    assert round(gate.cr_gap(0.43)) == -56 and gate.cr_gap(0.82) is None    # class rating, inside the window only
    assert "超出匹配窗口" in gate.cr_text(0.82, 0.1) and "-56" in gate.cr_text(0.43, 0.07)
    pair = gate.play_pair((0, 5, "random", "random", None, None, "ramp", "ramp", None, None))
    assert pair["k"] == 0 and len(pair["points"]) == 2 and all(p in (0.0, 0.5, 1.0) for p in pair["points"])


def test_the_encoding_knows_the_moment_and_counts_cards():
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.core.enums import Phase
    from svsim.learn import encode as E
    from svsim.search.evaluate import after_end_of_turn
    ramp = decks.build(decks.RAMP_DRAGON)
    state = new_game(ramp, ramp, seed=3, first=0)
    while state.phase != Phase.MAIN:
        apply(state, legal_actions(state)[0])
    me = state.active
    vocab = {c.defn.card_id: i for i, c in enumerate({c.defn.card_id: c for c in state.players[me].hand}.values())}
    x = E.encode(state, me, vocab)
    names = E.dense_names()
    assert len(x) == E.width(vocab) == len(names) + len(E.ZONES) * len(vocab)
    assert x[names.index("phase_act")] == 1.0 and x[names.index("phase_ended")] == 0.0
    hand = x[len(names):len(names) + len(vocab)]                      # the first zone: my hand
    assert sum(hand) == len(state.players[me].hand)
    ended = after_end_of_turn(state)
    y = E.encode(ended, me, vocab)
    assert E.phase(ended, me) == E.ENDED and y[names.index("phase_ended")] == 1.0


def test_a_value_net_trains_saves_and_scores_its_matchup(tmp_path):
    import numpy as np
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.learn import encode as E
    from svsim.learn.model import SCALE, Learned
    from svsim.learn.net import NetLearned, ValueNet, load_nets
    rng = np.random.default_rng(0)
    vocab = [101, 102]
    d = E.width({c: i for i, c in enumerate(vocab)})
    X = rng.normal(size=(2000, d))
    y = (X[:, 0] > 0).astype(float)
    net = ValueNet.train(X[:1600], y[:1600], vocab, X[1600:], y[1600:], hidden=(8, 4), epochs=30, lr=1e-2, batch=64,
                         say=lambda s: None)
    z = net.forward(X[1600:])
    assert np.mean((z > 0) == (y[1600:] > 0.5)) > 0.8
    net.save(tmp_path / "dragon-dragon.npz")
    again = load_nets(tmp_path)[next(iter(load_nets(tmp_path)))]
    assert np.allclose(again.forward(X[:5]), net.forward(X[:5]))
    ramp, rhino = decks.build(decks.RAMP_DRAGON), decks.build(decks.RHINO_FOREST)
    weights = NetLearned(nets=load_nets(tmp_path), fallback=Learned(models={}))
    mirror = new_game(ramp, ramp, seed=1, first=0)
    assert abs(weights.score(mirror, 0) - SCALE * again.logit(mirror, 0)) < 1e-9
    other = new_game(rhino, ramp, seed=1, first=0)
    assert weights.score(other, 0) == Learned(models={}).score(other, 0)       # no net: the fallback
