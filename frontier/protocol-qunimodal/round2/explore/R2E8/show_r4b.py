import pickle,collections,sys
rows=pickle.load(open(sys.argv[1],'rb'))
r=4
c=collections.Counter()
for a,delta,T6,F,mu in rows:
    c[(T6-1-F, delta, T6-delta-1-F)]+=1
print("(E6,delta,X=|U|-1-F):count",c)
