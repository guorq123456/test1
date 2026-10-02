# Adversarial sampler: tiny middle parts (values 2..8, n=0) with r large, plus residue 1/r-1 parts of varied sizes.
import sys, random, importlib.util
from core import U
mods=[]
for f in sys.argv[4:]:
    spec=importlib.util.spec_from_file_location(f,f); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); mods.append((f,m))
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); rhi=int(sys.argv[3])
err={f:0 for f,_ in mods}; inst=0; bad={}
for it in range(N):
    r=random.randint(10,rhi)
    nt=random.randint(1,4)
    mids=[random.randint(2,8) for _ in range(nt)]+[r*random.randint(0,(400-r)//r)+random.randint(2,r-2) for _ in range(4-nt)]
    n1=random.randint(0,6); nm=random.randint(0,14-n1)
    ext=[r*random.randint(1,(400-1)//r)+1 for _ in range(n1)]+[r*random.choice([0,0,1,random.randint(0,(400-r+1)//r)])+r-1 for _ in range(nm)]
    a=sorted(mids+ext)
    if any(x%r==0 for x in a) or sum(1 for x in a if 2<=x%r<=r-2)!=4 or max(a)>400: continue
    inst+=1; u,T6,_=U(r,a)
    for f,m in mods:
        for b in range(1,T6+3):
            if m.predict(r,a,b)!=(b in u): err[f]+=1; bad.setdefault(f,(r,a,u[-3:],T6))
print('inst',inst,err,bad)
