from brute import indep_poly_backtrack
from dp_bigint import run
import math
cnt = 0
for k in range(1, 8):
    res = run(k, 16)
    for n in range(2*k+1, 17):
        b = indep_poly_backtrack(n, k)
        assert b == res[n], (n, k, b, res[n])
        cnt += 1
print('all match', cnt)
