import pickle,sys,collections
tab=pickle.load(open(sys.argv[1],'rb'))
# does X depend on n1?
byk=collections.defaultdict(dict)
for (r,mids,n1,nm),(Xs,info) in tab.items():
    byk[(r,mids,nm)][n1]=(list(Xs)[0],info)
dep=[(k,v) for k,v in byk.items() if len(set(x[0] for x in v.values()))>1]
print("depends on n1:",len(dep),"of",len(byk))
for k,v in dep[:20]: print(k,v)
