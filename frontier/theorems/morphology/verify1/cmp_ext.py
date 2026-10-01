import sys, re, ast
sys.path.insert(0,'.')
from fast import *
F={'A':A_seq,'B':B_seq,'C':C_seq,'D':D_seq}
cache={}
def get(L,k,n):
    key=(L,k)
    if key not in cache: cache[key]=F[L](402,k)
    return cache[key][n]
cnt=bad=0
for line in open('../extended_terms.txt'):
    m=re.match(r'([ABCD])\(N?M?,(\d+)\) [NM]=0\.\.(\d+).*?: (\[.*\])',line)
    if m:
        L,k=m.group(1),int(m.group(2)); arr=ast.literal_eval(m.group(4))
        for i,v in enumerate(arr):
            cnt+=1
            if get(L,k,i)!=v: bad+=1; print('mismatch',L,k,i)
        continue
    m=re.match(r'([ABCD])\((\d+),(\d+)\) = (\d+)',line)
    if m:
        L,n,k,v=m.group(1),int(m.group(2)),int(m.group(3)),int(m.group(4)); cnt+=1
        if get(L,k,n)!=v: bad+=1; print('mismatch',L,n,k)
print('compared',cnt,'bad',bad)
