# Certificate C3: analytic coverage (same bounds as analytic_cert2) with a fixed small V,
# for the fit-box-excluded residue classes (exactly 4 or 5 middle residues, k>=20):
#   r=5: V <= floor((2/5)(2 sin(pi/5) phi^5 + 2 sin(2pi/5) phi^-5)) = 5
#   r=6: V <= floor(2^5/3 + (1+sqrt3)/3) = 11
import sys
import analytic_cert2 as ac
r=int(sys.argv[1]); V=int(sys.argv[2]); lo,hi=int(sys.argv[3]),int(sys.argv[4])
ac.Vbound=lambda rr,k: V
bad={}
for k in range(lo,hi+1):
    b=ac.check(r,k)
    if b: bad[k]=b
print("r",r,"V",V,"k range",lo,hi,"uncovered:",sorted(bad))
