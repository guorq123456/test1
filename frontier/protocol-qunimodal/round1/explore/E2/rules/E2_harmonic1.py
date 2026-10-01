"""Rule E2_harmonic1: fully closed form obtained from Theorem B by keeping only the first Fourier harmonic
(j=1 and j=r-1, whose amplitude A_1 = prod sin(pi t_i/r)/sin(pi/r) is always > 0) in
tau_c = (2/r) sum_j sin(pi j/r) A_j sin(pi j (Dpi+1-2c)/r).
Predict unimodal iff r | some a_i or  b <= 1 + S + 2*max(0, floor((Dpi + r + 3)/(2r)) - 1),
S = sum floor(a_i/r), Dpi = sum (t_i - 1), t_i = a_i mod r.
"""
def predict(r, a, b):
    if any(x % r == 0 for x in a): return True
    S = sum(x // r for x in a)
    Dpi = sum(x % r - 1 for x in a)
    return b <= 1 + S + 2 * max(0, (Dpi + r + 3) // (2 * r) - 1)
def domain(r, a): return True
