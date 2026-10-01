# Generate, for r=3 and every multiset a (k=1..8, a_i<=12, 3 does not divide a_i),
# the set of b in [1,60] for which P is unimodal. Output: data.tsv with columns
# a (comma-sep) ; bitstring of length 60 (b=1..60) ; critical B = max b such that all b'<=b unimodal ;
# isthreshold flag (unimodal set == [1..B]).
import numpy as np, itertools, sys
R=3; BMAX=60; KMAX=8; AMAX=12
vals=[v for v in range(1,AMAX+1) if v%R!=0]
def Qpoly(a):
    c=np.array([1],dtype=np.int64)
    for A in a:
        c=np.convolve(c,np.ones(A,dtype=np.int64))
    return c
def unimodal(c):
    d=np.diff(c)
    neg=np.nonzero(d<0)[0]; pos=np.nonzero(d>0)[0]
    if len(neg)==0 or len(pos)==0: return True
    return neg[0]>pos[-1]
out=open('/tmp/claude-0/qu/explore/E8/data.tsv','w')
for k in range(1,KMAX+1):
    for a in itertools.combinations_with_replacement(vals,k):
        Q=Qpoly(a)
        L=len(Q)+R*(BMAX-1)
        P=np.zeros(L,dtype=np.int64)
        bits=[]
        for b in range(1,BMAX+1):
            s=R*(b-1)
            P[s:s+len(Q)]+=Q
            bits.append('1' if unimodal(P[:len(Q)+s]) else '0')
        bs=''.join(bits)
        B=bs.find('0'); B = BMAX if B<0 else B
        thr = ('0' not in bs[B:]) if B<BMAX else True
        thr = bs[B:].count('1')==0
        out.write(f"{','.join(map(str,a))}\t{bs}\t{B}\t{int(thr)}\n")
out.close()
