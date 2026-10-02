# Full certificate (TP,E,O) for rho = rho' + m ones, for strong-failing rho'
from reslev import *
cases=[(30,[3, 4, 5, 5, 6, 9, 14, 15, 16, 16, 17, 18, 18, 19]),(30,[6, 10, 11, 11, 13, 14, 14, 15, 15, 20, 21, 22, 24, 25]),(24,[2, 4, 7, 8, 8, 9, 9, 9, 9, 11, 13, 13, 15, 16])]
for r,rp in cases:
    R=Res(r,rp); print('r',r,'rho\'',rp,'tau',R.tau,'mu_neg',mu_neg(r,R.tau))
    for m in [0,1,2,5,10,20,40,80,120]:
        rho=[1]*m+rp
        if not inbox(r,rho): print('skip',m); continue
        c=certificate(r,rho)
        print(' m',m,'k',len(rho),'mu*_inf',c['mu'],'TP',c['TP'],'E',c['E'],'O',c['O'],c['Ofail'],flush=True)
