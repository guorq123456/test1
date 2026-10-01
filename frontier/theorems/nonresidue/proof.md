# A112051(n) = A216244(n) = (prime(n)^2 - 1)/2 for n >= 4

All scripts named below are in `/tmp/claude-0/deep/nonresidue/`.

## 0. Definitions and statement

For an odd integer m >= 1 and an integer k, (k/m) denotes the Jacobi symbol.
Facts used about it (all standard):

* (J1) (ab/m) = (a/m)(b/m) and (k/m1 m2) = (k/m1)(k/m2);
* (J2) (k/m) = 0 iff gcd(k,m) > 1, otherwise (k/m) is +1 or -1;
* (J3) if m = q is prime, (k/q) is the Legendre symbol; for an odd prime q exactly
  (q-1)/2 of the integers 1..q-1 are quadratic non-residues.

For an odd prime q write chi(k) = (k/q) and let n(q) be the least positive
quadratic non-residue mod q (it exists by (J3), and 2 <= n(q) <= q-1).

For odd m >= 3 put

    f(m) = least k >= 1 with (k/m) != +1 .

It exists since (m/m) = 0, and 2 <= f(m) <= m because (1/m) = 1.

OEIS definitions (checked against the entries in the Oct 2026 snapshot):

* A112046(i) = least k >= 1 with Jacobi(k, 2i+1) != +1, i >= 1. So A112046(i) = f(2i+1).
* A112051: a(1) = 1, and a(n) = the first index i > a(n-1) such that A112046(i) is
  distinct from all of A112046(1), ..., A112046(a(n-1)). Offset 1.
* A216244(n) = (prime(n)^2 - 1)/2, n >= 2 (offset 2).
* (Also: A112052(n) = 2 A112051(n) + 1; A112049(i) = pi(A112046(i));
  A084921(n) = lcm(prime(n)-1, prime(n)+1) = (prime(n)^2-1)/2 for n >= 2.)

**Theorem 1.** A112051(1) = 1, A112051(2) = 3, A112051(3) = 11, and

    A112051(n) = (prime(n)^2 - 1)/2 = A216244(n)   for every n >= 4.

(The identity fails for n = 2, 3: A216244(2) = 4, A216244(3) = 12.)
Equivalently A112052(n) = prime(n)^2 for n >= 4.

The heart of the proof is the following statement about the least quadratic
non-residue, proved by elementary means in Section 2.

**Theorem 2.** For every odd prime q, n(q)^2 < q, except for q = 3, 7, 23
(where n(q) = 2, 3, 5 respectively).

## 1. Reduction of Theorem 1 to Theorem 2

**Lemma 1.1** (values are prime). For odd m >= 3, f(m) is prime.

*Proof.* f(m) >= 2. If f(m) = xy with 1 < x, y < f(m), then (x/m) = (y/m) = 1 by
minimality, so (xy/m) = 1 by (J1), a contradiction. []

**Lemma 1.2.** For every odd prime p, f(p^2) = p.

*Proof.* By (J1),(J2): (k/p^2) = (k/p)^2 = 1 if p does not divide k, and 0 if p | k. []

**Proposition 1.3.** Let m >= 3 be odd and p = f(m). If m < p^2 then m is a prime q > p
and p = n(q) (so n(q)^2 > q). Consequently, by Theorem 2, f(m)^2 > m holds only for
m in {3, 7, 23}, where f(3) = 2, f(7) = 3, f(23) = 5.

*Proof.* Suppose m < p^2. For 1 <= k < p we have (k/m) = 1, so gcd(k,m) = 1 by (J2);
hence every prime divisor of m is >= p.

*Case (p/m) = 0.* Then p | m (p is prime, Lemma 1.1). Write m = p m'. Every prime
divisor of m' is >= p, so m' = 1 or m' >= p; the latter gives m >= p^2. Hence
m = p, and (k/p) = 1 for all 1 <= k <= p-1. But m is odd, so p is an odd prime, and
by (J3) there are (p-1)/2 >= 1 non-residues in [1, p-1]. Contradiction; this case
cannot occur.

*Case (p/m) = -1.* Then gcd(p, m) = 1, so every prime divisor of m is > p. If m were
composite, m >= l1 l2 > p^2 for two (not necessarily distinct) prime divisors l1, l2,
contrary to m < p^2. So m = q is prime, q > p, and (.,q) is the Legendre symbol.
Since every k <= p is < q, (k/q) is never 0 for k <= p, so f(q) is the least
non-residue: p = n(q), and n(q)^2 = p^2 > q.

Finally, if f(m)^2 > m, i.e. m < p^2, then by what was just shown m = q is a prime
with n(q)^2 > q, so q is in {3, 7, 23} by Theorem 2. Conversely f(3) = 2, f(7) = 3,
f(23) = 5 (quadratic residues mod 3: 1; mod 7: 1,2,4; mod 23:
1,2,3,4,6,8,9,12,13,16,18), and 4 > 3, 9 > 7, 25 > 23. []

For a prime p let first(p) = min{ i >= 1 : A112046(i) = p }.

**Corollary 1.4.** (a) Every value of A112046 is prime and every prime occurs.
(b) first(2) = 1, first(3) = 3, first(5) = 11, and first(p) = (p^2-1)/2 for every
prime p >= 7. (c) first is strictly increasing in p.

*Proof.* (a) Lemma 1.1; f(3) = 2 and f(p^2) = p for odd p (Lemma 1.2).
(b) A112046(i) = f(2i+1). Direct computation: A112046(1..11) =
2,2,3,3,2,2,3,3,2,2,5, giving first(2) = 1, first(3) = 3, first(5) = 11.
Let p >= 7. Lemma 1.2 gives A112046((p^2-1)/2) = f(p^2) = p, so first(p) <= (p^2-1)/2.
If A112046(i) = p with i < (p^2-1)/2 then m = 2i+1 < p^2 with f(m) = p, so by
Proposition 1.3 m is in {3, 7, 23}, whose f-values are 2, 3, 5, none equal to p.
Hence first(p) = (p^2-1)/2.
(c) 1 < 3 < 11 < 24 = (7^2-1)/2, and (p^2-1)/2 is increasing in p. []

**Lemma 1.5** (what A112051 enumerates). Let E = {i : A112046(i) is not in
{A112046(j) : j < i}} (positions of first occurrences) and let e_1 < e_2 < ... be its
elements (E is infinite by Corollary 1.4(a)). Then A112051(n) = e_n for all n >= 1.

*Proof.* Induction on n. e_1 = 1 = a(1). Assume a(n-1) = e_{n-1} and put
V = {A112046(j) : j <= e_{n-1}}. For e_{n-1} < i <= e_n we have
{A112046(j) : j < i} = V (no index strictly between e_{n-1} and e_n is a first
occurrence, so no new value enters). Hence for e_{n-1} < i < e_n, A112046(i) is in V
(i is not in E), while A112046(e_n) is not in V (e_n is in E). By definition
a(n) = min{ i > a(n-1) : A112046(i) not in V } = e_n. []

*Proof of Theorem 1.* E = {first(p) : p prime}. By Corollary 1.4 its increasing
enumeration is first(prime(1)) < first(prime(2)) < ..., i.e. e_n = first(prime(n)).
By Lemma 1.5 and Corollary 1.4(b): A112051(1,2,3) = 1, 3, 11 and
A112051(n) = (prime(n)^2-1)/2 for n >= 4 (prime(4) = 7). This equals A216244(n). []

**Further consequences (same proof).**
* A112052(n) = prime(n)^2 for n >= 4 (the comment "From n>=4 onward seems to be squares
  of primes" in A112052 is a theorem); also A112051(n) = A084921(n) for n >= 4.
* A112049 comment: the first occurrence of the value k in A112049 = pi(A112046) is at
  A112051(k), and these positions are exactly the record positions of A112049 (and of
  A112046, A112050). Indeed, by Corollary 1.4(c), if i < first(prime(k)) then
  A112046(i) = p' has first(p') <= i < first(prime(k)), so p' < prime(k); thus the value
  at first(prime(k)) is a strict record, and a record position is necessarily a first
  occurrence.
* A112060 comment ("is a permutation provided ... every prime occurs infinitely many
  times"): the proviso holds. f(m) = 2 for all m == 3, 5 (mod 8), and for an odd prime
  p and any prime r > p, f(p^2 r^2) = p because (k/p^2 r^2) = 1 if gcd(k, pr) = 1 and
  0 otherwise.

## 2. Proof of Theorem 2 (elementary)

Throughout, q is an odd prime, chi(k) = (k/q), n = n(q). Every integer k with
1 <= k <= n-1 satisfies chi(k) = 1, and chi(n) = -1. Also n <= q-1, and n is prime
(same argument as Lemma 1.1).

**Lemma A** (classical, e.g. Niven-Zuckerman-Montgomery Thm 3.9). n(n-1) < q.

*Proof.* n does not divide q (1 < n < q). Let m = ceil(q/n), so (m-1)n < q < mn and
r := mn - q satisfies 1 <= r <= n-1; hence chi(r) = 1. Also m <= (q+n-1)/n = (q-1)/n + 1 <= (q+1)/2 < q,
so q does not divide m. Since mn == r (mod q), chi(m)chi(n) = chi(r) = 1, so chi(m) = -1,
and therefore m >= n. Thus q > (m-1)n >= (n-1)n. []

**Lemma B.** Suppose n^2 > q. Then chi(-1) = -1, and every integer x with
q-n+1 <= x <= q-1 satisfies chi(x) = -1.

*Proof.* By Lemma A and q < n^2, r := q - n(n-1) satisfies 1 <= r <= n-1, so chi(r) = 1.
Since r == -n(n-1) (mod q), and chi(n-1) = 1 because 1 <= n-1 < n:
1 = chi(-1) chi(n) chi(n-1) = -chi(-1). So chi(-1) = -1. If q-n+1 <= x <= q-1 then
k = q - x is in [1, n-1], and chi(x) = chi(-k) = chi(-1) chi(k) = -1. []

**Lemma C** (purely arithmetic). Let n >= 29 and q be odd integers with
n(n-1) < q < n^2. Then there are integers a, b with

    1 <= a <= b <= n-1   and   q - n + 2 <= 2ab <= q - 1.

*Proof.* Put N = (q - n + 2)/2; it is an integer (q - n is even) and N >= 1
(q > n(n-1) >= n). Let s = ceil(sqrt(N)) >= 1, D = s^2 - N, t = floor(sqrt(D)), and
a = s - t, b = s + t.

1. 0 <= D <= 2s - 2: from s - 1 < sqrt(N) <= s and s - 1 >= 0 we get
   (s-1)^2 < N <= s^2; as N is an integer, N >= (s-1)^2 + 1, so D <= 2s - 2.
2. t^2 <= D <= t^2 + 2t: from t <= sqrt(D) < t+1 and D an integer.
3. ab = s^2 - t^2 = N + (D - t^2), so N <= ab <= N + 2t.
4. 1 <= a <= b: t <= sqrt(D) <= sqrt(2s-2) < s (as s^2 - 2s + 2 = (s-1)^2 + 1 > 0);
   t is an integer, so t <= s-1 and a >= 1; b >= a since t >= 0.
5. Size bounds. q <= n^2 - 1 gives N <= (n^2 - n + 1)/2 < n^2/2, hence
   sqrt(N) < n/sqrt(2), s < n/sqrt(2) + 1, D <= 2s - 2 < sqrt(2) n, and
   t <= sqrt(D) < 2^(1/4) sqrt(n).
6. b <= n - 1: b = s + t < n/sqrt(2) + 1 + 2^(1/4) sqrt(n), and this is <= n - 1 iff
   g(n) := (1 - 1/sqrt 2) n - 2^(1/4) sqrt(n) - 2 >= 0. Now g is increasing for n >= 5
   (g'(n) = (1 - 1/sqrt2) - 2^(1/4)/(2 sqrt n) > 0.29 - 0.6/sqrt(n) > 0, using
   1 - 1/sqrt2 = 0.2928... and 2^(1/4)/2 = 0.5946...), and
   g(29) > 0: using 1/sqrt2 < 0.70711, 2^(1/4) < 1.18921, sqrt(29) < 5.38517 (each
   checked by squaring: 0.70711^2 = 0.500004..., 1.18921^4 = 2.00002..., 5.38517^2 =
   29.00005...), g(29) > 0.29289*29 - 1.18921*5.38517 - 2 > 8.49381 - 6.40410 - 2 =
   0.08971 > 0.
7. 2ab <= q - 1: by step 3, 2ab <= 2N + 4t = q - n + 2 + 4t, so it suffices that
   4t <= n - 3, which follows (t < 2^(1/4) sqrt(n) by step 5) from
   4 * 2^(1/4) sqrt(n) <= n - 3. For n >= 3 both sides are nonnegative, and squaring
   shows this is equivalent to 16 sqrt2 n <= (n-3)^2, i.e. to
   phi(n) := n^2 - (6 + 16 sqrt2) n + 9 >= 0 (squaring once more: (n-3)^4 >= 512 n^2). phi is increasing for
   n >= (6+16 sqrt2)/2 (about 14.3), and phi(29) = 676 - 464 sqrt2 > 0 because
   676^2 = 456976 > 430592 = 2 * 464^2.
8. 2ab >= q - n + 2 by step 3 (2ab >= 2N).  []

(Sanity check: `small_cases.py` part (3) runs this exact construction for all
2,000,909 pairs (n, q) with n odd in [29, 4001], q odd in (n(n-1), n^2), and confirms
the conclusion in every case. It also shows the construction fails for some q when
n is in {3, 5, 7, 11, 15, 19}, so a threshold is genuinely needed.)

**Proof of Theorem 2.** Suppose n^2 > q (equality is impossible, q being prime).

*Case n >= 29.* n is an odd prime and n(n-1) < q < n^2 (Lemma A). Take a, b from
Lemma C. Since 2 <= n - 1 and 1 <= a <= b <= n - 1, chi(2ab) = chi(2)chi(a)chi(b) = 1.
But k := q - 2ab satisfies 1 <= k <= n - 2, so 2ab lies in [q-n+1, q-1] and
chi(2ab) = -1 by Lemma B. Contradiction. Hence n <= 23 (n is prime).

*Case n <= 23* (finite check; done by hand below, and by machine in
`small_cases.py` parts (1)-(2) and `check.gp`). By Lemma A, n(n-1) < q < n^2.

* n = 2: q in (2, 4), so q = 3, and indeed n(3) = 2. Exception.
* n = 3: q in (6, 9), so q = 7; residues mod 7 are 1, 2, 4, so n(7) = 3. Exception.
* n = 5: q in (20, 25), so q = 23; residues mod 23 are 1,2,3,4,6,8,9,12,13,16,18, so
  n(23) = 5. Exception.
* n in {7, 11, 13, 17, 19, 23}: Lemma B gives chi(-1) = -1, i.e. q == 3 (mod 4), and
  chi(2) = 1 (as 2 < n), i.e. q == +-1 (mod 8). So q == 7 (mod 8). The primes in the
  intervals (n(n-1), n^2) are:
  (42,49): 43, 47; (110,121): 113; (156,169): 157, 163, 167; (272,289): 277, 281, 283;
  (342,361): 347, 349, 353, 359; (506,529): 509, 521, 523.
  Those == 7 (mod 8) are only 47 (n = 7), 167 (n = 13), 359 (n = 19). Each has a
  non-residue smaller than the corresponding n, so n(q) != n:
  (5/47) = (47/5) = (2/5) = -1;  (5/167) = (167/5) = (2/5) = -1;
  (7/359) = -(359/7) = -(2/7) = -1 (both 7 and 359 are == 3 mod 4; 359 = 51*7 + 2).

So n(q)^2 > q exactly for q = 3, 7, 23. []

This completes the proof of Theorem 2, hence of Proposition 1.3, Corollary 1.4 and
Theorem 1. No analytic input (Burgess, Polya-Vinogradov, GRH) is used.

*Remark (independent second route, not needed above).* Trevino (J. Number Theory 149
(2015) 201-224, Theorem 1.2) proves n(q) <= 1.1 q^(1/4) log q for every prime q > 3.
Since h(q) = q^(1/4) - 1.1 log q is increasing for q > 4.4^4 (about 375) and
h(10963) > 0, this gives n(q) < sqrt(q) for all q >= 10963; together with the machine
check below (no exceptions other than 3, 7, 23 for primes q < 10^7 in `check.gp`, and
for all odd m <= 10^10 in `ext.c`) this re-proves Theorem 2 independently of Lemma C.

## 3. Computations (independent confirmation)

* `verify_oeis.py`: own Jacobi-symbol routine (cross-checked against sympy for all odd
  m < 2000, 0 <= a < 300); A112046 computed from the definition reproduces the b-file
  (n = 1..20000); A112049 b-file (n = 1..32768) reproduced and all A112046(i), i <= 40000,
  are prime; A112051 computed *literally from its definition* reproduces the 43 stored
  terms and gives 60 terms (indices <= 40000), all equal to (prime(n)^2-1)/2 for
  n >= 4; A112052's 40 stored terms reproduced; A216244 b-file (n = 2..4000) equals
  (prime(n)^2-1)/2.
* `small_cases.py`: table of n(q) for all odd primes q < 529 (Euler's criterion),
  exceptions exactly 3, 7, 23; the hand check of the case n <= 23; exhaustive check of
  Lemma C's construction; exact check of the two numerical inequalities at n = 29.
* `check.gp` (PARI/GP, kronecker): first occurrences in A112046(1..10^6) are exactly
  1, 3, 11, (p^2-1)/2; odd primes q < 10^7 with n(q)^2 > q: only 3, 7, 23.
* `ext.c` (C, OpenMP; own binary Jacobi): for every odd m with 3 <= m <= X computes
  f(m) from the definition (k = 1, 2, 3, ... in turn), and checks (i) f(m)^2 > m only
  for m = 3, 7, 23; (ii) every value is prime; (iii) the first occurrence index of
  every value is 1, 3, 11, (p^2-1)/2, and every prime p with p^2 <= X occurs.
  Runs: X = 10^8 (1229 values, all as predicted) and X = 10^10 (`ext_1e10.log`, 3m13s:
  only m = 3, 7, 23 have f(m)^2 > m; 9592 distinct values = all primes below 10^5, each
  first occurring at the predicted index). The resulting terms A112051(1..9592)
  (last: A112051(9592) = (99991^2-1)/2 = 4999100040) are in `b112051_ext.txt`; they agree
  with the A216244 b-file for 4 <= n <= 4000. The stored A112051 has 43 terms.
* `run_all.sh` reruns everything.
