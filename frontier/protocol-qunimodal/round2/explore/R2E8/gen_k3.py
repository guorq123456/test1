# Generate all k=3 triples a1<=a2<=a3<=AMAX with all residues mod r in [2,r-2], r in [R0,R1]
import sys
R0,R1,AMAX=map(int,sys.argv[1:4])
for r in range(R0,R1+1):
    xs=[x for x in range(2,AMAX+1) if 2<=x%r<=r-2]
    for i in range(len(xs)):
        for j in range(i,len(xs)):
            for l in range(j,len(xs)):
                print(r,3,xs[i],xs[j],xs[l])
