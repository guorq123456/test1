# For failure instances: list violating j for each b in [T6-3,T6] using K-form:
# P_b unimodal iff for all j in [-rb, floor((K-1)/2)]: g_j - g_{K-j} <= tau_{j mod r}, K = D+1-r(b+1).
import json, glob
from core import Apoly, gseq, inv, U
def kform(r,a,b):
    D,F,tau,Gam=inv(r,a)
    K=D+1-r*(b+1)
    A=Apoly(a); g,_=gseq(r,A,D+r*b+r+5)
    G=lambda i: g[i] if i>=0 else 0
    v=[]
    for j in range(-r*b,(K-1)//2+1):
        if G(j)-G(K-j)>tau[j%r]: v.append((j,G(j),G(K-j),tau[j%r]))
    return K,v
if __name__=="__main__":
  for fn in sorted(glob.glob('fail_*.jsonl')):
      for l in open(fn):
          d=json.loads(l); r=d['r']; a=d['a']
          u=d['U']; T6=d['T6']
          res=[]
          for b in range(max(1,T6-3),T6+1):
              K,v=kform(r,a,b)
              assert (len(v)==0)==(b in u)
              res.append((b,K,v[:3]))
          print(r,a,'mu',d['mu'],'s',d['s'],'small',[x for x in a if x<r])
          for x in res: print('   ',x)
