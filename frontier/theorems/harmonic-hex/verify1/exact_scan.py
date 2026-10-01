# Exact rational brute force of the A228016 definition (single upward scan over k).
# a(1)=least k: H(5)-H(0) < H(k)-H(5); a(2)=least k: H(a1)-H(5) < H(k)-H(a1); a(n)=least k: H(a(n-1))-H(a(n-2)) < H(k)-H(a(n-1)).
import gmpy2, sys, time
from gmpy2 import mpq
NMAX = int(sys.argv[1])
Hs = {}  # store H at needed indices
def Hexact(k):
    h = mpq(0)
    for j in range(1,k+1): h += mpq(1,j)
    return h
prev2, prev1 = 0, 5
Hp2, Hp1 = mpq(0), Hexact(5)
k = 0; H = mpq(0)
res = []
t0=time.time()
for n in range(1, NMAX+1):
    T = 2*Hp1 - Hp2
    # least k with H(k) > T (strict <, as in %C and data); also record least k with H(k) >= T
    while not (H > T):
        k += 1; H += mpq(1,k)
    # check '<=' variant: least k with H(k) >= T; equality at k impossible? check H(k-1) != T
    Hkm1 = H - mpq(1,k)
    assert Hkm1 < T, "H(k-1)==T would change <= variant"
    res.append(k)
    print(n, k, "time", round(time.time()-t0,1), flush=True)
    prev2, prev1 = prev1, k
    Hp2, Hp1 = Hp1, H
print(res)
