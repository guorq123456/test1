# Test conjectured closed form: sum_{N>=0} A(N,k) x^N = b_k(x^2) / (b_k(x^2) - x*Bk(x^2))
from math import comb
from dp import A_all_fast
def series_div(p, q, n):
    out = []
    for i in range(n):
        s = (p[i] if i < len(p) else 0) - sum(q[j]*out[i-j] for j in range(1, min(i, len(q)-1)+1))
        assert s % q[0] == 0
        out.append(s // q[0])
    return out
ok_all = True
for k in range(0, 41):
    b = [comb(k+j, 2*j) for j in range(k+1)]
    Bk = [comb(k+1+j, 2*j+1) for j in range(k+1)]
    num = [0]*(2*k+3); den = [0]*(2*k+3)
    for j, c in enumerate(b): num[2*j] += c; den[2*j] += c
    for j, c in enumerate(Bk): den[2*j+1] -= c
    L = 120
    ser = series_div(num, den, L)
    A = A_all_fast(L-1, k)
    ok = ser == A
    ok_all &= ok
    if k < 8 or not ok: print(k, ok, 'den', den[:2*k+3])
print('all k<=40:', ok_all)
