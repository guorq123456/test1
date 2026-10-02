# Rerunnable exact check of the witness pairs used in proof_nonexistence.txt.
# For each pair: same r, k, residue multiset, sum, product => same F, D, Gamma vector (Lemma 2), checked directly too.
# U computed with two independent exact checkers (tools/uni in C __int128, and tools/uni_ref.py pure Python)
# for b = 1..T6+2; Thm C gives b > T6 not in U.
import subprocess, sys
from math import prod
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from uni_ref import poly, unimodal
from core import inv, Apoly
PAIRS=[(20,[1,14,59,65,79,105,123],[3,14,21,59,65,79,205]),
       (12,[1,11,29,42,129,189],[9,9,11,29,42,301]),
       (13,[1,8,27,33,38,110,114],[6,8,10,27,33,38,209])]
def gt_c(r,a,bs):
    lines='\n'.join(f"{r} {len(a)} {' '.join(map(str,a))} {b}" for b in bs)+'\n'
    o=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input=lines,capture_output=True,text=True).stdout.split()
    return [b for b,x in zip(bs,o) if x=='1']
def T6of(r,a):
    D,F,tau,Gam=inv(r,a)
    mu=next(t for t in range(r) if all(Gam[u]>=Gam[u+1] for u in range(t,r-1)))
    return 1+(D+1-2*mu)//r, mu
for r,a,b in PAIRS:
    print('r',r,'a',a,"a'",b)
    mid=lambda x: 2<=x%r<=r-2
    print('  k',len(a),len(b),' residues equal',sorted(x%r for x in a)==sorted(x%r for x in b),
          ' #middle',sum(map(mid,a)),sum(map(mid,b)),' others in {1,r-1}',all(x%r in (1,r-1) for x in a+b if not mid(x)))
    print('  sum',sum(a),sum(b),' prod',prod(a),prod(b))
    ia=inv(r,a); ib=inv(r,b)
    print('  D,F',ia[:2],ib[:2],' tau equal',ia[2]==ib[2],' Gamma equal',ia[3]==ib[3])
    print('  Gamma',ia[3])
    Ta,mua=T6of(r,a); Tb,mub=T6of(r,b); print('  mu',mua,mub,'T6',Ta,Tb)
    Ua=gt_c(r,a,range(1,Ta+3)); Ub=gt_c(r,b,range(1,Tb+3))
    Ua2=[x for x in range(1,Ta+3) if unimodal(poly(r,a,x))]; Ub2=[x for x in range(1,Tb+3) if unimodal(poly(r,b,x))]
    print('  U(a) =',Ua,' (python ref agrees:',Ua==Ua2,')')
    print("  U(a')=",Ub,' (python ref agrees:',Ub==Ub2,')')
