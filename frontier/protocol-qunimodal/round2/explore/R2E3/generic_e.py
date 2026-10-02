# Test: for an ARBITRARY odd function e with unimodal nonneg positive half (not from a product of q-integers),
# does U = {b : V_b(theta)>=0 for all theta>0} have shape [1,B] or [1,B]\{B-1} ?
# Work with d-sequence of length D+2 antisymmetric: d_m = -d_{D+1-m}, d_m>=0 & unimodal for m<=(D+1)/2 (reading m downward from centre).
import random, sys
def U_of_d(r,d,bmax):
    D=len(d)-2
    out=[]
    for b in range(1,bmax+1):
        N=D+r*(b-1); ok=True
        for n in range(0,N//2+1):
            s=sum(d[n-r*y] for y in range(b) if 0<=n-r*y<=D+1)
            if s<0: ok=False;break
        if ok: out.append(b)
    return out
def rand_d(D):
    # positive half indices m=0..floor((D+1)/2); m=(D+1)/2 (if integer) must be 0.
    H=(D+1)//2 + (0 if (D+1)%2==0 else 1)   # number of free entries m=0..H-1
    # e(u)=d_{M-u}, u decreasing as m increasing; unimodal in u <=> unimodal in m
    p=random.randint(0,H-1)
    vals=[0]*H
    v=random.randint(0,3)
    for m in range(p,-1,-1):
        vals[m]=v; v=max(0,v-random.randint(0,3))
    v=vals[p]
    for m in range(p+1,H):
        v=max(0,v-random.randint(0,3)); vals[m]=v
    d=[0]*(D+2)
    for m in range(H): d[m]=vals[m]; d[D+1-m]=-vals[m]
    if (D+1)%2==0: d[(D+1)//2]=0
    return d
def shape(U):
    if not U: return 'empty'
    B=max(U); S=set(U); full=set(range(1,B+1))
    if S==full: return 'interval'
    if S==full-{B-1}: return 'gap1'
    return 'other'
if __name__=='__main__':
    random.seed(int(sys.argv[1])); N=int(sys.argv[2])
    from collections import Counter
    c=Counter(); ex=[]
    for it in range(N):
        r=random.randint(2,7); D=random.randint(2,40)
        d=rand_d(D)
        U=U_of_d(r,d,(D+1)//r+4)
        sh=shape(U); c[sh]+=1
        if sh=='other' and len(ex)<5: ex.append((r,d,U))
    print(c)
    for e in ex: print(e)
