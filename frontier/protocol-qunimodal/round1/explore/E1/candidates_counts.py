# Error counts in the fit box (r=3, k<=8, a_i<=12 nondiv by 3, b<=60) for the rule candidates,
# and failure counts for proof-approach candidates (Lemma K, H unimodal).
from common import *
from explore_e import eseq, delta_fn
import subprocess
from rule_r3 import predict
lines=[];keys=[]
for a in box_instances():
    for b in range(1,61):
        lines.append("3 %d %s %d"%(len(a)," ".join(map(str,a)),b)); keys.append((a,b))
out=list(map(int,subprocess.run(["/tmp/claude-0/qu/tools/uni"],input="\n".join(lines)+"\n",capture_output=True,text=True).stdout.split()))
F=lambda a: sum(x//3 for x in a); S=lambda a: sum(1 for x in a if x%3==2)
R1=sum(1 for (a,b),o in zip(keys,out) if int(predict(3,a,b))!=o)
R0=sum(1 for (a,b),o in zip(keys,out) if int(b<=1+F(a))!=o)
print("instances",len(keys))
print("R1 prior rule b<=1+F+2floor(S/6): errors",R1)
print("R0 conj 5.4 condition b<=1+F: errors",R0)
# Lemma K: k_m = e_m - delta(m)/2 unimodal on [0,D-2]; H=(p-rho)/Phi3 unimodal
def unimod(x):
    i=0;N=len(x)-1
    while i<N and x[i]<=x[i+1]: i+=1
    while i<N and x[i]>=x[i+1]: i+=1
    return i==N
kfail=0;hfail=0;tot=0
for a in box_instances():
    a2=[x for x in a if x>=2]
    if not a2: continue
    p=[int(x) for x in pprod(a2)]; D=len(p)-1; dl=delta_fn(S(a2)); e=eseq(p,D+5)
    if D<2: continue
    tot+=1
    k=[2*e[m]-dl(m) for m in range(0,D-1)]
    h=[e[m]-dl(m) for m in range(0,D-1)]
    if not unimod(k): kfail+=1
    if not unimod(h): hfail+=1
print("polys",tot,"LemmaK(symmetrized e unimodal) failures",kfail,"H unimodal failures",hfail)
