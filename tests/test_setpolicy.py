"""learn.setpolicy: the move prior over card tokens (the architecture thread 2026-10-17 11:37Z, step 1)."""
import gzip
import json
import os
from pathlib import Path

import numpy as np
import pytest

from svsim.core.actions import Attack, PlayCard
from svsim.learn import setpolicy as SP
from svsim.learn import tokens as T
from svsim.learn.setnet import SetNet

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "analysis/scaling/data/elf-t3/rec/rec-74100038.jsonl.gz"


def _records(n):
    with gzip.open(REC, "rt") as fh:
        return [json.loads(next(fh)) for _ in range(n)]


@pytest.fixture(scope="module")
def shard(tmp_path_factory):
    """Two games of the gen-3 holdout encoded as a dec- file, with a static table."""
    d = tmp_path_factory.mktemp("dec")
    recs = d / "rec-74100038.jsonl.gz"
    with gzip.open(recs, "wt") as fh:
        for r in _records(2):
            fh.write(json.dumps(r) + "\n")
    SP._encode_shard((str(recs), d / "dec-74100038.npz"))
    z = np.load(d / "dec-74100038.npz")
    ids = sorted({int(c) for c in z["cards"]})
    defs = {}
    for r in _records(2):
        for _, state, *_ in SP.decisions(r):
            for p in state.players:
                for c in p.hand + p.field + p.leader_area + p.deck_view():
                    defs[c.defn.card_id] = c.defn
    np.savez(d / "cards.npz", card_id=np.asarray(ids, np.int64), static=np.stack([T.static(defs[c]) for c in ids]))
    return d


def test_rows_point_at_the_acting_cards_token():
    seen = 0
    for i, state, legal, reps, group, pi, start in SP.decisions(_records(1)[0]):
        me = state.active
        cards, toks, _ = T.encode(state, me)
        rows = SP.rows_of(state, me)
        kind, tkind, src, tgt, extras = SP.move_arrays(state, reps, rows)
        for j, a in enumerate(reps):
            if isinstance(a, PlayCard):
                assert toks[src[j], 0] == 0 and cards[src[j]] == state.in_hand(me, a.uid).defn.card_id
                seen += 1
            if isinstance(a, Attack):
                assert toks[src[j], 0] == 1 and cards[src[j]] == state.in_play(a.attacker).defn.card_id
                if a.target >= 0:
                    assert toks[tgt[j], 0] == 4 and cards[tgt[j]] == state.in_play(a.target).defn.card_id
                else:
                    assert tgt[j] == -1 and tkind[j] == 1
                seen += 1
        assert abs(pi.sum() - 1) < 1e-9 and len(group) == len(legal) and max(group) == len(reps) - 1
    assert seen > 50


def test_same_moves_share_one_visit_count():
    """Two legal moves with one action key are one move; the record gives both the child's count."""
    from svsim.search.mcts import _locator, action_key
    found = 0
    rec = _records(2)
    for r in rec:
        thoughts = r["search"]
        for i, state, legal, reps, group, pi, start in SP.decisions(r):
            if len(reps) < len(legal):
                where = _locator(state, state.active)
                keys = [action_key(state, a, where) for a in legal]
                for j, k in enumerate(keys):
                    assert thoughts[i]["visits"][j] == thoughts[i]["visits"][keys.index(k)]
                found += 1
    assert found > 0


def _tiny(shard, freeze_init=True, seed=3):
    data = SP.Decisions([shard / "dec-74100038.npz"], shard / "cards.npz")
    pol = SP.SetPolicy(data.static.shape[1], phi=(5, 4), rho=(6, 5), head=3, seed=seed)
    pol.card_ids, pol.static = data.card_ids, data.static.astype(np.float64)
    pol.smean, pol.sstd = pol.static.mean(0), pol.static.std(0) + 1e-3
    rng = np.random.default_rng(seed)
    for k in SP.SetPolicy.PARAMS:                     # biases off zero: no unit sits at a ReLU kink
        a = getattr(pol, k)
        setattr(pol, k, a + rng.normal(0, 0.05, a.shape))
    return data, pol


@pytest.mark.parametrize("freeze", [False, True])
def test_gradients_match_finite_differences(shard, freeze):
    data, pol = _tiny(shard)
    b = data.batch(np.arange(min(12, data.n)))
    loss, g = pol.grads(b, l2=1e-3, freeze=freeze)
    assert set(g) == (set(SP.HEAD) if freeze else set(SP.SetPolicy.PARAMS))
    rng = np.random.default_rng(0)

    def f():
        s = pol.forward(b)
        p = SP.seg_softmax(s, b["mstart"])
        reg = sum(np.sum(getattr(pol, k) ** 2) for k in (SP.HEAD[:2] + ("w",) if freeze else
                                                       ("W1s", "W1d", "W2", "V1", "V2", "A", "M", "w")))
        return -np.sum(b["pi"] * np.log(p + 1e-12)) / len(b["glob"]) + 1e-3 * reg

    assert abs(f() - loss - 1e-3 * sum(np.sum(getattr(pol, k) ** 2) for k in (
        ("A", "M", "w") if freeze else ("W1s", "W1d", "W2", "V1", "V2", "A", "M", "w")))) < 1e-9
    for k in g:
        a = getattr(pol, k)
        for _ in range(4):
            ix = tuple(rng.integers(0, n) for n in a.shape)
            old = a[ix]
            a[ix] = old + 1e-6
            up = f()
            a[ix] = old - 1e-6
            down = f()
            a[ix] = old
            num = (up - down) / 2e-6
            assert abs(num - g[k][ix]) < 1e-5 * max(1.0, abs(num)), (k, ix, num, g[k][ix])


def test_one_position_equals_the_batch(shard):
    data, pol = _tiny(shard)
    whole = pol.evaluate(data)
    r = _records(1)[0]
    n = 0
    for (i, state, legal, reps, group, pi, start), d in zip(SP.decisions(r), range(data.n)):
        assert data.g[d] == r["g"] and data.step[d] == i
        p = pol.priors(state, legal)
        lo, hi = data.moff[d], data.moff[d + 1]
        per = np.zeros(len(reps))
        np.add.at(per, group, p)
        assert np.allclose(per, whole[lo:hi], rtol=0, atol=1e-12) and abs(p.sum() - 1) < 1e-12
        n += 1
    assert n > 20


def test_trunk_from_a_value_net_is_the_value_nets(shard):
    """With the value net's trunk, the position vector h is the value net's last hidden layer at that position."""
    net = SetNet.load(ROOT / "analysis/scaling/models/net-elft-gen3-29000.npz")
    pol = SP.SetPolicy.from_value_net(net)
    data = SP.Decisions([shard / "dec-74100038.npz"], shard / "cards.npz")
    pol.card_ids, pol.static = data.card_ids, data.static.astype(np.float64)
    b = data.batch(np.arange(8))
    _, (S, H1, H2, U, Z1, Z2, Mv, Ah) = pol.forward(b, keep=True)
    net.card_ids, net.static = data.card_ids, data.static.astype(np.float64)
    out, (_, _, _, _, nZ1, nZ2) = net.forward(b["cards"], b["dyn"], b["count"], b["seg"], b["glob"], keep=True)
    assert np.allclose(Z2, nZ2, rtol=0, atol=1e-12)


def test_frozen_fit_keeps_the_trunk_and_save_load_round_trips(shard, tmp_path):
    data, pol = _tiny(shard)
    trunk = {k: getattr(pol, k).copy() for k in SP.TRUNK}
    before = pol.cross_entropy(data)
    pol.fit(data, data, epochs=3, batch=16, freeze=True, log=lambda s: None)
    assert all(np.array_equal(trunk[k], getattr(pol, k)) for k in SP.TRUNK)
    assert pol.cross_entropy(data) < before
    pol.save(tmp_path / "p.npz")
    back = SP.SetPolicy.load(tmp_path / "p.npz")
    assert np.array_equal(back.evaluate(data), pol.evaluate(data))


def test_fit_resumes_exactly_from_its_checkpoint(shard, tmp_path):
    data, a = _tiny(shard)
    a.fit(data, data, epochs=3, batch=16, log=lambda s: None)
    _, b = _tiny(shard)
    ck = tmp_path / "ck.npz"
    b.fit(data, data, epochs=1, batch=16, log=lambda s: None, checkpoint=ck)
    _, c = _tiny(shard)
    c.fit(data, data, epochs=3, batch=16, log=lambda s: None, checkpoint=ck)
    assert all(np.array_equal(getattr(a, k), getattr(c, k)) for k in SP.SetPolicy.PARAMS)



@pytest.mark.skipif(not os.path.isdir("/proc/self/fd"), reason="needs /proc/self/fd")
def test_resuming_leaves_no_handle_on_the_checkpoint_it_replaces(shard, tmp_path, monkeypatch):
    """As learn.setnet's: a resumed fit must not keep its checkpoint open when an epoch replaces it (Windows)."""
    from tests.fd_probe import open_handles, watch_replace
    data, b = _tiny(shard)
    ck = tmp_path / "ck.npz"
    b.fit(data, data, epochs=1, batch=16, log=lambda s: None, checkpoint=ck)
    seen = watch_replace(monkeypatch)
    _, c = _tiny(shard)
    c.fit(data, data, epochs=3, batch=16, log=lambda s: None, checkpoint=ck)
    assert seen and all(n == 0 for n in seen)
    c.save(tmp_path / "p.npz")
    SP.SetPolicy.load(tmp_path / "p.npz")
    assert open_handles(tmp_path / "p.npz") == 0

def test_tau_half_squares_the_visits_per_decision(shard):
    data = SP.Decisions([shard / "dec-74100038.npz"], shard / "cards.npz")
    before = data.pi.astype(np.float64).copy()
    data.sharpen(0.5)
    for d in range(data.n):
        lo, hi = data.moff[d], data.moff[d + 1]
        want = before[lo:hi] ** 2 / np.sum(before[lo:hi] ** 2)
        assert np.allclose(data.pi[lo:hi], want, atol=1e-6) and abs(data.pi[lo:hi].sum() - 1) < 1e-5
    same = SP.Decisions([shard / "dec-74100038.npz"], shard / "cards.npz")
    same.sharpen(1.0)
    assert np.array_equal(same.pi, before.astype(np.float32))


def test_split_file_by_file_equals_the_mask_on_the_whole(shard):
    whole = SP.Decisions([shard / "dec-74100038.npz"] * 2, shard / "cards.npz")
    v = whole.games() % 3 == 0
    train, valid = SP.Decisions.split([shard / "dec-74100038.npz"] * 2, shard / "cards.npz", every=3)
    for got, want in ((train, whole.subset(~v)), (valid, whole.subset(v))):
        for k in ("tokens", "cards", "globals", "offsets", "moff", "kind", "tkind", "src", "tgt", "extras", "pi",
                  "seed", "g", "step"):
            assert np.array_equal(getattr(got, k), getattr(want, k)), k
    assert train.n + valid.n == whole.n and valid.n > 0


def test_prior_continues_from_all_its_weights_and_checks_its_card_table(shard, tmp_path):
    import argparse
    data, pol = _tiny(shard)
    pol.fit(data, data, epochs=1, batch=16, log=lambda s: None)
    path = tmp_path / "prior.npz"
    pol.save(path)
    args = argparse.Namespace(prior=str(path), head=3, freeze=False, tau=0.5, shards=[74100038])
    got = SP._prior_to_continue(args, data.card_ids, data.static)
    for k in SP.SetPolicy.PARAMS + ("smean", "sstd", "card_ids", "static"):
        assert np.array_equal(getattr(got, k), getattr(pol, k))
    assert got.info["prior"] == str(path) and got.info["tau"] == 0.5
    with pytest.raises(SystemExit):                                        # another head width
        SP._prior_to_continue(argparse.Namespace(**{**vars(args), "head": 64}), data.card_ids, data.static)
    with pytest.raises(SystemExit):                                        # another card table
        SP._prior_to_continue(args, data.card_ids[::-1], data.static[::-1])


def test_a_prior_grown_to_a_new_pairing_records_where_it_came_from(shard, tmp_path):
    """--prior --extend-cards: the info names this fit (the prior and its sha256, the shards, the side), not the
    prior's own start; the weights are the prior's."""
    import argparse
    import hashlib
    data, pol = _tiny(shard)
    pol.info = {**pol.info, "init": "old-net.npz", "shards": [1, 2], "deck": "ramp-t", "opponent": "nemesis-t"}
    path = tmp_path / "prior.npz"
    pol.save(path)
    args = argparse.Namespace(prior=str(path), head=3, freeze=False, tau=0.5, shards=[74100038], extend_cards=True,
                              deck="nemesis-t", opponent="elf-t")
    got = SP._prior_to_continue(args, data.card_ids[::-1], data.static[::-1])     # another table: grown, not refused
    for k in SP.SetPolicy.PARAMS + ("smean", "sstd", "card_ids", "static"):
        assert np.array_equal(getattr(got, k), getattr(pol, k))
    assert "init" not in got.info and got.info["shards"] == [74100038]
    assert got.info["prior_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert (got.info["deck"], got.info["opponent"]) == ("nemesis-t", "elf-t")
    plain = SP._prior_to_continue(argparse.Namespace(**{**vars(args), "deck": None, "opponent": None}),
                                  data.card_ids, data.static)
    assert (plain.info["deck"], plain.info["opponent"]) == ("ramp-t", "nemesis-t")


@pytest.mark.parametrize("start", [[], ["--init", "N", "--prior", "P"]])
def test_fit_starts_from_exactly_one_of_a_value_net_or_a_prior(monkeypatch, start):
    import sys
    monkeypatch.setattr(SP, "fit_main", lambda args: None)
    monkeypatch.setattr(sys, "argv", ["setpolicy", "fit", "--data", "D", "--cards", "C", "--shards", "1",
                                      "--out", "O"] + start)
    with pytest.raises(SystemExit):
        SP.main()
