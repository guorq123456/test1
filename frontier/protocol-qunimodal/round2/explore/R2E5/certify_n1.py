# Certify E(1) = E_inf for 4<=r<=30, 2<=s<=r-2, 3<=k<=60 using the Window Lemma with the true g for a=r+s (exact integers).
# E(1) computed from g^(1) = [r+s]^k (1-q)/(1-q^r); E_inf from c = 1/((1-q)^(k-1)(1-q^r)); tau from [s]^k.
import sys
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import poly_a
from core import gseries
from rule_allequal_middle import _tau, _c
def wset(r,s,k,h,tau):
    out=[]
    for e in range(1,(k*(s-1)+1)//r+3):
        K=k*(s-1)+1-r*(2+e); M=(K-1)//2
        H=lambda j: h[j] if j>=0 else 0
        if all(tau[m%r]+H(K-m)-H(m)>=0 for m in range(M,M-r,-1)): out.append(e)
    return out
bad=0;tot=0;rows=[]
R=int(sys.argv[1]) if len(sys.argv)>1 else 30
for r in range(4,R+1):
    for s in range(2,r-1):
        for k in range(3,61):
            tau=_tau(r,s,k); L=k*(s-1)//2+2*r+4
            g1=gseries(poly_a([r+s]*k),r,L); c=_c(r,k,L)
            E1=wset(r,s,k,g1,tau); Ei=wset(r,s,k,c,tau)
            tot+=1
            if E1!=Ei: bad+=1; print('DIFF',r,s,k,E1,Ei)
            ev=[e for e in Ei if e%2==0]; od=[e for e in Ei if e%2==1]
            rows.append((r,s,k,max(ev) if ev else 0,max(od) if od else -1))
with open('Einf_table.txt','w') as f:
    f.write('# r s k E_even E_odd   (E_inf = odd e<=E_odd and even 2<=e<=E_even; E_odd=-1 means none)\n')
    for x in rows: f.write(' '.join(map(str,x))+'\n')
print('triples',tot,'E(1)!=E_inf:',bad)
