# Lemma CU (cyclic unimodality of class sums): for A=prod[a_i]_q, tau_t = Gamma_t - Gamma_{t-1}
# (Gamma_t = sum of alpha_n over n = t mod r).  Claim: tau_t > 0  =>  floor((D+1-2t)/r) is even.
import sys, random, itertools
sys.path.insert(0,'.')
from tcrit import poly_a
def check(a,r):
    al=poly_a(a); D=len(al)-1
    G=[sum(al[t::r]) for t in range(r)]
    bad=[]
    for t in range(r):
        tau=G[t]-G[(t-1)%r]
        F=sum(x//r for x in a)
        if tau>0 and ((D+1-2*t)//r - F)%2!=0: bad.append(t)
    return bad
if __name__=='__main__':
    mode=sys.argv[1]; n=0; nb=0
    if mode=='exh':
        r=int(sys.argv[2]); k=int(sys.argv[3]); amax=int(sys.argv[4])
        for a in itertools.combinations_with_replacement(range(1,amax+1),k):
            n+=1
            if check(list(a),r): nb+=1; print("BAD",r,a) if nb<5 else None
    else:
        random.seed(int(sys.argv[2])); N=int(sys.argv[3])
        for it in range(N):
            r=random.randint(2,30); k=random.randint(1,20)
            a=[random.randint(1,random.choice([r,3*r,100])) for _ in range(k)]
            a=[min(x,100) for x in a]
            n+=1
            if check(a,r): nb+=1; print("BAD",r,a) if nb<5 else None
    print(mode,sys.argv[2:],"tested",n,"violations",nb)
