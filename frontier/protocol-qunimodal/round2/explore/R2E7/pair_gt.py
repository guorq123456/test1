# Ground truth for a pair with equal (r,k,S,mu) but different U_inf: r=4, residues (1,2,3,3,3,3) vs (2,2,2,3,3,3).
import sys
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from core import gt_profile
import rule_B4
for a in ([5,6,7,7,7,7], [6,6,6,7,7,7], [9,10,11,11,11,11], [10,10,10,11,11,11]):
    r = 4; F = sum(x//r for x in a); bs = list(range(1, F+8))
    print(a, 'L0', rule_B4.L0(r, a), 'F', F, 'U =', [b for b, g in zip(bs, gt_profile(r, a, bs)) if g], 'pred', [b for b in bs if rule_B4.predict(r, a, b)])
