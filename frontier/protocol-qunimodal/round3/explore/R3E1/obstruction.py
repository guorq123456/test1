"""Proposition D (obstruction): explicit palindromic log-concave sequences A (not products of q-integers) satisfying every
qualitative ingredient of the class-pair framework, for which S2 FAILS.  Exact integer verification of:
  palindromic, log-concave, alpha unimodal, delta (=e) unimodal on the left half (Lemma 2.1 analogue),
  Wintner sign pattern of tau for a parity choice of F (Lemma 3.3 analogue, (F3)), Gamma cyclically unimodal (T11 Lemma 7),
  and the unimodality profile U (b<=Bmax) of A(q)[b]_{q^r}  (brute force, gt_big.times_b / unimodal).
Also prints kappa = r*ln(max ratio e(z)/e(z+1) on the geometric part) and whether (K) can hold (c<=1)."""
import sys, math
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import times_b, unimodal, poly_a
from geo2 import alpha
from geo3 import mul
from geo_check import checks
def profile(al,r,B): return [b for b in range(1,B+1) if unimodal(times_b(al,r,b))]
def K_possible(kap,r): return math.cos(math.pi/r)*(1-math.exp(-kap))**2 >= math.pi*math.exp(-kap*(0.75-1/(2*r)))
EX=[("D1: geometric-ramp m=8,G=10",alpha(8,10),3,0,math.log(9/8)),
    ("D2: geometric-ramp(13,40) * [6]_q [4]_q",mul(alpha(13,40),poly_a([6,4])),8,0,math.log(14/13)),
    ("D3: geometric-ramp(8,20) * [29]_q",mul(alpha(8,20),poly_a([29])),3,1,math.log(9/8))]
def kappa_eff(al,r,N):
    D=len(al)-1; X=D//2 if D%2==0 else (D+1)//2-1
    alx=al+[0]; d=[alx[x]-(alx[x-1] if x else 0) for x in range(D+1)]
    xR=min(math.floor(((D+1)-(N+2)*r+r)/2),(D+1)//2 if (D+1)%2==0 else D//2)
    best=float('inf')
    for x in range(1,xR+1):
        if d[x]<=0:
            if d[x-1]>0: return 0.0
            continue
        if d[x-1]<=0: continue
        if d[x-1]>=d[x]: return 0.0
        best=min(best,math.log(d[x])-math.log(d[x-1]))
    return r*best
for name,al,r,Fpar,rate in EX:
    D=len(al)-1
    pal=all(al[x]==al[D-x] for x in range(D+1))
    U=profile(al,r,2*D//r+8)
    N=max(b for b in range(1,len(U)+2) if all(c in U for c in range(1,b+1)))
    ch=checks(al,r,Fpar)
    print(name,"| r",r,"D",D,"palindromic",pal,{k:v for k,v in ch.items() if k not in('tau','Gamma')},
          "| U(b<=%d)="%(2*D//r+8),U,"| N*",N,"N*==F+1 mod 2:",(N-(Fpar+1))%2==0,
          "| N*+4 in U:",(N+4) in U,"(S2 violated)" if (N+4) in U else "",
          "| kappa_eff(H2', z>=L-r/2)=%.3f"%kappa_eff(al,r,N),"(K) possible even with c=1:",K_possible(kappa_eff(al,r,N),r))
