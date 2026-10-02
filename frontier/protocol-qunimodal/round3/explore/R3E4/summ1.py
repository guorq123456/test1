import json,collections,sys
L=[json.loads(l) for l in open(sys.argv[1])]
print(len(L), 'S2 fails', sum(1 for x in L if not x['S2']))
by=collections.defaultdict(list)
for x in L: by[x['fam']].append(x)
for f,v in by.items():
    g=sorted(x['gap'] for x in v); ks=[x.get('kappa',0) for x in v]
    print(f,len(v),'gap min/med/max %.3f %.3f %.3f'%(g[0],g[len(g)//2],g[-1]),'kappa min %.2f'%min(ks))
top=sorted(L,key=lambda x:-x['gap'])[:15]
for x in top: print(x['fam'],x['r'],x['k'],x['F'],x['Nstar'],x['beta'],round(x['gap'],3),round(x.get('kappa',0),2),x['Cv'],x['Cu'],x['a'][:6],x['a'][-3:])
