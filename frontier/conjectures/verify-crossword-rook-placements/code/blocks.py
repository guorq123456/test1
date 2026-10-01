import itertools, subprocess, sys
from sympy.functions.combinatorial.numbers import stirling
from math import factorial
def fam(n):
    return max(sum((int(stirling(m,k))*k**(n-2*m)*factorial(k))**2 for k in range(1,m+1)) for m in range(1,n//2+1))
for n in (14,15,16):
    best_fam = fam(n)
    for a in (3,4,5,6):
        for b in (a-1,a):
            mid = n-a-b
            if mid < 1 or mid > 8: continue
            lines=[str(n)]
            for s in itertools.permutations(range(a+1, a+mid+1)):
                w=list(range(a,0,-1))+list(s)+list(range(n,n-b,-1))
                lines.append(' '.join(map(str,w)))
            out=subprocess.run(['./batch'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
            vals=list(map(int,out))
            mx=max(vals); i=vals.index(mx)
            print(n,a,b,'best',mx,'w=',lines[1+i],'family max',best_fam,'EXCEEDS' if mx>best_fam else '', flush=True)
