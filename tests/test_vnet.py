"""The turn-end value network (learn.vnet): one forward pass for training and inference, gradients, what moves
its output, the +vnet evaluator, the self-play rows."""
import json
import time

import numpy as np
import pytest

from test_handvalue import _positions, _with_hand


def _net(seed=0, **kw):
    from svsim.cards import decks
    from svsim.learn.vnet import ValueNet
    return ValueNet(sorted({d.card_id for d in decks.build(decks.RAMP_DRAGON)}), seed=seed, **kw)


def _items(net, positions):
    from svsim.learn.vnet import raw
    return [net.tensors(raw(s, p, None)) for s, p in positions]


def test_inference_and_the_training_batch_agree():
    """logit(state) is the batch-of-one forward pass, and a batch scores each item as it would alone."""
    from svsim.learn.vnet import raw
    net = _net()
    positions, _ = _positions()
    items = _items(net, positions[4:14])
    batch = net.forward(*net.stack(items))
    for (state, player), item, z in zip(positions[4:14], items, batch):
        assert net.logit(state, player) == pytest.approx(z, abs=1e-12)
        assert float(net.forward(*net.stack([item]))[0]) == pytest.approx(z, abs=1e-12)


def test_the_gradients_match_finite_differences():
    net = _net(seed=1, embed=4, field=6, hand=5, hidden=(7, 5))
    positions, _ = _positions()
    rng = np.random.default_rng(0)
    batch = net.stack(_items(net, positions[3:15]))
    y, w = rng.uniform(0, 1, 12), rng.uniform(0.5, 2, 12)
    _, g = net.loss_and_grads(batch, y, w, l2=1e-3)
    for name in net.PARAMS:
        P = getattr(net, name)
        flat = P.reshape(-1)
        for j in rng.choice(flat.size, size=min(6, flat.size), replace=False):
            if name in ("Ef", "Eh") and j < P.shape[1]:
                continue
            keep = flat[j]
            flat[j] = keep + 1e-6
            up = net.loss_and_grads(batch, y, w, l2=1e-3)[0]
            flat[j] = keep - 1e-6
            down = net.loss_and_grads(batch, y, w, l2=1e-3)[0]
            flat[j] = keep
            num = (up - down) / 2e-6
            assert abs(num - g[name].reshape(-1)[j]) <= 1e-5 + 1e-4 * abs(num), (name, j)


def test_a_hand_card_swap_or_a_follower_s_stats_move_the_output():
    from svsim.cards import decks
    net = _net(seed=2)
    positions, _ = _positions()
    state, player = next((s, p) for s, p in positions[8:] if s.players[p].hand and
                         (s.players[0].followers or s.players[1].followers))
    hand = [c.defn for c in state.players[player].hand]
    swap = next(d for d in decks.build(decks.RAMP_DRAGON) if d.card_id not in {h.card_id for h in hand})
    a = _with_hand(state, player, hand)
    b = _with_hand(state, player, hand[:-1] + [swap])
    assert abs(net.logit(a, player) - net.logit(b, player)) > 1e-6
    c = a.clone()
    f = (c.players[0].followers or c.players[1].followers)[0]
    f.atk += 2
    f.life += 1
    assert abs(net.logit(a, player) - net.logit(c, player)) > 1e-6


def test_no_deck_identity_among_the_inputs():
    from svsim.learn.vnet import FIELD, SCALARS
    assert not [n for n in FIELD + SCALARS if "deck_" in n.replace("me_deck", "").replace("op_deck", "") or
                "pair" in n]
    net = _net(seed=3)
    positions, _ = _positions()
    state, player = positions[9]
    other = state.clone()
    for q in other.players:
        q.deck_name = "something-else"
    assert net.logit(state, player) == net.logit(other, player)


def test_it_fits_and_round_trips(tmp_path):
    """A made-up target the inputs carry (sigmoid of the leaders' HP difference / 4): fitted, held out, saved and
    read back to the same scores; a student can seed the hand encoder."""
    from svsim.learn.handvalue import HandValue
    from svsim.learn.vnet import ValueNet
    net = _net(seed=4, embed=4, field=8, hand=8, hidden=(16, 8))
    positions, _ = _positions(n_games=4)
    items = _items(net, positions)
    y = np.array([1 / (1 + np.exp(-(s.players[p].leader_hp - s.players[1 - p].leader_hp) / 4)) for s, p in positions])
    cut = len(items) * 3 // 4
    before = net.loss_and_grads(net.stack(items[cut:]), y[cut:])[0]
    before_train = net.loss_and_grads(net.stack(items[:cut]), y[:cut])[0]
    report = net.fit(items[:cut], y[:cut], iters=300, lr=3e-3, l2=1e-3, batch=64, holdout=(items[cut:], y[cut:]))
    assert report["train_loss"] < before_train and report["holdout_loss"] < before
    path = tmp_path / "ramp-ramp-vnet.npz"
    net.save(path)
    back = ValueNet.load(path)
    for s, p in positions[:8]:
        assert back.logit(s, p) == net.logit(s, p)
    student = HandValue(net.vocab, embed=8, width=16, hidden=4, seed=5)
    seeded = ValueNet.from_student(student)
    assert np.array_equal(seeded.Wa, student.Wa) and np.array_equal(seeded.Eh[1:], student.E[1:])


def test_vnet_replaces_the_turn_end_score_only(tmp_path):
    """+vnet=FOLDER: the turn-end score is SCALE x the network's logit, the in-turn score the base's; the agent
    plays a game with it."""
    from svsim.learn.model import SCALE
    from svsim.tools.arena import make_agent
    net = _net(seed=6)
    net.save(tmp_path / "ramp-ramp-vnet.npz")
    agent = make_agent(f"mcts:20+plan+learned+phased+vnet={tmp_path}", 1)
    plain = make_agent("mcts:20+plan+learned+phased", 1)
    from svsim.tools.gate import _search
    w, base = _search(agent).weights, _search(plain).weights
    positions, _ = _positions()
    state, player = positions[7]
    assert w.score(state, player, False) == pytest.approx(SCALE * net.logit(state, player))
    assert w.score(state, player, True) == base.score(state, player, True)
    from svsim.core.engine import legal_actions
    assert agent.act(state, legal_actions(state)) in legal_actions(state)


def test_self_play_rows_and_targets(tmp_path):
    """A row per search decision and per turn end, with the raw encoding, the root value and the result; the
    target mixes them by lambda; the rows command and the fit command run."""
    import subprocess
    import sys
    from svsim.learn.vnet import rows_from_record, target
    _, records = _positions(n_games=2)
    rows = rows_from_record(records[0])
    acts = [r for r in rows if r["moment"] == "act"]
    ends = [r for r in rows if r["moment"] == "ended"]
    assert acts and ends and all(r["q"] is not None for r in acts)
    from svsim.learn.netdata import search_value
    assert len(acts) == sum(1 for t in records[0]["search"] if search_value(t) is not None)
    winner = records[0]["winner"]
    assert all(r["result"] == (1.0 if winner == r["player"] else 0.0 if winner in (0, 1) else 0.5) for r in rows)
    r = acts[0]
    assert target(r, 0.5) == pytest.approx(0.5 * r["result"] + 0.5 * r["q"]) and target(r, 1.0) == r["result"]
    assert target(dict(r, q=None), 0.3) == r["result"]
    games = tmp_path / "games.jsonl"
    games.write_text("\n".join(json.dumps(dict(rec, g=g)) for g, rec in enumerate(records)) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, "-m", "svsim.learn.vnet", "rows", str(games), "--out", str(tmp_path / "rows.jsonl")],
                   check=True, capture_output=True)
    done = subprocess.run([sys.executable, "-m", "svsim.learn.vnet", "fit", str(tmp_path / "rows.jsonl"), "--out",
                           str(tmp_path / "ramp-ramp-vnet.npz"), "--iters", "20", "--hold-out-every", "2"],
                          check=True, capture_output=True, text=True)
    report = json.loads(done.stdout.strip().splitlines()[-1])
    assert report["parameters"] > 10000 and (tmp_path / "ramp-ramp-vnet.npz").is_file()


def test_per_leaf_time_against_the_linear_model(capsys):
    """Printed for the README (pytest -s): the network's cost per leaf, cold and with its memo, beside the installed
    linear turn-end model's."""
    from svsim.learn.model import ALIASES, matchup_keys
    from svsim.learn.phased import PhasedLearned
    net = _net(seed=7)
    positions, _ = _positions(n_games=2)
    models = PhasedLearned().models
    state, player = positions[5]
    lin = models[next(k for k in matchup_keys(state, player, ALIASES) if k + ("ended",) in models) + ("ended",)]
    reps = positions * 3
    t = time.perf_counter()
    for s, p in reps:
        lin.logit(s, p)
    t_lin = (time.perf_counter() - t) / len(reps)
    t = time.perf_counter()
    for s, p in reps:
        net._memo.clear()
        net.logit(s, p)
    t_cold = (time.perf_counter() - t) / len(reps)
    t = time.perf_counter()
    for s, p in reps:
        net.logit(s, p)
    t_warm = (time.perf_counter() - t) / len(reps)
    print(f"\nper leaf: linear {t_lin * 1e6:.0f} us, value network {t_cold * 1e6:.0f} us cold, {t_warm * 1e6:.0f} us "
          f"memo hit ({net.parameters()} parameters)")
    assert t_cold > 0 and t_lin > 0
