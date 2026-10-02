"""Second batch of candidates: asymptotic formula with the second-order (Stirling + amplitude) constant.
X = c k - kappa ln k - 2(ln mu - ln A0(theta*))/(r lambda),  E_pred = 2 floor((X+beta)/2)
A0(t) = sqrt((1+t)/(2 pi t)) / (t (1+t)^2 (1-(t/(1+t))^r)),  lambda = ln(1+1/theta*)
C9 : mu = mu0 = (4/r) sin(pi j*/r)  (amplitude of dominant Fourier mode of tau)
C10: mu = M e^{-kL} (exact, fluctuating)
"""
import sys, json, math
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from b4limit import tau_of
from theory import asym_pred, ell
from candidates_eval import evaluate


def A0(t, r):
    return math.sqrt((1 + t) / (2 * math.pi * t)) / (t * (1 + t) ** 2 * (1 - (t / (1 + t)) ** r))


def make(name, beta):
    def E_pred(r, a):
        s = [x % r for x in a]; k = len(a)
        q = asym_pred(r, s)
        th = q['theta']; lam = math.log(1 + 1 / th)
        js = max(range(1, r), key=lambda j: ell(r, s, j))
        if name == 'C9':
            mu = 4 / r * math.sin(math.pi * js / r)
        else:
            tau = tau_of(r, s); M = max(-t for t in tau)
            mu = math.exp(math.log(M) - k * q['L'])
        X = q['withlog'] - 2 * (math.log(mu) - math.log(A0(th, r))) / (r * lam)
        return 2 * math.floor((X + beta) / 2)
    return E_pred


rows = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
for name in ['C9', 'C10']:
    best = None
    for i in range(-40, 41):
        beta = i / 10
        ev = evaluate(rows, make(name, beta))
        if best is None or ev[0] < best[1][0]:
            best = (beta, ev)
    print(name, "free=1 best beta=%.1f errors(pairs, instances) =" % best[0], best[1], flush=True)
