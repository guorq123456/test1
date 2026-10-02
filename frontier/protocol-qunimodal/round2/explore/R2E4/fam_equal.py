# Family A: all a_i equal, r in 4..30, a<=100 with middle residue, k=3..60 (whole fit box for this family).
import sys,json
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E4')
from core import *
from multiprocessing import Pool
def mul(c,A):
    n=len(c)+A-1; d=[0]*n; s=0; L=len(c)
    for t in range(n):
        if t<L: s+=c[t]
        if 0<=t-A<L: s-=c[t-A]
        d[t]=s
    return d
def task(ra):
    r,a=ra; res=[]
    c=[1]
    for k in range(1,61):
        c=mul(c,a)
        if k<3: continue
        z=analyze(r,[a]*k,A=c)
        res.append((r,a,k,z['holds'],z['shape'],z['parity_ok'],z['Bstar'],z['F'],z['T6'],z['beyondT6'],z['close']))
    return res
if __name__=='__main__':
    tasks=[(r,a) for r in range(4,31) for a in range(1,101) if 2<=a%r<=r-2]
    tasks.sort(key=lambda t:-t[1])
    n=0;fails=[];shapes={}
    with Pool(4) as p, open('fam_equal.out','w') as f:
        for res in p.imap_unordered(task,tasks,chunksize=2):
            for row in res:
                n+=1; shapes[row[4]]=shapes.get(row[4],0)+1
                if not row[3] or row[9]: fails.append(row)
                f.write(json.dumps(row)+'\n')
    print('instances',n,'shapes',shapes,'S2 failures/beyondT6',len(fails))
    for x in fails[:20]: print(x)
