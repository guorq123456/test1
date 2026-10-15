"""The scaling test's DeepSets value net (learn.setnet) and its search switch (+setnet=PATH)."""
import numpy as np

from svsim.cards import decks
from svsim.core.engine import new_game
from svsim.learn import setnet as SN
from svsim.learn import tokens as T
from svsim.search.evaluate import after_end_of_turn
from svsim.ui.session import DECKS


def _positions(n=6):
    out = []
    for seed in range(n):
        cards = decks.build(DECKS["ramp-t"][1])
        s = new_game(cards, list(cards), seed=seed)
        out.append((after_end_of_turn(s), s.active))
    return out


def _data(positions):
    """A Data built in memory from encoded positions."""
    cids, toks, glob = zip(*(T.encode(s, p) for s, p in positions))
    ids = np.unique(np.concatenate(cids)).astype(np.int64)
    defs = {}
    for s, _ in positions:
        for pl in s.players:
            for c in pl.hand + pl.deck_view():
                defs[c.defn.card_id] = c.defn
    d = object.__new__(SN.Data)
    d.card_ids, d.static = ids, np.stack([T.static(defs[int(c)]) for c in ids])
    d.static_names = T.static_names()
    d.tokens = np.concatenate(toks)
    d.cards = np.searchsorted(ids, np.concatenate(cids)).astype(np.int32)
    d.offsets = np.concatenate([[0], np.cumsum([len(c) for c in cids])]).astype(np.int64)
    d.globals = np.stack(glob) / SN._GLOBAL_SCALE
    d.result = np.array([1.0, 0.0] * (len(positions) // 2), dtype=np.float32)
    d.linear = np.zeros(len(positions), np.float32)
    d.seed = np.zeros(len(positions), np.int32)
    d.g = np.arange(len(positions), dtype=np.int32)
    d.turn = np.ones(len(positions), np.int32)
    d.n = len(positions)
    return d


def _net(d, seed=1):
    net = SN.SetNet(d.static.shape[1], phi=(8, 6), rho=(10, 5), seed=seed, info={"deck": "ramp-t",
                                                                                  "opponent": "ramp-t"})
    net.set_cards(d.card_ids, d.static)
    return net


def test_gradients_match_finite_differences():
    d = _data(_positions())
    net = _net(d)
    idx = np.arange(d.n)
    batch, y = d.batch(idx), d.result.astype(float)
    _, g = net.grads(batch, y)
    rng = np.random.default_rng(0)
    for k in net.PARAMS:
        P = getattr(net, k)
        for _ in range(3):
            i = tuple(rng.integers(0, s) for s in P.shape)
            old = P[i]
            P[i] = old + 1e-6
            lp, _ = net.grads(batch, y)
            P[i] = old - 1e-6
            lm, _ = net.grads(batch, y)
            P[i] = old
            assert abs((lp - lm) / 2e-6 - g[k][i]) < 1e-6


def test_single_position_logit_matches_the_batch(tmp_path):
    positions = _positions()
    d = _data(positions)
    net = _net(d)
    batch_logits = net.forward(*d.batch(np.arange(d.n)))
    for (s, p), z in zip(positions, batch_logits):
        assert abs(net.logit(s, p) - z) < 1e-9
    net.save(tmp_path / "n.npz")
    back = SN.SetNet.load(tmp_path / "n.npz")
    assert back.info["deck"] == "ramp-t"
    for s, p in positions:
        assert abs(back.logit(s, p) - net.logit(s, p)) < 1e-12


def test_search_switch_scores_only_the_nets_turn_ends(tmp_path):
    from svsim.learn.model import SCALE
    from svsim.learn.netdata import _search
    from svsim.tools.arena import make_agent
    positions = _positions(2)
    net = _net(_data(positions))
    net.save(tmp_path / "n.npz")
    agent = make_agent(f"mcts:20+plan+learned+phased+setnet={tmp_path / 'n.npz'}", 0)
    w = _search(agent).weights
    assert isinstance(w, SN.SetNetEnded)
    s, p = positions[0]
    assert abs(w.score(s, p, False) - SCALE * net.logit(s, p)) < 1e-9
    assert w.score(s, p, True) == w.base.score(s, p, True)     # in-turn: as before
    other = make_agent("mcts:20+plan+learned+phased", 0)
    assert w.score(s, p, True) == _search(other).weights.score(s, p, True)
