# Evaluate every candidate statement tried on this path on a common fit-box test set; write candidates.txt.
# Test set T: (1) all multisets a with r in {4,5,6,7}, entries <= 2r+1 not divisible by r, k <= 6;
#             (2) equal-part families a=(t^k), r in 4..10, t in 1..r-1, k<=60;
#             (3) N1 / T7 instances from the brief.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS, Jset, Uset, Fval, S2_shape, T6
from limit import tau, Jinf
from decomp import bad_set, P_ok
from structure_helpers import mu_of
from s3star import estar
import s3star_rule as S

def testset():
    for r in (4, 5, 6, 7):
        vals = [x for x in range(1, 2 * r + 2) if x % r]
        for k in range(1, 7):
            for a in itertools.combinations_with_replacement(vals, k):
                yield r, list(a)
    for r in range(4, 11):
        for t in range(1, r):
            for k in range(1, 61):
                yield r, [t] * k
    yield 6, [2, 3, 3, 4, 4, 4, 5]
    yield 6, [2, 3, 4, 4, 4, 4, 4, 8]
    yield 6, [2, 2, 3, 4, 4, 4, 4, 10]

names = {
 'C01 S2 (target)': 0, 'C02 J(a) is a prefix of J_inf(rho)': 0,
 'C03 S3: U in {[1,T6],[1,T6]-{T6-1},[1,T6-2]}': 0,
 'C04 small-part instance alone certifies lifts: [0,E6-2] subset J(rho)': 0,
 'C05 A1: Bad(a) subset [0,mu]': 0, 'C06 P(K) fails only for K in {1,2} (small parts)': 0,
 'C07 S3*: U in {[1,B],[1,B]-{B-1}}, B from first negative coeff y* of A/[r]': 0,
 'C08 Par*: every y with d_y<0 has floor((2y-D-1)/r)=F mod 2': 0,
 'C09 bound: U subset [1,B]': 0,
 'C10 ND-even holds for all K (even family)': 0, 'C11 ND-odd holds for K>=2mu*+2r': 0,
 'C12 d nondecreasing on [0,D/2]': 0,
 'C13 E6=0 for k<=3': 0,
 'C14 rule s3star_rule.predict matches ground truth (per b)': 0,
}
tested = {k: 0 for k in names}
def bump(name, ok):
    tested[name] += 1
    if not ok: names[name] += 1

for r, a in testset():
    ds = DS(r, a); tt = tau(r, a); D = ds.D; F = Fval(r, a)
    rho = sorted(x % r for x in a); sigma = sum(x - 1 for x in rho); mu = mu_of(tt, r)
    e6 = (sigma + 1 - 2 * mu) // r
    J = Jset(r, a); U = [1 + F + j for j in J]; U = list(range(1, F + 1)) + U
    bump('C01 S2 (target)', S2_shape(J))
    if len(a) <= 6 or len(set(a)) == 1:
        Ji = Jinf(r, rho)
        bump('C02 J(a) is a prefix of J_inf(rho)', J == [x for x in Ji if x <= max(J)])
    full = list(range(e6 + 1))
    bump('C03 S3: U in {[1,T6],[1,T6]-{T6-1},[1,T6-2]}', J in (full, [x for x in full if x != e6 - 1], list(range(max(e6 - 1, 1)))))
    if all(x < r for x in a):
        bump('C04 small-part instance alone certifies lifts: [0,E6-2] subset J(rho)', set(range(max(e6 - 1, 0))) <= set(J))
        K = (sigma + 1) % r; okp = True
        while K <= sigma + 1 - 2 * r:
            if K not in (1, 2) and not P_ok(r, ds, tt, K): okp = False
            K += r
        bump('C06 P(K) fails only for K in {1,2} (small parts)', okp)
    bad = bad_set(r, a, ds, tt)
    bump('C05 A1: Bad(a) subset [0,mu]', all(u <= mu for u in bad))
    B = S.Bvalue(r, a)
    Uf = [b for b in range(1, B + 3) if b in U or (b <= F)]
    bump('C07 S3*: U in {[1,B],[1,B]-{B-1}}, B from first negative coeff y* of A/[r]',
         Uf in (list(range(1, B + 1)), [x for x in range(1, B + 1) if x != B - 1]))
    okp = all(((2 * y - D - 1) // r - F) % 2 == 0 for y in range(0, D + r + 1) if ds(y) < 0)
    bump('C08 Par*: every y with d_y<0 has floor((2y-D-1)/r)=F mod 2', okp)
    bump('C09 bound: U subset [1,B]', max(Uf) <= B)
    E, ms, _ = estar(r, a, ds, tt)
    K = (D + 1) % r - 4 * r; oke = oko = True
    while K <= D + 1 - 2 * r:
        even = ((K - sigma - 1) % (2 * r)) == 0
        nd = all(ds(K - x) - tt[(K - x) % r] >= ds(x) for x in range((K - r) // 2 - 1, (K + 1) // 2 + 1) if K - r <= 2 * x < K)
        if even and not nd: oke = False
        if (not even) and K >= 2 * ms + 2 * r and not nd: oko = False
        K += r
    bump('C10 ND-even holds for all K (even family)', oke)
    bump('C11 ND-odd holds for K>=2mu*+2r', oko)
    bump('C12 d nondecreasing on [0,D/2]', all(ds(y) >= ds(y - 1) for y in range(1, D // 2 + 1)))
    if len(a) <= 3: bump('C13 E6=0 for k<=3', e6 == 0)
    for b in range(1, B + 3):
        bump('C14 rule s3star_rule.predict matches ground truth (per b)', S.predict(r, a, b) == (b in Uf))

with open('/tmp/claude-0/qu/explore2/R2E2/candidates.txt', 'w') as f:
    f.write("# Candidates tried on path R2E2 (peeling induction for S2). Error counts on fit-box test set T\n")
    f.write("# T = all multisets r in {4..7}, parts<=2r+1 (r not dividing), k<=6; equal-part families r<=10,k<=60; N1/T7 instances.\n")
    for k in names:
        line = f"{k}: tested {tested[k]}, violations {names[k]}"
        print(line); f.write(line + "\n")
