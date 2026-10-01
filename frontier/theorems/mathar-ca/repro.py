# Exact re-implementation of Robert Price's Mathematica program (torus of size g=2*stages+1,
# ListConvolve with kernel {{0,2,0},{2,1,2},{0,2,0}} cyclic, new state = bit (c+2s) of code).
import numpy as np, sys
def run(code, stages=128):
    g = 2*stages+1
    a = np.zeros((g,g), dtype=np.int64); a[g//2, g//2] = 1
    bits = np.array([(code>>v)&1 for v in range(10)], dtype=np.int64)
    out = [a.copy()]
    ca = a
    for n in range(stages+1):
        v = ca + 2*(np.roll(ca,1,0)+np.roll(ca,-1,0)+np.roll(ca,1,1)+np.roll(ca,-1,1))
        ca = bits[v]
        out.append(ca)
    return out
def readouts(code, stages=128):
    out = run(code, stages)
    k = (2*stages+1+1)//2   # 1-based center index
    c = k-1                 # 0-based center
    right=[]; left=[]
    for i in range(1, stages):   # i = 1..stages-1, stage n=i-1
        n = i-1
        row = out[n][c]          # row through center
        r = row[c:c+n+1]         # origin .. right edge
        l = row[c-n:c+1]         # left edge .. origin
        right.append(int(''.join(map(str,r))))
        left.append(int(''.join(map(str,l))))
    return right, left
def bfile(A):
    d={}
    for line in open(f'/tmp/claude-0/deep/mathar-ca/b{A}.txt'):
        p=line.split()
        if len(p)==2 and not line.startswith('#'): d[int(p[0])]=int(p[1])
    return [d[i] for i in range(len(d))]
if __name__=='__main__':
    R451,L451 = readouts(451); R193,L193 = readouts(193)
    for A,v in [('282297',R451),('282295',L451),('279721',R193),('279720',L193)]:
        b=bfile(A)
        print('A'+A, len(b), 'all b-file terms reproduced:', v[:len(b)]==b)
    print('n>=2 R451==R193:', all(R451[n]==R193[n] for n in range(2,127)), 'diffs', [n for n in range(127) if R451[n]!=R193[n]])
    print('n>=2 L451==L193:', all(L451[n]==L193[n] for n in range(2,127)), 'diffs', [n for n in range(127) if L451[n]!=L193[n]])
