"""Evaluate candidate excess-estimators on the fit set. Each candidate gives E_pred(r, a); the rule is
   predict(r,a,b) = True if r | some a_i, else b <= 1 + F + E_pred.
Error count = number of (instance, b) pairs, b in [1, T6+2], where prediction != ground truth.
usage: candidates_eval.py fit_*.jsonl
"""
import sys, json, math
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from b4limit import tau_of
from theory import asym_pred, sandwich_b4, dgam_fn, Lrate


def nstar_cont(r, s):
    """continuous threshold: n with ln delta_n = ln M (linear interpolation of ln delta)."""
    k = len(s)
    tau = tau_of(r, s); M = max(-t for t in tau)
    d = dgam_fn(r, k)
    n = -1
    while d(n + 1) < M:
        n += 1
    # d(n) < M <= d(n+1)
    l0 = math.log(d(n)) if d(n) > 0 else -50.0
    l1 = math.log(d(n + 1))
    return n + (math.log(M) - l0) / (l1 - l0)


def make(name, beta=0.0):
    def E_pred(r, a):
        s = [x % r for x in a]; k = len(a)
        S1 = sum(x - 1 for x in s)
        if name == 'C1_lead':
            return math.floor(asym_pred(r, s)['lead'])
        if name == 'C2_log':
            return math.floor(asym_pred(r, s)['withlog'])
        if name == 'C3_log_even':
            X = asym_pred(r, s)['withlog']
            return 2 * math.floor((X + beta) / 2)
        if name == 'C3b_log_round':
            X = asym_pred(r, s)['withlog']
            return math.floor(X + beta)
        if name == 'C4_win_lo':
            return sandwich_b4(r, s)[0][2]
        if name == 'C5_win_hi':
            return sandwich_b4(r, s)[0][3]
        if name == 'C6_win_hi_even':
            e = sandwich_b4(r, s)[0][3]
            return e - (e % 2)
        if name == 'C6b_win_lo_even_up':
            e = sandwich_b4(r, s)[0][2]
            return e + (e % 2)
        if name == 'C7_nstar_even':
            X = (S1 - 2 * nstar_cont(r, s)) / r
            return 2 * math.floor((X + beta) / 2)
        if name == 'C7b_nstar_round':
            X = (S1 - 2 * nstar_cont(r, s)) / r
            return math.floor(X + beta)
        raise ValueError(name)
    return E_pred


def evaluate(rows, E_pred):
    err = 0; inst_err = 0
    for R in rows:
        r, a, F, U, T6 = R['r'], R['a'], R['F'], set(R['U']), R['T6']
        e = E_pred(r, a)
        bad = sum(1 for b in range(1, T6 + 3) if (b <= 1 + F + e) != (b in U))
        err += bad; inst_err += bad > 0
    return err, inst_err


if __name__ == '__main__':
    rows = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
    npairs = sum(R['T6'] + 2 for R in rows)
    print("instances", len(rows), "pairs", npairs)
    for name in ['C1_lead', 'C2_log', 'C4_win_lo', 'C5_win_hi', 'C6_win_hi_even', 'C6b_win_lo_even_up']:
        print(name, "free=0 errors(pairs, instances) =", evaluate(rows, make(name)))
    for name in ['C3_log_even', 'C3b_log_round', 'C7_nstar_even', 'C7b_nstar_round']:
        best = None
        for i in range(-40, 41):
            beta = i / 10
            ev = evaluate(rows, make(name, beta))
            if best is None or ev[0] < best[1][0]:
                best = (beta, ev)
        print(name, "free=1 best beta=%.1f errors(pairs, instances) =" % best[0], best[1])
