"""Reference only (Conjecture 5.4 as stated): unimodal iff r | some a_i or b <= 1 + sum floor(a_i/r)."""
def predict(r, a, b):
    return any(x % r == 0 for x in a) or b <= 1 + sum(x // r for x in a)
def domain(r, a): return True
