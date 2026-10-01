default(parisizemax, 2*10^9);
N=1300;
v=readvec("a_vals.txt");
x='x+O('x^(N+1));
G=Vec(2*(1-x^2)/(3*x^2-4*x+1+sqrt((1-x^2)^2-4*(x-x^2)*(1-x^2))));
H=Vec((1+x)*(sqrt((1+x)/(1-3*x))-1)/(2*x));
print(#G," ",#H," ",#v);
print(vector(N,i,G[i])==vector(N,i,v[i]));
print(vector(N-1,i,H[i])==vector(N-1,i,v[i]));
\\ coefficient form for n<=250
ok=1; for(n=1,250, y='y+O('y^(n+1)); c=polcoeff((1-y+y^2)^(n-1)/(1-y)^(n+2),n,'y); if(c!=v[n+1], ok=0; print("bad ",n))); print("coef form ",ok);
\\ also n=0 of coefficient form
y='y+O('y^2); print("n=0 coef form gives ", polcoeff((1-y+y^2)^(-1)/(1-y)^2,0,'y));
\\ ODE check symbolic
A=Ser(v,'x); print("ODE residual valuation: ", valuation(x*(1+x)*(1-3*x)*deriv(A)+(1-5*x)*A-(1+x),'x));
