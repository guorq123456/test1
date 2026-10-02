# Random fit-box test of S3* (rule file s3star_rule.py) against ground truth (lib.unimodal_d, validated vs tools/uni),
# plus the parity claim B == 1+F (mod 2) and the proven bound (U subset [1,B]).
# Instances: r in [2,30], k <= 40 (<= 60 if all equal), a_i <= 100.  Usage: python3 test_s3star_random.py seed n
import sys, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS, unimodal_d, Fval
import s3star_rule as S
seed, n = int(sys.argv[1]), int(sys.argv[2])
random.seed(seed)
err = 0; tot = 0; par_bad = 0; bound_bad = 0; shapes = {}
for it in range(n):
    r = random.choice([random.randint(2, 10), random.randint(2, 30)])
    style = random.random()
    if style < 0.25:
        k = random.randint(1, 60); t = random.randint(1, min(100, 3 * r)); a = [t] * k
    elif style < 0.6:
        k = random.randint(1, 12); a = [random.randint(1, r - 1) if r > 1 else 1 for _ in range(k)]
    else:
        k = random.randint(1, 10); a = [random.randint(1, min(100, 4 * r)) for _ in range(k)]
    a = [x if x % r else x + 1 for x in a]
    a = [min(x, 100) for x in a]
    if any(x % r == 0 for x in a): continue
    a.sort()
    if sum(x - 1 for x in a) > 2500: continue
    B = S.Bvalue(r, a); F = Fval(r, a)
    if (B - 1 - F) % 2: par_bad += 1; print("PARITY FAIL", r, a, B, F, flush=True)
    ds = DS(r, a)
    U = [b for b in range(1, B + 3) if unimodal_d(ds, b)]
    if U and max(U) > B: bound_bad += 1; print("BOUND FAIL", r, a, U, B, flush=True)
    for b in range(1, B + 3):
        tot += 1
        if S.predict(r, a, b) != (b in U):
            err += 1
            if err < 10: print("PRED FAIL", r, a, b, U, B, flush=True)
    sh = 'full' if U == list(range(1, B + 1)) else ('gap' if U == [x for x in range(1, B + 1) if x != B - 1] else 'OTHER')
    shapes[sh] = shapes.get(sh, 0) + 1
print(f"seed={seed}: instances(b-values) {tot}, rule errors {err}, parity failures {par_bad}, bound failures {bound_bad}, U-shapes {shapes}")
