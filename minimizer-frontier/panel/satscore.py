# For each candidate score, restrict h(W) to parities of the rising edges maximising the score; SAT-check feasibility.
from satframe import *
INF=100
def F(e,name):
    a,b,c,d=e['a'],e['b'],e['c'],e['d']
    mode=''
    while name[0] in 'TZ':
        mode+=name[0]; name=name[1:]
    if 'T' in mode:
        if e['ta']: a=INF
        if e['tb']: b=INF
    if 'Z' in mode:
        if e['ta']: a=0
        if e['tb']: b=0
    return {'sum':a+b,'min':min(a,b),'max':max(a,b),'prod':a*b,'absd':abs(a-b),'cd':c+d,
            'ext':a+b+c+d}[name]
def allowed_units(nu, key):
    U={}
    for W in range(1<<nu):
        b=format(W,f'0{nu}b'); E=edges(b)
        if not E: U[W]=b.count('1')%2; continue
        best=max(key(e) for e in E)
        ps={e['i']%2 for e in E if key(e)==best}
        if len(ps)==1: U[W]=ps.pop()
    return U
if __name__=='__main__':
    names=['sum','min','max','prod','absd','ext']
    for mode in ['','T','Z']:
        for nm in names:
            for sg in (1,-1):
                key=lambda e,n=mode+nm,sg=sg: sg*F(e,n)
                out=[]
                for nu in (7,9,11,13):
                    U=allowed_units(nu,key); sols=check(nu,U)
                    out.append((len(U),bool(sols)))
                    if not sols: break
                print(mode+nm, sg, out, flush=True)
