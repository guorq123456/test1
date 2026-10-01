qa(a)=sum(i=0,a-1,'q^i);
qbr(b,r)=sum(j=0,b-1,'q^(r*j));
unimod(P)={my(v=Vecrev(P),n=#v,i=1);while(i<n && v[i]<=v[i+1],i++);while(i<n && v[i]>=v[i+1],i++);i==n};
A=[2,4,9,9,10,10,11]; P0=prod(i=1,#A,qa(A[i])); F=sum(i=1,#A,A[i]\6); print("F=",F," D=",poldegree(P0));
for(b=1,14,print1(b,":",unimod(P0*qbr(b,6))," ")); print();
