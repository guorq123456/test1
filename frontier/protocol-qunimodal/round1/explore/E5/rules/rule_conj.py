# Baseline: the conjecture's bound read as an iff: unimodal <=> (r|a_i some i) or b <= 1+sum floor(a_i/r)
def domain(r, a): return True
def predict(r, a, b):
    if any(x % r == 0 for x in a): return True
    return b <= 1 + sum(x//r for x in a)
