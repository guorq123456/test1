# consistency: rule predicts (1+q)^k (1+q^r) unimodal iff k >= r^2-3 (Handelman), r=4..30, k=3..60 (a=2,b=2,n=0)
from rule_allequal_middle import predict
bad=0;tot=0
for r in range(4,31):
    for k in range(3,61):
        tot+=1
        if predict(r,[2]*k,2)!=(k>=r*r-3): bad+=1; print('X',r,k)
print('Handelman check pairs',tot,'disagreements',bad)
