"""Turn-level step 1 (learn.contrast): the contrast trainer and the teacher-line replay."""
import json

import numpy as np
import pytest

from test_handvalue import _positions


def _synthetic(seed=0, pairs=3000, calib=4000):
    """Features with the bias column in the middle (index 3) and two 'extras' after it, as learn.phased lays
    them out; true per-unit coefficients beta and intercept b0."""
    rng = np.random.default_rng(seed)
    beta = np.array([0.8, -0.5, 0.3, 0.0, 0.6, -0.4])           # index 3 is the bias column
    b0 = -0.3

    def draw(n):
        X = rng.normal([1, 2, 0, 0, 5, -1], [1, 2, 3, 1, 2, 1], size=(n, 6))
        X[:, 3] = 1.0
        return X
    z = lambda X: X @ beta + b0
    s = lambda v: 1 / (1 + np.exp(-v))
    XA, XB = draw(pairs), draw(pairs)
    dT = s(z(XA)) - s(z(XB)) + rng.normal(0, 0.02, pairs)
    XC = draw(calib)
    yc = (rng.uniform(size=calib) < s(z(XC))).astype(float)
    return XA, XB, dT, XC, yc, beta, b0, z, draw


def test_the_contrast_fit_finds_known_coefficients_and_with_results_the_intercept():
    from svsim.learn.contrast import fit_contrast
    XA, XB, dT, XC, yc, beta, b0, z, draw = _synthetic()
    model, report = fit_contrast(XA, XB, dT, None, XC, yc, mu=1.0, l2=0.0, iters=3000, bias=3)
    per_unit = model.w / model.std
    others = [0, 1, 2, 4, 5]
    assert np.allclose(per_unit[others], beta[others], atol=0.08)
    Xn = draw(2000)
    assert np.max(np.abs(model.forward(model.standardize(Xn)) - z(Xn))) < 0.35
    assert report["intercept_fitted"] and report["sign_agreement"] > 0.9


def test_pure_contrasts_hold_the_intercept_where_it_is_given():
    """Without results the contrasts barely see the intercept: it is held at fix_bias (default 0), never fitted;
    given the true one, the slopes come back."""
    from svsim.learn.contrast import fit_contrast
    XA, XB, dT, XC, yc, beta, b0, z, draw = _synthetic(seed=1)
    free, rep = fit_contrast(XA, XB, dT, None, None, None, mu=0.0, l2=0.0, iters=3000, bias=3)
    assert free.w[3] == 0.0 and not rep["intercept_fitted"]
    true_std_intercept = b0 + float(np.sum(beta[[0, 1, 2, 4, 5]] * free.mean[[0, 1, 2, 4, 5]]))
    held, _ = fit_contrast(XA, XB, dT, None, None, None, mu=0.0, l2=0.0, iters=3000, bias=3,
                           fix_bias=true_std_intercept)
    assert held.w[3] == true_std_intercept
    assert np.allclose((held.w / held.std)[[0, 1, 2, 4, 5]], beta[[0, 1, 2, 4, 5]], atol=0.1)


def test_replay_follows_keys_ends_at_T_and_hands_over_on_a_mismatch():
    from svsim.core.actions import EndTurn
    from svsim.learn.contrast import replay_turn
    from svsim.search.mcts import _locator, action_key
    from svsim.agents.crossturn_agent import principal_line
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    positions, _ = _positions()
    state, player = next((s, p) for s, p in positions[8:] if len(s.players[p].hand) >= 2)
    search = _search(make_agent("mcts:40+learned+phased", 3))
    search.choose(state.clone())
    keys = principal_line(search.last_root)
    acts, end = replay_turn(state, keys)
    s = state.clone()
    from svsim.core.engine import apply
    for k, a in zip(keys, acts):
        assert (k == ("T",) and isinstance(a, EndTurn)) or action_key(s, a, _locator(s, player)) == k
        if isinstance(a, EndTurn):
            break
        apply(s, a)
    assert isinstance(acts[-1], EndTurn)
    called = []
    acts2, _ = replay_turn(state, [("P", ("H", True, -1, 0), (), None)],
                           lambda s, legal: called.append(1) or EndTurn())
    assert called and acts2 == [EndTurn()]


def test_teacher_pairs_keep_the_card_and_replay_from_the_record(tmp_path):
    """A teacher row's keep:<card> against the line: the restricted turn doesn't play the card, both turns replay
    from the record to their ends; the fit command writes a turn-end model learn.phased reads."""
    import subprocess
    import sys
    from svsim.core.actions import PlayCard, from_dict
    from svsim.core.engine import apply
    from svsim.learn.contrast import pairs_for_position, teacher_lines, turn_end_of
    from svsim.search.lethal import state_key
    from svsim.tools import records as R
    kw = dict(samples=1, research=8, next_search=0)
    _, records = _positions(n_games=2)
    rec = dict(records[0], g=1)
    found = None
    for i, (st, _) in enumerate(R.steps(rec)):
        if st.phase.name == "MAIN" and i > 6 and st.players[st.active].hand:
            lines = teacher_lines(st.clone(), 7, **kw)
            keeps = [r for r in lines if r.startswith("keep:")]
            if keeps:
                found = (i, st.clone(), keeps[0])
                break
    assert found
    at, state, r = found
    row = {"seed": 7, "res": {r: {"teacher": 0.05, "se": 0.01}}}
    pairs = pairs_for_position(state, [row], spec_bot="mcts:20+plan+learned+phased", **kw)
    assert len(pairs) == 1 and pairs[0]["restriction"] == r and pairs[0]["dT"] == 0.05
    cid = int(r.split(":")[1])
    s = state.clone()
    for d in pairs[0]["a"]:
        a = from_dict(d)
        if isinstance(a, PlayCard):
            card = s.in_hand(s.active, a.uid)
            assert card is None or card.defn.card_id != cid
        if a.__class__.__name__ == "EndTurn":
            break
        apply(s, a)
    end_a = turn_end_of(rec, at, pairs[0]["a"])
    assert state_key(end_a) == state_key(turn_end_of(rec, at, pairs[0]["a"]))
    games = tmp_path / "selfplay.jsonl"
    games.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    pfile = tmp_path / "pairs.jsonl"
    pfile.write_text(json.dumps(dict(pairs[0], g=1, at=at, player=state.active)) + "\n", encoding="utf-8")
    out = tmp_path / "cand"
    done = subprocess.run([sys.executable, "-m", "svsim.learn.contrast", "fit", "--pairs", str(pfile), "--selfplay",
                           str(games), "--out", str(out), "--iters", "50", "--hold-out-every", "0",
                           "--act-from", "svsim/learn/phased_models"], check=True, capture_output=True, text=True)
    report = json.loads(done.stdout.strip().splitlines()[-1])
    assert report["pairs"] == 1 and report["intercept_fitted"]
    from svsim.learn.phased import load
    models = load(out)
    ended = next(m for k, m in models.items() if k[2] == "ended")
    assert len(models) == 2 and ended.info["contrast"] is True and ended.info["report"]["pairs"] == 1
