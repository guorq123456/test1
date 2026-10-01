# Mechanical checks of the finite case analyses used in proof_r3.txt, plus fit-box sanity checks of each lemma.
# Only residue-level computations and fit-box instances (r=3, k<=8, a_i<=12) are used.
import numpy as np, itertools
ok=True
def check(c,msg):
    global ok
    if not c: ok=False; print('FAIL:',msg)
# ---------- (a) p-table: Q = (1+q)^{n2 mod 6} mod Phi3, tail of R/Phi3 ----------
def polymod_phi3(c):
    c=list(c)
    for i in range(len(c)-1,1,-1):   # q^i = -q^{i-1}-q^{i-2} mod Phi3
        v=c[i]; c[i]=0; c[i-1]-=v; c[i-2]-=v
    return (c+[0,0])[:2]
def series_over_phi3(R,L):  # power series coefficients of R/(1+q+q^2)
    F=[0]*L
    for t in range(L):
        F[t]=(R[t] if t<len(R) else 0)-(F[t-1] if t>=1 else 0)-(F[t-2] if t>=2 else 0)
    return F
ptab={}
for j in range(6):
    from math import comb
    R=polymod_phi3([comb(j,i) for i in range(j+1)])   # (1+q)^j, increasing powers
    S=series_over_phi3(R,30)
    ptab[j]=tuple(int(S[27+c]) for c in range(3))   # residue c of index (27+c) = c mod 3
    check(all(S[t]==S[t-3] for t in range(5,30)),'periodicity')
print('p table (p_0,p_1,p_2) by n2 mod 6:',ptab)
expected={0:(1,-1,0),1:(1,0,-1),2:(0,1,-1),3:(-1,1,0),4:(-1,0,1),5:(0,-1,1)}
check(ptab==expected,'p table matches proof')
P=lambda n,t: expected[n][t%3]
# ---------- (b) necessity: y0 and inequalities, symbolic in M (check offsets) ----------
for n in range(6):
    # W* = M - n ; tail values F_{M-1},F_M,F_{M+1} with M = n mod 3
    for Mbase in range(n, n+60, 6):   # several M with M = n2 (mod 3) and M>=n2 ... only residue matters
        M=Mbase
        tail=[P(n,M-1),P(n,M),P(n,M+1)]
        y0=[M-1,M,M+1][[v<0 for v in tail].index(True)]
        check(all(v>=0 for v in tail[:[M-1,M,M+1].index(y0)]),'first negative')
        Wst=M-n
        W=Wst+3
        check(y0>=1 and y0-W-3<0 and 2*y0<=M+W,'necessity witness n=%d M=%d'%(n,M))
        check(P(n,y0)==-1,'witness value -1')
        # and for W<=W*: no tail index y in [M-1, floor((M+W)/2)] has p_y<0
        for W in range(0,Wst+1,3):
            for y in range(max(M-1,1),(M+W)//2+1):
                check(P(n,y)>=0,'tail ok for W<=W*')
print('necessity witnesses and tail checks done')
# ---------- (c) case (T): p_x>=0 for K+1<=x<K/2, K>=K*=(n2 mod 6)-5, K = M+1 = n2+1 (mod 3) ----------
for n in range(6):
    for K in range(n-5, 40):
        if (K-(n+1))%3: continue
        for x in range(K+1, 200):
            if not 2*x<K: break
            check(P(n,x)>=0,'(T) n=%d K=%d x=%d'%(n,K,x))
print('(T) checks done')
# ---------- (d) k=2 same-block residue check ----------
for n in range(3):            # k=2, a_i>=4 -> n2 in {0,1,2}, M = n2 (mod 3)
    for r1 in range(3):
        for r2 in range(r1+1,3):
            if (r1+r2-(n+1))%3==0:
                check(P(n,r1)>=0,'k=2 block n2=%d (%d,%d)'%(n,r1,r2))
print('k=2 block checks done')
# ---------- (e) fit-box sanity checks of lemmas ----------
vals=[v for v in range(1,13) if v%3]
def Fser(Q,lo,hi):
    D={}
    for t in range(len(Q)+1):
        D[t]=(Q[t] if t<len(Q) else 0)-(Q[t-1] if t>=1 else 0)
    F={}
    for t in range(lo,hi):
        F[t]=sum(D.get(s,0) for s in range(t,-1,-3)) if t>=0 else 0
    return F
cnt_case2=0
for k in range(1,9):
    for a in itertools.combinations_with_replacement(vals,k):
        M=sum(x-1 for x in a); n2=sum(1 for x in a if x%3==2); Wst=M-n2%6
        Q=np.array([1],dtype=np.int64)
        for A in a: Q=np.convolve(Q,np.ones(A,dtype=np.int64))
        Q=[int(v) for v in Q]
        F=Fser(Q,-12,M+12)
        # reflection identity F_t = F_{M-2-t} + p_t
        for t in range(-8,M+8):
            if -12<=M-2-t<M+12: check(F[t]==F[M-2-t]+P(n2%6,t),'reflection %s t=%d'%(a,t))
        if k<2: continue
        Wsub=[ (M-(x-1)) - ((n2-(x%3==2))%6) for x in a ]   # W*(a minus one factor)
        for W in range(0,Wst+1,3):
            if any(W<=ws for ws in Wsub): continue
            cnt_case2+=1
            K=M-W-5; amin=min(a)
            check(K<=amin-4,'case2 K<=amin-4 %s W=%d'%(a,W))
            check(all(x>=2 for x in a) and all(x!=2 or n2%6==0 for x in a),'case2 factor shape')
            for z in range(0,M):
                if not 2*z<M-4: break
                check(F[z]>=1,'(L) F_z>=1 %s z=%d'%(a,z))
            # f_k formula for t<amin
            for t in range(0,amin):
                fk=sum( (lambda s: __import__('math').comb(s+k-2,k-2) if s>=0 else 0)(t-3*j) for j in range(t//3+1))
                check(F[t]==fk,'f_k %s t=%d'%(a,t))
print('case-2 instances in box:',cnt_case2)
print('ALL CHECKS PASSED' if ok else 'SOME CHECK FAILED')
