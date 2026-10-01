# SAT: does P(nu) admit a solution in the 'rising-edge parity' framework?
import sys; sys.path.insert(0,'/home/user/test1/minimizer-frontier')
from runlib import *
from w2 import build
from pysat.solvers import Cadical153
import time
def frame_units(nu):
    U={}
    for W in range(1<<nu):
        b=format(W,f'0{nu}b'); E=edges(b)
        if not E: U[W]=b.count('1')%2; continue
        ps={e['i']%2 for e in E}
        if len(ps)==1: U[W]=ps.pop()
    return U
def check(nu, units, enum=False, cap=10**6):
    pool,cl=build(nu,restricted=True)
    s=Cadical153(bootstrap_with=cl)
    var=lambda W: pool.id(('c',W))
    for W,v in units.items(): s.add_clause([var(W) if v else -var(W)])
    n=0; sols=[]
    while s.solve():
        mdl=set(l for l in s.get_model() if l>0)
        h=np.array([1 if var(W) in mdl else 0 for W in range(1<<nu)]); sols.append(h); n+=1
        if not enum or n>=cap: break
        s.add_clause([-var(W) if h[W] else var(W) for W in range(1<<nu)])
    return sols
if __name__=='__main__':
    for nu in map(int,sys.argv[1:]):
        t=time.time(); U=frame_units(nu)
        sols=check(nu,U,enum=(nu<=7))
        print(nu,'fixed',len(U),'of',1<<nu,'nsols',len(sols),'%.1fs'%(time.time()-t), [excess(h,nu) for h in sols[:1]])
