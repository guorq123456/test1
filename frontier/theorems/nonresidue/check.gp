\\ Independent PARI/GP check: A112046 via kronecker(), first occurrences for odd m < 2*10^6,
\\ and n(q)^2 < q for primes q < 10^7 except 3, 7, 23.
f(m) = my(k=1); while(kronecker(k, m) == 1, k++); k;
N = 10^6;
firstocc = Map();
for(i = 1, N, my(v = f(2*i+1)); if(!mapisdefined(firstocc, v), mapput(firstocc, v, i)));
M = Mat(firstocc); M = vecsort(M~, 1)~;   \\ rows [value, first index]
ok = 1;
for(r = 1, matsize(M)[1], my(v = M[r,1], i = M[r,2]); \
  if(!isprime(v), ok = 0; print("composite value ", v)); \
  my(e = if(v==2, 1, v==3, 3, v==5, 11, (v^2-1)/2)); if(i != e, ok = 0; print("mismatch ", v, " ", i)));
print("PARI: values occurring in A112046(1..", N, "): ", matsize(M)[1], " primes; first indices as predicted: ", ok);
print("PARI: sorted first indices (A112051) first 20: ", vecsort(M[,2]~)[1..20]);
bad = List(); forprime(q = 3, 10^7, my(k = 2); while(kronecker(k, q) == 1, k++); if(k^2 > q, listput(bad, [q, k])));
print("PARI: odd primes q < 10^7 with n(q)^2 > q: ", bad);
