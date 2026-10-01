# Sanity checks (inside fit box only: r=3, k<=8, a_i<=12 nondiv by 3, b<=60) of each lemma used in proof.txt
from common import *
from explore_e import eseq, delta_fn
def G(p,v):
    if v<0: return 0
    return sum(p[j] for j in range(v%3, min(v,len(p)-1)+1, 3))
fails={'L1':0,'L3_u0':0,'L5_k1':0,'C1':0,'C2b_i':0,'C2b_ii':0,'C2b_m':0,'Rdiff':0}
n2b=0; n2a=0; n1=0
for a in box_instances():
    a=[x for x in a if x>=2]
    if not a: continue
    p=[int(x) for x in pprod(a)]; D=len(p)-1; S=sum(1 for x in a if x%3==2); s=S%6
    e=eseq(p,D+200); dl=delta_fn(S); E=lambda m: e[m] if m>=0 else 0
    # Lemma 3: u0 = first m>=D-1 with delta=-1 equals D+1-floor(s/2)
    u0=next(m for m in range(D-1,D+5) if dl(m)==-1)
    if u0!=D+1-s//2: fails['L3_u0']+=1
    R=[sum(p[j] for j in range(rho,D+1,3)) for rho in range(3)]
    if max(R)-min(R)!=1: fails['Rdiff']+=1
    if len(a)==1:
        if any(e[m]!=(1 if m%3==0 else 0) for m in range(0,D+1)): fails['L5_k1']+=1
    for b in range(1,61):
        L=3*(b-1); N=D+L
        c=[int(x) for x in withb(pprod(a),3,b)]
        # Lemma 1: c_u-c_{u-1} = e_u - e_{u-3b}
        for u in range(1,N//2+1):
            if c[u]-c[u-1]!=E(u)-E(u-3*b): fails['L1']+=1;break
        if L>D-s: continue
        if L>=D-5:
            n1+=1
            if any(c[u]<c[u-1] for u in range(1,N//2+1)): fails['C1']+=1
            continue
        # case 2: L<=D-6, remove each factor in turn (need A nontrivial)
        if len(a)<2: continue
        for idx in range(len(a)):
            A=a[:idx]+a[idx+1:]; aa=a[idx]
            pA=[int(x) for x in pprod(A)]; DA=len(pA)-1; sA=sum(1 for x in A if x%3==2)%6
            if L<=DA-sA: n2a+=1; continue
            n2b+=1
            NA=DA+L
            if not (2*(NA//2) < 2*3*b and NA < 2*3*b): fails['C2b_i']+=1
            cA=[int(x) for x in withb(pA,3,b)]
            CA=lambda v: cA[v] if 0<=v<=NA else 0
            for u in range(1,N//2+1):
                m=u-aa
                if m<0: continue
                if m>DA-4: fails['C2b_m']+=1
                up=min(u,NA-u)
                if CA(up)!=G(pA,up) or CA(m)!=G(pA,m) or G(pA,up)<G(pA,m): fails['C2b_ii']+=1
print("case1 instances",n1,"case2a",n2a,"case2b",n2b)
print(fails)
