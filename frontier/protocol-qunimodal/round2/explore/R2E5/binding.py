# for given r,s,k list, for e near the threshold, the r conditions Phi(m)=tau_m + c_{K-m}-c_m at the r largest m<K/2
import sys
from flat import tau_of, cser
def phis(r,s,k,e):
    tau=tau_of(r,s,k); K=k*(s-1)+1-r*(2+e)
    c=cser(r,k,max(0,K)+4*r+10)
    cc=lambda j: c[j] if j>=0 else 0
    m0=(K-1)//2
    return K,[(m,m%r,(K-m)-m,tau[m%r],cc(K-m)-cc(m),tau[m%r]+cc(K-m)-cc(m)) for m in range(m0,m0-r,-1)]
if __name__=='__main__':
    r,s,k=map(int,sys.argv[1:4])
    print('tau',tau_of(r,s,k))
    for e in range(1,int(sys.argv[4])+1):
        K,L=phis(r,s,k,e)
        bad=[x for x in L if x[5]<0]
        print('e',e,'K',K,'fail' if bad else 'ok', [(x[0],x[2],x[5]) for x in L])
