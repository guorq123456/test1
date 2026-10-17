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


def test_neteot_ends_a_mid_turn_position_first_and_leaves_turn_ends_alone(tmp_path):
    from svsim.learn.model import SCALE
    from svsim.learn.netdata import _search
    from svsim.tools.arena import make_agent
    positions = _positions(4)
    net = _net(_data(positions))
    net.save(tmp_path / "n.npz")
    spec = f"mcts:20+plan+learned+phased+setnet={tmp_path / 'n.npz'}"
    off, on = _search(make_agent(spec, 0)).weights, _search(make_agent(spec + "+neteot", 0)).weights
    assert not off.end_mid_turn and on.end_mid_turn
    for s, p in positions:                                     # turn ends: the scored player isn't to act
        assert s.active != p
        assert on.score(s, p, False) == off.score(s, p, False) == SCALE * net.logit(s, p)
    for seed in range(4):                                      # inside the player's own turn
        cards = decks.build(DECKS["ramp-t"][1])
        s = new_game(cards, list(cards), seed=seed)
        p = s.active
        ended = after_end_of_turn(s)
        assert on.score(s, p, False) == SCALE * net.logit(ended, p)
        assert off.score(s, p, False) == SCALE * net.logit(s, p)
        assert on.score(s, p, True) == off.score(s, p, True)   # in-turn (player moves next): the base, as before


def test_fit_resumed_from_a_checkpoint_matches_an_unbroken_fit(tmp_path):
    d = _data(_positions(8))
    quiet = lambda *_: None
    whole = _net(d, seed=3)
    whole.fit(d, d, epochs=4, batch=3, patience=10, log=quiet)
    broken = _net(d, seed=3)
    ck = tmp_path / "ck.npz"
    broken.fit(d, d, epochs=2, batch=3, patience=10, log=quiet, checkpoint=ck)   # stopped after 2 epochs
    again = _net(d, seed=3)
    again.fit(d, d, epochs=4, batch=3, patience=10, log=quiet, checkpoint=ck)    # goes on from epoch 3
    for k in SN.SetNet.PARAMS:
        assert np.array_equal(getattr(whole, k), getattr(again, k))
    assert [r["epoch"] for r in again.info["history"]] == [1, 2, 3, 4]


def test_flushing_subnormal_weights_keeps_the_logits(tmp_path):
    positions = _positions(4)
    d = _data(positions)
    net = _net(d)
    net.V1[:5, :3] = 1e-310                                   # subnormal weights, as l2 decay leaves them
    net.save(tmp_path / "n.npz")
    flushed = SN.load_cached(tmp_path / "n.npz", ftz=True)
    plain = SN.load_cached(tmp_path / "n.npz")
    assert flushed is not plain and not np.any((flushed.V1 != 0) & (np.abs(flushed.V1) < np.finfo(float).tiny))
    for s, p in positions:
        assert flushed.logit(s, p) == plain.logit(s, p)


def test_leaky_relu_gradients_and_single_position_path(tmp_path):
    positions = _positions()
    d = _data(positions)
    net = SN.SetNet(d.static.shape[1], phi=(8, 6), rho=(10, 5), seed=2, slope=0.01,
                    info={"deck": "ramp-t", "opponent": "ramp-t"})
    net.set_cards(d.card_ids, d.static)
    batch, y = d.batch(np.arange(d.n)), d.result.astype(float)
    _, g = net.grads(batch, y)
    rng = np.random.default_rng(1)
    for k in net.PARAMS:
        P = getattr(net, k)
        i = tuple(rng.integers(0, s) for s in P.shape)
        old = P[i]
        P[i] = old + 1e-6
        lp, _ = net.grads(batch, y)
        P[i] = old - 1e-6
        lm, _ = net.grads(batch, y)
        P[i] = old
        assert abs((lp - lm) / 2e-6 - g[k][i]) < 1e-6
    net.save(tmp_path / "leaky.npz")
    back = SN.SetNet.load(tmp_path / "leaky.npz")
    assert back.slope == 0.01
    z = net.forward(*batch)
    for (s, p), want in zip(positions, z):
        assert abs(back.logit(s, p) - want) < 1e-9


# --- input versions (learn.tokens INPUTS; the architecture thread 2026-10-17 01:30Z) --------------------------------

def _data_inputs(positions, inputs):
    """_data with the tokens / globals of an input version."""
    d = _data(positions)
    cids, toks, glob = zip(*(T.encode(s, p, inputs) for s, p in positions))
    d.tokens = np.concatenate(toks)
    d.globals = np.stack(glob) / SN.global_scale(inputs)
    d.inputs = SN.inputs_of(d.tokens.shape[1], np.stack(glob).shape[1])
    return d


def _played_positions(n=6, turns=7):
    """Turn ends a few turns into games (followers on both fields, attacks made, evolution turns reached)."""
    import random
    from svsim.core.engine import apply, legal_actions
    from svsim.core.enums import Phase
    out = []
    for seed in range(n):
        cards = decks.build(DECKS["ramp-t"][1])
        s = new_game(cards, list(cards), seed=seed)
        rng = random.Random(seed)
        while s.winner is None and s.turn <= turns:
            acts = legal_actions(s)
            ends = [a for a in acts if type(a).__name__ == "EndTurn"]
            others = [a for a in acts if type(a).__name__ != "EndTurn"]
            if s.phase == Phase.MAIN and others and rng.random() < 0.8:
                apply(s, rng.choice(others))
            else:
                if s.phase == Phase.MAIN and s.turn >= 3:
                    out.append((after_end_of_turn(s), s.active))
                apply(s, ends[0] if ends else rng.choice(acts))
    return [(s, p) for s, p in out if s.winner is None]


def test_old_nets_give_the_69e3ad2_numbers_bit_for_bit():
    """gen3, net-elft-10000 and gen4-59000 on 71 holdout turn ends: the logits the 69e3ad2 code gave (tests/data,
    computed in a 69e3ad2 checkout) are reproduced exactly; the v1 encoding and the v1 search path are unchanged."""
    import gzip
    import json
    from pathlib import Path
    from svsim.learn.netdata import ENDED, rows
    root = Path(__file__).resolve().parents[1]
    want = json.loads((root / "tests/data/setnet_golden_69e3ad2.json").read_text())
    nets = {n: SN.SetNet.load(root / f"analysis/scaling/models/{n}.npz") for n in want["logits"]}
    assert all(net.inputs == "v1" for net in nets.values())
    got = {n: [] for n in nets}
    with gzip.open(root / "analysis/scaling/data/heldout/rec-70200000.jsonl.gz", "rt") as fh:
        for line, _ in zip(fh, range(4)):
            for i, (phase, player, state, result) in rows(json.loads(line), index=True):
                if phase == ENDED:
                    for n, net in nets.items():
                        got[n].append(repr(net.logit(state, player)))
    assert got == want["logits"]


def test_v2_shares_next_turn_values_and_attack_state():
    from svsim.core.engine import EVOLVE_TURN, MAX_PP
    for s, me in _played_positions():
        cards, tok, glob = T.encode(s, me, "v2")
        v1 = T.encode(s, me)
        assert tok.shape[1] == len(T.TOKEN_V2) and np.array_equal(cards, v1[0])
        assert np.array_equal(glob, v1[2])
        col = {n: i for i, n in enumerate(T.TOKEN_V2)}
        z = tok[:, col["zone"]]
        deck, pool = tok[z == 3], tok[z == 6]
        o = s.players[1 - me]
        if len(deck):
            assert abs(int(deck[:, col["share"]].sum()) - 1000) <= len(deck)        # draw chances add up to 1
        if len(pool):
            assert abs(int(pool[:, col["share"]].sum()) - 1000 * len(o.hand)) <= len(pool)
        for zone, owner in ((0, me), (1, me), (3, me), (4, 1 - me), (6, 1 - me)):
            sel = tok[z == zone]
            pl = s.players[owner]
            assert (sel[:, col["next_pp"]] == min(pl.max_pp + 1, MAX_PP)).all()
            ev = int(pl.ep > 0 and pl.turns_taken + 1 >= EVOLVE_TURN[s.first == owner])
            assert (sel[:, col["next_evolve"]] == ev).all()
        same = [n for n in T.TOKEN if n not in ("can_hit_follower", "can_hit_leader", "attacks_left")]
        assert np.array_equal(tok[:, [col[n] for n in same]], v1[1][:, [T.TOKEN.index(n) for n in same]])
        from svsim.core.script import prop
        field = [c for c in s.players[me].field] + [c for c in o.field]
        rows = tok[(z == 1) | (z == 4)]
        for c, r in zip(field, rows):
            if c.defn.is_follower and not prop(c, "cant_attack"):
                assert r[col["attacks_left"]] == c.max_attacks and r[col["can_hit_leader"]] == 1


def test_v2_and_v2kc_single_position_logit_matches_the_batch_and_files_keep_the_version(tmp_path):
    positions = _played_positions()
    assert len(positions) >= 10
    for inputs in ("v2", "v2kc"):
        d = _data_inputs(positions, inputs)
        assert d.inputs == inputs
        net = SN.SetNet(d.static.shape[1], phi=(8, 6), rho=(10, 5), seed=4, inputs=inputs,
                        info={"deck": "ramp-t", "opponent": "ramp-t"})
        net.set_cards(d.card_ids, d.static)
        batch, y = d.batch(np.arange(d.n)), d.result.astype(float)
        if len(d.result) != d.n:
            y = np.resize(d.result, d.n).astype(float)
        _, g = net.grads(batch, y)
        rng = np.random.default_rng(5)
        for k in net.PARAMS:
            P = getattr(net, k)
            i = tuple(rng.integers(0, sh) for sh in P.shape)
            old = P[i]
            P[i] = old + 1e-6
            lp, _ = net.grads(batch, y)
            P[i] = old - 1e-6
            lm, _ = net.grads(batch, y)
            P[i] = old
            assert abs((lp - lm) / 2e-6 - g[k][i]) < 1e-6
        z = net.forward(*batch)
        for (s, p), want in zip(positions, z):
            assert abs(net.logit(s, p) - want) < 1e-9
        net.save(tmp_path / f"{inputs}.npz")
        back = SN.SetNet.load(tmp_path / f"{inputs}.npz")
        assert back.inputs == inputs
        for s, p in positions[:5]:
            assert back.logit(s, p) == net.logit(s, p)
    v1 = _net(_data(positions[:4]))
    v1.save(tmp_path / "v1.npz")
    assert "inputs" not in np.load(tmp_path / "v1.npz").files and SN.SetNet.load(tmp_path / "v1.npz").inputs == "v1"


def test_live_memo_hits_give_the_same_bits_as_a_cold_net():
    """The live part's memo (setnet._live_part): every position scored twice by a warm net, interleaved, equals a
    cold net's first score, for a v1 and a v2 net."""
    import gzip
    import json
    from pathlib import Path
    from svsim.learn.netdata import ENDED, rows
    root = Path(__file__).resolve().parents[1]
    states = []
    with gzip.open(root / "analysis/scaling/data/heldout/rec-70200002.jsonl.gz", "rt") as fh:
        for line, _ in zip(fh, range(3)):
            states += [(s, p) for i, (ph, p, s, r) in rows(json.loads(line), index=True) if ph == ENDED]
    for name in ("net-gen3-30000", "net-in2-59000"):
        path = root / f"analysis/scaling/models/{name}.npz"
        warm = SN.SetNet.load(path)
        first = [warm.logit(s, p) for s, p in states]
        again = [warm.logit(s, p) for s, p in states[::-1]][::-1]
        cold = []
        for s, p in states:
            net = SN.SetNet.load(path)
            cold.append(net.logit(s, p))
        assert first == again == cold
        assert warm._live_hits >= len(states)
