# Hill-climb (inside fit box) to minimize the relative slack of per-thread property (C):
# for j = F (mod 2) with V_j<0:  slack = -(V_{j+2}+d_{j+3})  (must be >0 for (C)); normalized by max(1,d_{j+3}).
import sys, random, math
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from threads import threads, V
from core import in_box
def score(r,a):
    if not in_box(r,a) or any(x%r==0 for x in a): return None
    F=sum(x//r for x in a)
    th,D=threads(r,a,(sum(a)//r)+8)
    best=None
    for (pair,ys,d) in th:
        Vs=[V(d,b) for b in range(len(d))]
        for j in range(0,len(d)-3):
            if (j-F)%2 or Vs[j]>=0: continue
            if d[j+3]==0: continue   # trivially fine: V_{j+2}<=... handled below anyway
            sl=-(Vs[j+2]+d[j+3])
            rel=sl/max(1,d[j+3])
            if best is None or rel<best[0]: best=(rel,pair,j,d[j:j+4],Vs[j],Vs[j+2])
    return best
random.seed(int(sys.argv[1])); iters=int(sys.argv[2])
def rand_inst():
    r=random.randint(4,30); k=random.randint(4,20)
    a=[]
    while len(a)<k:
        x=random.randint(2,100)
        if x%r: a.append(x)
    return r,sorted(a)
glob=None
for restart in range(int(sys.argv[3])):
    r,a=rand_inst(); s=score(r,a)
    tries=0
    while s is None and tries<50:
        r,a=rand_inst(); s=score(r,a); tries+=1
    if s is None: continue
    for it in range(iters):
        b=list(a); mv=random.random()
        if mv<0.4 and len(b)>2: b.pop(random.randrange(len(b)))
        elif mv<0.7 and len(b)<40: b.append(random.randint(2,100))
        else:
            i=random.randrange(len(b)); b[i]=max(2,min(100,b[i]+random.choice([-r,-1,1,r,-2,2])))
        b.sort()
        s2=score(r,b)
        if s2 is not None and s2[0]<=s[0]: a,s=b,s2
    if glob is None or s[0]<glob[0]: glob=(s[0],r,a,s)
    print("restart",restart,"rel slack",round(s[0],4),"r",r,"k",len(a),flush=True)
print("GLOBAL MIN",glob)
