"""The players' strategy interface (phase 2, item 2.1). Acceptance: the default strategy is reproduced through the
interface alone, decision for decision. Seeds 99001500-99001519 (host probe bank, SEEDS.md)."""
import random
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
from ladder import base  # noqa: E402
from ladder.interface import PlayerStrategy  # noqa: E402
from ladder.strategy import BotStrategy, play  # noqa: E402
from svsim.agents.greedy_agent import mulligan as bot_mulligan  # noqa: E402
from svsim.cards.decks import from_hash  # noqa: E402
from svsim.core.actions import Evolve  # noqa: E402
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
