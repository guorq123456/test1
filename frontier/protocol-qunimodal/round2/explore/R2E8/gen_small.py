# Generate 3-middle instances: all middle multisets, middle f in {0,1}, nm in 0..NM with (r-1)-elements
# a=r-1 (f=0) or 2r-1 (f=1) [all same], n1 in 0..N1 with a=r+1. r in [R0,R1].
import sys, itertools
R0,R1,NM,N1=map(int,sys.argv[1:5])
for r in range(R0,R1+1):
    seen=set()
    for mids in itertools.combinations_with_replacement(range(2,r-1),3):
        for fv in itertools.product((0,1),repeat=3):
            m=tuple(sorted(x+r*f for x,f in zip(mids,fv)))
            if m in seen: continue
            seen.add(m)
            for nm in range(NM+1):
                for fm in ((0,1) if nm else (0,)):
                    for n1 in range(N1+1):
                        a=sorted(list(m)+[r-1+r*fm]*nm+[r+1]*n1)
                        if max(a)>100: continue
                        print(r,len(a),*a)
