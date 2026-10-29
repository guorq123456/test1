"""S1 (ii): learn.ranked's children of searched decisions and advantage labels, and SetNet's ranking loss."""
import gzip
import json
from pathlib import Path

import numpy as np
import pytest

from svsim.core.actions import EndTurn
from svsim.core.engine import apply
from svsim.learn import ranked as RK
from svsim.learn import setnet as SN
from svsim.learn import tokens as T
from svsim.learn.setpolicy import decisions
from svsim.search.evaluate import after_end_of_turn

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "analysis/scaling/data/elf-t3/rec/rec-74100038.jsonl.gz"
NET = ROOT / "analysis/scaling/models/net-elft-gen2-19500.npz"


def _records(n):
    with gzip.open(REC, "rt") as fh:
        return [json.loads(next(fh)) for _ in range(n)]


@pytest.fixture(scope="module")
def shard(tmp_path_factory):
    """Four games as a rank- file (every decision, up to 3 others) with a cards.npz of its cards."""
    d = tmp_path_factory.mktemp("rank")
    recs = d / "rec-74100038.jsonl.gz"
    with gzip.open(recs, "wt") as fh:
        for r in _records(4):
            fh.write(json.dumps(r) + "\n")
    RK._encode_shard((str(recs), d / "rank-74100038.npz", 1.0, 3))
    with np.load(d / "rank-74100038.npz") as z:
        np.savez(d / "cards.npz", card_id=z["card_id"].astype(np.int64), static=z["static"],
                 static_names=np.asarray(T.static_names()))
    return d


def test_children_are_the_moves_from_the_mover_s_view_best_by_visits(shard):
    z = np.load(shard / "rank-74100038.npz")
    recs = _records(4)
    k = 0
    n_dec = 0
    for r in recs:
        used = {i: (me, rows) for i, me, rows in RK.children(r, 1.0, 3)}
        for i, state, _legal, reps, _group, v, _start in decisions(r):
            if i not in used:
                continue
            n_dec += 1
            me, rows = used[i]
            assert me == state.active and rows[0][4] and not any(x[4] for x in rows[1:])
            assert v.argmax() == int(np.argmax(v)) and int((v == v.max()).sum()) == 1
            assert 2 <= len(rows) <= 4
            for c, t, g, flag, best, visits, child in rows:
                assert child.winner is None and flag == float(child.active == me)
                cids, toks, glob = T.encode(child, me)
                lo, hi = z["offsets"][k], z["offsets"][k + 1]
                assert np.array_equal(z["tokens"][lo:hi], toks) and np.array_equal(z["cards"][lo:hi], cids)
                assert np.array_equal(z["globals"][k], glob) and z["flag"][k] == flag and z["best"][k] == best
                assert int(z["player"][k]) == me and z["g"][k] == r["g"] and z["i"][k] == i
                k += 1
    assert k == len(z["result"]) and n_dec == len(set(z["group"].tolist())) > 20


def test_the_best_child_is_the_most_visited_and_end_turn_is_after_the_turn_s_end():
    r = _records(1)[0]
    seen_end = False
    for i, me, rows in RK.children(r, 1.0, 10):
        st = next(s for j, s, *_ in decisions(r) if j == i)
        _, _, _, reps, _, v, _ = next(x for x in decisions(r) if x[0] == i)
        best = rows[0][6]
        want = reps[int(np.argmax(v))]
        if isinstance(want, EndTurn):
            ref = after_end_of_turn(st)
            seen_end = True
            assert rows[0][3] == 0.0
        else:
            ref = st.clone()
            apply(ref, want)
        assert np.array_equal(T.encode(ref, me)[1], T.encode(best, me)[1])
    assert seen_end


def test_rate_keeps_a_seeded_share_of_the_decisions():
    r = _records(1)[0]
    every = [i for i, *_ in RK.children(r, 1.0, 3)]
    some = [i for i, *_ in RK.children(r, 0.3, 3)]
    assert set(some) < set(every) and 0 < len(some) < len(every)
    assert some == [i for i, *_ in RK.children(r, 0.3, 3)]


def test_load_groups_decisions_with_one_best_each_split_by_game(shard):
    train, valid = RK.load([shard / "rank-74100038.npz"], shard / "cards.npz", every=2)
    z = np.load(shard / "rank-74100038.npz")
    games = z["seed"].astype(np.int64) * 100003 + z["g"].astype(np.int64)
    for d, want in ((train, games % 2 != 0), (valid, games % 2 == 0)):
        assert d.n == int(want.sum()) and d.n_dec == len(set(z["group"][want].tolist()))
        assert np.array_equal(d.globals[:, -1], z["flag"][want]) and np.array_equal(d.best, z["best"][want])
        for j in range(d.n_dec):
            assert d.best[d.dec_offsets[j]:d.dec_offsets[j + 1]].sum() == 1
    assert train.n_dec > 0 and valid.n_dec > 0


def _net_on(shard):
    net = SN.SetNet.flagged_from(SN.SetNet.load(NET))
    train, valid = RK.load([shard / "rank-74100038.npz"], shard / "cards.npz", every=2)
    SN.extend_table(net, train.card_ids, train.static)
    SN.extend_table(net, valid.card_ids, valid.static)
    for d in (train, valid):
        index = {int(c): i for i, c in enumerate(net.card_ids)}
        d.cards = np.asarray([index[int(c)] for c in d.card_ids], np.int32)[d.cards]
    return net, train, valid


def test_rank_gradient_matches_finite_differences(shard):
    net, train, _ = _net_on(shard)
    net.V1[-1] = np.linspace(-0.2, 0.2, net.V1.shape[1])
    decs = np.arange(min(6, train.n_dec))
    loss, g = net.rank_grads(train, decs, weight=0.7)
    rows, b, o = net._pairs(train, decs)
    assert len(b) == len(o) == len(rows) - len(decs)
    for name, at in (("v3", (3,)), ("V2", (5, 7)), ("W1d", (2, 4)), ("V1", (-1, 9))):
        w = getattr(net, name)
        old = w[at]
        w[at] = old + 1e-6
        up = net.rank_grads(train, decs, weight=0.7)[0]
        w[at] = old - 1e-6
        down = net.rank_grads(train, decs, weight=0.7)[0]
        w[at] = old
        assert abs((up - down) / 2e-6 - g[name][at]) < 1e-6 * max(1.0, abs(g[name][at])) + 1e-8


def test_value_gradient_is_the_one_before(shard):
    """grads is forward + backward: the same numbers as the loss's finite differences (and as before the split)."""
    net, train, _ = _net_on(shard)
    idx = np.arange(min(40, train.n))
    y = np.linspace(0.1, 0.9, len(idx))
    loss, g = net.grads(train.batch(idx), y, 1e-5)
    for name, at in (("c3", (0,)), ("W2", (1, 2)), ("W1s", (3, 5))):
        w = getattr(net, name)
        old = w[at]
        w[at] = old + 1e-6
        up = net.grads(train.batch(idx), y, 0.0)[0] + 1e-5 * sum(float((getattr(net, k) ** 2).sum()) for k in
                                                                ("W1s", "W1d", "W2", "V1", "V2", "v3"))
        w[at] = old - 1e-6
        down = net.grads(train.batch(idx), y, 0.0)[0] + 1e-5 * sum(float((getattr(net, k) ** 2).sum()) for k in
                                                                  ("W1s", "W1d", "W2", "V1", "V2", "v3"))
        w[at] = old
        assert abs((up - down) / 2e-6 - g[name][at]) < 1e-5 * max(1.0, abs(g[name][at])) + 1e-8


def test_fit_with_ranking_lowers_its_loss_and_resumes_exactly(shard, tmp_path):
    net, train, valid = _net_on(shard)
    before = net.rank_score(train)
    table = net.card_ids.copy(), net.static.copy()
    probe = SN.SetNet.flagged_from(SN.SetNet.load(NET))           # the ranking term alone moves the rank loss down
    probe.card_ids, probe.static = table
    probe.fit(train, None, epochs=4, batch=64, lr=3e-3, rank=train, rank_weight=10.0, rank_batch=8, log=lambda s: None)
    assert probe.rank_score(train)["loss"] < before["loss"] - 0.02
    net.fit(train, valid, epochs=3, batch=64, lr=3e-3, patience=9, rank=train, rank_valid=valid, rank_batch=8,
            log=lambda s: None)
    row = net.info["history"][-1]
    assert "train_rank" in row and "valid_rank_top1" in row and "valid_criterion" in row
    # resume: 1 epoch + resume to 3 = 3 straight
    ck = tmp_path / "ck.npz"
    b = SN.SetNet.flagged_from(SN.SetNet.load(NET))
    b.card_ids, b.static = table
    b.fit(train, valid, epochs=1, batch=64, lr=3e-3, patience=9, rank=train, rank_valid=valid, rank_batch=8,
          log=lambda s: None, checkpoint=ck)
    b.fit(train, valid, epochs=3, batch=64, lr=3e-3, patience=9, rank=train, rank_valid=valid, rank_batch=8,
          log=lambda s: None, checkpoint=ck)
    for k in net.PARAMS:
        assert np.array_equal(getattr(net, k), getattr(b, k)), k


def test_strength_model_and_advantage_labels():
    games = {}
    rng = np.random.default_rng(0)
    for k in range(3000):                          # deck A beats B 75% of the time, whichever seat
        seat_a = int(k % 2)
        names = ("A", "B") if seat_a == 0 else ("B", "A")
        winner = seat_a if rng.random() < 0.75 else 1 - seat_a
        games[k] = (names[0], names[1], int(rng.random() < 0.5), winner)
    model = RK.strength(games, list(games))
    assert model["s"]["A"] - model["s"]["B"] > 0.8
    p = RK.predicted(model, games, [0, 0, 1], [0, 1, 0])
    assert abs(p[0] + p[1] - 1) < 1e-12 and p[0] > 0.65 and p[2] < 0.35        # game 1: B in seat 0
    assert np.allclose(RK.advantage([1.0, 0.0, 0.5], [0.75, 0.25, 0.5]), [0.625, 0.375, 0.5])
    assert RK.predicted(model, {9: ("X", "Y", 0, 0)}, [9], [0])[0] == pytest.approx(
        1 / (1 + np.exp(-(model["b"] + model["c"]))))                             # unknown decks: strength 0
