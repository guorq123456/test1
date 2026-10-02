# Zero-parameter asymptotic model, variant B (dominant Fourier mode + exact log-binomial), path R3E8.
from rule_asym import domain as _domain
from variants import tops_B
def domain(r,a):
    return _domain(r,a)
def predict(r,a,b):
    s=[x%r for x in a]
    if any(x==0 for x in s): return True
    F=sum(x//r for x in a)
    if b<=F+1: return True
    Xo,Xe,eo,ee=tops_B(r,s)
    e=b-F
    return e<=eo if e%2==1 else e<=ee
