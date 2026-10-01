"""Rule E4-refined (one-sided, PROVED direction only; same mechanism as proof.txt Lemma 4).

Greedy peeling: feed the factors a_i (in a given order) into the Lemma-4 recursion, but always
peel at the SMALLEST admissible d0 = min(L mod r, a' mod r, min(L,a')), and move every V-chain whose
length is divisible by r into U.  U-pieces are good for every b (proof.txt Lemma 3); a V-chain
q^j[L] is good iff L >= r(b-1) (proof.txt Lemma 2; L = r(b-1) is impossible since r does not
divide L).  Hence P is unimodal whenever  r(b-1) <= Lmin, Lmin = min length of a V-chain
(Lmin = +infinity if V is empty).  Using the ascending and the descending order of the a_i and
taking the larger Lmin is still a proof.  The greedy d0 is <= the d0 of proof.txt, so
Lmin >= r*sum floor(a_i/r) + 1 and this rule implies the plain rule (it is at least as strong).

predict(r,a,b): True if r(b-1) <= Lmin (proved); False otherwise (NOT a claim).
"""
import math

def _lmin(r, seq):
    # V as dict j -> multiplicity, chains centred at D/2: length L = D+1-2j
    D = 0
    V = {0: 1}
    for ap in seq:
        D2 = D + ap - 1
        V2 = {}
        for j, mu in V.items():
            L = D + 1 - 2*j
            n = min(L, ap)
            d0 = min(L % r, ap % r, n)
            for d in range(d0):
                jj = j + d
                LL = D2 + 1 - 2*jj
                if LL % r != 0:          # chains with r | LL are U-pieces
                    V2[jj] = V2.get(jj, 0) + mu
            # remainder q^{j+d0}[L-d0][ap-d0] has a bracket divisible by r (or is 0): U-piece
        V = V2
        D = D2
        if not V:
            return math.inf
    return min(D + 1 - 2*j for j in V)

def lmin(r, a):
    a = list(a)
    return max(_lmin(r, sorted(a)), _lmin(r, sorted(a, reverse=True)))

def predict(r, a, b):
    if any(x % r == 0 for x in a):
        return True
    return r*(b-1) <= lmin(r, a)

def domain(r, a):
    return True
