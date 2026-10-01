import numpy as np
from itertools import combinations_with_replacement
def pprod(a):
    c=np.array([1],dtype=object)
    for A in a:
        c=np.convolve(c,np.ones(A,dtype=object))
    return c
def withb(p,r,b):
    n=np.zeros(len(p)+r*(b-1),dtype=object)
    for y in range(b): n[r*y:r*y+len(p)]+=p
    return n
def unimodal(c):
    i=0;N=len(c)-1
    while i<N and c[i]<=c[i+1]: i+=1
    while i<N and c[i]>=c[i+1]: i+=1
    return i==N
NONDIV=[x for x in range(1,13) if x%3]
def box_instances(kmax=8):
    for k in range(1,kmax+1):
        for a in combinations_with_replacement(NONDIV,k):
            yield list(a)
