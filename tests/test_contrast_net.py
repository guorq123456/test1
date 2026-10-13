"""The step-1 network (learn.contrast_net): gradients, inference against the batch, the clock features' cost."""
import numpy as np
import pytest

from test_handvalue import _positions


def _setup(n_states=16, seed=0):
    from svsim.cards import decks
    from svsim.learn.contrast import features_of
    from svsim.learn.contrast_net import ContrastNet, encode, stack
    from svsim.learn.fit import standardize
    from svsim.search.evaluate import after_end_of_turn
    positions, _ = _positions(n_games=2)
    ends = [(after_end_of_turn(s), p) for s, p in positions[4:] if not after_end_of_turn(s).over][:n_states]
    lin = [features_of(e, p, 2, ("clock",)) for e, p in ends]
    X = np.array(lin, float)
    from svsim.learn.contrast import feature_names
    names = feature_names(2, ("clock",))
    b = names.index("bias")
    mean, std = standardize(X, b)
    net = ContrastNet(sorted({d.card_id for d in decks.build(decks.RAMP_DRAGON)}), mean, std, b, embed=3, field=4,
                      hand=3, hidden=5, seed=seed)
    rng = np.random.default_rng(seed)
    for k in net.PARAMS:                                        # away from zero, so every path carries a gradient
        setattr(net, k, getattr(net, k) + rng.normal(0, 0.2, getattr(net, k).shape))
    net.Ef[0] = net.Eh[0] = 0.0
    encs = [encode(e, p, x) for (e, p), x in zip(ends, lin)]
    return net, ends, lin, encs, stack


def test_the_gradients_match_finite_differences():
    net, ends, lin, encs, stack = _setup()
    half = len(encs) // 2
    A, B = net.prepare(stack(encs[:half])), net.prepare(stack(encs[half:2 * half]))
    C = net.prepare(stack(encs))
    rng = np.random.default_rng(1)
    dT, w, y = rng.normal(0, 0.1, half), rng.uniform(0.5, 2, half), rng.integers(0, 2, len(encs)).astype(float)
    _, g = net.loss_and_grads(A, B, dT, w, C, y, mu=0.3, l2=1e-3)
    for name in net.PARAMS:
        P = getattr(net, name)
        flat = P.reshape(-1)
        for j in rng.choice(flat.size, size=min(5, flat.size), replace=False):
            if name in ("Ef", "Eh") and j < P.shape[1]:
                continue
            keep = flat[j]
            flat[j] = keep + 1e-6
            up = net.loss_and_grads(A, B, dT, w, C, y, mu=0.3, l2=1e-3)[0]
            flat[j] = keep - 1e-6
            down = net.loss_and_grads(A, B, dT, w, C, y, mu=0.3, l2=1e-3)[0]
            flat[j] = keep
            num = (up - down) / 2e-6
            assert abs(num - g[name].reshape(-1)[j]) <= 2e-5 + 1e-3 * abs(num), (name, j)


def test_inference_is_the_batch_of_one_and_a_follower_or_hand_card_moves_it():
    from svsim.core import effects as E
    net, ends, lin, encs, stack = _setup(seed=2)
    batch = net.forward(net.prepare(stack(encs)))
    for (e, p), x, z in zip(ends, lin, batch):
        assert net.logit(e, p, x) == pytest.approx(z, abs=1e-5)
    e, p = next((e, p) for e, p in ends if e.players[0].followers or e.players[1].followers)
    x = lin[ends.index((e, p))]
    f = (e.players[0].followers or e.players[1].followers)[0]
    e2 = e.clone()
    g = next(c for c in e2.players[0].field + e2.players[1].field if c.uid == f.uid)
    g.atk += 3
    assert abs(net.logit(e2, p, x) - net.logit(e, p, x)) > 1e-6       # the same linear part: the set encoder sees it


def test_the_clock_features_are_cheap_and_bounded():
    import time
    from svsim.learn.features import extra_features, features
    positions, _ = _positions(n_games=2)
    for s, p in positions:
        mb, ob, mc, oc, lead = extra_features(s, p, ("clock",))
        assert mb >= 0 and ob >= 0 and 0 <= mc <= 10 and 0 <= oc <= 10 and lead == pytest.approx(oc - mc)
    t = time.perf_counter()
    for s, p in positions * 3:
        extra_features(s, p, ("clock",))
    tc = time.perf_counter() - t
    t = time.perf_counter()
    for s, p in positions * 3:
        features(s, p, False, 2)
    assert tc < (time.perf_counter() - t)                              # cheaper than the version-2 features


def test_the_lethal_clock_features_are_bounded_and_cheap():
    import time
    from svsim.learn.features import _near, extra_features, features
    from svsim.search.evaluate import effective_hp
    positions, _ = _positions(n_games=2)
    for s, p in positions:
        mt, ot, lead, op_lead, me_lead, op_near, me_near = extra_features(s, p, ("kclock",))
        me_hp, op_hp = max(effective_hp(s.players[p]), 0), max(effective_hp(s.players[1 - p]), 0)
        assert 0 <= mt <= 10 and 0 <= ot <= 10 and lead == pytest.approx(ot - mt)
        assert op_lead == pytest.approx(op_hp * lead) and me_lead == pytest.approx(me_hp * lead)
        assert op_near == pytest.approx(op_hp * _near(mt)) and me_near == pytest.approx(me_hp * _near(ot))
    assert (_near(0.5), _near(2.0), _near(3.0)) == (1.0, 0.5, 0.0)
    for s, p in positions:                                             # measure the cards first
        extra_features(s, p, ("kclock",))
    t = time.perf_counter()
    for s, p in positions * 3:
        extra_features(s, p, ("kclock",))
    tc = time.perf_counter() - t
    t = time.perf_counter()
    for s, p in positions * 3:
        features(s, p, False, 2)
    assert tc < (time.perf_counter() - t)                              # cheaper than the version-2 features
