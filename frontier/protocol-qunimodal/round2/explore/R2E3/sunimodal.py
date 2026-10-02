# Test: is s_m = alpha_m - alpha_{m-1} (0<=m<=H=floor(D/2)) unimodal for A = prod [a_i]_q ?
import sys, itertools, random
sys.path.insert(0,'.')
from tcrit import poly_a
def unimod(c):
    i=0;N=len(c)-1
    while i<N and c[i]<=c[i+1]: i+=1
    while i<N and c[i]>=c[i+1]: i+=1
    return i==N
def s_of(a):
    al=poly_a(a); D=len(al)-1; H=D//2
    return [al[0]]+[al[m]-al[m-1] for m in range(1,H+1)]
if __name__=='__main__':
    k=int(sys.argv[1]); amax=int(sys.argv[2]); cnt=0; bad=0
    for a in itertools.combinations_with_replacement(range(1,amax+1),k):
        cnt+=1
        s=s_of(list(a))
        if not unimod(s):
            bad+=1
            if bad<=8: print("NONUNIMODAL s:",a,s)
    print("k",k,"amax",amax,"tuples",cnt,"non-unimodal s",bad)
