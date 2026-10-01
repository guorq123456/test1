from rp import *
import time, sys
from sympy.functions.combinatorial.numbers import stirling
from math import factorial
def prop315(n, m1, m2):
    m = min(m1, m2)
    return sum(int(stirling(m1, m-i))*int(stirling(m2, m-i))*((m-i)**(n-m1-m2)*factorial(m-i))**2 for i in range(m))
n = int(sys.argv[1])
shapes = [eval(s) for s in sys.argv[2:]]
for sh in shapes:
    w = layered(sh)
    assert sorted(w) == list(range(1, n+1))
    t = time.time(); a = grid_dp(w); t1 = time.time()-t
    t = time.time(); b = perm_generic(biadj(w)); t2 = time.time()-t
    t = time.time(); c = grid_dp(w[::-1]); t3 = time.time()-t   # left-right mirror
    f = prop315(n, sh[0], sh[-1]) if all(x == 1 for x in sh[1:-1]) else None
    print(sh, ' '.join(map(str, w)), a, b, c, 'prop3.15=', f, 'times %.1f %.1f %.1f' % (t1, t2, t3), flush=True)
