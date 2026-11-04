"""The value net's mid-turn branch (the architecture thread 2026-10-18 07:53Z): SetNet's flag, learn.midrows' rows
and loading, and the agent option +netmid."""
import gzip
import json
from pathlib import Path

import numpy as np
import pytest

from svsim.cards import decks
from svsim.core.engine import new_game
from svsim.learn import midrows as MR
from svsim.learn import setnet as SN
from svsim.learn import tokens as T
from svsim.learn.setpolicy import decisions
from svsim.search.evaluate import after_end_of_turn
from svsim.ui.session import DECKS

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "analysis/scaling/data/elf-t3/rec/rec-74100038.jsonl.gz"
NET = ROOT / "analysis/scaling/models/net-elft-gen2-19500.npz"


def _records(n):
    with gzip.open(REC, "rt") as fh:
        return [json.loads(next(fh)) for _ in range(n)]


@pytest.fixture(scope="module")
def shard(tmp_path_factory):
    """Three games of the gen-3 holdout as a mid- file and a tok- file (learn.scaledata), with a cards.npz."""
    from svsim.learn import scaledata
    d = tmp_path_factory.mktemp("mid")
    recs = d / "rec-74100038.jsonl.gz"
    with gzip.open(recs, "wt") as fh:
        for r in _records(3):
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


def _ramp_mid_positions(n=4):
    out = []
    for seed in range(n):
        cards = decks.build(DECKS["ramp-t"][1])
        s = new_game(cards, list(cards), seed=seed)
        out.append((s, s.active))                  # inside the mover's own turn
    return out


def test_mid_rows_are_the_prior_s_decisions_from_the_mover_s_view(shard):
    z = np.load(shard / "mid-74100038.npz")
    recs = _records(3)
    want = [(r["g"], i, st.active, float(r["winner"] == st.active)) for r in recs for i, st, *_ in decisions(r)]
    assert [(int(g), int(i), int(p), float(y)) for g, i, p, y in zip(z["g"], z["i"], z["player"], z["result"])] == want
    assert len(z["offsets"]) == len(want) + 1 and not z["linear"].any()
    for (g, i, me, _), k in zip(want[:30], range(30)):         # the tokens are T.encode of the mover's view
        r = recs[[x["g"] for x in recs].index(g)]
        st = next(s for j, s, *_ in decisions(r) if j == i)
        cids, toks, glob = T.encode(st, me)
        lo, hi = z["offsets"][k], z["offsets"][k + 1]
        assert np.array_equal(z["tokens"][lo:hi], toks) and np.array_equal(z["cards"][lo:hi], cids)
        assert np.array_equal(z["globals"][k], glob)


def test_phase_split_appends_the_flag_and_splits_by_game(shard):
    end, mid = [shard / "tok-74100038.npz"], [shard / "mid-74100038.npz"]
    whole = SN.Data(end + mid, shard / "cards.npz")
    allrows = MR.phase_data(end, mid, shard / "cards.npz")
    n_end = len(np.load(end[0])["result"])
    assert allrows.n == whole.n and np.array_equal(allrows.tokens, whole.tokens)
    assert np.array_equal(allrows.cards, whole.cards) and np.array_equal(allrows.offsets, whole.offsets)
    assert np.array_equal(allrows.globals[:, :-1], whole.globals.astype(np.float32))
    assert np.array_equal(allrows.globals[:, -1], np.r_[np.zeros(n_end), np.ones(whole.n - n_end)])
    train, valid = MR.phase_split(end, mid, shard / "cards.npz", every=3)
    v = whole.games() % 3 == 0
    for got, want in ((train, ~v), (valid, v)):
        assert got.n == int(want.sum())
        ref = whole.subset(want)
        assert np.array_equal(got.tokens, ref.tokens) and np.array_equal(got.offsets, ref.offsets)
        assert np.array_equal(got.result, ref.result)
    a, _ = MR.phase_split(end, mid, shard / "cards.npz", every=3, mid_rate=0.4, seed=7)
    b, _ = MR.phase_split(end, mid, shard / "cards.npz", every=3, mid_rate=0.4, seed=7)
    assert np.array_equal(a.tokens, b.tokens) and a.n == b.n                      # the thinning is seeded
    assert (a.flag == 0).sum() == (train.flag == 0).sum() and 0 < (a.flag == 1).sum() < (train.flag == 1).sum()


def test_flagged_net_scores_turn_ends_as_its_start_and_single_positions_match_the_batch(shard, tmp_path):
    base = SN.SetNet.load(NET)
    net = SN.SetNet.flagged_from(base, info=dict(base.info))
    assert net.flag and net.V1.shape[0] == base.V1.shape[0] + 1 and not net.V1[-1].any()
    rows = MR.phase_data([shard / "tok-74100038.npz"], [shard / "mid-74100038.npz"], shard / "cards.npz")
    index = {int(c): i for i, c in enumerate(net.card_ids)}
    rows.cards = np.array([index[int(c)] for c in rows.card_ids], dtype=np.int32)[rows.cards]
    flagged = net.forward(*rows.batch(np.arange(rows.n)))
    rows.globals = rows.globals[:, :-1]
    plain = base.forward(*rows.batch(np.arange(rows.n)))
    assert np.allclose(flagged, plain, rtol=0, atol=1e-12)                   # a zero row: the start is the base net
    net.V1[-1] = np.linspace(-0.3, 0.3, net.V1.shape[1])                    # a trained-looking flag row
    for s, p in _ramp_mid_positions(2):
        s_end = after_end_of_turn(s)
        assert abs(net.logit(s_end, 1 - s_end.active) - base.logit(s_end, 1 - s_end.active)) < 1e-12
        assert net.logit(s, p, mid=True) != net.logit(s, p)
    with pytest.raises(ValueError):
        base.logit(s, p, mid=True)
    net.save(tmp_path / "f.npz")
    back = SN.SetNet.load(tmp_path / "f.npz")
    assert back.flag and np.array_equal(back.V1, net.V1)
    assert back.logit(s, p, mid=True) == net.logit(s, p, mid=True)
    base.save(tmp_path / "b.npz")
    assert "flag" not in np.load(tmp_path / "b.npz").files                    # a file without the flag: as before


def test_mid_branch_single_position_matches_the_batch(shard):
    net = SN.SetNet.flagged_from(SN.SetNet.load(NET))
    net.V1[-1] = np.linspace(-0.3, 0.3, net.V1.shape[1])
    rows = MR.phase_data([], [shard / "mid-74100038.npz"], shard / "cards.npz")
    index = {int(c): i for i, c in enumerate(net.card_ids)}
    rows.cards = np.array([index[int(c)] for c in rows.card_ids], dtype=np.int32)[rows.cards]
    batch = net.forward(*rows.batch(np.arange(rows.n)))
    k = 0
    for r in _records(3):
        for _, st, *_ in decisions(r):
            if k < 40:
                assert abs(net.logit(st, st.active, mid=True) - batch[k]) < 1e-9
            k += 1
    assert k == rows.n


def test_netmid_scores_a_mid_turn_leaf_by_the_mid_branch_without_ending_the_turn(tmp_path, monkeypatch):
    from svsim.learn.model import SCALE
    from svsim.learn.netdata import _search
    from svsim.search import evaluate
    from svsim.tools.arena import make_agent
    base = SN.SetNet.load(ROOT / "analysis/scaling/models/net-gen3-30000.npz")
    net = SN.SetNet.flagged_from(base, info=dict(base.info))
    net.V1[-1] = np.linspace(-0.3, 0.3, net.V1.shape[1])
    net.save(tmp_path / "f.npz")
    base.save(tmp_path / "b.npz")
    spec = f"mcts:20+plan+learned+phased+setnet={tmp_path / 'f.npz'}"
    mid, eot = _search(make_agent(spec + "+netmid", 0)).weights, _search(make_agent(spec + "+neteot", 0)).weights
    assert mid.mid_turn and not eot.mid_turn
    for s, p in _ramp_mid_positions():
        assert eot.score(s, p, False) == SCALE * net.logit(after_end_of_turn(s), p)
        monkeypatch.setattr(evaluate, "after_end_of_turn", lambda *a: pytest.fail("+netmid ended a turn"))
        assert mid.score(s, p, False) == SCALE * net.logit(s, p, mid=True)
        monkeypatch.undo()
        ended = after_end_of_turn(s)                               # a turn end: the turn-end branch
        q = 1 - ended.active
        assert mid.score(ended, q, False) == eot.score(ended, q, False) == SCALE * net.logit(ended, q)
        assert mid.score(s, p, True) == eot.score(s, p, True)       # in-turn (player moves next): the base
    with pytest.raises(ValueError):                                # +netmid needs a flagged net
        make_agent(f"mcts:20+plan+learned+phased+setnet={tmp_path / 'b.npz'}+netmid", 0)
