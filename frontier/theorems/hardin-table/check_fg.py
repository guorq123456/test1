# Independent brute-force check of the finite ingredients of the proof:
#  - the 7 admissible TL patterns (d0,d1,e)
#  - f(W) = #{R : W-R has TL shape}, g(W) = #{R : R-W has BR shape}, g(W)=f(~W)
#  - S_k = sum_{W nonconstant} f(W) g(W)  (=36, 49, 9*2^(k-1)+12 for k=2,3,>=4)
#  - F = f(0)+f(1) = 6, G = g(0)+g(1) = 6
#  - the n=1 count 9*2^(k-1)+37 (k>=4) from the pattern formula
from itertools import product
def TL(d):   # d = W - R (length k+1): D row 0 = (p,q,0,...,0), p<=q<=0
    D=[d[j+1]-d[j] for j in range(len(d)-1)]
    return all(x==0 for x in D[2:]) and D[0]<=D[1]<=0
def BR(d):   # d = R - W: D row n-1 = (0,...,0,u,v), 0<=u<=v
    D=[d[j+1]-d[j] for j in range(len(d)-1)]
    return all(x==0 for x in D[:-2]) and 0<=D[-2]<=D[-1]
pats=sorted({(d0,d1,e) for d0,d1,e in product((-1,0,1),repeat=3) if TL((d0,d1,e,e))})
print("TL patterns:",pats)
assert pats==sorted([(a,b,b) for a in (-1,0,1) for b in (-1,0,1) if b<=a]+[(1,0,-1)])
for k in range(2,11):
    words=list(product((0,1),repeat=k+1))
    f={};g={}
    for W in words:
        f[W]=sum(1 for R in words if TL([w-r for w,r in zip(W,R)]))
        g[W]=sum(1 for R in words if BR([r-w for w,r in zip(W,R)]))
    for W in words:
        assert g[W]==f[tuple(1-W[k-j] for j in range(k+1))]
        # closed description of f
        w0,w1=W[0],W[1]; tail=set(W[2:])
        A0=[[3,1],[5,3]]; A1=[[1,1],[2,3]]
        fx = (1+w0) if len(tail)==2 else (A0 if tail=={0} else A1)[w0][w1]
        assert f[W]==fx,(W,f[W],fx)
    z=tuple([0]*(k+1)); o=tuple([1]*(k+1))
    S=sum(f[W]*g[W] for W in words if W not in (z,o))
    F=f[z]+f[o]; G=g[z]+g[o]
    expS={2:36,3:49}.get(k,9*2**(k-1)+12)
    # n=1: pairs (R0,R1) with d=R1-R0 having D row (p,q,0..0,u,v)
    print(k,"S_k=",S,"expected",expS,"F=",F,"G=",G, "f(0)g(0)+f(1)g(1)=",f[z]*g[z]+f[o]*g[o])
    assert S==expS and F==6 and G==6
# n=1 count by pattern formula vs direct enumeration of pairs
def valid_row(d):
    D=[d[j+1]-d[j] for j in range(len(d)-1)]
    return all(D[j]<=D[j+1] for j in range(len(D)-1))
for k in range(4,11):
    words=list(product((0,1),repeat=k+1))
    direct=sum(1 for R0 in words for R1 in words if valid_row([b-a for a,b in zip(R0,R1)]))
    print("n=1 k=",k,direct,9*2**(k-1)+37); assert direct==9*2**(k-1)+37
print("all finite checks OK")
# Table of Lemma 6 (k>=4): the 14 words with W' or V constant; sum f*g over the 12 nonconstant = 44,
# baseline sum (1+w0)(2-wk) over all 14 = 32.
for k in range(4,10):
    words=list(product((0,1),repeat=k+1))
    E=[W for W in words if len(set(W[2:]))==1 or len(set(W[:k-1]))==1]
    fE={W:sum(1 for R in words if TL([w-r for w,r in zip(W,R)])) for W in E}
    gE={W:sum(1 for R in words if BR([r-w for w,r in zip(W,R)])) for W in E}
    s1=sum(fE[W]*gE[W] for W in E if len(set(W))>1); s0=sum((1+W[0])*(2-W[k]) for W in E)
    print("k=",k,"|E|=",len(E),"sum fg (nonconst)=",s1,"baseline=",s0); assert (len(E),s1,s0)==(14,44,32)
print("Lemma 6 table OK")
