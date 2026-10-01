\\ (1+q)^k (1+q^3) unimodality for k=1..400, using exact binomials
unimodv(v)={my(n=#v,i=1);while(i<n && v[i]<=v[i+1],i++);while(i<n && v[i]>=v[i+1],i++);i==n};
bad=List();for(k=1,400,v=vector(k+4,t,binomial(k,t-1)+if(t-1>=3,binomial(k,t-4),0)); if(!unimodv(v),listput(bad,k)));
print("non-unimodal k: ",bad);
\\ also (1+q)^k(1+q^3+...+q^{3(b-1)}) for b=3, for curiosity
for(b=2,5,bad=List();for(k=1,120,P=(1+'q)^k*sum(j=0,b-1,'q^(3*j)); if(!unimodv(Vecrev(P)),listput(bad,k))); print("b=",b," non-unimodal k: ",bad));
