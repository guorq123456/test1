# evaluate a rule file on the full fit-box dataset (a_i in 2..12, r not | a_i, k<=8, b<=60, r=2..6)
# usage: python3 evalrule.py rules/rule_x.py [sample_fraction]
import sys, importlib.util, random
from load import load
spec=importlib.util.spec_from_file_location("rule",sys.argv[1]); R=importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
frac=float(sys.argv[2]) if len(sys.argv)>2 else 1.0
random.seed(7)
tot=0; err=0; outdom=0; per={}
for r in range(2,7):
    e_r=0; t_r=0
    for a,mask in load(r):
        if frac<1 and random.random()>frac: continue
        if hasattr(R,'domain') and not R.domain(r,a): outdom+=60; continue
        for b in range(1,61):
            t_r+=1
            if bool(R.predict(r,a,b))!=bool((mask>>(b-1))&1): e_r+=1
    per[r]=(e_r,t_r); tot+=t_r; err+=e_r
print(sys.argv[1],"frac",frac,"in-domain instances",tot,"errors",err,"out-of-domain",outdom,"per r (errors,instances):",per)
