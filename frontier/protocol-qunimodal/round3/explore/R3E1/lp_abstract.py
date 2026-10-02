"""Abstract LP: is S2 a consequence of 'A palindromic with delta unimodal on the left half' (+ optional extra linear
constraints)?  Variables delta_0..delta_X (D=2X even), delta_{D+1-x}=-delta_x.  Require P_b unimodal (window criterion)
for b in [1,n0] u {n0+2, n0+4} and one window of size n0+1 with sum <= -1.  Feasible => abstract S2 counterexample.
Options: sign=True imposes the cyclic Wintner sign pattern of tau for given (F parity, sigma mod 2r) -- i.e. the sign lemma.
Only r<=120 is used."""
import numpy as np, sys, itertools
from scipy.optimize import linprog
def window_rows(X,r,b):
    D=2*X; N=D+r*(b-1); rows=[]
    for n in range(0,N//2+1):
        row={}
        for j in range(b):
            x=n-r*j
            if 0<=x<=X: row[x]=row.get(x,0)+1
            elif X+1<=x<=D+1: xx=D+1-x; row[xx]=row.get(xx,0)-1
        if row: rows.append((n,row))
    return rows
def solve(X,r,n0,p,bad_n,sign_pattern=None,extra=None):
    nv=X+1; A_ub=[]; b_ub=[]
    def add(row,rhs):  # sum row*delta <= rhs
        v=np.zeros(nv)
        for k,c in row.items(): v[k]+=c
        A_ub.append(v); b_ub.append(rhs)
    # unimodal delta, peak p
    for x in range(1,p+1): add({x-1:1,x:-1},0)      # delta_{x-1} <= delta_x
    for x in range(p+1,X+1): add({x:1,x-1:-1},0)    # delta_x <= delta_{x-1}
    for b in list(range(1,n0+1))+[n0+2,n0+4]:
        for n,row in window_rows(X,r,b): add({k:-c for k,c in row.items()},0)
    # bad window of size n0+1
    rows=dict(window_rows(X,r,n0+1))
    if bad_n not in rows: return None
    add(rows[bad_n],-1)
    if sign_pattern is not None:
        for t,sgn in sign_pattern:  # sgn*tau(t) >= 0, tau(t)=sum_{x==t mod r} delta_x over all x in [0,D+1]
            row={}
            for x in range(0,2*X+2):
                if x%r==t%r:
                    if x<=X: row[x]=row.get(x,0)+1
                    else: row[2*X+1-x]=row.get(2*X+1-x,0)-1
            add({k:-sgn*c for k,c in row.items()},0)
    if extra: 
        for row,rhs in extra(X): add(row,rhs)
    res=linprog(np.zeros(nv),A_ub=np.array(A_ub),b_ub=np.array(b_ub),bounds=[(0,None)]*nv,method="highs")
    return res.x if res.status==0 else None
if __name__=="__main__":
    found=0
    for r in [6,8,10,12,16]:
        for X in [2*r,3*r,4*r,6*r]:
            for n0 in [1,2,3,4,5]:
                for p in range(0,X+1,max(1,X//12)):
                    for bad_n in range(0,(2*X+r*n0)//2+1,max(1,r//4)):
                        sol=solve(X,r,n0,p,bad_n)
                        if sol is not None:
                            print("FEASIBLE r",r,"X",X,"n0",n0,"peak",p,"bad window top",bad_n); found+=1; break
                    if found: break
                if found: break
            if found: break
        if found: break
    if found:
        np.save("lp_sol.npy",sol); print(np.round(sol/ sol.max(),4).tolist())
