# Local search for counterexamples to S3* / S2 inside the fit box.
# Objective: minimal normalized slack of the conjectured-true pair conditions:
#   K = K_{E*} (in [2mu*, 2mu*+r)) and all K >= 2mu*+2r (K = D+1 mod r, K <= D+1-2r):  min_x (Q_{K-x} - d_x) / (1+max|tau|)
# A negative value is a counterexample to S3* (then check S2 directly).
import sys, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS, Fval, Jset, S2_shape
from limit import tau
from s3star import estar

def objective(r, a):
    ds = DS(r, a); tt = tau(r, a)
    E, ms, bad = estar(r, a, ds, tt)
    D = ds.D
    scale = 1 + max(abs(t) for t in tt)
    best = None
    K = (D + 1) % r
    while K <= D + 1 - 2 * r:
        if (2 * ms <= K < 2 * ms + r) or K >= 2 * ms + 2 * r:
            for x in range(0, (K + 1) // 2):
                if 2 * x >= K: break
                s = ds(K - x) - tt[(K - x) % r] - ds(x)
                v = s / scale
                if best is None or v < best: best = v
        K += r
    return best if best is not None else 10.0

def mutate(r, a):
    a = list(a)
    op = random.random()
    if op < 0.3 and len(a) > 1: a.pop(random.randrange(len(a)))
    elif op < 0.6 and len(a) < 14: a.append(random.randint(1, r - 1) + r * random.choice([0, 0, 1, 2]))
    else:
        i = random.randrange(len(a)); a[i] = max(1, min(100, a[i] + random.choice([-r, r, -1, 1, 2, -2])))
    a = [x for x in a if x % r != 0 and x <= 100]
    if not a: a = [1]
    return sorted(a)

if __name__ == '__main__':
    seed = int(sys.argv[1]); iters = int(sys.argv[2])
    random.seed(seed)
    found = 0; evals = 0; global_best = (10, None)
    for restart in range(iters):
        r = random.randint(4, 12)
        a = sorted(random.randint(1, r - 1) + r * random.choice([0, 0, 1]) for _ in range(random.randint(2, 9)))
        a = [x for x in a if x % r] or [1]
        cur = objective(r, a); evals += 1
        for step in range(60):
            b = mutate(r, a)
            if sum(x - 1 for x in b) > 400: continue
            v = objective(r, b); evals += 1
            if v <= cur: a, cur = b, v
        if cur < global_best[0]: global_best = (cur, (r, a))
        if cur < 0:
            J = Jset(r, a)
            found += 1
            print("S3* VIOLATION", r, a, cur, "J", J, "S2", S2_shape(J), flush=True)
    print(f"seed={seed} restarts={iters} evals={evals} violations={found} best normalized slack={global_best}")
