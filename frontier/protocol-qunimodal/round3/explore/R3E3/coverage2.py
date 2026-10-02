# r=4 analytic coverage with two-sided ratio bounds:
#   j/(j+k-1) <= rho_j = alpha_{j-1}/alpha_j <= min(1, j/(k-j+1))   (1<=j<=D/2), rho_0 := 0
#   alpha_x >= C(k,x)  (k = #parts >= 2)
# A position x = x_{n*+1} (gap g to next chain point) is COVERED if
#   (L) E_lb(x,g) >= R_ub(x,g)    [L' holds], or x-g-4<0 [L' automatic], or
#   (T) sum_{t>=0} max(0, C(k,x-4t)*E_lb(x-4t,g)) >= V=2^floor((k-1)/2)  [then n* cannot sit here]
from fractions import Fraction as Fr
from math import comb
def rhi(j,k):
    if j<=0: return Fr(0)
    return min(Fr(1), Fr(j,k-j+1)) if j<=k else Fr(1)
def rlo(j,k):
    if j<=0: return Fr(0)
    return Fr(j,j+k-1)
def pihi(x,g,k):
    p=Fr(1)
    for i in range(g):
        if x-i<=0: return Fr(0)
        p*=rhi(x-i,k)
    return p
def E_lb(x,g,k):
    # lower bound of (delta_x - delta_{x-g})/alpha_x
    if x<0: return Fr(0)
    if x-g<0: return 1-rhi(x,k)
    return 1-rhi(x,k)-pihi(x,g,k)*(1-rlo(x-g,k))
def R_ub(x,g,k):
    # upper bound of delta_{x-g-4}/alpha_x
    j=x-g-4
    if j<0: return Fr(0)
    return pihi(x,g+4,k)*(1-rlo(j,k))
def Tlb(x,g,k):
    s=Fr(0); t=x
    while t>=0:
        e=E_lb(t,g,k)
        if e>0: s+=comb(k,t)*e if t<=k else 0
        t-=4
    return s
def uncovered(k,xmax):
    V=2**((k-1)//2); bad=[]
    for g in (1,2,3):
        for x in range(g+4,xmax):
            if E_lb(x,g,k)>=R_ub(x,g,k): continue
            if Tlb(x,g,k)>=V: continue
            bad.append((g,x))
    return bad
if __name__=='__main__':
    import sys
    for k in range(4,int(sys.argv[1]) if len(sys.argv)>1 else 80):
        u=uncovered(k,4*k+60)
        print(k,len(u),u[:20])
