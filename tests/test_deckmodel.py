import numpy as np

from svsim.learn.deckmodel import DeckModel


def test_gradients_match_finite_differences():
    rng = np.random.default_rng(1)
    m = DeckModel(6, 4, 3, seed=2)
    X, Cm, Co, y = rng.normal(size=(10, 6)), rng.random((5, 10)) / 4, rng.random((5, 10)) / 4, rng.random(5)

    def loss():
        p = 1 / (1 + np.exp(-m.forward(X, Cm, Co)[0]))
        return np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p)))

    logit, cache = m.forward(X, Cm, Co)
    g = m.backward((1 / (1 + np.exp(-logit)) - y) / 5, cache)
    for k, w in m.p.items():
        for i in np.ndindex(w.shape):
            old = w[i]
            w[i] = old + 1e-6
            a = loss()
            w[i] = old - 1e-6
            b = loss()
            w[i] = old
            assert abs((a - b) / 2e-6 - g[k][i]) < 1e-6


def test_a_deck_against_itself_and_saved_model(tmp_path):
    from svsim.cards.pool import POOL
    from svsim.learn.deckmodel import static_rows
    ids = sorted(POOL)[:200]
    m = DeckModel(static_rows(ids[:1]).shape[1], 8, 8, seed=3)
    m.mu = static_rows(ids).mean(0)
    deck = [ids[100 + i // 3] for i in range(40)]
    other = [ids[150 + i // 3] for i in range(40)]
    p = m.predict([deck, other], [other, deck])
    m.save(str(tmp_path / "m.npz"))
    assert np.allclose(DeckModel.load(str(tmp_path / "m.npz")).predict([deck, other], [other, deck]), p)


def test_a_feature_never_seen_to_change_reads_0():
    m = DeckModel(3, 4, 4, seed=1)
    X = np.array([[1.0, 0.0, 2.0], [3.0, 0.0, 2.5], [2.0, 0.0, 4.0]])
    m.set_scale(X)
    Z = m.standardize(np.array([[2.0, 1.0, 100.0]]))       # a new card: column 1 never varied, column 2 far out
    assert Z[0, 1] == 0.0 and Z[0, 2] == m.standardize(X)[:, 2].max()
