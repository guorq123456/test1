# For r=4: for each k' find x>=5 (x = x_{n*+1}) not covered by the analytic argument.
from fractions import Fraction as Fr
from math import comb
def rb(j,k):  # ratio bound alpha_{j-1}/alpha_j <= j/(k-j+1), valid for 1<=j<=k; None if useless
    if j<=0: return Fr(0)
    if j>k: return None
    return Fr(j,k-j+1)
def prodrb(x,g,k):
    p=Fr(1)
    for i in range(g):
        j=x-i
        if j<=0: return Fr(0)   # alpha_{x-g}=0 if x-g<0 ... careful: alpha_{j-1} with j-1<0 is 0
        t=rb(j,k)
        if t is None or t>=1: t=Fr(1)  # alpha nondecreasing? not guaranteed; use log-concave? keep conservative below
        p*=t
    return p
def Lprime_ok(x,g,k):
    # sufficient: 1 - rb(x) - prod_{i<g} rb(x-i) - prod_{i<g+4} rb(x-i) >= 0, all ratio bounds < 1 required
    for i in range(g+4):
        j=x-i
        if j>=1:
            t=rb(j,k)
            if t is None or t>=1: return False
    return 1-rb(x,k)-prodrb(x,g,k)-prodrb(x,g+4,k)>=0
def LB(x,g,k):
    # lower bound for y_m - y_{m+1} at position x with gap g
    for i in range(g):
        j=x-i
        if j>=1:
            t=rb(j,k)
            if t is None or t>=1: return 0
    if x>=1 and (rb(x,k) is None): return 0
    return comb(k,x)*(1-rb(x,k)-prodrb(x,g,k))
def uncovered(k,xmax=None):
    V=2**((k-1)//2)
    if xmax is None: xmax=4*k+40
    bad=[]
    for g in (1,2,3):
        for x in range(5,xmax):
            if x-g-4<0: continue
            if Lprime_ok(x,g,k): continue
            if any(LB(x-4*j,g,k)>=V for j in range(0,x//4+1)): continue
            bad.append((g,x))
    return bad
if __name__=='__main__':
    for k in range(4,60):
        u=uncovered(k)
        print(k,len(u),u[:12])
