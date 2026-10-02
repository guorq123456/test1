# Check Conjecture S2 (parity-gap) against holdout profiles.
# S2: if r divides no a_i, U = [1,B*] or [1,B*]\{B*-1}, with B* = 1+F (mod 2), F = sum floor(a_i/r).
import json, sys
def check(r,a,bs,us):
    if any(x%r==0 for x in a): return ('div', all(us))
    F=sum(x//r for x in a); U=[b for b,u in zip(bs,us) if u]
    if not U: return ('empty', False)
    Bs=max(U); ok = (Bs-1-F)%2==0
    for b,u in zip(bs,us):
        if b<Bs and not u and b!=Bs-1: ok=False
    gap = any((b==Bs-1 and not u) for b,u in zip(bs,us))
    return ('gap' if gap else 'interval', ok)
from collections import Counter
for path in sys.argv[1:]:
    c=Counter(); bad=[]
    for l in open(path):
        o=json.loads(l)
        bs=o.get('bs') or list(range(1,len(o['profile'])+1)); us=o.get('unimodal') or o['profile']
        kind,ok=check(o['r'],o['a'],bs,us); c[(kind,ok)]+=1
        if not ok and len(bad)<5: bad.append((o['r'],o['a'][:12],len(o['a'])))
    print(path.split('/')[-1], dict(c), 'violations:',bad)
