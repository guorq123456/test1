# Rigorous (ball arithmetic, python-flint arb) computation of A228016 directly from its definition.
# H(k) = digamma(k+1) + Euler gamma, enclosed in an arb ball; every comparison must be certified.
import sys, time
sys.set_int_max_str_digits(0)
from flint import arb, ctx, fmpz
N = int(sys.argv[1])
def H(k, ):
    if k == 0: return arb(0)
    return (arb(k+1)).digamma() + arb.const_euler()
def gt(a,b):  # certified a>b ; returns True/False, or None if undecided
    d = a-b
    if d > 0: return True
    if d < 0: return False
    return None
seq = []
p2, p1 = 0, 5
t0 = time.time()
for n in range(1, N+1):
    bits = 2*max(p1,2).bit_length() + 256
    ctx.prec = bits
    T = 2*H(p1) - H(p2)
    # candidate from inversion H(w) ~ log(w+1/2) + gamma
    w = (T - arb.const_euler()).exp() - arb(0.5)
    k = int(w.mid().floor().unique_fmpz()) + 1 if True else None
    k = max(k, 1)
    steps = 0
    while True:
        steps += 1
        if steps > 50: raise SystemExit("too many adjust steps at n=%d" % n)
        c_hi = gt(H(k), T)      # H(k) > T ?
        c_lo = gt(T, H(k-1))    # H(k-1) < T ?
        if c_hi is None or c_lo is None:
            raise SystemExit("undecided at n=%d k=%d" % (n,k))
        if c_hi and c_lo: break
        if not c_hi: k += 1
        elif not c_lo: k -= 1
    # '<=' variant also: need H(k-1) != T (certified strict) -> c_lo True already strict
    seq.append(k)
    p2, p1 = p1, k
    if n % 100 == 0 or n <= 12:
        print(n, str(k)[:30], "len", len(str(k)), "steps", steps, "t=%.1f" % (time.time()-t0), flush=True)
with open(sys.argv[2] if len(sys.argv)>2 else "arb_seq.txt","w") as f:
    for i,v in enumerate(seq,1): f.write("%d %d\n" % (i,v))
print("done", N)
