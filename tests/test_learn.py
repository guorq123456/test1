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
    # a folder without a ramp-t mirror of its own (Version 15's, frozen): the stand-in is on by default
    on = make_agent("mcts:5+plan+learned+phased=ref-5558960", 1).base.search.weights
    off = make_agent("mcts:5+plan+learned+phased=ref-5558960+noalias", 1).base.search.weights
    assert make_agent("v2+alias", 1).base.search.weights.aliases == on.aliases == ALIASES and off.aliases is None
    ramp = opening("ramp", "ramp", True, 3)
    assert on.score(ramp, 0) == off.score(ramp, 0)                            # the Game8 mirror as before
    assert on.score(mirror, 0) != off.score(mirror, 0)
    swap = ramp.clone()
    for p, q in zip(swap.players, mirror.players):                            # same position, other deck name
        p.deck_name = q.deck_name
    assert on.score(swap, 0) == off.score(ramp, 0)
    installed = make_agent("mcts:5+plan+learned+phased", 1).base.search.weights   # since C2: its own file first
    assert installed.score(mirror, 0) == make_agent("mcts:5+plan+learned+phased+noalias", 1).base.search.weights.score(
        mirror, 0) != on.score(mirror, 0)


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
    assert VERSIONS["ruler20261008"] == "mcts:200+plan+learned+phased=ruler-20261008+mull=by:elf-t=rules"
    monkeypatch.chdir(tmp_path)                    # found by name from any directory
    folder = folder_of("ruler-20261008")
    assert len(load(folder)) == 20
    readme = (folder / "README.md").read_text(encoding="utf-8")
    sums = dict(line.split()[::-1] for line in readme.splitlines() if line.endswith(".json") and len(line) > 64)
    assert len(sums) == 20 and all(hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
                                   for name, digest in sums.items())
    assert Path(folder).name == "ruler-20261008"
    ref = folder_of("ref-5558960")                 # Version 15's reference, the same way
    assert VERSIONS["ref5558960"] == "mcts:200+plan+learned+phased=ref-5558960+mull=default" and len(load(ref)) == 22
    sums = dict(line.split()[::-1] for line in (ref / "README.md").read_text(encoding="utf-8").splitlines()
                if line.endswith(".json") and len(line) > 64)
    assert len(sums) == 22 and all(hashlib.sha256((ref / n).read_bytes()).hexdigest() == d for n, d in sums.items())
    ref = folder_of("ref-352ae51")                 # after C2 went in (352ae51), the same way
    assert VERSIONS["ref352ae51"] == "mcts:200+plan+learned+phased=ref-352ae51+mull=default" and len(load(ref)) == 24
    sums = dict(line.split()[::-1] for line in (ref / "README.md").read_text(encoding="utf-8").splitlines()
                if line.endswith(".json") and len(line) > 64)
    assert len(sums) == 24 and all(hashlib.sha256((ref / n).read_bytes()).hexdigest() == d for n, d in sums.items())


def test_the_named_feature_sets_by_hand_and_models_without_them_unchanged(tmp_path):
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.learn.features import extra_features, extra_names, features, names
    from svsim.learn.model import LinearValue
    from svsim.learn.roles import card_roles
    state = new_game(decks.build(decks.RAMP_T), decks.build(decks.ELF_T), seed=5, first=1)
    me, op = state.players[0], state.players[1]
    me.max_pp, op.max_pp, me.turns_taken = 3, 3, 6           # I move second: the opponent goes to 4 next, I'm at 3
    assert extra_features(state, 0, ("tempo",)) == [1.0, 1.0, 0.0]               # t = 1, my turn 6 (5-7)
    me.turns_taken = 9
    assert extra_features(state, 0, ("tempo",)) == [1.0, 0.0, 1.0]               # turn 8 or later
    op.max_pp = 2
    assert extra_features(state, 0, ("tempo",))[0] == 0.0                         # moving first: no gap
    me.max_pp = op.max_pp = 10
    assert extra_features(state, 0, ("tempo",))[0] == 0.0                         # the cap of 10
    me.max_pp = 3                                            # next turn: 4 play points
    cheap, dear = me.hand[0], me.hand[1]
    cheap.cost, dear.cost = 2, 8
    me.hand[:] = [cheap, dear]
    want = [a + 0.5 * b for a, b in zip(card_roles(cheap.defn), card_roles(dear.defn))]   # 4 / 8 = 0.5
    got = extra_features(state, 0, ("hand",))
    assert len(got) == 6 and all(abs(g - w) < 1e-9 for g, w in zip(got, want))
    assert extra_names(("tempo", "hand")) == ["me_tempo", "me_tempo_x_mid", "me_tempo_x_late"] + \
        [f"me_handplay_{r}" for r in ("face", "removal", "heal", "draw", "ramp", "body")]
    n = len(names(False, 2))                                 # a model without them reads exactly the version's features
    plain = LinearValue([0.1] * n, [0.0] * n, [1.0] * n, False, version=2)
    assert plain.inputs(state, 0) == features(state, 0, False, 2) and plain.names() == names(False, 2)
    m = n + 3                                                # ... and one with them records and reads them by name
    tempo = LinearValue([0.0] * n + [1.0, 0.0, 0.0], [0.0] * m, [1.0] * m, False, version=2, extras=("tempo",))
    tempo.save(tmp_path / "t.json")
    loaded = LinearValue.load(tmp_path / "t.json")
    assert loaded.extras == ("tempo",) and abs(loaded.logit(state, 0) - extra_features(state, 0, ("tempo",))[0]) < 1e-9


def test_the_hand_feature_set_kept_by_hand_is_bit_for_bit_the_plain_sum(monkeypatch):
    """playable_hand_roles is kept by (play points, each card's id and cost): the same floats as summing the hand
    card by card from 0.0, warm or cold, and after the memo is cleared at its cap."""
    import struct
    from svsim.agents.random_agent import RandomAgent
    from svsim.core.engine import apply
    from svsim.core.state import MAX_PP
    from svsim.learn import features as FT
    from svsim.learn.roles import card_roles

    def plain(state, player):                     # the definition before the memo (2026-10-08, 94dd88e)
        p = state.players[player]
        pp = min(p.max_pp + 1, MAX_PP)
        out = [0.0] * 6
        for c in p.hand:
            f = 1.0 if c.cost <= 0 else min(1.0, pp / c.cost)
            for i, v in enumerate(card_roles(c.defn)):
                out[i] += v * f
        return out

    bits = lambda xs: [struct.pack("<d", x) for x in xs]          # noqa: E731
    monkeypatch.setattr(FT, "_HAND_MEMO_MAX", 50)                 # cleared many times over
    seen = 0
    for d0, d1, seed in ((decks.RAMP_T, decks.ELF_T, 3), (decks.PIRATE_T, decks.NEMESIS_T, 4)):
        state = new_game(decks.build(d0), decks.build(d1), seed=seed)
        agents = [RandomAgent(seed=seed), RandomAgent(seed=seed + 1)]
        while not state.over:
            for player in (0, 1):
                want = bits(plain(state, player))
                assert bits(FT.playable_hand_roles(state, player)) == want      # cold or warm
                assert bits(FT.playable_hand_roles(state, player)) == want      # warm
                seen += 1
            apply(state, agents[state.active].act(state, legal_actions(state)))
        if state.players[0].hand:
            state.players[0].hand[0].cost += 3                         # a cost change is a new key
        assert bits(FT.playable_hand_roles(state, 0)) == bits(plain(state, 0))
    assert seen > 100 and len(FT._HAND_MEMO) <= 50
    got = FT.playable_hand_roles(state, 0)
    got[0] += 1.0                                                   # callers get their own list
    assert bits(FT.playable_hand_roles(state, 0)) == bits(plain(state, 0))


def test_c2_is_installed_in_the_three_pairings_that_passed_and_nothing_else_moved():
    """2026-10-08: C2 (the hand feature set) passed its gates in the ramp-t mirror, the elf-t mirror and elf-t vs
    nemesis-t; those three pairs of files are the candidates' bytes, the other 18 installed files are as before, a
    pairing's own file comes before the ramp mirror's stand-in (ramp-ramp, kept for the Game8 deck and the
    snapshots), and the normal level stays on Version 15's frozen models."""
    import hashlib
    from pathlib import Path
    from svsim.core.engine import new_game as start
    from svsim.learn.model import ALIASES, matchup_keys
    from svsim.learn.phased import PhasedLearned, folder_of
    from svsim.tools.arena import VERSIONS
    from svsim.ui.session import LEVELS
    installed = Path(__file__).resolve().parents[1] / "svsim" / "learn" / "phased_models"
    pins = {
        "elf-t-elf-t-act.json": "d895d212e537dd0d2a822740cdc1b1f177f223909cf041171eb21bf68a6da906",
        "elf-t-elf-t-ended.json": "e8509021f50b024aac3bbbf88b889250967f6f713ba126aa32c8324abcb064dc",
        "elf-t-nemesis-t-act.json": "ca6a4f2faa82ea504f194db699411af38d44b40cf4e315b15e32846de977ee86",
        "elf-t-nemesis-t-ended.json": "e9a27705f12c7c521d47421e79d42243c99be039ac34b55edabcc8d95097c329",
        "elf-t-ramp-t-act.json": "df7e7bff1452d0eccf7e4f23c92c1ed596fa65cc77eee7e5c9c4dc16d38bc64e",
        "elf-t-ramp-t-ended.json": "8be505d77b9c630631686f89c574c4977053daaa460779af1a797103ab567bb0",
        "nemesis-t-elf-t-act.json": "3ff16f2022a5839eca3731dfabbf2e507bbd46cd5fd814d384474aab7ce221b8",
        "nemesis-t-elf-t-ended.json": "85a74b7ff825cacdcfcfd7379e49cd26eee29baf11f485cea829ba5436bc1b41",
        "nemesis-t-ramp-t-act.json": "daafbf1b6831148faf817e16780cbfc08b4230c4670fccbe892188d044ba5ca3",
        "nemesis-t-ramp-t-ended.json": "a16ecfe405bfec08849a3d0c9d7db216d9e0d929eb33d8f54d02046c9a29b6a7",
        "pirate-t-elf-t-act.json": "9500ec681feee9bc27a6105758b4d2e743e04d47322f54c9d9b2e42f97e635c1",
        "pirate-t-elf-t-ended.json": "9142f45909e6f93dfa350c16b9cb71c600ec3c26028e86dbda42dd6b3e156af2",
        "pirate-t-pirate-t-act.json": "865a1a022449cbae35d396cf56a4b53bd7bb1666244e91df7b398f058e11a972",
        "pirate-t-pirate-t-ended.json": "114e08c70989c30a689902999fc705289fd1e2a41ac2800c2991832d366ddb5e",
        "ramp-ramp-act.json": "f6638159fa561712c03f29f3e0c51a9519e3a543227112887731fcca831cd0c2",
        "ramp-ramp-ended.json": "97b0a8f2e747fe2509906c70595ecd702d9805ba2111e08eb52d3c8314bb100e",
        "ramp-t-elf-t-act.json": "9fea10f191afa715d7633a9bca77978b1325cabc84faafd03dd74220de50f865",
        "ramp-t-elf-t-ended.json": "b2f24b13bd13d0711a3c531c7505a92e2b9d384e1d7cbb5ed64fba7e3dcd1b27",
        "ramp-t-nemesis-t-act.json": "719ddf1233ad42406cf60dab06e0ea7465d8b12048c73beb2e62ae1d7c57ff69",
        "ramp-t-nemesis-t-ended.json": "0e76127c561695699e24edd9bd32d940d20094a12f768b135078465795cd01ed",
        "ramp-t-pirate-t-act.json": "836a671948cf8386573bb58088c25355aa87c72922cd282fcb62840752b52b71",
        "ramp-t-pirate-t-ended.json": "d575a8ad8d802bbfdf875eff165e3dd68462dbdf1dbc8a88d41d95f1e70dd23f",
        "ramp-t-ramp-t-act.json": "094ff4452d602df4130e66aec3de2828a3efe8408ea05c76165ce2bee3fe6f37",
        "ramp-t-ramp-t-ended.json": "244341725b14bfd4f64adfa1fe93c9f3c0d52f21d68de756f52e133fcc918dbe",
    }
    assert {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in installed.glob("*.json")} == pins
    for pairing, folder in (("ramp-t-ramp-t", "cand-c2-hand-ramp"), ("elf-t-elf-t", "cand-c2-hand-elf-t-elf-t"),
                            ("elf-t-nemesis-t", "cand-c2-hand-elf-t-nemesis-t")):
        for moment in ("act", "ended"):
            name = f"{pairing}-{moment}.json"
            assert (installed / name).read_bytes() == (installed / folder / name).read_bytes()
    models = PhasedLearned().models
    named = {"ramp-t": decks.RAMP_T, "elf-t": decks.ELF_T, "nemesis-t": decks.NEMESIS_T, "pirate-t": decks.PIRATE_T,
             "ramp": decks.RAMP_DRAGON}
    for mine, theirs, key, extras in (("ramp-t", "ramp-t", ("ramp-t", "ramp-t"), ("hand",)),
                                      ("elf-t", "elf-t", ("elf-t", "elf-t"), ("hand",)),
                                      ("elf-t", "nemesis-t", ("elf-t", "nemesis-t"), ("hand",)),
                                      ("nemesis-t", "elf-t", ("nemesis-t", "elf-t"), ()),
                                      ("elf-t", "ramp-t", ("elf-t", "ramp-t"), ()),
                                      ("ramp-t", "elf-t", ("ramp-t", "elf-t"), ()),
                                      ("ramp", "ramp", ("ramp", "ramp"), ())):
        state = start(decks.build(named[mine]), decks.build(named[theirs]), seed=1)
        hit = next(k for k in matchup_keys(state, 0, ALIASES) if k + ("ended",) in models)
        assert hit == key and models[hit + ("ended",)].extras == extras
    assert LEVELS["normal"] == VERSIONS["v2r5558960"] == "mcts:115+plan+learned+phased=ref-5558960+reuse+mull=default"
    assert LEVELS["strong"] == VERSIONS["v2s"] == "mcts:200+plan+learned+phased"
    before = {n: d for n, d in pins.items() if not n.startswith(("ramp-t-ramp-t", "elf-t-elf-t", "elf-t-nemesis-t"))}
    ref = folder_of("ref-5558960")                 # normal's models: the installed set before C2, file for file
    assert {f.name for f in ref.glob("*.json")} == set(before) | {f"{p}-{m}.json" for p in ("elf-t-elf-t",
                                                                   "elf-t-nemesis-t") for m in ("act", "ended")}
    assert all(hashlib.sha256((ref / n).read_bytes()).hexdigest() == d for n, d in before.items())


def test_alloc_legal_gives_each_decision_k_times_its_legal_moves_and_changes_nothing_when_off():
    """Line B1 (2026-10-08): +alloc=legal:K[:LO:HI] searches clip(round(K x legal moves), LO, HI) iterations per
    decision; with LO = HI it is the fixed count, move for move; off, the agent is as before."""
    import pytest
    from svsim.agents.mulligan import opening
    from svsim.core.engine import apply, legal_actions
    from svsim.tools.arena import _alloc_option, make_agent
    from svsim.tools.gate import _search, iteration_summary
    assert _alloc_option(["plan"]) is None and _alloc_option(["alloc=legal:16"]) == ("legal", 16.0, 50, 800)
    assert _alloc_option(["alloc=legal:2.5:10:90"]) == ("legal", 2.5, 10, 90)
    with pytest.raises(ValueError):
        _alloc_option(["alloc=bank:50"])
    state = opening("ramp-t", "elf-t", True, 3)
    n = len(legal_actions(state))
    for k, lo, hi in ((7, 1, 1000), (1, 30, 1000), (500, 1, 40)):
        agent = make_agent(f"mcts:200+plan+learned+phased+alloc=legal:{k}:{lo}:{hi}", 3)
        search = _search(agent)                    # under the lethal check
        search.choose(state)
        assert search.last_iterations == min(hi, max(lo, round(k * n)))
    plain, fixed = make_agent("mcts:25+plan+learned+phased", 5), make_agent("mcts:25+plan+learned+phased+alloc=legal:9:25:25", 5)
    a, b = state.clone(), state.clone()
    for _ in range(6):                             # the same moves: LO = HI is the fixed count
        if a.over:
            break
        x, y = plain.act(a, legal_actions(a)), fixed.act(b, legal_actions(b))
        assert repr(x) == repr(y)
        apply(a, x)
        apply(b, y)
    assert _search(plain).alloc is None and _search(make_agent("level-strong", 1)).alloc is None
    assert iteration_summary([50, 200, 120, 800]) == {"n": 4, "median": 200, "p90": 800, "total": 1170}
    assert iteration_summary([]) == {"n": 0, "median": 0, "p90": 0, "total": 0}


def test_alloc_bank_stops_once_settled_and_keeps_the_rest_for_the_turn():
    """Line B2 (2026-10-08): +alloc=bank[:CHUNK:STOP:CAP] searches the spec's count plus the turn's account in
    chunks, stops once the most visited move has STOP of the visits (or can't be caught), and keeps what's left
    for the turn's later decisions, at most CAP, emptied when a new turn starts."""
    import pytest
    from svsim.agents.mulligan import opening
    from svsim.tools.arena import _alloc_option, make_agent
    from svsim.tools.gate import _search
    assert _alloc_option(["alloc=bank"]) == ("bank", 50, 0.8, 400, 800)
    assert _alloc_option(["alloc=bank:25:0.9:300"]) == ("bank", 25, 0.9, 300, 800)
    with pytest.raises(ValueError):
        _alloc_option(["alloc=bank:25"])
    state = opening("ramp-t", "elf-t", True, 3)
    search = _search(make_agent("mcts:200+plan+learned+phased+alloc=bank:50:0:300", 3))   # STOP 0: one chunk
    search.choose(state)
    assert search.last_iterations == 50 and search._bank == 150
    search.choose(state)                           # the same turn: 200 + 150 to spend, one chunk again
    assert search.last_iterations == 50 and search._bank == 300            # 150 + 150, capped at 300
    later = state.clone()
    later.players[later.active].turns_taken += 1   # a new turn: the account starts empty
    search.choose(later)
    assert search.last_iterations == 50 and search._bank == 150
    never = _search(make_agent("mcts:120+plan+learned+phased+alloc=bank:40:1.1:400", 3))  # STOP above 1
    never.choose(state)
    assert never.last_iterations in (40, 80, 120) and never._bank == 120 - never.last_iterations
    big = _search(make_agent("mcts:700+plan+learned+phased+alloc=bank:50:1.1:400", 3))
    big._bank, big._bank_turn = 400, (state.active, state.players[state.active].turns_taken)
    assert big._bank_budget(state, state.active) == 800                    # 700 + 400, at most 800


def test_hand_inference_weights_only_what_they_could_and_should_have_played_and_is_off_by_default():
    """search.infer (2026-10-08): the opponent's left play points are still in `pp` on my turn; a kind they could
    pay for and that scores above passing for them gets ALPHA; determinize draws by weight; off, as before."""
    import random
    from svsim.agents.mulligan import opening
    from svsim.core.view import determinize
    from svsim.learn.model import Learned
    from svsim.learn.phased import PhasedLearned
    from svsim.search.infer import unplayed_gains, unplayed_weights
    from svsim.tools.arena import _infer_option, make_agent
    from svsim.tools.gate import _search
    assert _infer_option(["plan"]) is None and _infer_option(["infer=0.3"]) == (0.3, 0.0)
    assert _infer_option(["infer=0.3:1.5"]) == (0.3, 1.5)
    assert _search(make_agent("level-strong", 1)).infer is None
    from svsim.agents.random_agent import RandomAgent
    from svsim.core.engine import apply, legal_actions
    from svsim.core.enums import Phase
    state = opening("ramp-t", "elf-t", True, 3)
    bot = RandomAgent(seed=2)
    while state.phase != Phase.MAIN:               # past the redraws
        apply(state, bot.act(state, legal_actions(state)))
    me = state.active
    them = state.players[1 - me]
    weights = PhasedLearned(fallback=Learned())
    them.pp = 0                                    # nothing left: nothing they could have played but 0-cost cards
    assert all(next(c for c in them.hand + them.deck if c.defn.card_id == cid).cost == 0
               for cid in unplayed_gains(state, me, weights))
    them.pp = 10
    gains = unplayed_gains(state, me, weights)
    assert gains and all(isinstance(g, float) for g in gains.values())
    w = unplayed_weights(state, me, 0.25, -1e9, weights)        # every playable kind flagged
    assert w and set(w.values()) == {0.25} and unplayed_weights(state, me, 1.0, 0.0, weights) == {}
    a, b = determinize(state, me, random.Random(4)), determinize(state, me, random.Random(4), None)
    assert [c.uid for c in a.players[1 - me].hand] == [c.uid for c in b.players[1 - me].hand]   # off: as before
    pool = sorted(c.uid for c in them.hand + them.deck)
    drawn = determinize(state, me, random.Random(5), w)
    assert sorted(c.uid for c in drawn.players[1 - me].hand + drawn.players[1 - me].deck) == pool
    assert len(drawn.players[1 - me].hand) == len(them.hand)
    rng, hits, light = random.Random(6), 0, set(pool[::4])          # a quarter of the cards made light
    for _ in range(300):                           # the flagged cards come up less often than the others
        hand = {c.uid for c in determinize(state, me, rng, {u: 0.01 for u in light}).players[1 - me].hand}
        hits += len(hand & light)
    assert hits / 300 < len(them.hand) * len(light) / len(pool)


def test_gate_pairs_carry_each_side_s_wall_time_on_the_moves_it_searched():
    """Line B (2026-10-08): with allocations that change the time per iteration, compute is matched by wall time:
    each pair carries A's and B's ms per searched decision (n = 1 moves left out) next to their iterations."""
    from svsim.tools.gate import ms_summary, play_pair
    assert ms_summary([]) == {"n": 0, "mean": 0.0, "total": 0.0}
    assert ms_summary([0.002, 0.004]) == {"n": 2, "mean": 3.0, "total": 6.0}
    out = play_pair((0, 11, "mcts:6+plan+learned+phased", "mcts:6+plan+learned+phased+alloc=legal:2:6:12", None,
                     None, "ramp-t", "ramp-t", None, None))
    assert len(out["ms"]) == len(out["ms_b"]) == len(out["iterations"]) == 2
    for ms, its in zip(out["ms"] + out["ms_b"], out["iterations"] + out["iterations_b"]):
        assert ms["n"] == its["n"] > 0 and ms["total"] > 0 and abs(ms["mean"] * ms["n"] - ms["total"]) < 0.2


def test_alloc_self_scales_by_legal_moves_against_the_game_s_own_mean():
    """Line B1, second try (2026-10-08): +alloc=self:C[:W:LO:HI] gives clip(round(C x N x n / m), LO, HI), m this
    game's mean of legal moves so far with a prior of SELF_M0 weighing W decisions; a new game starts over."""
    import pytest
    from svsim.agents.mulligan import opening
    from svsim.agents.random_agent import RandomAgent
    from svsim.core.engine import apply, legal_actions
    from svsim.core.enums import Phase
    from svsim.search.mcts import SELF_M0
    from svsim.tools.arena import _alloc_option, make_agent
    from svsim.tools.gate import _search
    assert _alloc_option(["alloc=self:0.8"]) == ("self", 0.8, 10.0, 50, 800)
    assert _alloc_option(["alloc=self:1:4:20:300"]) == ("self", 1.0, 4.0, 20, 300)
    with pytest.raises(ValueError):
        _alloc_option(["alloc=self:1:4"])
    state = opening("ramp-t", "elf-t", True, 3)
    bot = RandomAgent(seed=2)
    while state.phase != Phase.MAIN:
        apply(state, bot.act(state, legal_actions(state)))
    n = len(legal_actions(state))
    search = _search(make_agent("mcts:40+plan+learned+phased+alloc=self:1:2:1:1000", 3))
    search.choose(state)                           # m = the prior
    assert search.last_iterations == round(40 * n / SELF_M0)
    search.choose(state)                           # m = (2 x M0 + n) / 3
    assert search.last_iterations == round(40 * n / ((2 * SELF_M0 + n) / 3))
    assert (search._seen_n, search._seen_k) == (2 * n, 2)
    later = state.clone()
    later.players[later.active].turns_taken += 2   # the same game, later: the mean carries on
    search.choose(later)
    assert search._seen_k == 3
    search.choose(state)                           # own turns went back: a new game, the prior again
    assert search._seen_k == 1 and search.last_iterations == round(40 * n / SELF_M0)
    plain, fixed = make_agent("mcts:25+plan+learned+phased", 5), make_agent("mcts:25+plan+learned+phased+alloc=self:1:10:25:25", 5)
    a, b = state.clone(), state.clone()
    for _ in range(5):                             # LO = HI: the fixed count, move for move
        if a.over:
            break
        x, y = plain.act(a, legal_actions(a)), fixed.act(b, legal_actions(b))
        assert repr(x) == repr(y)
        apply(a, x)
        apply(b, y)


def test_whole_game_cost_counts_only_the_searched_decisions():
    """search_cost --whole-games times per searched decision (the search ran), gate's ms definition, and reports
    searched next to all decisions."""
    from svsim.tools.search_cost import _whole_game, game_cost
    secs, searched, decisions, iterations, all_s = _whole_game(("mcts:5+plan+learned+phased", "ramp-t", "ramp-t", 3))
    assert 0 < searched < decisions and iterations == 5 * searched and 0 < secs <= all_s
    r = game_cost("mcts:5+plan+learned+phased", "ramp-t", "ramp-t", 1, 3)
    assert r["searched_per_game"] == searched and r["decisions_per_game"] == decisions
    assert abs(r["s_per_decision"] * searched - r["search_s_per_game"]) < 1e-9


def test_oracle_sees_the_opponent_s_real_hand_and_off_draws_as_before():
    """+oracle (2026-10-08, an experiment: what knowing the opponent's hand is worth): the drawn hand is their real
    hand and only their deck is shuffled; off, determinize uses the random numbers exactly as before."""
    import random
    from svsim.agents.mulligan import opening
    from svsim.agents.random_agent import RandomAgent
    from svsim.core.engine import apply, legal_actions
    from svsim.core.enums import Phase
    from svsim.core.view import determinize
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search

    def before(state, player, rng):               # the definition before weights and oracle (2026-10-08)
        s = state.clone()
        me, opp = s.players[player], s.players[1 - player]
        rng.shuffle(me.deck)
        pool = opp.hand + opp.deck
        rng.shuffle(pool)
        opp.hand, opp.deck = pool[:len(opp.hand)], pool[len(opp.hand):]
        s.rng.seed(rng.getrandbits(64))
        return s

    state = opening("ramp-t", "elf-t", True, 3)
    bot = RandomAgent(seed=2)
    while state.phase != Phase.MAIN:
        apply(state, bot.act(state, legal_actions(state)))
    me = state.active
    them = state.players[1 - me]
    for seed in range(5):
        a, b = determinize(state, me, random.Random(seed)), before(state, me, random.Random(seed))
        for x, y in zip(a.players, b.players):
            assert [c.uid for c in x.hand] == [c.uid for c in y.hand] and [c.uid for c in x.deck] == [c.uid for c in y.deck]
        assert a.rng.random() == b.rng.random()
        o = determinize(state, me, random.Random(seed), oracle=True)
        assert [c.uid for c in o.players[1 - me].hand] == [c.uid for c in them.hand]
        assert sorted(c.uid for c in o.players[1 - me].deck) == sorted(c.uid for c in them.deck)
    shuffled = [[c.uid for c in determinize(state, me, random.Random(s), oracle=True).players[1 - me].deck]
                for s in range(4)]
    assert len({tuple(d) for d in shuffled}) > 1                  # the deck's order is still a guess
    assert _search(make_agent("mcts:5+plan+learned+phased+oracle", 1)).oracle is True
    assert _search(make_agent("level-strong", 1)).oracle is False


def test_a_new_named_feature_set_needs_only_its_function_and_names(monkeypatch, tmp_path):
    """C3 "board" (dimensions to come from the analysis thread) will be one function in EXTRA_FNS and its names
    in EXTRAS: learn.phased's rows, the model's extras and its inputs pick it up by name, after "hand" as given."""
    import json
    from svsim.learn import features as FT
    from svsim.learn.model import LinearValue
    from svsim.learn.netdata import play
    from svsim.learn.phased import _rows
    monkeypatch.setitem(FT.EXTRAS, "probe", ["probe_followers", "probe_hp"])
    monkeypatch.setitem(FT.EXTRA_FNS, "probe", lambda state, player: [float(len(state.players[1 - player].followers)),
                                                                     float(state.players[player].leader_hp)])
    record = play((0, 13, "ramp", "ramp", "mcts:5+plan+learned+phased", 0.0, 0.0, False))
    n = len(FT.names(False, 2))
    rows = _rows((json.dumps(record), 2, 1.0, 1.0, 1.0, None, None, ("hand", "probe")))
    assert rows and all(len(r[2]) == n + 6 + 2 for r in rows)
    assert FT.extra_names(("hand", "probe"))[-2:] == ["probe_followers", "probe_hp"]
    m = n + 8
    model = LinearValue([0.0] * (n + 7) + [1.0], [0.0] * m, [1.0] * m, False, version=2, extras=("hand", "probe"))
    model.save(tmp_path / "x.json")
    loaded = LinearValue.load(tmp_path / "x.json")
    from svsim.agents.mulligan import opening
    state = opening("ramp-t", "elf-t", True, 3)
    assert loaded.extras == ("hand", "probe") and loaded.names()[-1] == "probe_hp"
    assert loaded.logit(state, 0) == float(state.players[0].leader_hp)
    import pytest
    with pytest.raises(ValueError):
        FT.extra_features(state, 0, ("nothing",))


def test_the_board_set_is_pressure_and_hp_by_turn_for_both_sides():
    """C3 "board" (analysis/c3-threat section 4): per side, min(enemy board threat / own HP, 1.5) and own HP in the
    scored player's turns 1-4 and 5-7; mine first, then the opponent's."""
    from svsim.agents.mulligan import opening
    from svsim.learn.features import EXTRAS, _board_threat, extra_features
    state = opening("ramp-t", "elf-t", True, 3)
    me, op = state.players[0], state.players[1]
    assert EXTRAS["board"] == ["me_pressure", "me_hp_early", "me_hp_mid", "op_pressure", "op_hp_early", "op_hp_mid"]
    me.leader_hp, op.leader_hp, me.turns_taken = 12, 17, 3
    got = extra_features(state, 0, ("board",))
    assert got == [min(_board_threat(state, 1) / 12, 1.5), 12.0, 0.0, min(_board_threat(state, 0) / 17, 1.5), 17.0, 0.0]
    me.turns_taken, op.turns_taken = 6, 9               # the scored player's turn for both sides
    assert extra_features(state, 0, ("board",))[1:3] == [0.0, 12.0] and extra_features(state, 0, ("board",))[4:6] == [0.0, 17.0]
    me.turns_taken = 9
    assert extra_features(state, 0, ("board",))[1:3] == [0.0, 0.0]
    me.leader_hp = 0                                    # no division by zero, capped at 1.5
    assert 0 <= extra_features(state, 0, ("board",))[0] <= 1.5
    assert len(extra_features(state, 1, ("hand", "board"))) == 12
