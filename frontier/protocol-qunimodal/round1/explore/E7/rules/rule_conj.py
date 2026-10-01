"""Candidate CONJ (Conjecture 5.4 read as an iff): unimodal <=> r | a_i for some i, or b <= 1 + sum floor(a_i/r)."""
def predict(r, a, b):
    return any(x % r == 0 for x in a) or b <= 1 + sum(x // r for x in a)
