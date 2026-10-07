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


def test_decks_are_known_by_name_through_the_game():
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.learn.model import deck_key, matchup_keys
    from svsim.core.enums import Craft
    ramp, face, rhino = (decks.build(decks.NAMED[k]) for k in ("ramp", "face", "rhino"))
    assert decks.identify(ramp) == "ramp" and decks.identify(face) == "face" and decks.identify(rhino) == "rhino"
    state = new_game(ramp, face, seed=3, first=0)
    assert [p.deck_name for p in state.players] == ["ramp", "face"]
    copy = state.clone()
    copy.players[0].deck.extend(copy.players[0].deck[:4])  # more copies than the list has (Dragonewt Promoter)
    assert decks.identify(copy.players[0].deck) is None
    assert deck_key(copy, 0) == "ramp"                       # the registered deck still counts
    assert matchup_keys(copy, 1) == [("face", "ramp"), (Craft.DRAGON, Craft.DRAGON)]
    other = new_game(ramp, ramp[:-1] + rhino[:1], seed=3, first=0)
    assert other.players[1].deck_name == "" and deck_key(other, 1) is None
    assert matchup_keys(other, 0) == [(Craft.DRAGON, Craft.DRAGON)]


def test_matchup_models_by_deck_come_before_the_class_pair(tmp_path):
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.core.enums import Craft
    from svsim.learn.features import names
    from svsim.learn.model import SCALE, Learned, LinearValue, load_all
    from svsim.learn.phased import PhasedLearned, load

    def constant(bias):
        n = len(names(False, 2))
        return LinearValue([0.0] * (n - 1) + [bias], [0.0] * n, [1.0] * n, False, version=2)

    constant(1.0).save(tmp_path / "dragon.json")
    constant(2.0).save(tmp_path / "ramp-ramp.json")
    constant(3.0).save(tmp_path / "dragon-dragon.json")       # an old file by classes still reads
    models = load_all(tmp_path)
    assert set(models) == {Craft.DRAGON, ("ramp", "ramp"), (Craft.DRAGON, Craft.DRAGON)}
    ramp, face, rhino = (decks.build(decks.NAMED[k]) for k in ("ramp", "face", "rhino"))
    learned = Learned(models=models)
    assert learned.score(new_game(ramp, ramp, seed=1, first=0), 0) == SCALE * 2.0
    assert learned.score(new_game(face, ramp, seed=1, first=0), 0) == SCALE * 3.0
    assert learned.score(new_game(ramp, rhino, seed=1, first=0), 0) == SCALE * 1.0
    del models[(Craft.DRAGON, Craft.DRAGON)]
    assert learned.score(new_game(face, ramp, seed=1, first=0), 0) == SCALE * 1.0
    folder = tmp_path / "phased"
    folder.mkdir()
    constant(4.0).save(folder / "ramp-ramp-ended.json")
    constant(5.0).save(folder / "dragon-dragon-act.json")
    phased = PhasedLearned(models=load(folder), fallback=learned)
    assert set(phased.models) == {("ramp", "ramp", "ended"), (Craft.DRAGON, Craft.DRAGON, "act")}
    mirror, other = new_game(ramp, ramp, seed=1, first=0), new_game(face, ramp, seed=1, first=0)
    assert phased.score(mirror, 0) == SCALE * 4.0
    assert phased.score(mirror, 0, player_moves_next=True) == SCALE * 5.0
    assert phased.score(other, 0) == learned.score(other, 0)  # no model for Face Dragon: the fallback
    assert phased.score(other, 0, player_moves_next=True) == SCALE * 5.0
    from svsim.tools.arena import make_agent                  # phased=FOLDER: one agent's own models
    own = make_agent(f"mcts:5+learned+phased={folder}", 1).base.search.weights
    assert own.models.keys() == phased.models.keys() and own.score(mirror, 0) == SCALE * 4.0
    assert make_agent("mcts:5+learned+phased", 1).base.search.weights.models.keys() == load().keys()
    import pytest
    with pytest.raises(ValueError):
        make_agent("mcts:5+learned+phased=no-such-folder", 1)
    assert make_agent("mcts:5+plan+screen=1000", 1).search.screen == 1000      # the lethal search's screen budget
    assert make_agent("mcts:5+plan", 1).search.screen == 200
    near = make_agent("mcts:5+plan+screen=200:1000:4", 1).search            # ... and for a near miss
    assert (near.screen, near.near) == (200, (1000, 4))
    assert make_agent("mcts:5+plan", 1).search.near == (1000, 4)                # the default since 2026-10-07
    assert make_agent("mcts:5+plan+screen=200", 1).search.near is None          # ... "+screen=N" the old way
    with pytest.raises(ValueError):
        make_agent("mcts:5+plan+screen=200:1000", 1)


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
    assert gate.cr_text(0.595, 0.035).startswith("CR 分差约 +91（+57～+126；游戏稳态公式 +76，+48～+104")   # the player's scale first
    pair = gate.play_pair((0, 5, "random", "random", None, None, "ramp", "ramp", None, None))
    assert pair["k"] == 0 and len(pair["points"]) == 2 and all(p in (0.0, 0.5, 1.0) for p in pair["points"])
    assert pair["same"] in (True, False)                                  # both games went move for move alike
    both = gate.play_pair((0, 5, "random", "random", None, None, "elf-t", "ramp-t", None, None, "random"))
    assert len(both["points"]) == len(both["b_points"]) == 2           # A and B each from both seats vs a third
    assert both["same"] == [True, True] and gate.pair_score(both) == 0.5   # the same agent: the same games
    split = gate.first_split([pair], "ramp", "ramp")                      # by who really went first
    assert len(split["先手"]) == len(split["后手"]) == 1
    assert sorted(split["先手"] + split["后手"]) == sorted(pair["points"])


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
    net.save(tmp_path / "ramp-ramp.npz")
    again = load_nets(tmp_path)[next(iter(load_nets(tmp_path)))]
    assert np.allclose(again.forward(X[:5]), net.forward(X[:5]))
    ramp, rhino = decks.build(decks.RAMP_DRAGON), decks.build(decks.RHINO_FOREST)
    weights = NetLearned(nets=load_nets(tmp_path), fallback=Learned(models={}))
    mirror = new_game(ramp, ramp, seed=1, first=0)
    assert abs(weights.score(mirror, 0) - SCALE * again.logit(mirror, 0)) < 1e-9
    other = new_game(rhino, ramp, seed=1, first=0)
    assert weights.score(other, 0) == Learned(models={}).score(other, 0)       # no net: the fallback


def test_cross_turn_candidates_restrict_the_rest_of_the_turn():
    from svsim.agents.crossturn_agent import NONE, forbids, principal_line, restrictions
    from svsim.core.actions import EndTurn, Evolve, PlayCard, UseBonusPP
    from svsim.search.mcts import Node
    line = [("B",), ("P", ("H", True, 101, 2), (), ()), ("E", ("F", True, 0, 102), False, (), ()),
            ("P", ("H", True, 101, 2), (), ()), ("T",)]
    assert restrictions(line) == [NONE, "keep:101", "save", "noevo"]
    assert restrictions([("T",)]) == [NONE] and forbids(NONE) is None
    assert forbids("save")(None, UseBonusPP()) and not forbids("save")(None, EndTurn())
    assert forbids("noevo")(None, Evolve(5)) and not forbids("noevo")(None, PlayCard(5))
    root, a, b, c = Node(), Node(), Node(), Node()
    root.children = {("B",): a, ("T",): b}
    a.visits, b.visits = 5, 3
    a.children = {("T",): c}
    c.visits = 4
    assert principal_line(root) == [("B",), ("T",)]
    from svsim.agents.crossturn_agent import restricted_line
    assert restricted_line(root, "save") == [("T",)] and restricted_line(root, NONE) == [("B",), ("T",)]
    assert restrictions(line, max_keeps=1) == [NONE, "keep:101", "save", "noevo"]
    assert restrictions(line, kinds=("noevo",)) == [NONE, "noevo"]
    from svsim.agents.crossturn_agent import ALL_KINDS, key_forbidden
    sup = [("E", ("F", True, 0, 77), True, (), ()), ("T",)]
    assert restrictions(sup, ALL_KINDS, supers=[77, 88]) == [NONE, "noevo", "nosuper", "superonly:88", "super:88"]
    assert key_forbidden("superonly:88", sup[0]) and key_forbidden("nosuper", sup[0])
    assert not key_forbidden("superonly:77", sup[0]) and not key_forbidden("keep:77", sup[0])
    assert "super:88" in restrictions(sup, ALL_KINDS, supers=[77, 88]) and not key_forbidden("super:88", sup[0])
    assert restrictions([("T",)], ALL_KINDS, supers=[77]) == [NONE, "superany:77"]
    from svsim.agents.crossturn_agent import leaf_lines, one_turn_q
    tree, a, b, c, d = Node(), Node(), Node(), Node(), Node()
    play = ("P", ("H", True, 101, 2), (), ())
    tree.children = {play: a, ("T",): b}
    a.children, a.visits, b.visits, c.visits = {("E", ("F", True, 0, 77), True, (), ()): c}, 3, 2, 3
    c.value, b.value = 0.6, 0.55
    found = leaf_lines(tree, lambda n: n.value)
    assert sorted(v for _, v in found) == [0.55, 0.6]
    assert abs(one_turn_q(found, "keep:101") - (0.55 - 0.6)) < 1e-12        # keeping it: best without minus with
    assert abs(one_turn_q(found, "superany:77") - (0.6 - 0.55)) < 1e-12
    assert one_turn_q(found, "superany:88") is None and one_turn_q(found, "save") is None


def test_a_forced_start_plays_a_card_and_super_evolves_it():
    import random
    from svsim.agents.crossturn_agent import CrossTurnAgent
    from svsim.cards import decks
    from svsim.core.actions import Evolve, PlayCard, UseBonusPP
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.search.lethal import hidden_info
    from svsim.tools.arena import make_agent
    ramp = decks.build(decks.RAMP_DRAGON)
    planner = CrossTurnAgent(make_agent("mcts-raw:10+learned+phased", 1))
    found = 0
    for seed in range(30):
        state, rng = new_game(ramp, ramp, seed=seed, first=0), random.Random(seed)
        while not state.over and state.turn < 16:
            if state.phase.name == "MAIN" and state.active == 0 and state.players[0].sep > 0:
                for cid in CrossTurnAgent._supers(state):
                    start = planner.prefix(state, f"superany:{cid}")
                    if start is None:
                        continue
                    found += 1
                    assert isinstance(start[-1], Evolve) and start[-1].super_
                    assert all(isinstance(a, (PlayCard, UseBonusPP, Evolve)) for a in start)
                    s, before = state.clone(), hidden_info(state)
                    for a in start:
                        assert a in legal_actions(s)
                        apply(s, a)
                    assert hidden_info(s) == before and s.in_play(start[-1].uid).defn.card_id == cid
            apply(state, rng.choice(legal_actions(state)))
        if found >= 3:
            break
    assert found >= 3


def test_keep_value_and_the_planners_records():
    import random
    from svsim.agents.crossturn_agent import CrossTurnAgent, keep_value
    from svsim.cards import decks
    from svsim.core.actions import PlayCard
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.learn.netdata import play
    from svsim.tools.arena import make_agent
    ramp = decks.build(decks.RAMP_DRAGON)
    state, rng = new_game(ramp, ramp, seed=8, first=0), random.Random(0)
    while state.phase.name != "MAIN" or state.players[state.active].turns_taken < 3:
        apply(state, rng.choice(legal_actions(state)))
    agent = CrossTurnAgent(make_agent("mcts-raw:30+learned+phased", 1), samples=2, next_turn=True)
    values = [keep_value(state, state.active, c.uid, agent) for c in state.players[state.active].hand]
    assert all(v is None or -1.0 <= v <= 1.0 for v in values)
    assert keep_value(state, 1 - state.active, state.players[state.active].hand[0].uid, agent) is None
    searched = CrossTurnAgent(make_agent("mcts-raw:30+learned+phased", 1), samples=2, next_turn=True, research=10,
                              next_search=5, opp_search=5)
    values = [keep_value(state, state.active, c.uid, searched) for c in state.players[state.active].hand]
    assert all(v is None or -1.0 <= v <= 1.0 for v in values)
    record = play((0, 3, "ramp", "ramp", "mcts:20+plan+learned+phased+crossn2", 0.0))
    assert record["names"] == ["ramp", "ramp"] and record["plans"]
    plan = record["plans"][0]
    assert plan["samples"]["line"] and len(plan["samples"]["line"]) == 2 and plan["deck"] == "ramp"
    assert all(0 <= p["i"] < len(record["actions"]) for p in record["plans"])


def test_the_search_reuses_its_subtree_after_a_move_that_reveals_nothing():
    import random
    from svsim.agents.mcts_agent import MCTSAgent
    from svsim.cards import decks
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.search.lethal import hidden_info
    ramp = decks.build(decks.RAMP_DRAGON)
    rng, reused, checked = random.Random(2), 0, 0
    for seed in range(6):
        state = new_game(ramp, ramp, seed=seed, first=0)
        agent = MCTSAgent(30, seed=seed, reuse=True, min_new=5)
        direct = False                              # the position right after the agent's own move
        while not state.over and state.turn < 12:
            legal = legal_actions(state)
            if state.active == 0 and state.phase.name == "MAIN" and len(legal) > 1:
                pending = agent.search._next
                before = hidden_info(state)
                action = agent.act(state, legal)
                if pending is not None and direct:
                    checked += 1
                    if agent.search.last_root is pending[1]:
                        reused += 1
                        assert agent.search.last_root.visits >= 5       # new iterations on the kept subtree
                expected = agent.search._next
                apply(state, action)
                direct = True
                if expected is not None:            # only moves that reveal nothing are expected to be reused
                    assert hidden_info(state) == before and not isinstance(action, EndTurn)
            else:
                apply(state, rng.choice(legal))
                direct = False
    assert reused > 0 and reused == checked
