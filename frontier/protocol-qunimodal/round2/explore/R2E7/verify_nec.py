# Universal necessity (proofs.txt Thm 4): for ANY a with r | no a_i, with a' = parts >= 2 (k' = |a'| >= 2):
#   U(a) is contained in [1,F+1] u (F + U_inf(r, a' mod r)).
# Random instances with small parts allowed.  Usage: python3 verify_nec.py SEED N
import sys, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
import rule_B4
from core import gt_profile, in_box
rng = random.Random(int(sys.argv[1])); viol = nb = ni = strict = 0
for _ in range(int(sys.argv[2])):
    r = rng.randint(2, 30); k = rng.randint(2, 20)
    a = sorted(x for x in (rng.randint(1, rng.choice([r, 2*r, 3*r, 100])) for _ in range(k)) if x <= 100 and x % r)
    ap = [x for x in a if x >= 2]
    if len(ap) < 2 or not in_box(r, a): continue
    F = sum(x//r for x in a); U = rule_B4.Uinf(r, [x % r for x in ap])
    bs = list(range(1, F + max(U) + 4)); gt = gt_profile(r, a, bs); ni += 1; nb += len(bs)
    for b, g in zip(bs, gt):
        env = b <= F + 1 or (b - F) in U
        if g and not env: viol += 1; print('VIOLATION', r, a, b)
        if env and not g: strict += 1
print(f'seed={sys.argv[1]} instances={ni} b-values={nb} violations={viol} (envelope-true but non-unimodal b-values: {strict})')
