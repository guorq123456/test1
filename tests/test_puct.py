"""search.mcts PUCT (puct=, agent option +puct=PATH[:C[:T]]; the architecture thread 2026-10-17, "B"). Off, the search
is the frozen one (tests/test_golden_search.py replays bit for bit); on, every node's prior is computed once, over
its open moves (one per action key), and moves are picked by PUCT without being tried first."""
import gzip
import json
from pathlib import Path

import numpy as np
import pytest

from svsim.core.engine import legal_actions
from svsim.core.enums import Phase
from svsim.search.mcts import ISMCTS, _locator, action_key
from svsim.tools import records as R

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / "analysis/scaling/models/prior-elft-fz.npz"


def _positions(n=6, wide=4):
    """Main-phase positions of the gen-3 holdout's first game with `wide` distinct moves or more (copies)."""
    with gzip.open(ROOT / "analysis/scaling/data/elf-t3/rec/rec-74100038.jsonl.gz", "rt") as fh:
        rec = json.loads(next(fh))
    out = []
    for state, action in R.steps(rec):
        if state.phase == Phase.MAIN and state.winner is None:
            where = _locator(state, state.active)
            if len({action_key(state, a, where) for a in legal_actions(state)}) >= wide:
                out.append(state.clone())
                if len(out) == n:
                    break
    return out


class Counting:
    """A prior that records each call; `peak`: almost all the mass on the last open move."""

    def __init__(self, peak=False):
        self.calls, self.peak = [], peak

    def priors(self, state, actions):
        self.calls.append(len(actions))
        if self.peak:
            p = np.full(len(actions), 1e-3)
            p[-1] = 1.0
            return p / p.sum()
        return np.full(len(actions), 1.0 / len(actions))


def _nodes(node):
    yield node
    for child in node.children.values():
        yield from _nodes(child)


def test_each_node_computes_its_prior_once_over_its_open_moves():
    for state in _positions(3):
        prior = Counting()
        search = ISMCTS(iterations=60, seed=1, puct=prior)
        search.choose(state)
        picked = [n for n in _nodes(search.last_root) if n.prior is not None]
        assert len(prior.calls) == len(picked) > 1           # once per node a move was picked at
        for n in picked:
            assert abs(sum(n.prior.values()) - 1) < 1e-12
        root = search.last_root
        where = _locator(state, state.active)
        keys = {action_key(state, a, where) for a in legal_actions(state)}
        assert set(root.prior) <= keys                       # one entry per action key at most


def test_unvisited_moves_are_not_forced_and_a_peaked_prior_concentrates_the_visits():
    for state in _positions(3, wide=5):
        flat = ISMCTS(iterations=40, seed=2)
        flat.choose(state)
        assert len(flat.last_root.children) == len(flat._root_options)     # the old search tries every move
        peaked = ISMCTS(iterations=40, seed=2, puct=Counting(peak=True), c_puct=4.0)
        peaked.choose(state)
        root = peaked.last_root
        last = list(peaked._root_options)[-1]
        assert root.children[last].visits >= 0.5 * root.visits          # the prior's move takes most visits
        assert len(root.children) < len(peaked._root_options)             # some moves never tried


def test_puct_is_deterministic_and_the_spec_option_builds_it():
    from svsim.learn.netdata import _search
    from svsim.learn.setpolicy import SetPolicy
    from svsim.tools.arena import make_agent
    spec = f"mcts:30+puct={PRIOR}:2:0.5"
    state = _positions(1)[0]
    runs = []
    for _ in range(2):
        search = _search(make_agent(spec, 5))
        assert isinstance(search.puct, SetPolicy) and (search.c_puct, search.puct_temp, search.fpu) == (2.0, 0.5, 0.1)
        move = search.choose(state.clone())
        runs.append((repr(move), {repr(k): (c.visits, c.value) for k, c in search.last_root.children.items()}))
    assert runs[0] == runs[1]
    assert _search(make_agent("mcts:30", 5)).puct is None


def test_the_prior_is_the_setpolicy_prior_sharpened_by_the_temperature():
    from svsim.learn.setpolicy import SetPolicy
    pol = SetPolicy.load(PRIOR)
    state = _positions(1)[0]
    for temp in (1.0, 0.5):
        search = ISMCTS(iterations=1, seed=3, puct=pol, puct_temp=temp)
        search.choose(state.clone())
        root = search.last_root
        opts = search._root_options
        p = np.asarray(pol.priors(state, list(opts.values()))) ** (1 / temp)
        p = p / p.sum()
        assert np.allclose([root.prior[k] for k in opts], p, atol=1e-12)


def test_puct_and_the_root_prior_are_not_combined():
    with pytest.raises(ValueError):
        ISMCTS(puct=Counting(), prior=Counting())
