# Ground-truth evaluation (fit box only) of candidate predictors on instances in the B4 domain.
# Candidates: B4 (rule_B4), TYPES (rule_types), T6only (b<=T6), T1only (b<=1+F).
# Mode 'rand': random instances; mode 'exh': every residue multiset for r in RLIST, k in KLIST,
#   parts = least admissible >= L0 (+ r on a random subset).  Usage:
#   python3 eval_gt.py rand SEED N      |     python3 eval_gt.py exh RLIST KLIST SEED
import sys, random, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
import rule_B4, rule_types, rule_chains
from core import gt_profile, in_box
def T6(r, a):
    res = [x % r for x in a]; tau = rule_B4._tau(r, res); k = len(a)
    mu = max([t for t in range(r) if tau[t] > 0], default=0)
    D = sum(x-1 for x in a)
    return 1 + (D + 1 - 2*mu)//r
cands = {
 'B4': rule_B4.predict, 'TYPES': rule_types.predict, 'CHAINS': (lambda r, a, b: rule_chains.predict(r, a, b) if len(a) >= 2 else rule_B4.predict(r, a, b)),
 'T6only': lambda r, a, b: b <= T6(r, a),
 'T1only': lambda r, a, b: b <= 1 + sum(x//r for x in a),
}
err = {c: 0 for c in cands}; nb = ni = 0
def test(r, a):
    global nb, ni
    if not in_box(r, a) or not rule_B4.domain(r, a): return
    F = sum(x//r for x in a); bs = list(range(1, F + (sum(x % r for x in a))//r + 5))
    gt = gt_profile(r, a, bs); ni += 1; nb += len(bs)
    for c, f in cands.items():
        e = sum(1 for b, g in zip(bs, gt) if f(r, a, b) != g)
        err[c] += e
        if c == 'B4' and e: print('B4 ERROR', r, a)
def least(s, L, r):
    x = s
    while x < L: x += r
    return x
mode = sys.argv[1]
if mode == 'rand':
    rng = random.Random(int(sys.argv[2]))
    for _ in range(int(sys.argv[3])):
        r = rng.randint(2, 30); k = rng.choice([1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 30, 40])
        res = [rng.randint(1, r-1) for _ in range(k)]
        L = rule_B4.L0(r, res)
        a = sorted(least(s, rng.randint(L, max(L, 100 - r)), r) for s in res)
        if max(a) <= 100: test(r, a)
else:
    RL = list(map(int, sys.argv[2].split(','))); KL = list(map(int, sys.argv[3].split(','))); rng = random.Random(int(sys.argv[4]))
    for r in RL:
        for k in KL:
            for res in itertools.combinations_with_replacement(range(1, r), k):
                L = rule_B4.L0(r, list(res))
                a = sorted(least(s, L, r) + r*rng.randint(0, 1) for s in res)
                if max(a) <= 100: test(r, a)
print(f'{sys.argv[1:]} instances={ni} b-values={nb} errors={err}')
