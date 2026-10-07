"""Learning evaluations (svsim.learn): features, the fit, and agents using the result."""
import json

import numpy as np

from svsim.cards import decks
from svsim.core.engine import legal_actions, new_game
from svsim.core.enums import Craft, Phase
from svsim.learn import data, fit as F
from svsim.learn.features import features, names
from svsim.learn.model import Learned, LinearValue, deck_craft, load_all
from svsim.search.evaluate import DEFAULT, evaluate
from svsim.tools import records


def test_features_are_per_side_and_named():
    state = new_game(decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON), seed=1)
    x = features(state, 0)
    assert len(x) == len(names(True)) == 53 and x[-1] == 1.0
    assert x[names(True).index("me_hand")] == len(state.players[0].hand)
    assert len(features(state, 0, potential=False)) == len(names(False))
    assert deck_craft(state, 0) == Craft.FOREST and deck_craft(state, 1) == Craft.DRAGON


def test_the_fit_finds_the_weights_behind_outcomes_and_choices():
    rng = np.random.default_rng(0)
    true = np.array([1.5, -2.0, 0.0, 0.7])
    X = np.c_[rng.normal(size=(4000, 3)), np.ones(4000)]
    y = (rng.random(4000) < 1 / (1 + np.exp(-(X @ true)))).astype(float)
    w, mean, std, report = F.fit(X, y, iters=2000)
    assert np.allclose(w[:3] / std[:3], true[:3], atol=0.15) and report["value_accuracy"] > 0.7
    # Choices: the chosen candidate always has the largest first feature; the fit learns
    # to rank it first even with no outcomes at all.
    prefs = []
    for _ in range(60):
        cands = np.c_[rng.normal(size=(5, 3)), np.ones(5)]
        prefs.append((int(np.argmax(cands[:, 0])), cands.tolist()))
    w, mean, std, report = F.fit(np.zeros((0, 4)), np.zeros(0), prefs, mean=np.zeros(4), std=np.ones(4), iters=1500)
    assert report["choice_top1"] == 1.0 and w[0] > 0
    # Ties for the top only get partial credit (all-zero weights: 1 in 5).
    assert abs(F.top1(np.zeros(4), F.choice_groups(prefs, np.zeros(4), np.ones(4))) - 0.2) < 1e-9


def test_a_recorded_game_gives_one_choice_per_decision():
    from svsim.ui.session import Session
    session = Session()
    view = session.start("rhino", "ramp", "fast", 3, "you")
    for _ in range(200):
        if view["over"] or session.state.turn > 6:
            break
        if view["active"] == 1:
            view = session.ai_step()
        elif view.get("mulligan"):
            view = session.mulligan([])
        else:
            view = session.act(view["actions"][0]["i"])
    record = json.loads(json.dumps(session.record_data()))
    rows = data.choices(record, potential=False)
    assert rows and all(0 <= k < len(c) for k, c in rows)
    assert all(len(x) == len(names(False)) for _, c in rows for x in c)
    # Moves the player marked as mistakes are not learned as good choices.
    mine = [k for k, (state, _) in enumerate(records.steps(record)) if state.active == 0 and state.phase == Phase.MAIN]
    assert len(data.choices({**record, "mistakes": mine[:1]}, potential=False)) == len(rows) - 1
    assert data.choices({**record, "mistakes": mine}, potential=False) == []


def test_whole_turns_are_compared_with_other_ways_of_playing_them():
    from svsim.ui.session import Session
    session = Session()
    view = session.start("rhino", "ramp", "fast", 5, "you")
    for _ in range(300):
        if view["over"] or session.state.turn > 8:
            break
        if view["active"] == 1:
            view = session.ai_step()
        elif view.get("mulligan"):
            view = session.mulligan([])
        else:
            plays = [a for a in view["actions"] if a["type"] == "PlayCard"]
            end = next(a for a in view["actions"] if a["type"] == "EndTurn")
            view = session.act((plays[0] if plays else end)["i"])
    record = json.loads(json.dumps(session.record_data()))
    turns = data.turn_choices(record, potential=False, alternatives=("end", "random", "random"))
    assert turns and all(k == 0 and 2 <= len(c) <= 4 for k, c in turns)     # the player's turn comes first
    assert all(len(x) == len(names(False)) for _, c in turns for x in c)
    # A turn with a move marked as a mistake is not held up as the better way to play it.
    first = next(k for k, (state, _) in enumerate(records.steps(record)) if state.active == 0 and state.phase == Phase.MAIN)
    marked = data.turn_choices({**record, "mistakes": [first]}, potential=False, alternatives=("end", "random", "random"))
    assert len(marked) == len(turns) - 1


def test_learned_models_are_used_per_deck_with_a_fallback(tmp_path):
    n = len(names(False))
    coef = [0.0] * n
    coef[names(False).index("me_hand")] = 1.0              # a toy model: cards in hand are good
    model = LinearValue(coef, [0.0] * n, [1.0] * n, potential=False)
    model.save(tmp_path / "forest.json")
    models = load_all(tmp_path)
    assert set(models) == {Craft.FOREST}
    learned = Learned(models)
    state = new_game(decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON), seed=2)
    assert evaluate(state, 0, learned) == 8.0 * len(state.players[0].hand)       # Forest: the model
    assert evaluate(state, 1, learned) == evaluate(state, 1, DEFAULT)            # Dragon: hand-set


def test_learned_agents_play_legal_moves(tmp_path, monkeypatch):
    n = len(names(False))
    LinearValue([0.1] * n, [0.0] * n, [1.0] * n, potential=False).save(tmp_path / "forest.json")
    monkeypatch.setenv("SVSIM_WEIGHTS", str(tmp_path))
    from svsim.tools.arena import make_agent
    agent = make_agent("mcts:20+learned", 1)
    state = new_game(decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON), seed=4, first=0)
    from svsim.core.engine import apply
    for _ in range(30):
        if state.over:
            break
        action = agent.act(state, legal_actions(state)) if state.active == 0 else legal_actions(state)[-1]
        assert action in legal_actions(state)
        apply(state, action)


def test_defense_and_lethal_features_keep_their_direction():
    from svsim.learn.features import signs
    s = dict(zip(names(False), signs(False)))
    assert s["me_hp"] == s["me_hp_sqrt"] == 1 and s["me_hp_low"] == -1
    assert s["op_hp"] == s["op_hp_sqrt"] == -1 and s["op_hp_low"] == 1
    assert s["me_board_lethal"] == 1 and s["op_board_lethal"] == -1 and s["me_deck_out"] == -1
    assert s["me_atk"] == 0 and s["bias"] == 0
    # Data that says the opposite (winning more with the own leader low) can't flip them.
    rng = np.random.default_rng(0)
    X = np.column_stack([rng.normal(size=400), np.ones(400)])
    y = (X[:, 0] < 0).astype(float)                         # more of feature 0, fewer wins
    w_free, *_ = F.fit(X, y, iters=500)
    w_kept, *_ = F.fit(X, y, iters=500, signs=[1, 0])
    assert w_free[0] < -0.5 and w_kept[0] == 0.0
    # The shipped models obey them.
    for model in load_all().values():
        coef = dict(zip(names(model.potential), model.coef))
        assert all(c * sign >= 0 for (n, c), sign in zip(coef.items(), signs(model.potential)))


def test_held_evolution_points_enter_by_context():
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.learn.features import CONTEXT, SIDE3, features, held_points, names
    state = new_game(decks.build(decks.RAMP_DRAGON), decks.build(decks.RAMP_DRAGON), seed=4, first=0)
    assert len(features(state, 0, False, 3)) == len(names(False, 3)) == len(names(False, 2)) + 2 * len(SIDE3)
    assert features(state, 0, False, 3)[:len(names(False, 2)) - 1] == features(state, 0, False, 2)[:-1]
    from svsim.learn.features import context
    held, p = held_points(state, 0, False), state.players[0]
    assert held[:len(CONTEXT)] == [p.ep * c for c in context(state, 0, False)]
    assert held[len(CONTEXT):] == [p.sep * c for c in context(state, 0, False, True)]
    from svsim.cards import library
    from svsim.learn.payoff import tier
    assert tier(next(c for c in decks.RAMP_DRAGON if c.card_id == 10544110)) == 2      # Justice: measured, not listed
    state.players[0].ep, state.players[0].sep = 0, 0
    assert all(v == 0 for v in held_points(state, 0, False)[:2 * len(CONTEXT)])


def test_evolution_point_usage_is_read_from_a_record():
    import random
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools import records as R
    from svsim.tools.evo_usage import usage
    ramp = decks.build(decks.RAMP_DRAGON)
    rng = random.Random(3)
    state = new_game(ramp, ramp, seed=3, first=0)
    record = R.new_record(ramp, ramp, 3, state.first, "random / random", first_arg=0)
    while not state.over:
        a = rng.choice(legal_actions(state))
        R.add(record, a)
        apply(state, a)
    record["winner"] = state.winner
    for side, u in enumerate(usage(record)):
        p = state.players[side]
        assert u["left"] == p.ep + p.sep and u["turns"] == p.turns_taken
        assert all(1 <= t <= p.turns_taken for t in u["spent"])
        assert u["spent"] == sorted(u["spent"])


def test_a_forked_game_keeps_its_evolution_points_in_the_branch():
    import json
    from svsim.learn.netdata import play, rows
    found = False
    for g in range(4):
        out = play((g, 13, "ramp", "ramp", "mcts:15+plan+learned+phased", 0.0, 0.0, True))
        if len(out) < 2:
            continue
        control, branch = (json.loads(json.dumps(r)) for r in out)
        i = control["branch"]["i"]
        assert control["branch"]["kind"] == "control" and branch["branch"]["kind"] == "hold"
        assert control["actions"][:i] == branch["actions"][:i] and branch["holds"][0]["i"] == i
        assert sum(1 for _ in rows(branch, start=i)) < sum(1 for _ in rows(branch))
        found = True
        break
    assert found
