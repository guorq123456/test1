# Direct verification (via certificate(), i.e. ND checks over the full O range) that O_rho fails for
# rho = rho' + m ones; finds the minimal such m (k = k'+m <= 140, fit box checked).
from reslev import *
cases=[(57,[6, 7, 9, 15, 18, 20, 22, 23, 25, 26, 27, 28, 30, 33, 37]),
       (50,[7, 13, 14, 14, 15, 17, 18, 22, 22, 23, 25, 26, 28, 32, 33, 39, 43]),
       (31,[3, 6, 6, 9, 9, 10, 12, 12, 12, 13, 13, 14, 15, 16, 17, 17, 18, 26, 27]),
       (28,[2, 3, 5, 5, 6, 7, 7, 7, 9, 10, 11, 12, 12, 13, 13, 17, 17, 18, 18, 23, 23]),
       (21,[5, 5, 6, 8, 8, 8, 8, 9, 9, 9, 9, 10, 11, 11, 12, 14, 14, 15, 15, 16, 16, 16, 17, 18, 18, 19, 19, 20, 20])]
for r,rp in cases:
    lo=None
    for m in range(0,141-len(rp)):
        rho=[1]*m+rp
        assert inbox(r,rho)
        c=certificate(r,rho)
        if not c['O']:
            lo=m; print('r',r,"k'",len(rp),'minimal m',m,'k',len(rho),'sigma',c['sigma'],'mu*_inf',c['mu'],'TP',c['TP'],'E',c['E'],'O fails at j',c['Ofail'],flush=True); break
    if lo is None: print('r',r,'no failure up to k=140')
