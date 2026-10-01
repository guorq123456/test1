# Count fit errors of rule files on the entire fit box (all 37,790,700 instances).
import importlib.util, sys
from load import load
recs=load()
for fn in sys.argv[1:]:
    spec=importlib.util.spec_from_file_location('rule',fn); M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
    err=0; n=0; outdom=0
    for r,a,m in recs:
        if not M.domain(r,list(a)): outdom+=60; continue
        for b in range(1,61):
            n+=1
            if bool(M.predict(r,list(a),b))!=bool((m>>(b-1))&1): err+=1
    print(fn,'instances in domain',n,'out of domain',outdom,'errors',err)
