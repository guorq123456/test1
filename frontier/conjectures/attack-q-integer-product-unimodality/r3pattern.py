import numpy as np
from verify import poly, unimodal
r=3
for S in range(0,43):
    out=[]
    for extra in [(),(4,),(7,7),(5,),(4,10,13)]:
        a=(2,)*S+extra
        if not a: continue
        F=sum(x//r for x in a)
        # find set of b>=F+2 that are unimodal, up to F+2+30
        us=[b-F-2 for b in range(F+2,F+2+S+6) if unimodal(list(poly(a,b,r)))]
        out.append((extra,us))
    print(S,out)
