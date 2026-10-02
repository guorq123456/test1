# T-formulation of unimodality (derived in this path; see proof file Lemma 1-2):
# s_m = alpha_m - alpha_{m-1} for 0<=m<=D/2 (alpha = coeffs of A=prod [a_i]_q), 0 otherwise.
# T_z = sum_{m>=z, m=z mod r} s_m  (for z<=0: total of class z mod r).
# P unimodal at b  <=>  for all integers x<y with x+y = K_b := D+1-r(b-1):  T_x >= T_y.
import sys
def poly_a(a):
    c=[1]
    for A in a:
        n=len(c)+A-1; d=[0]*n; s=0
        for t in range(n):
            if t<len(c): s+=c[t]
            if 0<=t-A<len(c): s-=c[t-A]
            d[t]=s
        c=d
    return c
class TS:
    def __init__(self,r,a):
        self.r=r; self.a=sorted(a)
        al=poly_a(a); D=len(al)-1; self.D=D
        H=D//2; self.H=H
        s=[al[0]]+[al[m]-al[m-1] for m in range(1,H+1)]
        self.s=s
        # T_z for 0<=z<=H+r ; class totals
        T=[0]*(H+1+r)
        for z in range(H,-1,-1):
            T[z]=s[z]+(T[z+r] if z+r<=H else 0)
        self.Tarr=T
        self.Sig=[T[rho] if rho<=H else 0 for rho in range(r)]
    def T(self,z):
        if z>self.H: return 0
        if z<=0: return self.Sig[z%self.r]
        return self.Tarr[z]
    def uni(self,b):
        K=self.D+1-self.r*(b-1)
        # y ranges over (K/2, H]
        y0=K//2+1
        for y in range(max(y0,K-10**9),self.H+1):
            x=K-y
            if x>=y: continue
            if self.T(x)<self.T(y): return False
            if x<=0 and y<=0:
                pass
        return True
    def uni_fast(self,b):
        # same but y range limited: once x<=0 and y<=0 everything is class totals -> periodic; y from max(y0, K-H-r? ) 
        K=self.D+1-self.r*(b-1); r=self.r
        y0=K//2+1
        lo=max(y0, -2*r)  # y<=0 values only depend on residue: check y in [-r+1..0] window suffices if y0<=-r
        for y in range(lo,self.H+1):
            x=K-y
            if x>=y: continue
            if self.T(x)<self.T(y): return False
        return True
def F_of(r,a): return sum(x//r for x in a)
if __name__=='__main__':
    for line in sys.stdin:
        x=list(map(int,line.split())); r,k=x[0],x[1]; a=x[2:2+k]; b=x[2+k]
        print(1 if TS(r,a).uni(b) else 0)
