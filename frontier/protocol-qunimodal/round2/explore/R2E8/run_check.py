# Read ufast output alongside input lines; report: count, non-interval U, H1 mismatches, X distribution
import sys,collections
inp=open(sys.argv[1]).read().split('\n'); out=open(sys.argv[2]).read().split('\n')
n=0; nonint=[]; mism=[]; Xd=collections.Counter()
for l,o in zip(inp,out):
    if not l.strip(): continue
    T6,F,Bh,bits=o.split(); T6=int(T6);F=int(F);Bh=int(Bh)
    n+=1
    m=len(bits)-len(bits.lstrip('1'))
    if '1' in bits[m:]: nonint.append((l,bits)); continue
    Xd[(T6-1-F, m-1-F)]+=1
    if m!=Bh: mism.append((l,T6,F,Bh,m))
print("n",n,"nonint",len(nonint),"H1 mismatch",len(mism))
print("(E6,X) dist",sorted(Xd.items())[:30])
for x in nonint[:10]: print("NONINT",x)
for x in mism[:20]: print("MISM",x)
