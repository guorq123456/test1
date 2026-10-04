"""Dynamic Bradley-Terry: each player's skill drifts as a random walk.

The static model (bt.py) treats skill as fixed and only down-weights old results, so a long
record keeps dominating: 200 decayed wins from 2021-2023 still outweigh 10 recent results.
Here skill moves: b_i(t + dt) = b_i(t) + N(0, drift * dt / 365). Old results then only pin
down how strong someone *was*; their pull on the current estimate is capped by the drift
accumulated since, however many there were.

Inference is assumed-density filtering, event by event (like Glicko / TrueSkill):
* predict: every participant's variance grows by drift * days since their last event / 365;
  newcomers start at N(0, newcomer_sd^2);
* update: a joint Laplace (MAP + Hessian) step on all of the event's series, with each
  player's current Gaussian as the prior; the new mean is the MAP, the new variance the
  diagonal of the inverse Hessian.
Ratings after each event are the filtered means: what was known at that date.
"""
import math
from collections import defaultdict

import numpy as np
from scipy.special import expit, log_expit

ELO_SCALE = 400 / math.log(10)


def _event_update(mu, var, winners, losers):
    """MAP of sum log sigmoid(b_w - b_l) - sum (b - mu)^2 / (2 var) by Newton; returns (b, posterior var)."""
    b = mu.copy()
    prec = 1.0 / var
    for _ in range(50):
        d = b[winners] - b[losers]
        p = expit(d)
        g = prec * (b - mu)
        np.add.at(g, winners, p - 1.0)
        np.add.at(g, losers, 1.0 - p)
        h = p * (1.0 - p)
        H = np.diag(prec.copy())
        np.add.at(H, (winners, winners), h)
        np.add.at(H, (losers, losers), h)
        np.add.at(H, (winners, losers), -h)
        np.add.at(H, (losers, winners), -h)
        step = np.linalg.solve(H, g)
        b -= step
        if np.max(np.abs(step)) < 1e-9:
            break
    d = b[winners] - b[losers]
    p = expit(d)
    h = p * (1.0 - p)
    H = np.diag(prec.copy())
    np.add.at(H, (winners, winners), h)
    np.add.at(H, (losers, losers), h)
    np.add.at(H, (winners, losers), -h)
    np.add.at(H, (losers, winners), -h)
    return b, np.diag(np.linalg.inv(H))


def run(matches, drift, newcomer_sd, newcomer_mean=None, on_event=None):
    """Filter through events in time order.

    matches: list of (time, winner_id, loser_id, weight, event); weight is ignored (no decay here).
    newcomer_mean: optional f(player_id, event) -> prior mean in log-odds for a first appearance.
    on_event(event, start, end, state_before, state_after, event_matches): called per event, where a
    state is {player: (mean, var, last_time)} as of just before / just after the event.
    Returns the final state.
    """
    events = defaultdict(list)
    for m in matches:
        events[m[4]].append(m)
    order = sorted(events, key=lambda e: (max(m[0] for m in events[e]), e))
    state = {}
    for ev in order:
        ms = events[ev]
        start, end = min(m[0] for m in ms), max(m[0] for m in ms)
        players = sorted({p for m in ms for p in (m[1], m[2])})
        before = {}
        for p in players:
            if p in state:
                mu, v, last = state[p]
                v = v + drift * max((start - last).total_seconds(), 0) / 86400 / 365
            else:
                mu = newcomer_mean(p, ev) if newcomer_mean else 0.0
                v = newcomer_sd ** 2
            before[p] = (mu, v, start)
        if on_event:
            on_event(ev, start, end, {**state, **before}, None, ms)
        idx = {p: i for i, p in enumerate(players)}
        mu = np.array([before[p][0] for p in players])
        var = np.array([before[p][1] for p in players])
        b, post = _event_update(mu, var, np.array([idx[m[1]] for m in ms]), np.array([idx[m[2]] for m in ms]))
        for p, i in idx.items():
            state[p] = (b[i], post[i], end)
        if on_event:
            on_event(ev, start, end, None, state, ms)
    return state


def predict(state, a, b, newcomer_sd, newcomer_mean=0.0, predictive=True):
    """P(a beats b) from a state; predictive=True integrates over rating uncertainty (probit approximation)."""
    ma, va = state.get(a, (newcomer_mean, newcomer_sd ** 2, None))[:2]
    mb, vb = state.get(b, (newcomer_mean, newcomer_sd ** 2, None))[:2]
    d = ma - mb
    if predictive:
        d /= math.sqrt(1 + math.pi * (va + vb) / 8)
    return float(expit(d))
