"""The opponent-hand zone (SetNet ophand; a diagnostic, the architecture thread 2026-10-18 17:47Z): the opponent's
real hand, card by card, as one more zone with its own rows V1h. Off it changes nothing; added at 0 it changes nothing
to the last bit; its gradients and its single-position path agree with the batch."""
import gzip
import json
from pathlib import Path

import numpy as np
import pytest

from svsim.learn import midrows as MR
from svsim.learn import setnet as SN
from svsim.learn import tokens as T
from svsim.learn.setpolicy import decisions

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "analysis/scaling/data/elf-t3/rec/rec-74100038.jsonl.gz"
NET = ROOT / "analysis/scaling/models/net-mid-elf-t.npz"


def _records(n):
    with gzip.open(REC, "rt") as fh:
        return [json.loads(next(fh)) for _ in range(n)]


@pytest.fixture(scope="module")
def shard(tmp_path_factory):
    """Two games of the gen-3 holdout: tok-, mid- and both hand- files, with a cards.npz."""
    from svsim.learn import scaledata
    d = tmp_path_factory.mktemp("oph")
    recs = d / "rec-74100038.jsonl.gz"
    with gzip.open(recs, "wt") as fh:
        for r in _records(2):
            fh.write(json.dumps(r) + "\n")
    MR._encode_shard((str(recs), d / "mid-74100038.npz"))
    scaledata._encode_shard((str(recs), d / "tok-74100038.npz", scaledata.SPEC, None))
    MR._encode_hand_shard((str(recs), d / "hand-tok-74100038.npz", "end"))
    MR._encode_hand_shard((str(recs), d / "hand-mid-74100038.npz", "mid"))
    static = {}
    for f in ("mid-74100038.npz", "tok-74100038.npz"):
        with np.load(d / f) as z:
            static.update({int(c): r for c, r in zip(z["card_id"], z["static"])})
    ids = sorted(static)
    np.savez(d / "cards.npz", card_id=np.asarray(ids, np.int64), static=np.stack([static[c] for c in ids]),
             static_names=np.asarray(T.static_names()))
    return d


def _rows(shard, net):
    d = MR.phase_data([shard / "tok-74100038.npz"], [shard / "mid-74100038.npz"], shard / "cards.npz",
                      hand_dir=shard)
    index = {int(c): i for i, c in enumerate(net.card_ids)}
    table = np.array([index[int(c)] for c in d.card_ids], dtype=np.int32)
    d.cards, d.hand_cards = table[d.cards], table[d.hand_cards]
    return d


def test_hand_files_hold_the_opponent_s_real_hand_at_each_position(shard):
    z = np.load(shard / "hand-mid-74100038.npz")
    want = [len(st.players[1 - st.active].hand) for r in _records(2) for _, st, *_ in decisions(r)]
    assert np.diff(z["offsets"]).tolist() == want
    assert (z["tokens"][:, T.TOKEN.index("zone")] == SN.OP_HAND).all()
    end = np.load(shard / "hand-tok-74100038.npz")
    tok = np.load(shard / "tok-74100038.npz")
    assert np.array_equal(end["g"], tok["g"]) and np.array_equal(end["i"], tok["i"])


def test_added_at_zero_it_scores_as_the_net_to_the_last_bit(shard, tmp_path):
    base = SN.SetNet.load(NET)
    net = SN.SetNet.with_ophand_from(base, info=dict(base.info))
    assert net.ophand and not net.V1h.any() and "V1h" in net.PARAMS and "V1h" not in SN.SetNet.PARAMS
    d = _rows(shard, net)
    idx = np.arange(d.n)
    assert np.array_equal(net.forward(*d.batch(idx), hand=d.hand_batch(idx)), base.forward(*d.batch(idx)))
    assert np.array_equal(net.predict(d), base.predict(d))
    k = 0
    for r in _records(2):
        for _, st, *_ in decisions(r):
            if k < 25:
                assert net.logit(st, st.active, mid=True) == base.logit(st, st.active, mid=True)
                assert net.logit(st, st.active) == base.logit(st, st.active)
            k += 1
    net.save(tmp_path / "o.npz")
    back = SN.SetNet.load(tmp_path / "o.npz")
    assert back.ophand and np.array_equal(back.V1h, net.V1h)
    base.save(tmp_path / "b.npz")
    assert "ophand" not in np.load(tmp_path / "b.npz").files and "V1h" not in np.load(tmp_path / "b.npz").files


def test_trained_zone_single_position_matches_the_batch_and_gradients_match(shard):
    base = SN.SetNet.load(NET)
    net = SN.SetNet.with_ophand_from(base)
    net.V1h = np.random.default_rng(0).normal(0, 0.05, net.V1h.shape)
    d = _rows(shard, net)
    rows = MR.phase_data([], [shard / "mid-74100038.npz"], shard / "cards.npz", hand_dir=shard)
    index = {int(c): i for i, c in enumerate(net.card_ids)}
    table = np.array([index[int(c)] for c in rows.card_ids], dtype=np.int32)
    rows.cards, rows.hand_cards = table[rows.cards], table[rows.hand_cards]
    batch = net.forward(*rows.batch(np.arange(rows.n)), hand=rows.hand_batch(np.arange(rows.n)))
    k = 0
    for r in _records(2):
        for _, st, *_ in decisions(r):
            if k < 30:
                assert abs(net.logit(st, st.active, mid=True) - batch[k]) < 1e-9
            k += 1
    assert np.abs(batch - base.forward(*rows.batch(np.arange(rows.n)))).max() > 1e-6   # the zone counts now
    idx = np.arange(12)
    y = d.result[idx].astype(np.float64)
    b = net._batch(d, idx)
    _, g = net.grads(b, y)
    eps = 1e-6
    for k, spot in (("V1h", (3, 5)), ("W2", (2, 4)), ("W1d", (1, 7)), ("b1", (6,))):
        a = getattr(net, k)
        old = a[spot]
        a[spot] = old + eps
        lp = net.grads(b, y)[0]
        a[spot] = old - eps
        lm = net.grads(b, y)[0]
        a[spot] = old
        assert abs((lp - lm) / (2 * eps) - g[k][spot]) < 1e-5 * max(1.0, abs(g[k][spot]))
