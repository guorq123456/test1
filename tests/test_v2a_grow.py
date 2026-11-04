"""A v1 net grown to v2a inputs (SetNet xcols, with_v2a_from; D14a, the architecture thread 2026-10-18 19:38Z):
V2_EXTRA's columns go through rows of their own, W1x, added after v1's. Added at 0 it scores as the v1 net to the
last bit, in the batch and the search's single-position path, at turn ends and mid-turn; trained, its single-position
path agrees with the batch and its gradients with finite differences."""
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

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "analysis/scaling/data/elf-t3/rec/rec-74100038.jsonl.gz"
NET = ROOT / "analysis/scaling/models/net-mid-elf-t.npz"


def _records(n):
    with gzip.open(REC, "rt") as fh:
        return [json.loads(next(fh)) for _ in range(n)]


@pytest.fixture(scope="module")
def shard(tmp_path_factory):
    """Two games of the gen-3 holdout as v1 and v2a tok- and mid- files, with a cards.npz each."""
    from svsim.learn import scaledata
    out = {}
    recs = tmp_path_factory.mktemp("rec") / "rec-74100038.jsonl.gz"
    with gzip.open(recs, "wt") as fh:
        for r in _records(2):
            fh.write(json.dumps(r) + "\n")
    for inputs in ("v1", "v2a"):
        d = tmp_path_factory.mktemp(inputs)
        MR._encode_shard((str(recs), d / "mid-74100038.npz", inputs))
        scaledata._encode_shard((str(recs), d / "tok-74100038.npz", scaledata.SPEC, None, inputs))
        static = {}
        for f in ("mid-74100038.npz", "tok-74100038.npz"):
            with np.load(d / f) as z:
                static.update({int(c): r for c, r in zip(z["card_id"], z["static"])})
        ids = sorted(static)
        np.savez(d / "cards.npz", card_id=np.asarray(ids, np.int64), static=np.stack([static[c] for c in ids]),
                 static_names=np.asarray(T.static_names()))
        out[inputs] = d
    return out


def _rows(d, net, end=True, mid=True):
    data = MR.phase_data([d / "tok-74100038.npz"] if end else [], [d / "mid-74100038.npz"] if mid else [],
                         d / "cards.npz")
    index = {int(c): i for i, c in enumerate(net.card_ids)}
    data.cards = np.array([index[int(c)] for c in data.card_ids], dtype=np.int32)[data.cards]
    return data


def _positions():
    """(state, player, mid) at the two games' turn ends and mid-turn decisions."""
    out = []
    for r in _records(2):
        out += [(st.clone(), p, False) for _i, (ph, p, st, _y) in rows(r, index=True) if ph == ENDED]
        out += [(st.clone(), st.active, True) for _i, st, *_ in decisions(r)]
    return out


def test_v2a_files_are_v1_s_columns_then_v2_extra(shard):
    for f in ("tok-74100038.npz", "mid-74100038.npz"):
        a, b = np.load(shard["v1"] / f), np.load(shard["v2a"] / f)
        assert str(b["inputs"]) == "v2a" and "inputs" not in a.files
        assert np.array_equal(a["tokens"], b["tokens"][:, :len(T.TOKEN)])
        for k in ("cards", "offsets", "globals", "result", "g", "turn"):
            assert np.array_equal(a[k], b[k])


def test_grown_at_zero_it_scores_as_the_v1_net_to_the_last_bit(shard, tmp_path):
    base = SN.SetNet.load(NET)
    net = SN.SetNet.with_v2a_from(base, info=dict(base.info))
    assert net.xcols and net.inputs == "v2a" and net.flag and not net.W1x.any()
    assert "W1x" in net.PARAMS and "W1x" not in SN.SetNet.PARAMS
    d1, d2 = _rows(shard["v1"], base), _rows(shard["v2a"], net)
    assert d2.inputs == "v2a" and d1.n == d2.n
    assert np.array_equal(net.predict(d2), base.predict(d1))
    for k, (st, p, mid) in enumerate(_positions()):
        if k % 3 == 0:
            assert net.logit(st, p, mid=mid) == base.logit(st, p, mid=mid)
    net.save(tmp_path / "x.npz")
    back = SN.SetNet.load(tmp_path / "x.npz")
    assert back.xcols and back.inputs == "v2a" and np.array_equal(back.W1x, net.W1x)
    assert np.array_equal(back.predict(d2), net.predict(d2))


def test_trained_rows_single_position_matches_the_batch_and_gradients_match(shard):
    base = SN.SetNet.load(NET)
    net = SN.SetNet.with_v2a_from(base)
    net.W1x = np.random.default_rng(0).normal(0, 0.3, net.W1x.shape)
    d = _rows(shard["v2a"], net)
    z = net.forward(*d.batch(np.arange(d.n)))
    assert np.abs(z - base.forward(*_rows(shard["v1"], base).batch(np.arange(d.n)))).max() > 1e-6  # the rows count
    n_end = int((d.flag == 0).sum())
    ends = [x for x in _positions() if not x[2]]
    mids = [x for x in _positions() if x[2]]
    for k in range(0, n_end, 7):
        st, p, _ = ends[k]
        assert abs(net.logit(st, p) - z[k]) < 1e-9
    for k in range(0, len(mids), 7):
        st, p, _ = mids[k]
        assert abs(net.logit(st, p, mid=True) - z[n_end + k]) < 1e-9
    idx = np.arange(12)
    y = d.result[idx].astype(np.float64)
    b = net._batch(d, idx)
    _, g = net.grads(b, y, l2=1e-3)
    eps = 1e-6
    for k, spot in (("W1x", (0, 5)), ("W1x", (2, 9)), ("W1d", (1, 7)), ("V1", (3, 4))):
        a = getattr(net, k)
        old = a[spot]
        a[spot] = old + eps
        lp = net.grads(b, y, l2=1e-3)[0] + 1e-3 * sum(float((getattr(net, q) ** 2).sum()) for q in
                                                       ("W1s", "W1d", "W2", "V1", "V2", "v3", "W1x"))
        a[spot] = old - eps
        lm = net.grads(b, y, l2=1e-3)[0] + 1e-3 * sum(float((getattr(net, q) ** 2).sum()) for q in
                                                       ("W1s", "W1d", "W2", "V1", "V2", "v3", "W1x"))
        a[spot] = old
        assert abs((lp - lm) / (2 * eps) - g[k][spot]) < 1e-5 * max(1.0, abs(g[k][spot]))
