import pickle,collections,sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8')
rows=pickle.load(open(sys.argv[1],'rb'))
r=4
g=collections.defaultdict(set)
for a,delta,T6,F,mu in rows:
    n1=sum(1 for x in a if x%r==1); n3=sum(1 for x in a if x%r==3)
    g[(n1,n3,F)].add((delta,T6-1-F,mu))
for k in sorted(g): print(k,sorted(g[k]))
