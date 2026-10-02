# Tabulate X=|U|-1-F for r in [R0,R1], all middle multisets, n1 in N1 list, nm in [0,NMMAX],
# using canonical rep (middle a=rho, r-1 elements a=r-1, residue-1 elements a=r+1), plus R random reps (f in 0..FM).
import sys, itertools, random, pickle
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
from core import *
R0,R1,NMMAX,NREP,FM=map(int,sys.argv[1:6]); N1=list(map(int,sys.argv[6].split(',')))
random.seed(7)
tab={}; incons=[]
for r in range(R0,R1+1):
  for mids in itertools.combinations_with_replacement(range(2,r-1),3):
    for n1 in N1:
      for nm in range(NMMAX+1):
        res=list(mids)+[1]*n1+[r-1]*nm
        if len(res)>40: continue
        reps=[[rho if rho!=1 else r+1 for rho in res]]
        for _ in range(NREP):
            reps.append([rho+r*random.randint(1 if rho==1 else 0, min(FM,(100-rho)//r)) for rho in res])
        Xs=set(); info=None
        for a in reps:
            a=sorted(a); D,F,Gam,mu,T6=stats(r,a); U=Uset(r,a)
            if list(U)!=list(range(1,len(U)+1)): Xs.add(('nonint',tuple(U),F)); continue
            Xs.add(len(U)-1-F); info=(T6-1-F,mu)
        tab[(r,mids,n1,nm)]=(Xs,info)
        if len(Xs)>1: incons.append(((r,mids,n1,nm),Xs)); print("INCONS",r,mids,n1,nm,Xs)
pickle.dump(tab,open(f'table_{R0}_{R1}_{NMMAX}_{NREP}_{FM}_{sys.argv[6]}.pkl','wb'))
print("entries",len(tab),"inconsistent",len(incons))
