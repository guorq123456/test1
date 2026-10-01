"""Rule E4 (one-sided, PROVED direction only).

sufficient(r,a,b): True iff  b <= 1 + sum_i floor(a_i/r)  or  r | a_i for some i.
THEOREM (proof.txt): sufficient(r,a,b) => P(q) = prod [a_i]_q * [b]_{q^r} is (symmetric) unimodal,
for all r>=2, k>=1, a_i>=1, b>=1.
predict(r,a,b) returns sufficient(r,a,b). A True prediction is a theorem. A False prediction is
NOT a claim (necessity is known to fail, e.g. r=3, a=(2,2,2,2,2,2), b=2).
domain(r,a) is True everywhere: the rule is evaluated everywhere, but only its True outputs are
proved; see description.
"""

def sufficient(r, a, b):
    return (b <= 1 + sum(ai // r for ai in a)) or any(ai % r == 0 for ai in a)

def predict(r, a, b):
    return sufficient(r, a, b)

def domain(r, a):
    return True
