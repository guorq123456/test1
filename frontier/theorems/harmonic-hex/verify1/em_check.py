# Second independent method: Euler-Maclaurin enclosure of H(k) with mpmath (k>=54):
# ln k + g + 1/(2k) - 1/(12k^2) + 1/(120k^4) - 1/(252k^6) < H(k) < ln k + g + 1/(2k) - 1/(12k^2) + 1/(120k^4)
import mpmath as mp, sys
from fractions import Fraction as F
sys.set_int_max_str_digits(0)
N=int(sys.argv[1])
def Hb(k):
    if k < 200:
        h = sum(F(1,j) for j in range(1,k+1)); x = mp.mpf(h.numerator)/h.denominator
        return x - mp.mpf(10)**(-mp.mp.dps+5), x + mp.mpf(10)**(-mp.mp.dps+5)
    K=mp.mpf(k); base = mp.log(K)+mp.euler+1/(2*K)-1/(12*K**2)+1/(120*K**4)
    eps = mp.mpf(10)**(-mp.mp.dps+10)
    return base - 1/(252*K**6) - eps, base + eps
p2,p1=0,5; out=[]
for n in range(1,N+1):
    mp.mp.dps = 2*len(str(p1))+60
    l2,u2 = Hb(p2) if p2 else (mp.mpf(0),mp.mpf(0))
    l1,u1 = Hb(p1)
    Tlo, Thi = 2*l1-u2, 2*u1-l2
    k = int(mp.floor(mp.exp((Tlo+Thi)/2 - mp.euler) - mp.mpf(1)/2)) + 1
    for _ in range(20):
        lk,uk = Hb(k); lm,um = Hb(k-1)
        if lk > Thi and um < Tlo: break
        if uk < Tlo: k+=1
        elif lm > Thi: k-=1
        else: raise SystemExit("undecided n=%d"%n)
    else: raise SystemExit("no conv")
    out.append(k); p2,p1=p1,k
e=[0,5]
while len(e)<N+3: e.append(10*e[-1]-e[-2]+4)
print("EM method terms", N, "all equal e_{n+1}:", all(out[n-1]==e[n+1] for n in range(1,N+1)))
