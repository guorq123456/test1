import pickle,collections,sys
rows=pickle.load(open(sys.argv[1],'rb'))
r=4
g=collections.defaultdict(lambda: collections.defaultdict(set))
for a,delta,T6,F,mu in rows:
    n1=sum(1 for x in a if x%r==1); n3=sum(1 for x in a if x%r==3)
    g[(n1,n3)][(T6-1-F,delta)].add(F)
for k in sorted(g):
    print(k, {kk:(min(v),max(v),len(v)) for kk,v in g[k].items()})
