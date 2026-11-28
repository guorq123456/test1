"""The players' strategy interface (phase 2, item 2.1). Acceptance: the default strategy is reproduced through the
interface alone, decision for decision. Seeds 99001500-99001519 (host probe bank, SEEDS.md); the turn-start hook's
tests (interface-2, 11-28) 96510000-96519999 (host probe bank, third part, SEEDS.md)."""
import dataclasses
import functools
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
from ladder import base, interface  # noqa: E402
from ladder.interface import PlayerStrategy, action_key, sample_states, to_next_turn  # noqa: E402
from ladder.strategy import BotStrategy, play  # noqa: E402
from svsim.agents.greedy_agent import GreedyAgent  # noqa: E402
from svsim.agents.greedy_agent import mulligan as bot_mulligan  # noqa: E402
from svsim.cards.decks import from_hash  # noqa: E402
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard  # noqa: E402
from svsim.core.engine import apply, legal_actions, new_game  # noqa: E402
from svsim.core.enums import Phase  # noqa: E402
from svsim.core.state import leader_uid  # noqa: E402
from svsim.search.evaluate import DEFAULT, Weights, evaluate  # noqa: E402

ROOT = HERE.parents[2]
LINES = [l.strip().split("|") for l in (ROOT / "analysis/pilot/fields/bot-frozen7.txt").read_text(encoding="utf-8")
         .splitlines() if l.strip() and not l.startswith("#")]
DECKS = [from_hash(c) for _, c in LINES]
GAMES = [(0, 3, 99001500), (2, 6, 99001501), (5, 1, 99001502)]     # (deck, deck, seed): seven classes covered


class Explicit(PlayerStrategy):
    """Every hook written out by hand with the public functions, doing what the default does."""
    def guess(self, pos):
        return base.default_guess(pos.opp_craft)

    def mulligan(self, state):
        return bot_mulligan(state)

    def evaluate(self, state, me, me_next):
        return evaluate(state, me, DEFAULT, player_moves_next=me_next)

    def veto(self, state, action):
        return False

    def search(self, pos):
        return {"iterations": 100, "c": 0.5, "scale": 8.0}

    def turn_start(self, pos):
        return None


class EmptyHook(PlayerStrategy):
    """turn_start overridden and doing nothing: it is called, and the play is the default's (tools/check_interface)."""
    def turn_start(self, pos):
        return None


class Lookahead(PlayerStrategy):
    """turn_start draws a lot from self.random (samples, two-turn rollouts by greedy agents) and throws it all away:
    the play is still the default's, decision for decision, as the hook touches no stream of the decisions
    (tools/check_interface)."""
    def __init__(self, seed=0):
        super().__init__(seed)
        self.calls = 0

    def turn_start(self, pos):
        self.calls += 1
        guess = self.guess(pos)
        sample_states(pos, guess, self.random, 3)
        for _ in range(3):
            seed = self.random.getrandbits(31)
            to_next_turn(pos, guess, random.Random(seed), mine=GreedyAgent(seed=seed, samples=1))


def record(deck_a, deck_b, strategies, seed):
    moves = []
    winner, state, _ = play(DECKS[deck_a], DECKS[deck_b], strategies, seed=seed,
                            on_decision=lambda s, seat, t, pos, a: moves.append((seat, repr(a))))
    return winner, moves


@pytest.mark.parametrize("deck_a,deck_b,seed", GAMES)
def test_the_default_strategy_through_the_interface(deck_a, deck_b, seed):
    ref = record(deck_a, deck_b, [BotStrategy(seed=seed * 2), BotStrategy(seed=seed * 2 + 1)], seed)
    plain = record(deck_a, deck_b, [PlayerStrategy(seed=seed * 2), PlayerStrategy(seed=seed * 2 + 1)], seed)
    explicit = record(deck_a, deck_b, [Explicit(seed=seed * 2), BotStrategy(seed=seed * 2 + 1)], seed)
    assert len(ref[1]) > 20
    assert plain == ref                              # same winner, same moves, every decision
    assert explicit == ref


def test_hooks_change_the_play():
    class NoEvolve(PlayerStrategy):
        def veto(self, state, action):
            return isinstance(action, Evolve)

    class Aggro(PlayerStrategy):
        def weights(self, pos):
            return Weights(hp=1.5, hand=0.6)

    seed = 99001503
    _, ref = record(1, 4, [BotStrategy(seed=1), BotStrategy(seed=2)], seed)
    _, nev = record(1, 4, [NoEvolve(seed=1), BotStrategy(seed=2)], seed)
    assert any("Evolve" in a for s, a in ref if s == 0)
    assert not any("Evolve" in a for s, a in nev if s == 0)
    _, agg = record(1, 4, [Aggro(seed=1), BotStrategy(seed=2)], seed)
    assert agg != ref


def test_refusals():
    class Both(PlayerStrategy):
        def weights(self, pos):
            return DEFAULT

        def evaluate(self, state, me, me_next):
            return 0.0

    with pytest.raises(ValueError):
        Both(seed=1)

    class Bad(PlayerStrategy):
        LETHAL = "maybe"

    with pytest.raises(ValueError):
        Bad(seed=1)

    class Knob(PlayerStrategy):
        def search(self, pos):
            return {"reply": True}

    with pytest.raises(ValueError, match="not open"):
        record(0, 3, [Knob(seed=1), BotStrategy(seed=2)], 99001504)


def test_the_lethal_budget_settings(monkeypatch):
    """S18 (2.2, LD-60): LETHAL_NODES / LETHAL_SCREEN set the lethal search's budget; the defaults are the bot's own
    (the test above: the default strategy decision for decision); a bigger budget finds Salem's Pirate puzzle, whose
    damage the quick estimate can't see (analysis/speed/LETHAL.md)."""
    from ladder import codecheck
    from ladder.interface import LETHAL_NODES_MAX
    from svsim.core.engine import apply, legal_actions
    from svsim.tools.puzzles import puzzles
    a = PlayerStrategy(seed=1).agent.search
    assert (a.max_nodes, a.screen, a.near) == (2000, 200, (1000, 4))

    class Full(PlayerStrategy):
        LETHAL_NODES = 20000
        LETHAL_SCREEN = None

    b = Full(seed=1).agent.search
    assert (b.max_nodes, b.screen, b.near) == (20000, None, None)
    for nodes, screen in [(0, None), (LETHAL_NODES_MAX + 1, None), (2000.0, None), (True, None), (2000, (200, 1000)),
                          (2000, (3000, 1000, 4)), (2000, [200, 1000, 4])]:
        class Bad(PlayerStrategy):
            LETHAL_NODES = nodes
            LETHAL_SCREEN = screen
        with pytest.raises(ValueError):
            Bad(seed=1)

    import importlib.util                            # the bank's setups import the simulator's tests/helpers.py,
    spec = importlib.util.spec_from_file_location("helpers", ROOT / "tests" / "helpers.py")   # not this folder's
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    monkeypatch.setitem(sys.modules, "helpers", helpers)
    build = {n: f for n, f, _ in puzzles()}["pirate-flags-lethal"]

    def turn(strat):
        state = build(1)
        me, tracker = state.active, base.Tracker(state)
        while not state.over and state.active == me:
            a = strat.act(base.public_position(state, me, tracker), legal_actions(state))
            tracker.before(state)
            apply(state, a)
            tracker.after(state)
        return state.winner == me
    assert not turn(PlayerStrategy(seed=3)) and turn(Full(seed=3))
    src = "from ladder.interface import PlayerStrategy\n\nclass Deep(PlayerStrategy):\n" \
          "    LETHAL_NODES = 20000\n    LETHAL_SCREEN = None\n\n    def search(self, pos):\n" \
          "        return {'iterations': 60 if self.LETHAL_SCREEN is None else 100}\n"
    assert codecheck.check_code(src, "Deep") == []


# --- the turn-start hook (interface-2, 11-28) ------------------------------------------------------------------------

class Recorder(PlayerStrategy):
    """Writes down at which of its decisions turn_start runs (a cheap search: the play doesn't matter here)."""
    LETHAL = "off"

    def __init__(self, seed=0):
        super().__init__(seed)
        self.asked, self.hooks = 0, []                # hooks: (index of the decision, global turn)

    def search(self, pos):
        return {"iterations": 8}

    def turn_start(self, pos):
        self.hooks.append((self.asked - 1, pos.state.turn))

    def act(self, pos, actions):
        self.asked += 1
        return super().act(pos, actions)


def _log_opens(seen, seat) -> list:
    """The seat's decisions (their indices among its own) that open a turn, by the host's log rule: not a mulligan,
    and the decision before it (either seat's) the first one or an EndTurn or a mulligan."""
    mine = [i for i, x in enumerate(seen) if x[0] == seat]
    return [n for n, i in enumerate(mine) if seen[i][1] != "Mulligan" and
            (i == 0 or seen[i - 1][1] in ("EndTurn", "Mulligan"))]


@pytest.mark.parametrize("seed,first", [(96510000, 0), (96510001, 1)])
def test_turn_start_runs_once_at_the_first_decision_of_each_own_turn(seed, first):
    rec = [Recorder(seed=1), Recorder(seed=2)]
    seen = []                                         # (seat, move, global turn, pos, legal moves) per decision

    def on(s, seat, t, pos, a):
        seen.append((seat, type(a).__name__, s.turn, pos, legal_actions(s)))
    play(DECKS[1], DECKS[4], rec, seed=seed, first=first, on_decision=on)
    assert any(m == "UseBonusPP" for _, m, *_ in seen)  # the extra PP was used: it opens no turn (11-28 review)
    for seat in (0, 1):                               # both the first player and the second
        assert [n for n, _ in rec[seat].hooks] == _log_opens(seen, seat)
        turns = [t for _, t in rec[seat].hooks]
        assert len(turns) == len(set(turns)) >= 3
        assert all(t % 2 == (1 if seat == first else 0) for t in turns)
        assert seen[[i for i, x in enumerate(seen) if x[0] == seat][0]][1] == "Mulligan"   # never at the mulligan
    # an object built mid-turn (a resumed game, a puzzle) runs it at the first decision it is asked, once
    i = next(i for i, x in enumerate(seen) if i > 2 and x[1] != "Mulligan" and seen[i - 1][0] == x[0] and
             seen[i - 1][1] not in ("EndTurn", "Mulligan"))
    fresh = Recorder(seed=3)
    fresh.act(seen[i][3], seen[i][4])
    fresh.act(seen[i][3], seen[i][4])
    assert fresh.hooks == [(0, seen[i][2])]

    class Shadowed(PlayerStrategy):                   # an instance attribute of that name is no override
        LETHAL = "off"

        def __init__(self, seed=0):
            super().__init__(seed)
            self.calls = []
            self.turn_start = self.calls.append

        def search(self, pos):
            return {"iterations": 8}
    sh = Shadowed(seed=4)
    j = next(i for i, x in enumerate(seen) if x[1] != "Mulligan")
    sh.act(seen[j][3], seen[j][4])
    assert sh.calls == []


def test_a_hook_on_self_random_leaves_the_play_alone():
    # the hook draws samples and plays two-turn rollouts from self.random, then throws them away; an empty override
    # on the other seat: both play exactly the default (probe6: self.rng or self.agent there would not)
    seed = 96510002
    ref = record(2, 5, [BotStrategy(seed=seed * 2), BotStrategy(seed=seed * 2 + 1)], seed)
    a, b = Lookahead(seed=seed * 2), EmptyHook(seed=seed * 2 + 1)
    got = record(2, 5, [a, b], seed)
    assert len(ref[1]) > 20 and a.calls >= 3
    assert a.random.getstate() != PlayerStrategy(seed=seed * 2).random.getstate()
    assert got == ref


def _doc_planner(tmp_path):
    """The planning example of public/base-interface.md as a module on sys.path, and a subclass in another module
    that writes down each turn's plan (PLANS)."""
    doc = (HERE.parent / "public" / "base-interface.md").read_text(encoding="utf-8")
    blocks = [b.split("```")[0] for b in doc.split("```python")[1:]]
    src = next(b for b in blocks if "def turn_start" in b and "to_next_turn" in b)
    (tmp_path / "doc_planner_t.py").write_text(src, encoding="utf-8")
    (tmp_path / "doc_planner_w.py").write_text(
        "from doc_planner_t import Planner\n\nPLANS = []\n\n\nclass Watched(Planner):\n"
        "    def turn_start(self, pos):\n        super().turn_start(pos)\n"
        "        PLANS.append((pos.state.turn, self.first))\n", encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    return "py:doc_planner_w:Watched"


def test_a_real_planner_replays_and_passes_the_peek_check(tmp_path):
    # the documented planner (turn_start: candidates on shared samples, two turns by greedy agents; the plan kept on
    # self, carried out by prior) replays decision for decision, and swapping the hidden cards at its turn starts and
    # within a turn changes no decision
    from ladder.replay import replay_decisions
    from ladder.runner import play_job
    from ladder.submit import peek_check
    spec, seed = _doc_planner(tmp_path), 96510003
    try:
        job = {"id": "hook-plan", "seed": seed, "decks": [LINES[0][1], LINES[3][1]],
               "strategies": [spec, "bot:mcts:100+plan"], "strategy_seeds": [2 * seed + 1, 2 * seed + 2]}
        log = json.loads(json.dumps(play_job(job)))
        plans = list(__import__("doc_planner_w").PLANS)
        assert log["result"] in ("normal", "draw"), log.get("error")
        assert len(plans) >= 4 and any(first is not None for _, first in plans)      # it did plan, and act on it
        assert replay_decisions(log) == (True, "ok")
        seen = [(s, a["type"]) for (s, _, _), a in zip(log["steps"], log["actions"])]
        opens = _log_opens(seen, 0)
        assert len(opens) == len(plans)
        planned = [n for n, (_, first) in zip(opens, plans) if first is not None]
        mine = [i for i, (s, _) in enumerate(seen) if s == 0]
        mid = [n for n, i in enumerate(mine) if n not in opens and seen[i][1] != "Mulligan"]
        ks = sorted(set(planned[:2] + opens[1:3])) + mid[:1]
        assert len(ks) >= 4
        assert [peek_check(log, 0, k, random.Random(seed + k)) for k in ks] == ["same"] * len(ks)
    finally:                                          # the made-up modules off the path and out of sys.modules
        sys.path.remove(str(tmp_path))
        for m in ("doc_planner_t", "doc_planner_w"):
            sys.modules.pop(m, None)


def test_a_hook_that_hangs_loses_by_timeout(tmp_path, monkeypatch):
    # turn_start is on its decision's step clock (helpers.Slow's hang, in the hook at the second own turn)
    from ladder import runner
    (tmp_path / "hook_stuck_t.py").write_text(
        "import time\nfrom ladder.interface import PlayerStrategy\n\n\nclass StuckPlan(PlayerStrategy):\n"
        "    def __init__(self, seed=0):\n        super().__init__(seed)\n        self.turns = 0\n\n"
        "    def turn_start(self, pos):\n        self.turns += 1\n        if self.turns == 2:\n"
        "            time.sleep(600)\n", encoding="utf-8")
    monkeypatch.setenv("LADDER_EXTRA_PATH", str(tmp_path))
    job = {"id": "hook-stuck", "seed": 96510004, "first": 0, "decks": [LINES[1][1], LINES[4][1]],
           "strategies": ["py:hook_stuck_t:StuckPlan", "bot:greedy"], "strategy_seeds": [1, 2]}
    out = tmp_path / "g.jsonl"
    runner.run([job], str(out), workers=1, step_limit=3.0, quiet=True, key=None)
    row = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert row["result"] == "timeout" and row["loser"] == 0 and "one decision ran past" in row["error"]


# --- the helpers -----------------------------------------------------------------------------------------------------

def _opening(deck_a, deck_b, seed):
    """A new game past both mulligans (the bot's redraw, on the real state): (state, tracker)."""
    state = new_game(DECKS[deck_a], DECKS[deck_b], seed=seed)
    tracker = base.Tracker(state)
    while state.phase != Phase.MAIN:
        tracker.before(state)
        apply(state, bot_mulligan(state))
        tracker.after(state)
    return state, tracker


@functools.lru_cache(maxsize=1)
def _turn_starts():
    """The public positions at the first decision of each own turn of a greedy game (seed 96510005), with the legal
    moves of the real state (no pytest fixture: tools/base2_checks.py imports this module under a small shim)."""
    out, seen = [], set()

    def on(s, seat, t, pos, a):
        if s.phase == Phase.MAIN and (s.turn, seat) not in seen:
            seen.add((s.turn, seat))
            out.append((pos, legal_actions(s)))
    play(DECKS[3], DECKS[6], [BotStrategy("greedy", seed=1), BotStrategy("greedy", seed=2)], 96510005, on_decision=on)
    return out


def _key(s):
    return base.fingerprint(base.PublicPosition(s, 0, 0, 0, 0, 0, Counter(), [], 0, ()))


def _by_engine(pos, seed, mine=None):
    """to_next_turn written out: the same draws from Random(seed), then the engine's apply alone."""
    rng = random.Random(seed)
    s, _ = base.sample(pos, base.default_guess(pos.opp_craft), rng)
    opp, me = GreedyAgent(seed=rng.getrandbits(31), samples=1), pos.me
    while not s.over and s.active == me:
        apply(s, EndTurn() if mine is None else mine.act(s, legal_actions(s)))
    while not s.over and s.active != me:
        apply(s, opp.act(s, legal_actions(s)))
    return s


def _no_apply_after_the_end(monkeypatch) -> list:
    """The helpers' applies, each checked to come before the game's end."""
    real, calls = interface.apply, []

    def checked(state, action):
        assert not state.over
        calls.append(action)
        real(state, action)
    monkeypatch.setattr(interface, "apply", checked)
    return calls


def test_to_next_turn_is_the_engine_s_own_turn_change(monkeypatch):
    from svsim.search.impact import reply
    turn_starts, no_apply_after_the_end = _turn_starts(), _no_apply_after_the_end(monkeypatch)
    for n, (pos, _) in enumerate(turn_starts[:8]):
        before = base.fingerprint(pos)
        guess = base.default_guess(pos.opp_craft)
        for seed in (96510100 + 2 * n, 96510101 + 2 * n):
            s, info = to_next_turn(pos, guess, random.Random(seed))
            assert _key(s) == _key(_by_engine(pos, seed))
            rng = random.Random(seed)                 # svsim.search.impact.reply: the same calls, written apart
            t, _ = base.sample(pos, guess, rng)
            t, _ = reply(t, pos.me, GreedyAgent(seed=rng.getrandbits(31), samples=1))
            assert _key(s) == _key(t)
            if not s.over:                            # stopped before my next turn's first decision
                assert info["stopped"] == "next_turn" and info["winner"] is None
                assert (s.active, s.phase, s.turn) == (pos.me, Phase.MAIN, pos.state.turn + 2)
                assert s.players[pos.me].turns_taken == pos.state.players[pos.me].turns_taken + 1
            else:
                assert info["stopped"] == "over" and info["winner"] == s.winner
            assert info["line_ok"] and info["line"] == 0 and info["actions"] >= 2
            mine = GreedyAgent(seed=seed, samples=1)  # my turn played by an agent first
            s, info = to_next_turn(pos, guess, random.Random(seed), mine=GreedyAgent(seed=seed, samples=1))
            assert _key(s) == _key(_by_engine(pos, seed, mine))
        assert base.fingerprint(pos) == before        # pos is never changed
    assert no_apply_after_the_end


def test_to_next_turn_stops_where_it_says(monkeypatch):
    turn_starts, no_apply_after_the_end = _turn_starts(), _no_apply_after_the_end(monkeypatch)
    pos, legal = next((p, a) for p, a in turn_starts[4:] if any(isinstance(x, PlayCard) for x in a))
    guess, seed = base.default_guess(pos.opp_craft), 96510120
    same = to_next_turn(pos, guess, random.Random(seed))
    again = to_next_turn(pos, guess, random.Random(seed))
    assert _key(same[0]) == _key(again[0]) and same[1] == again[1]          # the same seed, the same result
    bad = Attack(9999, 9998)                          # a step that isn't legal stops the line; the turn goes on
    s, info = to_next_turn(pos, guess, random.Random(seed), line=[bad, EndTurn()])
    assert (info["line"], info["line_ok"]) == (0, False) and _key(s) == _key(same[0])
    card = next(x for x in legal if isinstance(x, PlayCard))
    s, info = to_next_turn(pos, guess, random.Random(seed), line=[card, bad])
    assert (info["line"], info["line_ok"], info["stopped"]) == (1, False, "next_turn")
    s, info = to_next_turn(pos, guess, random.Random(seed), line=[card], max_actions=1)
    assert (info["line"], info["line_ok"], info["actions"], info["stopped"]) == (1, True, 1, "max_actions")
    assert s.active == pos.me
    s, info = to_next_turn(pos, guess, random.Random(seed), max_actions=1)
    assert (info["actions"], info["stopped"]) == (1, "max_actions") and s.active != pos.me
    s, info = to_next_turn(pos, guess, random.Random(seed), max_actions=0)
    assert (info["actions"], info["stopped"]) == (0, "max_actions")

    class Never:                                      # nothing is asked or applied once the game is over
        def act(self, state, actions):
            raise AssertionError("asked after the end")
    pos, atk = next((p, x) for p, a in turn_starts for x in a
                    if isinstance(x, Attack) and x.target == leader_uid(1 - p.me))
    low = dataclasses.replace(pos, state=pos.state.clone())
    low.state.players[1 - pos.me].leader_hp = 1
    n = len(no_apply_after_the_end)
    s, info = to_next_turn(low, guess, random.Random(seed), line=[atk, EndTurn()], mine=Never(), opponent=Never())
    assert (info["stopped"], info["winner"], info["line"], info["actions"]) == ("over", pos.me, 1, 1)
    assert len(no_apply_after_the_end) == n + 1 and pos.state.players[1 - pos.me].leader_hp > 1
    mull = base.public_position(*_mulligan_position())
    with pytest.raises(ValueError):
        to_next_turn(mull, guess, random.Random(seed))
    with pytest.raises(ValueError):
        to_next_turn(pos, guess, random.Random(seed), max_actions=-1)
    with pytest.raises(ValueError):                   # not my turn (11-28 review)
        to_next_turn(dataclasses.replace(pos, me=1 - pos.me), guess, random.Random(seed))
    done = dataclasses.replace(pos, state=pos.state.clone())
    done.state.phase = Phase.OVER
    with pytest.raises(ValueError):                   # the game over
        to_next_turn(done, guess, random.Random(seed))

    class Wrong:                                      # an agent's move that isn't legal is played as EndTurn
        def act(self, state, actions):
            return bad
    pos, _ = turn_starts[4]
    s, info = to_next_turn(pos, guess, random.Random(seed), mine=Wrong())
    ref, ref_info = to_next_turn(pos, guess, random.Random(seed))
    assert _key(s) == _key(ref) and info == ref_info
    s, info = to_next_turn(pos, guess, random.Random(seed), opponent=Wrong())
    assert (info["stopped"], info["actions"]) == ("next_turn", 2) and s.turn == pos.state.turn + 2
    assert (s.active, s.phase) == (pos.me, Phase.MAIN)


def _mulligan_position():
    state = new_game(DECKS[0], DECKS[1], seed=96510006)
    return state, state.active, base.Tracker(state)


def test_sample_states_and_action_keys():
    turn_starts = _turn_starts()
    from svsim.search.mcts import action_key as svsim_key
    pos, legal = next((p, a) for p, a in turn_starts[2:] if any(isinstance(x, PlayCard) for x in a))
    before, guess = base.fingerprint(pos), base.default_guess(pos.opp_craft)
    xs = sample_states(pos, guess, random.Random(96510130), 4)
    ys = sample_states(pos, guess, random.Random(96510130), 4)
    assert len(xs) == 4 and [_key(x) for x in xs] == [_key(y) for y in ys]
    assert len({_key(x) for x in xs}) == 4 and base.fingerprint(pos) == before
    assert sample_states(pos, guess, random.Random(1), 0) == []
    with pytest.raises(ValueError):
        sample_states(pos, guess, random.Random(1), -1)
    card = next(x for x in legal if isinstance(x, PlayCard))
    keys = {action_key(x, card) for x in xs}          # the same move, the same key in every sample: by card id
    defn = next(c for c in pos.state.players[pos.me].hand if c.uid == card.uid).defn
    assert len(keys) == 1 and keys.pop()[1][:3] == ("H", True, defn.card_id)
    assert action_key(xs[0], card) == svsim_key(xs[0], card)

