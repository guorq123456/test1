# cross-validate s2enum (C) gap counts against core.analyze (python) on small exhaustive sets
import sys,itertools,subprocess
sys.path.insert(0,'.')
from core import *
for r,k,vmax in [(5,5,14),(6,6,13),(8,4,23),(7,5,13)]:
    vals=[v for v in range(1,vmax+1) if v%r]
    n=gap=viol=0
    for a in itertools.combinations_with_replacement(vals,k):
        if nmiddle(r,a)<3: continue
        z=analyze(r,list(a)); n+=1; gap+=z['shape']=='gap'; viol+=(not z['holds']) or z['beyondT6']
    out=subprocess.run(['./s2enum',str(r),str(k),'1',str(vmax),'3'],capture_output=True,text=True).stdout.strip().splitlines()[-1]
    print(r,k,vmax,'py: inst',n,'gap',gap,'viol',viol,'| C:',out)
