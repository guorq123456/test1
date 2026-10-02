"""HEURISTIC model (not a proof): exponential tail e(z)~exp(-kappa z/r) beyond the crossing, single-mode class profile
psi(t)=A sin(2 pi t/r).  S2 holds in the model iff
   m(kappa) = min_{0<u<1/2} [ -sin(2 pi u) + (pi e^{-kappa}/kappa)(2 sinh(kappa u) + (1-e^{-kappa}) e^{-kappa u}) ] < 0.
Prints kappa_crit = sup{kappa : m(kappa) >= 0}."""
import numpy as np
from scipy.optimize import brentq
u=np.linspace(1e-6,0.5-1e-6,200001)
def m(k): return np.min(-np.sin(2*np.pi*u)+(np.pi*np.exp(-k)/k)*(2*np.sinh(k*u)+(1-np.exp(-k))*np.exp(-k*u)))
for k in [0.05,0.1,0.2,0.3,0.5,0.7,1.0,1.5,2.0,3.0,6.28]: print("kappa %.2f  m=%.4f"%(k,m(k)))
print("kappa_crit = %.4f"%brentq(m,0.05,3.0))
