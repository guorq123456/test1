# compare exact (uinf.py) vs closed form (rule_asym.py) along family block*m, k<=kmax
import sys
from uinf import uinf
from rule_asym import asym_tops
def run(r,block,kmax,verbose=False):
    p=len(block); errE=0; erro=0; erre=0; n=0; rows=[]
    for m in range(1,kmax//p+1):
        s=block*m; k=len(s)
        if k<3: continue
        ex=uinf(r,s); Xo,Xe,eo,ee=asym_tops(r,s)
        n+=1
        eE=(ex['E']!=eo-1); errE+=eE; erro+=(ex['e_odd']!=eo); erre+=(ex['e_even']!=ee)
        rows.append((k,ex['E'],eo-1,ex['e_odd'],eo,ex['e_even'],ee,round(Xo,3),round(Xe,3)))
    return n,errE,erro,erre,rows
if __name__=='__main__':
    r=int(sys.argv[1]); kmax=int(sys.argv[2]); block=list(map(int,sys.argv[3:]))
    n,a,b,c,rows=run(r,block,kmax)
    print('r',r,'block',block,'n',n,'E-errors',a,'eodd-err',b,'eeven-err',c)
    for row in rows:
        flag='' if (row[1]==row[2] and row[5]==row[6]) else ' <--'
        print(*row,flag)
