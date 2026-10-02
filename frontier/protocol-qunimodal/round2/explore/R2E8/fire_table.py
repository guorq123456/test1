# Exhaustive table of the H1 firing condition over residue data (r, middle multiset, nm mod 2r), r in [4,R].
# (tau, s, mu depend only on these.) Reports distribution of (s - r, tau_s, mu) for firing cases.
import sys, itertools, collections
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
import rule_H1
R=int(sys.argv[1]); c=collections.Counter(); tot=0; fire=0
for r in range(4,R+1):
  for mids in itertools.combinations_with_replacement(range(2,r-1),3):
    for nm in range(2*r):
      a=list(mids)+[r-1]*nm
      D=sum(x-1 for x in a); tau=rule_H1._tau(r,a); s=(D+1)%r
      pos=[j for j in range(1,r) if tau[j]>0]; mu=max(pos) if pos else 0
      tot+=1
      if tau[s]<=-2 and s>=2*mu:
        fire+=1; c[(s-r, tau[s], 'nm%2='+str(nm%2), 'tau_{s+1}='+str(tau[(s+1)%r]))]+=1
print("configs",tot,"fire",fire); 
for k,v in sorted(c.items()): print(k,v)
