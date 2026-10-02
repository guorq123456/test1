# Explicit examples, verified with ground truth /tmp/claude-0/qu/tools/uni (all instances in fit box).
# (1) two residue multisets with same (r,k,S,tau) [hence same U_inf] but different sharp L0;
# (2) same residue multiset, same a_min, different stabilization.
import subprocess
from core import *
def U_true(r,a,bmax):
    k=len(a); lines=[f"{r} {k} {' '.join(map(str,a))} {b}" for b in range(1,bmax+1)]
    out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input='\n'.join(lines)+'\n',capture_output=True,text=True).stdout.split()
    return [b for b,o in zip(range(1,bmax+1),out) if o=='1']
def report(r,a,R):
    assert in_box(r,a)
    F=sum(x//r for x in a); bmax=F+R.T+4
    U=U_true(r,a,bmax); target=list(range(1,F+1))+[F+e for e in R.Uinf]
    print(f"  r={r} a={a} F={F} U(a)={U} [1,F]u(F+Uinf)={target} stable={U==target}")
    return U==target
for (r,s) in [(7,(1,1,3,4,4,4,4,5,5)),(7,(1,2,2,4,4,4,4,4,6))]:
    R=Res(r,s); print(f"r={r} s={s} S={R.S} tau={R.tau} Uinf={R.Uinf} T={R.T} R2E7 L0={R.L0_R2E7()}")
    # verify U_inf on a large-part instance (min >= R2E7 L0)
    big=R.aL(max(2,R.L0_R2E7())); print(" large-part check:"); report(r,big,R)
    for L in [2,3]:
        print(f" a^{L}:"); report(r,R.aL(L),R)
print("Example 2 (same residues, same a_min=2):")
r=7; s=(1,2,2,4,4,4,4,4,6); R=Res(r,s)
report(r,sorted([2,2,4,4,4,4,4,6,8]),R)
report(r,sorted([2,9,11,11,11,11,11,13,8]),R)
report(r,sorted([2,9,4,4,4,4,4,6,8]),R)
print("Example 2b (r=5, residues (2,2,3^7), a_min=2 in both):")
r=5; R=Res(r,(2,2,3,3,3,3,3,3,3)); print("  Uinf",R.Uinf)
report(r,[2,7,8,8,8,8,8,8,8],R)
report(r,[2,2,8,8,8,8,8,8,8],R)
print("Example 2c (r=6, residues (2,2,2,3,4^5), a_min=2):")
r=6; R=Res(r,(2,2,2,3,4,4,4,4,4)); print("  Uinf",R.Uinf)
report(r,[2,8,8,9,10,10,10,10,10],R)
report(r,[2,2,8,9,10,10,10,10,10],R)
print("Example 2b sharp threshold: a^2, a^3 for r=5, s=(2,2,3^7), and a large-part instance")
r=5; R=Res(r,(2,2,3,3,3,3,3,3,3))
for L in [2,3]: print(" a^%d"%L, R.aL(L)); report(r,R.aL(L),R)
report(r,R.aL(max(2,R.L0_R2E7())),R)
