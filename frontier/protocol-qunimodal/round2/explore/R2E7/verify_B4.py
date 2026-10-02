# Verify: for k>=2, r | no a_i, min a_i >= L0(r,res): U = [1,F+1] U (F + Uinf(r,res)).
# Random instances inside the fit box. Usage: python3 verify_B4.py SEED NTRIALS
import sys, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import *
seed = int(sys.argv[1]); NT = int(sys.argv[2])
rng = random.Random(seed)
bad = 0; tested = 0; nb = 0
for trial in range(NT):
    r = rng.randint(2, 30)
    k = rng.choice([2,2,3,3,4,5,6,7,8,10,12,15,20])
    res = [rng.randint(1, r-1) for _ in range(k)]
    L = L0(r, res)
    a = []
    for s in res:
        # smallest admissible part >= L with residue s, plus random multiple of r
        base = s
        while base < L: base += r
        if base > 100: break
        top = (100 - base)//r
        a.append(base + r*rng.randint(0, min(top, rng.choice([0,0,1,2,5,100]))))
    if len(a) < k: continue
    a.sort()
    if not in_box(r, a): continue
    F = sum(x//r for x in a)
    ui = Uinf(r, res)
    bs = list(range(1, F + max(ui) + 4))
    gt = gt_profile(r, a, bs)
    pred = [(b <= F+1) or ((b - F) in ui) for b in bs]
    tested += 1; nb += len(bs)
    if gt != pred:
        bad += 1
        print('MISMATCH', r, a, 'F', F, 'gt', [b for b,g in zip(bs,gt) if g], 'pred', [b for b,p in zip(bs,pred) if p])
print(f'seed={seed} instances={tested} b-values={nb} mismatches={bad}')
