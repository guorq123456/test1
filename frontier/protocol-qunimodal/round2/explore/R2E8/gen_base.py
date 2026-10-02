# Generate the base family: r, three middle values m1<=m2<=m3 in [2,r-2], nm copies of r-1 (nm in 0..NM).
import sys, itertools
r=int(sys.argv[1]); NM=int(sys.argv[2])
for mids in itertools.combinations_with_replacement(range(2,r-1),3):
    for nm in range(NM+1):
        a=list(mids)+[r-1]*nm
        print(r,len(a),*a)
