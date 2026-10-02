"""Leading constant c(r,s) = (s-1-2 theta*)/r and log coefficient kappa for single-residue families."""
import sys
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from theory import asym_pred
print('r s sigma1 L theta* c kappa')
for r in [4, 5, 6, 7, 8, 10, 12, 16, 20, 30]:
    for s in range(2, r - 1):
        q = asym_pred(r, [s])
        print(r, s, '%.3f %.4f %.4f %.4f %.4f' % (q['sigma1'], q['L'], q['theta'], q['c'], q['kappa']))
