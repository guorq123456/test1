\\ Independent multiprecision check of A228016 from its definition (PARI psi function),
\\ H(k) = psi(k+1) + Euler.  c_{-1}=0, c_0=5, c_n = least k with H(k) > 2H(c_{n-1}) - H(c_{n-2}).
\\ The least k is found by a local search started from a crude guess and is
\\ compared with e_{n+1}, e = A087125 via e_m = 10 e_{m-1} - e_{m-2} + 4.
N = 1000;
\p 2600
H(k) = if(k==0, 0., psi(k+1) + Euler);
e = vector(N+3); e[1]=0; e[2]=5; for(m=3, N+3, e[m] = 10*e[m-1] - e[m-2] + 4);  \\ e[m] = A087125(m-1)
cm2 = 0; cm1 = 5; Hm2 = H(0); Hm1 = H(5); bad = 0; mingap = 1.;
{
for(n=1, N,
  T = 2*Hm1 - Hm2;
  g = floor(exp(T - Euler) - 1/2);           \\ crude guess only
  Hg = H(g);
  while(Hg > T, g--; Hg = H(g));
  while(Hg <= T, g++; Hg = H(g));
  \\ now H(g-1) <= T < H(g): g is the least k with H(k) > T
  gapabove = Hg - T; gapbelow = T - (Hg - 1/g);
  \\ normalised gaps: ratio to the scale 1/c_{n-1}^2 and 1/g
  mingap = min(mingap, min(gapabove, gapbelow) * 10^(2*#digits(g)));
  if(g != e[n+2], print("MISMATCH at n=", n, " got ", g, " expected ", e[n+2]); bad=1; break);
  if(gapabove < 10^(-2400) || gapbelow < 10^(-2400), print("PRECISION INSUFFICIENT at n=", n); bad=1; break);
  if(n<=6 || n%100==0, printf("n=%d a(n)~%.6e (%d digits)  gap above T=%.3e  gap below T=%.3e\n", n, g, #digits(g), gapabove, gapbelow));
  cm2 = cm1; cm1 = g; Hm2 = Hm1; Hm1 = Hg);
if(!bad, print("A228016(n) = A087125(n+1) verified for n = 1..", N));
}
\q
