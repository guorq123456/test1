"""What the second player's bonus PP on turn 1 is worth: a measurement, not a rule for the bot.

    cd <svsim checkout> && PYTHONPATH=. python3 keep_bonus_run.py --a "mcts:100+plan+learned+phased+keepbonus" \
        --b "mcts:100+plan+learned+phased" --pairs 600 --seed 17000000 --out FILE

The same as fixed_run.py, with one extra agent option, "+keepbonus": the agent
may not press the bonus PP on its own first turn as the second player (the
search's veto, and the legal moves it is handed); everything else is the agent
as specified. Run against the same agent without it, the score is what keeping
the bonus for turn 2 is worth to that agent at equal compute.
"""
import sys

import svsim.tools.arena as arena
from svsim.core.actions import UseBonusPP

import fixed_run

_make_agent = arena.make_agent


def first_turn_bonus(state, action) -> bool:
    p = state.players[state.active]
    return isinstance(action, UseBonusPP) and state.active != state.first and p.turns_taken == 1


class KeepBonus:
    def __init__(self, base):
        self.base = base

    def act(self, state, legal):
        return self.base.act(state, [a for a in legal if not first_turn_bonus(state, a)] or legal)


def make_agent(spec: str, seed: int):
    if not spec.endswith("+keepbonus"):
        return _make_agent(spec, seed)
    agent = _make_agent(spec[:-len("+keepbonus")], seed)
    inner = agent
    while not (hasattr(inner, "search") and hasattr(inner.search, "veto")):   # the ISMCTS, below LethalAgent
        inner = inner.base
    old = inner.search.veto
    inner.search.veto = (lambda s, a: first_turn_bonus(s, a) or old(s, a)) if old else first_turn_bonus
    return KeepBonus(agent)


arena.make_agent = make_agent          # gate._agent imports it from arena at call time (workers fork after this)

if __name__ == "__main__":
    sys.argv[0] = fixed_run.__file__
    fixed_run.main()
