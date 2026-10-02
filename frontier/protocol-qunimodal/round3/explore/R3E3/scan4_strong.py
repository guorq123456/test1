# r=4: rho'=(2^n2,3^n3); TP and E/O with mu_lim (k->infinity limit) and with mu_inf(k=len)
import sys
from cert import Inst
from lib4 import in_box
r=4; tot=0; fl=[]; fk=[]
for n2 in range(0,60):
  for n3 in range(0,60):
    rho=[2]*n2+[3]*n3
    if not rho or not in_box(r,rho): continue
    s=Inst(r,rho); tot+=1
    tp=s.TP(); e1=s.EO(s.mu_lim()); e2=s.EO(s.mu_inf())
    if not tp or e1: fl.append((n2,n3,tp,e1[:3]))
    if not tp or e2: fk.append((n2,n3,tp,e2[:3]))
print("checked",tot,"strong-limit fails",len(fl),"k=len fails",len(fk))
print("min n2 among strong-limit fails:", min(x[0] for x in fl) if fl else None)
for x in fl[:40]: print("L",x)
for x in fk[:20]: print("K",x)
