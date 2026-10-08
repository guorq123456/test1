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


def test_contexts_remember_the_unseen_cards_without_changing_a_value():
    import random
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.learn import features as F
    ramp = decks.build(decks.RAMP_DRAGON)
    state, rng, seen = new_game(ramp, ramp, seed=8, first=0), random.Random(8), []
    while not state.over and len(seen) < 120:
        seen.append(state.clone())
        apply(state, rng.choice(legal_actions(state)))
    def fresh(s, side, hidden):
        F._UNSEEN.clear()
        return F.contexts(s, side, hidden)
    for s in seen:
        for side in (0, 1):
            for hidden in (False, True):
                warm = F.contexts(s, side, hidden)
                assert F.contexts(s, side, hidden) == warm == fresh(s, side, hidden)
    p = seen[-1].players[1]
    deck = list(p.deck)
    assert F._fingerprint(deck) == F._fingerprint(deck[::-1])                # any order
    cheaper = deck[0].copy()
    cheaper.cost -= 1
    assert F._fingerprint([cheaper] + deck[1:]) != F._fingerprint(deck)     # a cost change is another key
    from svsim.cards.pool import POOL                                         # two different multisets whose
    from svsim.core.state import CardInstance                                 # tuple hashes summed alike
    def cards(spec):
        out = []
        for cid, cost, n in spec:
            for _ in range(n):
                c = CardInstance.create(len(out) + 1, POOL[cid], 0)
                c.cost = cost
                out.append(c)
        return out
    a = cards([(10944120, 7, 2), (10644110, 7, 1), (10042310, 3, 1)])
    b = cards([(10844120, 8, 1), (10544110, 10, 1), (10644120, 2, 1), (10542310, 4, 1)])
    assert sum(hash((c.defn.card_id, c.cost)) for c in a) == sum(hash((c.defn.card_id, c.cost)) for c in b)
    assert F._fingerprint(a) != F._fingerprint(b)


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


def test_a_deck_fork_waits_for_any_tier_two_card_and_only_fires_when_asked():
    from svsim.cards import decks
    from svsim.core.engine import EVOLVE_TURN, new_game
    from svsim.learn.netdata import _fork_point
    from svsim.learn.payoff import tier
    state = new_game(decks.build(decks.RAMP_DRAGON), decks.build(decks.RAMP_DRAGON), seed=4, first=0)
    p = state.players[state.active]
    p.turns_taken, p.ep, p.max_pp = EVOLVE_TURN[state.first == state.active], 2, 10
    p.deck.extend(c for c in p.hand if tier(c.defn) > 0)          # nothing to evolve for in hand
    p.hand[:] = [c for c in p.hand if tier(c.defn) == 0]
    assert sum(1 for c in p.deck if tier(c.defn) == 2) >= 3
    assert _fork_point(state, ("deck",)) == ("deck", "tier2")
    assert _fork_point(state, ("payoff",)) is None
    p.deck[:] = [c for c in p.deck if tier(c.defn) < 2]            # none left to draw
    assert _fork_point(state, ("deck",)) is None


def test_a_selective_hold_only_keeps_points_from_poor_targets():
    from types import SimpleNamespace
    from svsim.cards import decks
    from svsim.core import effects as E
    from svsim.core.actions import Evolve
    from svsim.core.engine import EVOLVE_TURN, new_game
    from svsim.learn.netdata import _keep
    from svsim.learn.payoff import tier
    state = new_game(decks.build(decks.RAMP_DRAGON), decks.build(decks.RAMP_DRAGON), seed=4, first=0)
    me = state.active
    p = state.players[me]
    p.turns_taken, p.ep, p.max_pp = EVOLVE_TURN[state.first == me], 2, 3
    pool = {c.defn.card_id: c.defn for c in p.deck + p.hand}
    good = next(d for d in pool.values() if d.is_follower and tier(d) == 2)
    poor = next(d for d in pool.values() if d.is_follower and tier(d) < 2)
    p.hand[:] = [c for c in p.hand if tier(c.defn) < 2]                   # no tier 2 playable
    g, q = E.summon(state, me, good), E.summon(state, me, poor)
    p.max_pp = 1
    for f in (g, q):
        f.entered_turn = -1
    search, record = SimpleNamespace(veto=None), {"actions": []}
    keep = {"player": me, "trigger": "payoff", "target": poor.card_id, "held": 0, "mode": "selective"}
    _keep(state, search, None, keep, record)
    assert keep["held"] == -1 and search.veto is None                     # a tier-2 follower on the field: done
    g.super_evolved = True                                                 # nothing left to spend on it
    keep["held"] = 0
    _keep(state, search, None, keep, record)
    assert keep["held"] == 1 and record["holds"][-1]["hold"] == "poor"
    assert search.veto(state, Evolve(q.uid)) and not search.veto(state, Evolve(g.uid, super_=True))
    keep = {"player": me, "trigger": "payoff", "target": poor.card_id, "held": 0}   # the old hold: no evolving
    _keep(state, search, None, keep, record)
    assert keep["held"] == -1                                              # (its target, the poor one, is on the field)


def test_tournament_decks_are_registered_everywhere_and_files_name_them():
    from svsim.agents.mulligan import _deck_key
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.core.enums import Craft
    from svsim.learn.model import split_keys
    from svsim.tools.learn import DECKS as LEARN_DECKS
    from svsim.ui.session import DECKS
    hashes = {"elf-t": decks.ELF_T_HASH, "nemesis-t": decks.NEMESIS_T_HASH, "ramp-t": decks.RAMP_T_HASH,
              "pirate-t": decks.PIRATE_T_HASH}
    crafts = {"elf-t": Craft.FOREST, "nemesis-t": Craft.PORTAL, "ramp-t": Craft.DRAGON, "pirate-t": Craft.SWORD}
    for key, h in hashes.items():
        cards = decks.from_hash(h)
        assert len(cards) == 40 and decks.to_hash(cards) == h and decks.validate(cards) == []
        assert decks.craft_of(cards) == crafts[key] and not decks.unimplemented(cards)
        assert sorted(c.card_id for c in decks.build(decks.NAMED[key])) == sorted(c.card_id for c in cards)
        assert decks.identify(cards) == key and key in DECKS and key in LEARN_DECKS
        state = new_game(cards, decks.build(decks.RAMP_DRAGON), seed=1, first=0)
        assert state.players[0].deck_name == key and state.players[1].deck_name == "ramp"
        assert _deck_key(state.players[0].hand + state.players[0].deck) == key
    assert split_keys("elf-t-ramp-t") == ["elf-t", "ramp-t"] and split_keys("ramp-ramp") == ["ramp", "ramp"]
    assert split_keys("ramp-t-ramp") == ["ramp-t", "ramp"] and split_keys("dragon-forest") == [Craft.DRAGON, Craft.FOREST]
    import pytest
    with pytest.raises(KeyError):
        split_keys("elf-x")


def test_tournament_matchup_models_load_by_file_name(tmp_path):
    from svsim.learn.features import names
    from svsim.learn.model import LinearValue, load_all
    from svsim.learn.phased import load
    n = len(names(False, 2))
    model = LinearValue([0.0] * n, [0.0] * n, [1.0] * n, False, version=2)
    model.save(tmp_path / "elf-t-ramp-t-ended.json")
    model.save(tmp_path / "ramp-t-ramp-t-act.json")
    model.save(tmp_path / "nemesis-t-elf-t.json")
    assert set(load(tmp_path)) == {("elf-t", "ramp-t", "ended"), ("ramp-t", "ramp-t", "act")}
    assert set(load_all(tmp_path)) == {("nemesis-t", "elf-t")}


def test_a_self_play_record_keeps_what_a_paired_play_out_needs():
    from svsim.cards import decks
    from svsim.core.enums import Phase
    from svsim.learn.netdata import play
    from svsim.tools import records as R
    record = play((3, 11, "elf-t", "ramp-t", "mcts:5+learned", 0.0))
    assert record["deck_keys"] == (["elf-t", "ramp-t"] if 3 % 2 == 0 else ["ramp-t", "elf-t"])
    assert [sorted(c.card_id for c in decks.from_hash(h)) for h in record["deck_hashes"]] == \
        [sorted(ids) for ids in record["decks"]]
    assert record["rng_seed"] == 11 * 7919 + 3 and record["agent_seeds"] == [11 * 1000 + 6, 11 * 1000 + 7]
    starts = {t["i"]: t for t in record["turn_starts"]}
    seen = 0
    for i, (state, _) in enumerate(R.steps(record)):
        if i in starts and state.phase == Phase.MAIN:
            p = state.players[starts[i]["player"]]
            assert starts[i]["hand"] == [c.uid for c in p.hand] and starts[i]["deck"] == [c.uid for c in p.deck]
            seen += 1
    assert seen == len(starts) > 4


def test_cards_are_named_for_the_player_by_the_glossary():
    from svsim.cards import decks
    from svsim.tools.glossary import GLOSSARY, common, names
    assert GLOSSARY.exists() and len(names()) > 200
    by_name = {c.name_zh: c for c in decks.build(decks.RAMP_T)}
    assert common(by_name["断头的斩姬·相枛津"]) == "口人魔（7费 5/4）"
    assert common(by_name["禁牙的变貌·诺玛格达拉"]) == "牢头（7费 5/6）"
    assert common(by_name["约束的《正义》·伊兰翠"]) == "正义（10费 8/8）"
    from dataclasses import replace
    unknown = replace(by_name["断头的斩姬·相枛津"], name_zh="某个新卡·试作品")      # not in the glossary
    assert common(unknown) == "试作品（7费 5/4）"


def test_a_card_that_does_something_on_entering_can_be_measured():
    import svsim.cards.library  # noqa: F401  (the scripts: Analyzing Artifact draws when it enters)
    from svsim.cards import portal
    from svsim.learn.payoff import evolve_parts
    from svsim.learn.roles import recurring
    from svsim.search import combo
    d = portal.ANALYZING_ARTIFACT          # made by Nemesis cards mid-game: the planner met it in a smoke game
    combo.evolve_profile.cache_clear()
    assert combo.evolve_profile(d, False) and combo.evolve_profile(d, True)
    evolve_parts(d, False)
    recurring(d)


def test_a_torn_search_forks_and_its_branch_keeps_points_only_while_torn():
    import json
    from svsim.learn.netdata import _qgap_mode, play
    assert _qgap_mode("qgap") == (0.05, 2, "first", 0) and _qgap_mode("qgap:0.1:3") == (0.1, 3, "first", 0)
    assert _qgap_mode("qgap:0.05:2:random:1")[2:] == ("random", 1) and _qgap_mode("all") is None
    assert _qgap_mode("qgap:0.05:2:weighted:1")[2] == "weighted"
    found = False
    for g in range(3):
        out = [json.loads(json.dumps(r)) for r in
               play((g, 77, "ramp", "ramp", "mcts:30+plan+learned+phased", 0.0, 0.0, True, None, "qgap:0.05:2"))]
        if len(out) < 2:
            continue
        control, branch = out
        i = control["branch"]["i"]
        assert control["actions"][:i] == branch["actions"][:i] and abs(control["branch"]["q_gap"]) < 0.05
        assert branch["branch"]["hold"] == "qgap:0.05:2"
        for h in branch.get("holds", []):
            assert h["hold"] == "torn" and h["q_gap"] < 0.05 and h["i"] >= i
        turns = {h["turn"] for h in branch.get("holds", [])}
        assert len(turns) <= 2 and branch["branch"]["end"] in ("released", "reached", "cap", "game over")
        found = True
    assert found


def test_a_reverse_fork_evolves_where_the_torn_search_chose_not_to():
    import json
    from svsim.core.actions import Evolve, from_dict
    from svsim.learn.netdata import _evolve_mode, play
    assert _evolve_mode("evolve") == (0.05, 0, "first", 0) and _evolve_mode("evolve:0.05:random:1") == (0.05, 0, "random", 1)
    assert _evolve_mode("qgap") is None
    found = False
    for g in range(4):
        out = [json.loads(json.dumps(r)) for r in
               play((g, 78, "ramp", "ramp", "mcts:30+plan+learned+phased", 0.0, 0.0, True, None, "evolve:0.05"))]
        if len(out) < 2:
            continue
        control, branch = out
        i = control["branch"]["i"]
        assert control["actions"][:i] == branch["actions"][:i] and abs(control["branch"]["q_gap"]) < 0.05
        assert not isinstance(from_dict(control["actions"][i]), Evolve)          # the side chose not to evolve
        assert branch["branch"]["end"] == "forced" and branch["actions"][i] == branch["branch"]["forced"]
        assert isinstance(from_dict(branch["actions"][i]), Evolve) and branch["branch"]["source"] in ("branch", "control")
        found = True
    assert found


def test_the_tournament_ramp_mirror_borrows_the_game8_mirror_models_unless_told_not_to():
    from svsim.agents.mulligan import opening
    from svsim.core.enums import Craft
    from svsim.learn.model import ALIASES, matchup_keys
    from svsim.tools.arena import make_agent
    mirror, other = opening("ramp-t", "ramp-t", True, 3), opening("ramp-t", "elf-t", True, 3)
    assert matchup_keys(mirror, 0) == [("ramp-t", "ramp-t"), (Craft.DRAGON, Craft.DRAGON)]
    assert matchup_keys(mirror, 0, ALIASES)[1] == ("ramp", "ramp")
    assert matchup_keys(other, 0, ALIASES) == matchup_keys(other, 0)          # a mirror only
    on = make_agent("mcts:5+plan+learned+phased", 1).base.search.weights     # on by default
    off = make_agent("mcts:5+plan+learned+phased+noalias", 1).base.search.weights
    assert make_agent("v2+alias", 1).base.search.weights.aliases == on.aliases == ALIASES and off.aliases is None
    ramp = opening("ramp", "ramp", True, 3)
    assert on.score(ramp, 0) == off.score(ramp, 0)                            # the Game8 mirror as before
    assert on.score(mirror, 0) != off.score(mirror, 0)
    swap = ramp.clone()
    for p, q in zip(swap.players, mirror.players):                            # same position, other deck name
        p.deck_name = q.deck_name
    assert on.score(swap, 0) == off.score(ramp, 0)


def test_a_keeping_branch_can_be_left_out_of_the_in_turn_model_only():
    import json
    from svsim.learn.netdata import ACT, ENDED, play
    from svsim.learn.phased import _rows
    for g in range(4):
        out = play((g, 13, "ramp", "ramp", "mcts:15+plan+learned+phased", 0.0, 0.0, True))
        if len(out) == 2:
            break
    control, branch = (json.dumps(r) for r in out)
    full, without = _rows((branch, 3, 1.0, 1.0, 1.0)), _rows((branch, 3, 1.0, 1.0, 0.0))
    assert not any(r[1] == ACT for r in without) and any(r[1] == ACT for r in full)
    assert sum(r[1] == ENDED for r in without) == sum(r[1] == ENDED for r in full) > 0
    assert len(_rows((control, 3, 1.0, 1.0, 0.0))) == len(_rows((control, 3, 1.0, 1.0, 1.0)))
    ended_only = _rows((control, 3, 1.0, 1.0, 1.0, (ENDED,)))          # --moments ended: no in-turn features
    assert ended_only and all(r[1] == ENDED for r in ended_only)
    assert len(ended_only) == sum(r[1] == ENDED for r in _rows((control, 3, 1.0, 1.0, 1.0)))


def test_a_matchup_of_two_named_decks_is_fitted_on_its_own_side_only():
    import json
    from svsim.learn.netdata import play
    from svsim.learn.phased import _rows
    line = json.dumps(play((0, 5, "elf-t", "ramp-t", "mcts:5+plan", 0.0)))
    every = _rows((line, 2))
    elf, ramp = _rows((line, 2, 1.0, 1.0, 1.0, None, ("elf-t", "ramp-t"))), _rows((line, 2, 1.0, 1.0, 1.0, None, ("ramp-t", "elf-t")))
    assert elf and ramp and len(elf) + len(ramp) == len(every)
    assert not _rows((line, 2, 1.0, 1.0, 1.0, None, ("elf-t", "elf-t")))


def test_a_deck_s_payoff_does_not_depend_on_its_order():
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.learn.features import deck_payoff
    state = new_game(decks.build(decks.RAMP_DRAGON), decks.build(decks.RAMP_DRAGON), seed=4, first=0)
    pool = state.players[0].hand + state.players[0].deck
    justice = [c for c in pool if c.defn.card_id == 10544110][:2]
    justice[0].cost -= 3                                     # one copy made cheaper: 7 and 10
    filler = [c for c in pool if c.cost <= 1][:10]
    deck = justice + filler
    values = {round(deck_payoff(order, 6), 12) for order in (deck, deck[::-1], [justice[1]] + filler + [justice[0]])}
    assert len(values) == 1


def test_a_payoff_card_still_in_the_deck_counts_by_its_draw_chances():
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.learn.features import deck_payoff, first_draw
    assert abs(first_draw(2, 30)[0] - 2 / 30) < 1e-12 and abs(sum(first_draw(30, 30, 3)) - 1.0) < 1e-12
    state = new_game(decks.build(decks.RAMP_DRAGON), decks.build(decks.RAMP_DRAGON), seed=4, first=0)
    p = state.players[0]
    justice = [c for c in p.deck if c.defn.card_id == 10544110]            # 10 play points, tier 2
    assert justice and deck_payoff(justice, 10) > deck_payoff(justice, 1) > 0    # out of reach counts less
    assert deck_payoff([c for c in p.deck if c.defn.cost <= 1], 10) == 0.0


def test_the_mimic_prior_mixes_two_heads_without_card_ids(tmp_path):
    import numpy as np
    from svsim.cards import decks
    from svsim.core.actions import EndTurn, Mulligan
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.learn.mimic import MOVE_WIDTH, MimicNet, MimicPrior, position, rows

    def opening(a, b):
        state = new_game(decks.build(decks.NAMED[a]), decks.build(decks.NAMED[b]), seed=3)
        apply(state, Mulligan(()))
        apply(state, Mulligan(()))
        p = state.players[state.active]
        p.pp = p.max_pp = 6                                                  # a choice of plays
        return state
    state = opening("ramp", "ramp")
    assert len(legal_actions(state)) > 2
    legal = legal_actions(state)
    X = rows(state, legal)
    assert X.shape == (len(legal), len(position(state)) + MOVE_WIDTH)
    end = X[[i for i, a in enumerate(legal) if isinstance(a, EndTurn)][0]]
    assert end[len(position(state)) + 4] == 1.0                           # the end-turn kind, no card one-hot
    rng = np.random.default_rng(0)
    for name in ("player", "selfplay"):
        params = {"W1": rng.normal(size=(X.shape[1], 4)), "b1": np.zeros(4), "w2": rng.normal(size=4), "b2": np.zeros(())}
        MimicNet(params, np.zeros(X.shape[1]), np.ones(X.shape[1]), info={"matchup": "ramp-ramp"}).save(tmp_path / f"{name}.npz")
    mixed = MimicPrior(0.3, tmp_path).priors(state, legal)
    alone = MimicPrior(0.0, tmp_path).priors(state, legal)
    selfplay = MimicNet.load(tmp_path / "selfplay.npz").priors(state, legal)
    assert abs(mixed.sum() - 1) < 1e-9 and np.allclose(alone, selfplay) and not np.allclose(mixed, alone)
    other = opening("elf-t", "ramp-t")
    assert MimicPrior(0.3, tmp_path).priors(other, legal_actions(other)) is None   # its matchup only


def test_the_mimic_fit_leaves_out_or_weights_flagged_decisions(tmp_path):
    import json
    import numpy as np
    from svsim.learn.mimic import decision_weights, player_decisions, stack
    from svsim.learn.netdata import play
    from svsim.learn.policy import PolicyNet
    record = play((0, 4, "ramp", "ramp", "mcts:5+plan", 0.0))
    every = player_decisions(record, 0)
    assert every and all(w == 1.0 for _, _, w in every)
    ks = [k for k in range(len(record["actions"]))]
    path = tmp_path / "mistakes.jsonl"
    path.write_text("\n".join(json.dumps({"game": "g", "at": k, "regret": 0.2, "flags": ["F1"] if k % 2 else [],
                                          "evolve": False}) for k in ks))
    table = decision_weights(str(path), drop_flags=["F1"], soft=0.1)
    kept = player_decisions(record, 0, lambda k: table.get(("g", k), 1.0))
    assert 0 < len(kept) < len(every) and all(abs(w - np.exp(-2.0)) < 1e-9 for _, _, w in kept)
    X, starts, target, weights = stack(kept)
    net = PolicyNet.train(X, starts, target, [], hidden=4, epochs=2, weights=weights, say=lambda *_: None)
    assert np.isfinite(net.info["cross_entropy"])


def test_the_mlp_fit_starts_at_the_linear_model_and_learns_what_it_cannot():
    import numpy as np
    from svsim.learn import mlp
    from svsim.learn.features import names, signs
    from svsim.learn.netdata import ACT, ENDED
    from svsim.learn.phased import STOCK
    N, sg = names(False, 2), signs(False, 2)
    a, b = [i for i, n in enumerate(N[:-1]) if not n.startswith(STOCK) and sg[i] == 0][:2]
    rng = np.random.default_rng(1)
    games = []
    for g in range(400):                           # win iff the two features agree in sign: no linear model can
        rows = []
        for _ in range(10):
            x = [0.0] * len(N)
            x[-1], x[a], x[b] = 1.0, rng.normal(), rng.normal()
            rows += [(g, ENDED, x, 1.0 if x[a] * x[b] > 0 else 0.0, None, 1.0), (g, ACT, x, 0.5, None, 1.0)]
        games.append(((0, g), rows))
    assert sum(mlp.held_out(gid) for gid, _ in games) == 40
    model, report = mlp.fit_moment(games, ENDED, hidden=8, epochs=60, lr=1e-2, batch=128, min_epochs=40,
                                   say=lambda _: None)
    assert report["held_out_positions"] == 400 and report["train_positions"] == 3600
    assert report["linear"]["accuracy"] < 0.6 < 0.85 < report["network"]["accuracy"]
    assert len(model.hidden["w2"]) == 8 and model.version == 2


def test_a_deck_description_is_what_its_cards_do_and_a_shared_model_reads_both_decks(tmp_path):
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.learn import deckdesc
    from svsim.learn.features import names
    from svsim.learn.model import LinearValue
    ramp, elf = deckdesc.describe(decks.RAMP_T), deckdesc.describe(decks.ELF_T)
    assert len(ramp) == len(elf) == len(deckdesc.names()) and ramp != elf
    at = deckdesc.names().index
    assert ramp[at("cost_mean")] > elf[at("cost_mean")] and ramp[at("cost_ge8")] > elf[at("cost_ge8")]
    # the same cards in another order, or under another deck's name, describe the same
    assert deckdesc.describe(dict(reversed(list(decks.RAMP_T.items())))) == ramp
    state = new_game(decks.build(decks.ELF_T), decks.build(decks.RAMP_T), seed=3, first=0)
    assert deckdesc.pair(state, 0) == elf + ramp and deckdesc.pair(state, 1) == ramp + elf
    n = len(names(False, 2)) + 2 * len(deckdesc.names())
    coef = [0.0] * n
    coef[len(names(False, 2)) + at("cost_mean")] = 1.0      # the logit is my deck's mean cost
    model = LinearValue(coef, [0.0] * n, [1.0] * n, False, version=2, deck_desc=True)
    model.save(tmp_path / "m.json")
    loaded = LinearValue.load(tmp_path / "m.json")
    assert loaded.deck_desc and len(loaded.names()) == n
    assert abs(loaded.logit(state, 0) - elf[at("cost_mean")]) < 1e-9
    assert abs(loaded.logit(state, 1) - ramp[at("cost_mean")]) < 1e-9


def test_the_ruler_s_models_are_frozen_and_found_from_any_directory(tmp_path, monkeypatch):
    import hashlib
    from pathlib import Path
    from svsim.learn.phased import folder_of, load
    from svsim.tools.arena import VERSIONS
    assert VERSIONS["ruler20261008"] == "mcts:200+plan+learned+phased=ruler_models/20261008"
    monkeypatch.chdir(tmp_path)                    # the folder resolves from the repository root
    folder = folder_of("ruler_models/20261008")
    assert len(load(folder)) == 20
    readme = (folder / "README.md").read_text(encoding="utf-8")
    sums = dict(line.split()[::-1] for line in readme.splitlines() if line.endswith(".json") and len(line) > 64)
    assert len(sums) == 20 and all(hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
                                   for name, digest in sums.items())
    assert Path(folder).name == "20261008"
