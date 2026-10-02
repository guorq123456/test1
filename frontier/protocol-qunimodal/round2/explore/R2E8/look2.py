import pickle,sys,collections
tab=pickle.load(open(sys.argv[1],'rb')); R=int(sys.argv[2])
rows=collections.defaultdict(dict)
for (r,mids,n1,nm),(Xs,info) in tab.items():
    if r!=R or n1!=0: continue
    X=list(Xs)[0]; E6,mu=info
    rows[mids][nm]=(X,E6,mu)
for mids in sorted(rows):
    print(mids, ' '.join(f"{nm}:{X}/{E6}/{mu}" for nm,(X,E6,mu) in sorted(rows[mids].items())))
