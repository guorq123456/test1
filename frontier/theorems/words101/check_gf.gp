\\ Expand the g.f. printed as "Theorem" in A225034 and the simplified g.f. (1+x)(R-1)/(2x), and the
\\ generalised Arndt count; compare with a(n) from the automaton DP (file a225034_dp.txt).
N = 1200;
x = 'x + O('x^(N+2));
g1 = 2*(1-x^2)/(3*x^2-4*x+1+sqrt((1-x^2)^2-4*(x-x^2)*(1-x^2)));
R = sqrt((1+x)/(1-3*x));
g2 = (1+x)*(R-1)/(2*x);
v1 = Vec(g1); v2 = Vec(g2);
dp = readvec("a225034_dp.txt");
ok = 1;
for(n=0, N, if(v1[n+1] != dp[n+1] || v2[n+1] != dp[n+1], if(ok, print("first MISMATCH at ", n)); ok = 0));
print("PARI: both g.f.s agree with DP for 0<=n<=", N, " : ", ok);
\\ Berselli recurrence on the g.f. coefficients
ok2 = 1; for(n=2, N, if((n+1)*v1[n+1]-(2*n+3)*v1[n]-3*(n-2)*v1[n-1] != 0, ok2 = 0));
print("PARI: Berselli recurrence holds for 2<=n<=", N, " : ", ok2);
quit;
