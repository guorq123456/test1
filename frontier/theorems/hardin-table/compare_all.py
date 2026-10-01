# Compare: theorem formula  vs  exhaustive brute force (brute_out.txt)  vs  transfer-matrix DP
# (dp.cpp outputs in dpout/, dp_big.py outputs in dpbig/)  vs  OEIS data and b-files.
import os, glob, subprocess
from fractions import Fraction
H='/tmp/claude-0/deep/hardin-table'
SMALL={(1,1):16,(1,2):39,(1,3):69,(2,1):39,(2,2):58,(2,3):70,(3,1):69,(3,2):73,(3,3):85}
def T(n,k):
    if n>=2 and k>=4: return 9*2**(n-1)+9*2**(k-1)+12
    if n==1 and k>=4: return 9*2**(k-1)+37
    if k==1 and n>=4: return 9*2**(n-1)+37
    if k==2 and n>=4: return 9*2**(n-1)+36
    if k==3 and n>=3: return 9*2**(n-1)+49
    return SMALL[(n,k)]
vals={}   # (n,k) -> set of (source,value)
def add(n,k,v,src):
    vals.setdefault((n,k),[]).append((src,v))
for line in open(f'{H}/brute_out.txt'):
    n,k,m,c=map(int,line.split()); add(n,k,c,'brute')
for f in glob.glob(f'{H}/dpout/W*_m*.txt'):
    b=os.path.basename(f)[1:-4]; W,m=b.split('_m'); W=int(W); m=int(m)
    for line in open(f):
        r,c=map(int,line.split())
        if m==0: add(r,W-1,c,'dp')
        else: add(W-1,r,c,'dp')
for f in glob.glob(f'{H}/dpbig/W*_m*.txt'):
    b=os.path.basename(f)[1:-4]; W,m=b.split('_m'); W=int(W); m=int(m)
    for line in open(f):
        r,c=map(int,line.split())
        if m==0: add(r,W-1,c,'dpbig')
        else: add(W-1,r,c,'dpbig')
bad=0
for (n,k),L in vals.items():
    for src,v in L:
        if v!=T(n,k): bad+=1; print("MISMATCH",n,k,src,v,T(n,k))
print("computed entries:",len(vals),"  computed values:",sum(len(L) for L in vals.values()),"  mismatches vs theorem:",bad)
print("max n with k>=..: computed entries with n,k>=4:",sum(1 for (n,k) in vals if n>=4 and k>=4))
# entries computed by >=2 independent methods
print("entries computed by >=2 independent runs:",sum(1 for L in vals.values() if len(L)>=2))
# OEIS b-file of A253435, read by antidiagonals: a(1)=T(1,1), then T(1,2),T(2,1), T(1,3),T(2,2),T(3,1),...
idx=[]
s=2
while len(idx)<2000:
    for n in range(1,s): idx.append((n,s-n))
    s+=1
bt=[tuple(map(int,l.split())) for l in open(f'{H}/b253435.txt') if l.strip() and not l.startswith('#')]
nb=0; ncomp=0
for i,v in bt:
    n,k=idx[i-1]
    if v!=T(n,k): nb+=1; print("bfile mismatch",i,n,k,v,T(n,k))
    if (n,k) in vals: ncomp+=1
print("b253435: terms",len(bt),"mismatches vs theorem",nb,"; terms also recomputed by brute/DP:",ncomp)
# other b-files
seqs={'253152':('col',1),'253429':('col',2),'253430':('col',3),'253431':('col',4),'253432':('col',5),'253433':('col',6),
      '253434':('col',7),'253436':('row',2),'253437':('row',3),'253438':('row',4),'253439':('row',5),'253440':('row',6),
      '253441':('row',7),'253428':('diag',0)}
for a,(typ,c) in seqs.items():
    fn=f'{H}/b{a}.txt'
    if not os.path.exists(fn) or os.path.getsize(fn)<10:
        subprocess.run(['curl','-sS','-o',fn,f'https://oeis.org/A{a}/b{a}.txt'])
    L=[tuple(map(int,l.split())) for l in open(fn) if l.strip() and not l.startswith('#')]
    nb=0; nd=0
    for i,v in L:
        n,k=(i,c) if typ=='col' else ((c,i) if typ=='row' else (i,i))
        if v!=T(n,k): nb+=1
        if (n,k) in vals: nd+=1
    print(f"A{a} ({typ} {c}): b-file terms {len(L)}, mismatches vs theorem {nb}, also recomputed by DP {nd}")
