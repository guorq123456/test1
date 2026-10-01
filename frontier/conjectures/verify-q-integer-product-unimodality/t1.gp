qa(a)=sum(i=0,a-1,'q^i);
qbr(b,r)=sum(j=0,b-1,'q^(r*j));
unimod(P)={my(v=Vecrev(P),n=#v,i=1);while(i<n && v[i]<=v[i+1],i++);while(i<n && v[i]>=v[i+1],i++);i==n};
P=qa(2)^6*qbr(2,3); print(Vecrev(P)); print("unimodal: ",unimod(P));
for(k=1,12,P=qa(2)^k*qbr(2,3); print(k," ",unimod(P)," ",Vecrev(P)));
\\ paper's own example
P=qa(3)^4*qbr(2,4); print(Vecrev(P)," ",unimod(P));
