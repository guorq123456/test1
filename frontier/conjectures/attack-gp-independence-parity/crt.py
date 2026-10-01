# Reconstruct integer coefficients from residues (mod 2^64 and 7 primes ~2^62); total modulus ~2^498.
import sys
from sympy.ntheory.modular import crt
P = [2**64, 4611686018427387847, 4611686018427387817, 4611686018427387787, 4611686018427387761, 4611686018427387751, 4611686018427387737, 4611686018427387733]
M = 1
for p in P: M *= p
def parse_line(line):
    t = line.split()
    k, m, top = int(t[0]), int(t[1]), int(t[2])
    coeffs = []
    for tok in t[3:]:
        r = [int(z) for z in tok.split(',')]
        v, _ = crt(P, r)
        v = int(v)
        if v > M//2: v -= M
        coeffs.append(v)
    return k, m, coeffs
