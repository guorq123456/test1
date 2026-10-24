"""A SetNet grown wider with a trainable leaky ReLU (learn.widenet; D14b, the architecture thread 2026-10-18 19:38Z).
Grown, it scores as the net it grew from to the last bit, in the batch and the search's single-position path, at
turn ends and mid-turn; with every new block and slope away from 0, its single-position path agrees with the batch
and its gradients with finite differences."""
import gzip
import json
from pathlib import Path

import numpy as np
import pytest

from svsim.learn import midrows as MR
from svsim.learn import setnet as SN
from svsim.learn import tokens as T
from svsim.learn.netdata import ENDED, rows
from svsim.learn.setpolicy import decisions
from svsim.learn.widenet import NEW, WideSetNet

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "analysis/scaling/data/elf-t3/rec/rec-74100038.jsonl.gz"
NET = ROOT / "analysis/scaling/models/net-mid-elf-t.npz"


def _records(n):
    with gzip.open(REC, "rt") as fh:
        return [json.loads(next(fh)) for _ in range(n)]


@pytest.fixture(scope="module")
def shard(tmp_path_factory):
    from svsim.learn import scaledata
    d = tmp_path_factory.mktemp("wide")
    recs = d / "rec-74100038.jsonl.gz"
    with gzip.open(recs, "wt") as fh:
        for r in _records(2):
            fh.write(json.dumps(r) + "\n")
    MR._encode_shard((str(recs), d / "mid-74100038.npz"))
    scaledata._encode_shard((str(recs), d / "tok-74100038.npz", scaledata.SPEC, None))
    static = {}
    for f in ("mid-74100038.npz", "tok-74100038.npz"):
        with np.load(d / f) as z:
            static.update({int(c): r for c, r in zip(z["card_id"], z["static"])})
    ids = sorted(static)
    np.savez(d / "cards.npz", card_id=np.asarray(ids, np.int64), static=np.stack([static[c] for c in ids]),
             static_names=np.asarray(T.static_names()))
    return d


def _rows(d, net):
    data = MR.phase_data([d / "tok-74100038.npz"], [d / "mid-74100038.npz"], d / "cards.npz")
    index = {int(c): i for i, c in enumerate(net.card_ids)}
    data.cards = np.array([index[int(c)] for c in data.card_ids], dtype=np.int32)[data.cards]
    return data


def _positions():
    """(state, player, mid) in the data's order: the turn ends of both games, then their mid-turn decisions."""
    ends, mids = [], []
    for r in _records(2):
        ends += [(st.clone(), p, False) for _i, (ph, p, st, _y) in rows(r, index=True) if ph == ENDED]
        mids += [(st.clone(), st.active, True) for _i, st, *_ in decisions(r)]
    return ends + mids


def test_grown_it_scores_as_the_net_to_the_last_bit(shard, tmp_path):
    base = SN.SetNet.load(NET)
    net = WideSetNet.grown_from(base, info=dict(base.info))
    assert net.extra == (64, 64, 128, 64) and net.flag and not net.a.any()
    for k in ("W2_no", "V1_no", "V2_no", "v3_n"):
        assert not getattr(net, k).any()
    for k in ("W1s_n", "W1d_n", "W2_on", "W2_nn", "V1_on", "V1_nn", "V2_on", "V2_nn"):
        assert getattr(net, k).std() > 0
    d = _rows(shard, base)
    assert np.array_equal(net.predict(d), base.predict(d))
    for k, (st, p, mid) in enumerate(_positions()):
        if k % 3 == 0:
            assert net.logit(st, p, mid=mid) == base.logit(st, p, mid=mid)
    net.save(tmp_path / "w.npz")
    back = SN.SetNet.load(tmp_path / "w.npz")
    assert isinstance(back, WideSetNet) and back.extra == net.extra and back.flag
    assert all(np.array_equal(getattr(back, k), getattr(net, k)) for k in net.PARAMS)
    assert np.array_equal(back.predict(d), net.predict(d))


def test_trained_single_position_matches_the_batch_and_gradients_match(shard):
    net = WideSetNet.grown_from(SN.SetNet.load(NET))
    rng = np.random.default_rng(0)
    for k, sd in (("W2_no", 0.05), ("V1_no", 0.002), ("V2_no", 0.05), ("v3_n", 0.05)):
        setattr(net, k, rng.normal(0, sd, getattr(net, k).shape))
    net.a = np.array([0.05, 0.1, 0.02, 0.2])
    d = _rows(shard, net)
    z = net.forward(*d.batch(np.arange(d.n)))
    assert np.abs(z).max() < 20                      # inside the loss's clip, where finite differences hold
    for k, (st, p, mid) in enumerate(_positions()):
        if k % 5 == 0:
            assert abs(net.logit(st, p, mid=mid) - z[k]) < 1e-9
            assert abs(net.logit(st, p, mid=mid) - z[k]) < 1e-9          # the memos' second answer
    idx = np.arange(16)
    y = d.result[idx].astype(np.float64)
    b = net._batch(d, idx)
    _, g = net.grads(b, y)
    assert set(g) == set(net.PARAMS)
    eps = 1e-6
    for k, spot in (("a", (0,)), ("a", (1,)), ("a", (2,)), ("a", (3,)), ("W1s_n", (3, 5)), ("W1d_n", (2, 7)),
                    ("W2_no", (4, 1)), ("W2_on", (5, 6)), ("W2_nn", (7, 8)), ("V1_no", (9, 3)), ("V1_on", (2, 10)),
                    ("V1_nn", (11, 4)), ("V2_no", (5, 2)), ("V2_on", (3, 7)), ("V2_nn", (8, 9)), ("v3_n", (6,)),
                    ("W1s", (1, 2)), ("W2", (3, 4)), ("V1", (5, 6)), ("b1_n", (3,)), ("c2_n", (4,))):
        arr = getattr(net, k)
        old = arr[spot]
        arr[spot] = old + eps
        lp = net.grads(b, y)[0]
        arr[spot] = old - eps
        lm = net.grads(b, y)[0]
        arr[spot] = old
        assert abs((lp - lm) / (2 * eps) - g[k][spot]) < 1e-5 * max(1.0, abs(g[k][spot])), k
    assert set(NEW) <= set(net.PARAMS)


def test_a_fit_step_moves_the_new_blocks_and_the_slopes(shard, tmp_path):
    net = WideSetNet.grown_from(SN.SetNet.load(NET))
    d = _rows(shard, net)
    net.fit(d, d, epochs=1, batch=64, log=lambda *_: None)
    assert net.a.any() and net.v3_n.any() and net.W2_no.any()
