"""The hand-value student (learn.handvalue): structure, gradients, the search's unknown cards, the feature."""
import json

import numpy as np
import pytest


def _positions(n_games=1, seed=5, deck="ramp"):
    """(state, player) at each player's first main-phase decision of a turn, from short self-play games."""
    from svsim.learn.netdata import play
    from svsim.tools import records as R
    out, records = [], []
    for g in range(n_games):
        record = play((g, seed + g, deck, deck, "mcts:5+plan", 0.0))
        records.append(record)
        seen = set()
        for state, _ in R.steps(record):
            if state.phase.name != "MAIN":
                continue
            key = (state.active, state.turn)
            if key in seen:
                continue
            seen.add(key)
            out.append((state.clone(), state.active))
    return out, records


def _student(seed=0, vocab=None):
    from svsim.cards import decks
    from svsim.learn.handvalue import HandValue
    vocab = vocab or sorted({d.card_id for d in decks.build(decks.RAMP_DRAGON)})
    return HandValue(vocab, embed=4, width=8, hidden=8, seed=seed)


def _with_hand(state, player, defns, pp=None, max_pp=None):
    """A copy of `state` whose `player` holds exactly `defns` (new cards), play points as given."""
    from svsim.core import effects as E
    s = state.clone()
    p = s.players[player]
    p.hand.clear()
    for d in defns:
        E.add_to_hand(s, player, d)
    if max_pp is not None:
        p.max_pp = max_pp
    if pp is not None:
        p.pp = pp
    return s


def test_the_gradients_match_finite_differences():
    student = _student(seed=3)
    positions, _ = _positions()
    rng = np.random.default_rng(0)
    ex = []
    for state, player in positions[4:16]:
        hand = state.players[player].hand
        if hand:
            c = hand[rng.integers(len(hand))]
            ex.append(student.example(state, player, c.uid, float(rng.normal()), float(rng.uniform(0.5, 2))))
    batch = student.batch(ex)
    _, g = student.loss_and_grads(*batch, l2=1e-3)
    for name in student.PARAMS:
        P = getattr(student, name)
        flat = P.reshape(-1)
        for j in rng.choice(flat.size, size=min(5, flat.size), replace=False):
            if name == "E" and j < P.shape[1]:
                continue                                  # the never-seen row is held at zero
            keep = flat[j]
            flat[j] = keep + 1e-6
            up = student.loss_and_grads(*batch, l2=1e-3)[0]
            flat[j] = keep - 1e-6
            down = student.loss_and_grads(*batch, l2=1e-3)[0]
            flat[j] = keep
            num = (up - down) / 2e-6
            assert abs(num - g[name].reshape(-1)[j]) <= 1e-5 + 1e-4 * abs(num), (name, j)


def test_the_same_card_is_worth_different_amounts_at_2_and_9_play_points():
    """The design's second test: one card's marginal value moves with the play points (an untrained student
    already: the structure has no fixed per-card score)."""
    from svsim.cards import decks
    student = _student()
    positions, _ = _positions()
    state, player = positions[6]
    deck = decks.build(decks.RAMP_DRAGON)
    big = max(deck, key=lambda d: d.cost)
    others = [d for d in deck if d.cost <= 3][:3]
    deltas = []
    for pp in (2, 9):
        s = _with_hand(state, player, others + [big], pp=pp, max_pp=pp)
        uid = s.players[player].hand[-1].uid
        deltas.append(student.delta(s, player, uid))
    assert abs(deltas[0] - deltas[1]) > 1e-6


def test_a_card_s_marginal_value_is_not_a_constant_across_positions():
    """Salem's rule: no fixed score per card. The same kind of card, priced in different positions and hands."""
    student = _student(seed=1)
    positions, _ = _positions(n_games=2)
    by_kind: dict = {}
    for state, player in positions:
        for c in state.players[player].hand:
            by_kind.setdefault(c.defn.card_id, []).append(student.delta(state, player, c.uid))
    spread = [np.std(v) for v in by_kind.values() if len(v) >= 3]
    assert spread and min(spread) > 1e-6


def test_removing_or_swapping_a_card_moves_the_score_where_the_installed_model_does_not():
    """The architecture's J13: the installed Ramp mirror model scores a hand by its size, so swapping a card in hand
    for another kind leaves the score where it was; the student's hand value moves, and so does a model with
    the hand_value feature."""
    from svsim.cards import decks
    from svsim.learn.model import LinearValue
    from svsim.learn.phased import PhasedLearned
    from svsim.learn.model import ALIASES, matchup_keys
    student = _student(seed=2)
    positions, _ = _positions()
    state, player = positions[8]
    hand = [c.defn for c in state.players[player].hand]
    assert len(hand) >= 2
    swap = next(d for d in decks.build(decks.RAMP_DRAGON) if d.card_id not in {h.card_id for h in hand})
    a = _with_hand(state, player, hand)
    b = _with_hand(state, player, hand[:-1] + [swap])
    c = _with_hand(state, player, hand[:-1])
    ha, hb, hc = (student.value(s, player) for s in (a, b, c))
    assert abs(ha - hb) > 1e-6 and abs(ha - hc) > 1e-6
    models = PhasedLearned().models
    key = next(k for k in matchup_keys(a, player, ALIASES) if k + ("ended",) in models)
    installed = models[key + ("ended",)]
    assert installed.logit(a, player) == installed.logit(b, player)      # J13: a swap is invisible to it
    n = len(installed.coef)
    with_hv = LinearValue(list(installed.coef) + [1.0], list(installed.mean) + [0.0], list(installed.std) + [1.0],
                          installed.potential, version=installed.version, extras=installed.extras + ("hand_value",),
                          hv=student)
    assert len(with_hv.names()) == n + 1 and with_hv.names()[-1] == "me_hand_value"
    assert abs((with_hv.logit(a, player) - with_hv.logit(b, player)) - (ha - hb)) < 1e-9


def test_cards_drawn_after_the_search_root_are_priced_as_their_pool():
    """Under a search root, a card drawn from the root deck counts as one of its pool, so what a determinization
    drew doesn't move the value; the opponent's hand is all unknown; outside a search every card is known."""
    from svsim.learn.handvalue import root
    student = _student(seed=4)
    positions, _ = _positions()
    state, player = next((s, p) for s, p in positions[6:] if len(s.players[p].deck) >= 2 and s.players[p].hand)
    p = state.players[player]
    root_deck = [c.uid for c in p.deck]
    s1 = state.clone()                                   # draw the top card, and in another world a different one
    q1 = s1.players[player]
    q1.hand.append(q1.deck.pop())
    s2 = state.clone()
    q2 = s2.players[player]
    pick = next(i for i, c in enumerate(q2.deck) if c.defn.card_id != q1.hand[-1].defn.card_id)
    q2.hand.append(q2.deck.pop(pick))
    assert q1.hand[-1].defn.card_id != q2.hand[-1].defn.card_id
    with root(player, root_deck):
        assert student.value(s1, player) == pytest.approx(student.value(s2, player), abs=1e-12)
        other = student.encode(s1, 1 - player)
        assert len(other[1]) == 0 or np.all(other[1][:, -1] == 1.0)
    assert abs(student.h(student.encode(s1, player)) - student.h(student.encode(s2, player))) > 1e-9


def test_the_inputs_hold_no_deck_identity():
    """No deck id, deck key or pairing among the inputs: the same hand and position under another deck name
    scores the same."""
    from svsim.learn.handvalue import CARD, CTX, FIT
    assert not [n for n in CTX + CARD + FIT if "deck_" in n or "pair" in n or n.startswith("deck")]
    student = _student(seed=5)
    positions, _ = _positions()
    state, player = positions[7]
    other = state.clone()
    for q in other.players:
        q.deck_name = "something-else"
    assert student.h(student.encode(state, player)) == student.h(student.encode(other, player))


def test_fitting_learns_a_target_that_depends_on_the_position():
    """A made-up teacher: a card is worth 1 if it can be paid next turn and 0 otherwise. The student fits it on
    one set of positions and gets it on positions it didn't see (well above chance)."""
    student = _student(seed=6)
    positions, _ = _positions(n_games=3)
    rng = np.random.default_rng(1)
    ex = []
    for state, player in positions:
        p = state.players[player]
        nxt = min(p.max_pp + 1, 10)
        for c in p.hand:
            ex.append((student.example(state, player, c.uid, float(c.cost <= nxt)), c.cost <= nxt))
    rng.shuffle(ex)
    cut = len(ex) * 3 // 4
    train, test = [e for e, _ in ex[:cut]], ex[cut:]
    before = student.loss_and_grads(*student.batch([e for e, _ in test]))[0]
    report = student.fit(train, iters=400, lr=0.02, batch=64, holdout=[e for e, _ in test])
    assert report["holdout_loss"] < 0.5 * before
    pos = [student.loss_and_grads(*student.batch([e]))[0] for e, _ in test]
    assert np.mean(pos) == pytest.approx(report["holdout_loss"], rel=1e-6)


def test_a_student_file_round_trips_and_sits_beside_its_models(tmp_path):
    """Saved and read back it scores the same (numpy only, no pickle); in a models folder the <pairing>-hv.npz is
    the student of the models with hand_value, not a value network of its own."""
    from svsim.learn.model import LinearValue
    from svsim.learn.phased import PhasedLearned, load
    student = _student(seed=7)
    positions, _ = _positions()
    path = tmp_path / "ramp-ramp-hv.npz"
    student.save(path)
    back = type(student).load(path)
    for state, player in positions[5:12]:
        assert back.h(back.encode(state, player)) == student.h(student.encode(state, player))
    installed = PhasedLearned().models
    from svsim.learn.model import ALIASES, matchup_keys
    state, player = positions[9]
    key = next(k for k in matchup_keys(state, player, ALIASES) if k + ("ended",) in installed)
    base = installed[key + ("ended",)]
    for moment in ("ended", "act"):
        LinearValue(list(base.coef) + [0.5], list(base.mean) + [0.0], list(base.std) + [1.0], base.potential,
                    version=base.version, extras=base.extras + ("hand_value",), hv=student
                    ).save(tmp_path / f"ramp-ramp-{moment}.json")
    models = load(tmp_path)
    assert set(models) == {key + ("ended",), key + ("act",)}
    m = models[key + ("ended",)]
    assert m.hv is not None and m.extras[-1] == "hand_value"
    assert m.logit(state, player) == pytest.approx(base.logit(state, player) + 0.5 * student.value(state, player))


def test_the_hand_value_feature_needs_a_student():
    from svsim.learn.features import extra_features
    positions, _ = _positions()
    state, player = positions[5]
    with pytest.raises(ValueError):
        extra_features(state, player, ("hand_value",))


def test_fitting_reads_the_draws_of_the_turn_as_unknown(tmp_path):
    """learn.phased with hand_value: the turn's draws are unknown as in the search (the record's turn_starts), and
    --hand-value puts the student beside the fitted models."""
    import subprocess
    import sys
    from svsim.learn.handvalue import root
    from svsim.learn.netdata import ENDED, rows
    from svsim.learn.phased import _rows
    student = _student(seed=8)
    path = tmp_path / "student.npz"
    student.save(path)
    _, records = _positions(n_games=2)
    line = json.dumps(records[0])
    got = _rows((line, 2, 1.0, 1.0, 1.0, (ENDED,), None, ("hand_value",), str(path)))
    starts = records[0]["turn_starts"]
    want = []
    for i, (phase, me, state, result, q) in rows(records[0], with_search=True, index=True):
        if phase != ENDED:
            continue
        start = max((s for s in starts if s["player"] == me and s["i"] <= i), key=lambda s: s["i"])
        with root(me, start["deck"]):
            want.append(student.value(state, me))
    assert [r[2][-1] for r in got] == pytest.approx(want)
    games = tmp_path / "games.jsonl"
    games.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    out = tmp_path / "fit"
    subprocess.run([sys.executable, "-m", "svsim.learn.phased", "--games", str(games), "--matchup", "ramp-ramp",
                    "--features", "hand_value", "--hand-value", str(path), "--out", str(out), "--workers", "1"],
                   check=True, capture_output=True)
    assert (out / "ramp-ramp-hv.npz").read_bytes() == path.read_bytes()
    d = json.loads((out / "ramp-ramp-ended.json").read_text(encoding="utf-8"))
    assert d["extras"] == ["hand_value"] and d["info"]["hand_value"]["file"] == "ramp-ramp-hv.npz"
    bad = subprocess.run([sys.executable, "-m", "svsim.learn.phased", "--games", str(games), "--matchup",
                          "ramp-ramp", "--features", "hand_value", "--out", str(out)], capture_output=True)
    assert bad.returncode != 0


@pytest.mark.skip(reason="waits for the trained student and the analysis line's data for the top-ten #3 position "
                         "(discrimination experiment, 1791317238047 step 53): 留口人魔 +0.69, 留班德 +0.41, "
                         "留 Sloth +0.53, 留 Promoter +0.31 positive; 《世界》的呈现 -0.50 negative")
def test_the_trained_student_agrees_in_sign_on_the_top_ten_position_3():
    pass


def test_the_feature_without_a_model_reads_svsim_hv(tmp_path, monkeypatch):
    """The analysis line's checks call extra_features(state, me, ("hand_value",)) alone: SVSIM_HV names the
    student, a file or a models folder holding <pairing>-hv.npz."""
    from svsim.learn.features import extra_features
    student = _student(seed=9)
    positions, _ = _positions()
    state, player = positions[6]
    student.save(tmp_path / "ramp-ramp-hv.npz")
    for where in (tmp_path / "ramp-ramp-hv.npz", tmp_path):
        monkeypatch.setenv("SVSIM_HV", str(where))
        assert extra_features(state, player, ("hand_value",)) == [pytest.approx(student.value(state, player))]
    monkeypatch.setenv("SVSIM_HV", str(tmp_path / "nowhere"))
    with pytest.raises(ValueError):
        extra_features(state, player, ("hand_value",))


def test_the_analysis_line_s_teacher_data_reads_into_examples(tmp_path):
    """student_data.py's files: positions at own-turn starts, a teacher row per seed with keep:<card id>. T is the
    seeds' mean, the weight 1 / (mean se^2 / seeds); a card not in hand at the turn start (drawn or made during
    the turn) is left out; the split follows positions.jsonl. The fit command runs on them."""
    import subprocess
    import sys
    from svsim.learn.handvalue import examples_from_teacher
    positions, records = _positions(n_games=2)
    records = [dict(r, g=g) for g, r in enumerate(records)]
    sp = tmp_path / "selfplay.jsonl"
    sp.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    from svsim.tools import records as R
    pos_rows, teach_rows, n = [], [], 0
    absent = None
    for rec in records:
        seen = set()
        for i, (state, _) in enumerate(R.steps(rec)):
            key = (state.active, state.turn)
            if state.phase.name != "MAIN" or key in seen:
                continue
            seen.add(key)
            hand = state.players[state.active].hand
            if not hand:
                continue
            absent = absent or next(c.defn.card_id for c in state.players[state.active].deck
                                    if c.defn.card_id not in {h.defn.card_id for h in hand})
            pos_rows.append({"n": n, "g": rec["g"], "at": i, "seat": state.active,
                             "split": "val" if n % 3 == 0 else "train"})
            cid = hand[0].defn.card_id
            res0 = {f"keep:{cid}": {"teacher": 0.2, "se": 0.1}}
            res1 = {f"keep:{cid}": {"teacher": 0.4, "se": 0.3}}
            if not any(h.defn.card_id == absent for h in hand):
                res0[f"keep:{absent}"] = {"teacher": 9.0, "se": 0.1}       # drawn during the turn: dropped
            if len(hand) >= 2 and hand[1].defn.card_id != cid:          # the restriction changed nothing: dropped
                same = {"teacher": 0.0, "se": 0.0}
                res0[f"keep:{hand[1].defn.card_id}"] = res1[f"keep:{hand[1].defn.card_id}"] = same
            teach_rows += [{"n": n, "s": 0, "res": res0}, {"n": n, "s": 1, "res": res1}]
            n += 1
    (tmp_path / "positions.jsonl").write_text("\n".join(json.dumps(p) for p in pos_rows) + "\n", encoding="utf-8")
    (tmp_path / "teacher.jsonl").write_text("\n".join(json.dumps(t) for t in teach_rows) + "\n", encoding="utf-8")
    student = _student(seed=10)
    stats = {}
    train = examples_from_teacher(student, sp, tmp_path / "positions.jsonl", tmp_path / "teacher.jsonl", "train",
                                  stats)
    assert stats["no_change"] > 0
    val = examples_from_teacher(student, sp, tmp_path / "positions.jsonl", tmp_path / "teacher.jsonl", "val")
    assert len(train) == sum(p["split"] == "train" for p in pos_rows)
    assert len(val) == sum(p["split"] == "val" for p in pos_rows)
    assert all(e[2] == pytest.approx(0.3) and e[3] == pytest.approx(1 / ((0.01 + 0.09) / 2 / 2)) for e in train)
    shuffled = tmp_path / "selfplay_unsorted.jsonl"      # netdata writes games as they finish: by "g", not line
    shuffled.write_text("\n".join(json.dumps(r) for r in reversed(records)) + "\n", encoding="utf-8")
    again = examples_from_teacher(student, shuffled, tmp_path / "positions.jsonl", tmp_path / "teacher.jsonl",
                                  "train")
    assert [(e[1], e[2], e[3], e[4]) for e in again] == [(e[1], e[2], e[3], e[4]) for e in train]
    assert all(np.array_equal(x[0][k], y[0][k]) for x, y in zip(again, train) for k in range(4))
    out = tmp_path / "student.npz"
    done = subprocess.run([sys.executable, "-m", "svsim.learn.handvalue", "--selfplay", str(sp), "--positions",
                           str(tmp_path / "positions.jsonl"), "--teacher", str(tmp_path / "teacher.jsonl"),
                           "--out", str(out), "--iters", "20"], check=True, capture_output=True, text=True)
    report = json.loads(done.stdout.strip().splitlines()[-1])
    assert report["train_labels"] == len(train) and report["val_labels"] == len(val) and out.is_file()
    assert report["left_out"]["train"]["no_change"] == stats["no_change"]


def test_weights_carried_by_a_few_examples_fall_back_to_equal():
    """The effective sample size (sum w)^2 / sum w^2 of the 1 / var weights: under 30% of the examples, the fit
    uses equal weights and says so; otherwise the weights stand."""
    student = _student(seed=11)
    positions, _ = _positions()
    ex = [student.example(s, p, s.players[p].hand[0].uid, 0.1) for s, p in positions if s.players[p].hand]
    even = [(e[0], e[1], e[2], 1.0 + 0.1 * (i % 3)) for i, e in enumerate(ex)]
    skew = [(e[0], e[1], e[2], 1e5 if i == 0 else 1.0) for i, e in enumerate(ex)]
    r_even = _student(seed=11).fit(even, iters=2)
    r_skew = _student(seed=11).fit(skew, iters=2)
    assert not r_even["equal_weights"] and r_even["ess_share"] > 0.9
    assert r_skew["equal_weights"] and r_skew["ess_share"] < 0.3
