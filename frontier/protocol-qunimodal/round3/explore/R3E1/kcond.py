"""Threshold of condition (K') of Theorem B: exists t1 in T with c*sin(2 pi t1/r)*(1-e^{-kappa})^2 >= pi*e^{-kappa(1-t1/r)}.
For r -> infinity (t1/r = u free) prints kappa_0(c) = least kappa for which (K') is satisfiable, for several c."""
import math
from scipy.optimize import brentq
def best(k,c):
    u=math.atan(2*math.pi/k)/(2*math.pi)
    return c*math.sin(2*math.pi*u)*math.exp(-k*u)*(1-math.exp(-k))**2-math.pi*math.exp(-k)
for c in [1.0,0.9,0.75,0.5,0.25,0.1]:
    k0=brentq(lambda k:best(k,c),0.05,40)
    print("c=%.2f  kappa_0=%.4f"%(c,k0))
