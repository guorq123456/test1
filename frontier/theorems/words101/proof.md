# A225034 (101-avoiding words), A163765, A048775, A005773: a complete proof

All files referred to are in `/tmp/claude-0/deep/words101/`.

## 0. The sequences (exact definitions and offsets)

* **a(n) = A225034(n)**, offset 0: the number of binary words `w` with exactly `n` letters 1 and
  at most `n` letters 0 which do not contain `101` as a *factor* (three consecutive letters).
  (Factor, not subsequence: the entry's example for n = 2 lists `1001`.)
  Data: 1, 3, 7, 18, 48, 131, 363, 1017, ...
* **D(n) = A005773(n)**, offset 0: D(0) = 1 and, for n >= 1, D(n) = number of directed (site)
  animals of size n on the square lattice. Data: 1, 1, 2, 5, 13, 35, 96, 267, ...
* **b(n) = A048775(n)**, offset 1: number of pairs (I, f) where I = [i..j] is a nonempty interval of
  {1..n} and f : I -> {1..n} is weakly increasing. Data: 1, 7, 31, 121, 456, ...
* **c(n) = A163765(n)**, offset 1: "inverse binomial transform of A048775 (assuming offset zero in
  both sequences)", i.e. with b re-indexed from 0 as b(k+1), k >= 0, and c re-indexed from 0 as
  c(m+1), m >= 0:

      c(m+1) = Sum_{k=0..m} (-1)^(m-k) C(m,k) b(k+1),   m >= 0.          (0.1)

  This reading reproduces all 28 stored terms 1, 6, 18, 48, 131, ... and the entry's own example
  48 = (-1,3,-3,1).(1,7,31,121) (checked in `verify.py`, check 8/9).

Notation: C(r,k) is the binomial coefficient, [P] is 1 if P holds and 0 otherwise,
[y^j]F is the coefficient of y^j in the formal power series F. All generating functions are
formal power series over Q; no analytic convergence is used anywhere.

Throughout, **R(x)** denotes the unique formal power series with R(0) = 1 and

    R(x)^2 = (1+x)/(1-3x).                                                  (0.2)

(Uniqueness: if R1^2 = R2^2 with R1(0) = R2(0) = 1, then (R1-R2)(R1+R2) = 0 and R1+R2 has
constant term 2, hence is a unit, so R1 = R2. Existence follows e.g. from Lemma 4 below.)

## 1. Statement

**Theorem.**

1. (Explicit form) For every n >= 1,

       a(n) = Sum_{k=0..n-1} (-1)^(n-1-k) C(n-1,k) C(2k+3,k+1),

   i.e. (a(n+1))_{n>=0} = 3, 7, 18, 48, ... is the inverse binomial transform of
   (C(2n+3,n+1))_{n>=0} = 3, 10, 35, 126, ... Also a(n) = Sum_{j=0..n-1} C(n-1,j) C(j+3,n-j), n >= 1.
2. (Generating function) A(x) := Sum_{n>=0} a(n) x^n satisfies 2x A(x) = (1+x)(R(x) - 1), i.e.

       A(x) = (1+x) (sqrt((1+x)/(1-3x)) - 1) / (2x),

   and this equals the g.f. stated as "Theorem" in A225034,
   2(1-x^2)/(3x^2-4x+1+sqrt((1-x^2)^2-4(x-x^2)(1-x^2))).
3. (Directed animals) a(0) = D(1) = 1 and **a(n) = D(n) + D(n+1) for all n >= 1**.
   [Uses one external input, the classical g.f. of directed animals, see Section 4.]
4. (A163765) c(1) = a(1) - 2 = 1, c(2) = a(2) - 1 = 6, and **c(n) = a(n) for all n >= 3**.
   Equivalently Sum_{n>=1} c(n) x^n = A(x) - 1 - 2x - x^2.
5. (Berselli's recurrence) For all n >= 2,

       (n+1) a(n) - (2n+3) a(n-1) - 3(n-2) a(n-2) = 0,

   (and 2a(1) - 5a(0) = 1). This recurrence is a direct consequence of the g.f. printed as
   "Theorem" in A225034 (by part 2 that g.f. equals (1+x)(R-1)/(2x)), and it is also proved here
   from the definition alone.

Parts 1, 2, 4, 5 are proved from the definitions with no external input. Part 3 uses only the
(published, classical) theorem that the directed-animal numbers have g.f. (1 + R(x))/2.

## 2. From words to a coefficient (Lemma 1)

**Lemma 1 (gap decomposition).** For n >= 1 and m >= 0 let W(n,m) be the number of binary words
with exactly n ones and m zeros that avoid the factor 101. Then

    W(n,m) = [y^m] (1-y)^(-2) * (1/(1-y) - y)^(n-1).

Consequently, for every n >= 0,

    a(n) = [y^n] (1 - y + y^2)^(n-1) / (1-y)^(n+2)          (n >= 1),   a(0) = 1.   (2.1)

*Proof.* A word with n >= 1 ones and m zeros is uniquely of the form

    w = 0^{g_0} 1 0^{g_1} 1 0^{g_2} ... 0^{g_{n-1}} 1 0^{g_n},

and w <-> (g_0, ..., g_n) is a bijection onto (n+1)-tuples of nonnegative integers with sum m.

*Claim:* w contains the factor 101 iff g_i = 1 for some 1 <= i <= n-1.
(<=) If g_i = 1 with 1 <= i <= n-1, the i-th one, the single zero 0^{g_i}, and the (i+1)-st one are
three consecutive letters 101. (=>) Suppose w_p w_{p+1} w_{p+2} = 101. The ones at positions p and
p+2 have no one strictly between them (position p+1 holds 0), so they are the i-th and (i+1)-st
ones for some 1 <= i <= n-1, and exactly one zero lies between them, i.e. g_i = 1.

Hence W(n,m) counts tuples with sum m in which the internal gaps g_1..g_{n-1} avoid the value 1 and
the end gaps g_0, g_n are arbitrary. The generating polynomial (in y, marking zeros) of an end gap
is Sum_{g>=0} y^g = 1/(1-y), and of an internal gap Sum_{g>=0, g != 1} y^g = 1/(1-y) - y. The
gaps are chosen independently, so the generating function of the tuples by sum is the product
(1-y)^(-2) (1/(1-y) - y)^(n-1), proving the formula for W(n,m).

For n >= 1, a(n) = Sum_{m=0..n} W(n,m) = [y^n] (1-y)^(-1) * (1-y)^(-2) (1/(1-y)-y)^(n-1)
(multiplying by 1/(1-y) forms partial sums of coefficients). Since 1/(1-y) - y = (1-y+y^2)/(1-y),
this is [y^n] (1-y+y^2)^(n-1) (1-y)^(-(n+2)). For n = 0 the only word with zero ones and at most
zero zeros is the empty word (which avoids 101), so a(0) = 1. QED

We use the standard coefficient formula, valid for every integer r >= 1 and j >= 0:

    [y^j] (1-y)^(-r) = C(r+j-1, j),                                         (2.2)

and, for every integer e and j >= 0, [y^j](1-y)^e = (-1)^j C(e,j) with the upper-negation rule
(-1)^j C(e,j) = C(j-e-1, j) (both standard; (2.2) is the case e = -r).

## 3. Part 1: the inverse binomial transform form

**Lemma 2.** For n >= 1, a(n) = Sum_{i=0..n-1} (-1)^(n-1-i) C(n-1,i) C(2i+3, i+1).

*Proof.* Write 1 - y + y^2 = 1 - y(1-y). Since n - 1 >= 0, the binomial theorem gives the finite
expansion (1 - y(1-y))^(n-1) = Sum_{k=0..n-1} (-1)^k C(n-1,k) y^k (1-y)^k. Insert in (2.1):

    a(n) = Sum_{k=0..n-1} (-1)^k C(n-1,k) [y^(n-k)] (1-y)^(-(n+2-k)).

Here r = n+2-k >= 3 and j = n-k >= 1, so by (2.2) the coefficient is
C((n+2-k)+(n-k)-1, n-k) = C(2n-2k+1, n-k). Put i = n-1-k (so k = n-1-i, C(n-1,k) = C(n-1,i)):
C(2n-2k+1, n-k) = C(2i+3, i+1) and (-1)^k = (-1)^(n-1-i). QED

**Corollary 2' (positive formula).** For n >= 1, a(n) = Sum_{j=0..n-1} C(n-1,j) C(j+3, n-j).

*Proof.* Write 1-y+y^2 = (1-y)^2 + y, so by (2.1)
a(n) = Sum_{j=0..n-1} C(n-1,j) [y^(n-j)] (1-y)^(n-4-2j). By the rule after (2.2) with e = n-4-2j,
j' = n-j: [y^(n-j)](1-y)^(n-4-2j) = C((n-j)-(n-4-2j)-1, n-j) = C(j+3, n-j). QED

(Both formulas are checked against the automaton count for n <= 1200 and n <= 300 respectively,
`verify.py` check 3.)

## 4. Part 2: the generating function, and Part 3

**Lemma 3 (inverse binomial transform).** Let s(k), k >= 0, have g.f. S(x) and
t(m) = Sum_{k=0..m} (-1)^(m-k) C(m,k) s(k). Then Sum_{m>=0} t(m) x^m = S(x/(1+x)) / (1+x).

*Proof.* z = x/(1+x) has zero constant term, so F(x) -> F(z) is a well-defined ring homomorphism
of Q[[x]]. Using the negative binomial series (1+x)^(-k-1) = Sum_{j>=0} (-1)^j C(k+j,j) x^j,

    S(z)/(1+x) = Sum_k s(k) x^k (1+x)^(-k-1) = Sum_k Sum_j s(k) (-1)^j C(k+j,k) x^(k+j),

and collecting x^m (only k <= m contribute, so all sums are finite) gives
Sum_{k<=m} (-1)^(m-k) C(m,k) s(k) = t(m). QED

**Lemma 4.** Let B(x) = Sum_{j>=0} C(2j,j) x^j. Then B(x)^2 = 1/(1-4x), B(x/(1+x)) = R(x), and

    2x^2 * Sum_{k>=0} C(2k+3,k+1) x^k = B(x) - 1 - 2x.                       (4.1)

*Proof.* B(x) is the binomial series (1-4x)^(-1/2), because C(-1/2, j)(-4)^j = C(2j,j); the formal
binomial series satisfy (1+u)^alpha (1+u)^beta = (1+u)^(alpha+beta) (Vandermonde), so
B^2 = (1-4x)^(-1). (Equivalently, Sum_{i+j=n} C(2i,i)C(2j,j) = 4^n.) Applying the homomorphism of
Lemma 3: B(z)^2 = 1/(1-4z) = (1+x)/(1-3x) since 1 - 4z = (1-3x)/(1+x); and B(z) has constant
term 1, so B(z) = R(x) by the uniqueness in (0.2). For (4.1): for k >= 0, with N = k+2 >= 1,
C(2N,N) = (2N/N) C(2N-1,N-1) = 2 C(2k+3,k+1); hence
Sum_k 2C(2k+3,k+1) x^(k+2) = Sum_{N>=2} C(2N,N) x^N = B(x) - 1 - 2x. QED

**Proof of Part 2.** Let S(x) = Sum_{k>=0} C(2k+3,k+1) x^k and T(x) = Sum_{m>=0} a(m+1) x^m.
By Lemma 2, (a(m+1))_m is the inverse binomial transform of (C(2k+3,k+1))_k, so by Lemma 3
T(x) = S(z)/(1+x), z = x/(1+x). Apply the homomorphism to (4.1) and use Lemma 4:
2 z^2 S(z) = R - 1 - 2z. Multiply by (1+x)^2 (note z^2 (1+x)^2 = x^2) and then divide by the unit
(1+x):

    2x^2 T(x) = (1+x)(R - 1) - 2x.

Since A(x) = a(0) + x T(x) = 1 + x T(x), this reads 2x(A(x) - 1) = (1+x)(R-1) - 2x, i.e.

    2x A(x) = (1+x) (R(x) - 1).                                             (4.2)

(R - 1 has zero constant term, so the right side is divisible by x and (4.2) determines A
uniquely.)

*Agreement with the entry's "Theorem" g.f.* Let G = 2(1-x^2)/(3x^2-4x+1+Q) where Q is the square
root with constant term 1 of Delta = (1-x^2)^2 - 4(x-x^2)(1-x^2). Factor:
Delta = (1-x^2)[(1-x^2) - 4x(1-x)] = (1-x^2)(1-x)(1-3x) = (1-x)^2 (1+x)(1-3x).
The series (1-x)(1-3x)R has constant term 1 and square (1-x)^2(1-3x)^2 (1+x)/(1-3x) = Delta, so
Q = (1-x)(1-3x)R. Also 3x^2-4x+1 = (1-x)(1-3x). Hence the denominator is (1-x)(1-3x)(1+R)
(constant term 2, a unit) and G = 2(1+x)/((1-3x)(1+R)). Now
(1+x)(R-1)(1-3x)(1+R) = (1+x)(1-3x)(R^2-1) = (1+x)(1-3x) * 4x/(1-3x) = 4x(1+x)
because R^2 - 1 = (1+x)/(1-3x) - 1 = 4x/(1-3x). Thus (1+x)(R-1)/(2x) = 2(1+x)/((1-3x)(1+R)) = G.
So the entry's g.f. (proved by Bilotta, Grazzini, Pergola, JIS 16 (2013) 13.4.8, Prop. 4 with
j = 1, by the ECO method) and the g.f. derived here coincide; our derivation is independent.

**External input for Part 3 (directed animals).** It is a classical theorem (D. Dhar, PRL 49
(1982) 959-962; D. Gouyou-Beauchamps and G. Viennot, Adv. Appl. Math. 9 (1988) 334-357; see also
M. Bousquet-Melou, Discrete Math. 180 (1998) 73-106) that the number of directed animals of size
n >= 1 on the square lattice has g.f. Sum_{n>=1} D(n) x^n = (R(x) - 1)/2; this is the g.f.
1/2 + (1/2) sqrt((1+x)/(1-3x)) listed in A005773 (with D(0) = 1). Equivalently
D(n) = Sum_{q} C(n-1,q) C(q, floor(q/2)) for n >= 1. We re-checked it by brute-force enumeration of
directed animals for 1 <= n <= 15 (`animals.py`) and against the 201 b-file terms of A005773
(`verify.py`).

**Proof of Part 3.** By the cited theorem, R - 1 = 2 Sum_{n>=1} D(n) x^n. Substituting in (4.2)
and dividing by 2:

    x A(x) = (1+x) Sum_{n>=1} D(n) x^n.

Comparing coefficients of x^(n+1), n >= 0: a(n) = D(n+1) + D(n)[n >= 1]. Hence a(0) = D(1) = 1
and a(n) = D(n) + D(n+1) for n >= 1. QED

(Note: at n = 0 the formula D(0)+D(1) = 2 does not give a(0) = 1; the identity holds exactly for
n >= 1.)

## 5. Part 4: A163765

**Lemma 5.** For n >= 1, b(n) = A048775(n) = C(2n+1, n+1) - (n+1).

*Proof.* For an interval of length s (1 <= s <= n) there are n+1-s positions, and weakly increasing
maps from an s-element chain to {1..n} are s-multisets of {1..n}, of which there are C(n+s-1, s).
So b(n) = Sum_{s=1..n} (n+1-s) C(n-1+s, s) (this is N. J. A. Sloane's comment in A048775).
Add the s = 0 term (n+1) C(n-1,0) = n+1. Writing n+1-s = #{t : s <= t <= n},

    Sum_{s=0..n} (n+1-s) C(n-1+s, s) = Sum_{t=0..n} Sum_{s=0..t} C(n-1+s, s)
                                     = Sum_{t=0..n} C(n+t, t) = C(2n+1, n),

using the hockey-stick identity Sum_{s=0..t} C(r+s, s) = C(r+t+1, t) twice (r = n-1 >= 0, then
r = n). Hence b(n) = C(2n+1,n) - (n+1) = C(2n+1,n+1) - (n+1). QED

(Brute-force check of the *definition* for n <= 9 and of the sum for n <= 1201: `verify.py`
check 7; also all 1000 b-file terms.)

**Proof of Part 4.** By (0.1) and Lemma 5, b(k+1) = C(2k+3,k+2) - (k+2) = C(2k+3,k+1) - (k+2), so
for m >= 0

    c(m+1) = Sum_{k=0..m} (-1)^(m-k) C(m,k) C(2k+3,k+1) - E(m),
    E(m)   = Sum_{k=0..m} (-1)^(m-k) C(m,k) (k+2).

The first sum is a(m+1) by Lemma 2. For E: Sum_k (-1)^(m-k) C(m,k) = (1-1)^m = [m=0], and
Sum_k (-1)^(m-k) C(m,k) k = m Sum_{k>=1} (-1)^(m-k) C(m-1,k-1) = m (1-1)^(m-1) = [m=1] for
m >= 1 (and 0 for m = 0). So E(m) = 2[m=0] + [m=1], and with n = m+1:

    c(n) = a(n) - 2[n=1] - [n=2]     (n >= 1).

Thus c(1) = 3-2 = 1, c(2) = 7-1 = 6, and c(n) = a(n) for every n >= 3. The g.f. statement follows
from a(0) = 1. QED

(In particular c(n) = A005773(n) + A005773(n+1) for n >= 3, and c satisfies Berselli's recurrence
for n >= 5, since then c(n), c(n-1), c(n-2) all equal the corresponding a-values.)

## 6. Part 5: Berselli's recurrence

**Lemma 6.** (1+x)(1-3x) R'(x) = 2 R(x).

*Proof.* Differentiate (1-3x) R^2 = 1+x (formal derivative; product rule holds in Q[[x]]):
2(1-3x) R R' - 3R^2 = 1. Multiply by (1+x) and use 1+x = (1-3x)R^2:
2(1-3x)(1+x) R R' = (1+x) + 3(1+x)R^2 = (1-3x)R^2 + 3(1+x)R^2 = 4R^2.
R is a unit (R(0) = 1); cancel 2R. QED

**Proof of Part 5.** Put V = R - 1, so by (4.2) (1+x) V = 2x A, and by Lemma 6
(1+x)(1-3x) V' = 2V + 2. Differentiating (1+x)V = 2xA gives V + (1+x)V' = 2A + 2xA'. Multiply by
(1-3x) and substitute: (1-3x)V + 2V + 2 = 2(1-3x)(A + xA'), i.e. 3(1-x) V + 2 = 2(1-3x)(A + xA').
Multiply by (1+x) and use (1+x)V = 2xA: 6x(1-x) A + 2(1+x) = 2(1-3x)(1+x)(A + xA'). Since
(1-3x)(1+x) - 3x(1-x) = 1 - 5x, this is the linear ODE

    x(1+x)(1-3x) A'(x) + (1-5x) A(x) = 1 + x.                               (6.1)

Now x(1+x)(1-3x) = x - 2x^2 - 3x^3, and [x^n] x^(1+i) A' = (n-i) a(n-i). Taking [x^n] in (6.1),
with a(-1) = a(-2) = 0:

    n a(n) - 2(n-1) a(n-1) - 3(n-2) a(n-2) + a(n) - 5 a(n-1) = [n=0] + [n=1],

i.e. (n+1) a(n) - (2n+3) a(n-1) - 3(n-2) a(n-2) = [n=0] + [n=1]. For n >= 2 the right side is 0,
which is exactly Berselli's conjecture ("for n > 1"). (n = 0: a(0) = 1; n = 1: 2*3 - 5*1 = 1.) QED

Since the leading coefficient n+1 never vanishes, the recurrence together with a(0) = 1, a(1) = 3
determines the sequence; conversely (6.1) with A(0) = 1 has a unique power-series solution, so the
recurrence is equivalent to the g.f. Because Section 4 shows the entry's "Theorem" g.f. equals
(1+x)(R-1)/(2x), **the recurrence was already a formal consequence of the g.f. proved by Bilotta,
Grazzini and Pergola**; it should never have needed the label "Conjecture". The derivation above
uses only (4.2) and (0.2), and (4.2) is proved here from the definition, so the recurrence is now
proved twice over.

## 7. A side remark on J. Arndt's comment in A225034

The comment says "Number of weakly increasing words of length n+1 with n+2 letters such that no
up-step is by 1". The words listed in its example for n = 3 have length 3 (e.g. [0 2 4]), and the
correct statement is **length n** (with n+2 letters {0,...,n+1}). Words of length n+1 give
2, 4, 10, 26, 70, 192, ... (= A025565(n+2), offset 1), not A225034 (`arndt_check.py`, n <= 11).

*Proof of the corrected statement (n >= 1).* For w_1 <= ... <= w_n in {0..n+1} put h_0 = w_1,
h_i = w_{i+1} - w_i (1 <= i <= n-1), h_n = n+1 - w_n. This is a bijection onto tuples
(h_0..h_n) of nonnegative integers with sum n+1, and "no up-step by 1" means h_i != 1 for
1 <= i <= n-1. As in Lemma 1 the count is [y^(n+1)] (1-y)^(-2) P^(n-1), P = 1/(1-y) - y, while
a(n) = [y^n] (1-y)^(-3) P^(n-1). The difference is [y^(n+1)] (1-2y)(1-y+y^2)^(n-1)(1-y)^(-(n+2))
(because (1-y)^(-2) - y(1-y)^(-3) = (1-2y)(1-y)^(-3)). Expanding (1 - y(1-y))^(n-1) as in Lemma 2,
the k-th term is (-1)^k C(n-1,k) times
[y^N](1-y)^(-(N+1)) - 2[y^(N-1)](1-y)^(-(N+1)) = C(2N,N) - 2C(2N-1,N-1) = 0, N = n+1-k >= 2.
So the difference is 0. (n = 0: the empty word, count 1 = a(0).) QED

## 8. Computations (all exact integer arithmetic)

| script | what it does | range |
|---|---|---|
| `enum101.c` | brute force from the definition: enumerates every word with n ones and m <= n zeros (Gosper's hack), tests for factor 101 | n <= 17 (`enum101_17.out`) |
| `verify.py` | (1) 3-state automaton DP over (#1, #0) from the definition; (2) Lemma 1 coefficient formula, n <= 60; (3) Lemma 2 for n <= 1200 and Cor. 2' for n <= 300; (4) a(n) = D(n)+D(n+1), D from the g.f. via exact series square root, n <= 1200 (and Somos' recurrence for D); (5) Berselli recurrence 2 <= n <= 1200; (6) sympy expansion of the entry's g.f. and of (1+x)(R-1)/(2x), n < 60; (7) A048775 definition brute force n <= 9 and Lemma 5 n <= 1201; (8) A163765 from (0.1) vs a(n), n <= 1200; (9) all OEIS b-files: A225034 (n <= 1000), A005773 (n <= 200), A048775 (n <= 1000), A163765 (28 terms), and the enumeration outputs | as stated |
| `check_gf.gp` | PARI/GP: expands the entry's g.f. and (1+x)(R-1)/(2x) to O(x^1202), compares with the DP values `a225034_dp.txt`, and checks the recurrence | n <= 1200 |
| `animals.py` | brute-force directed animals (N/E steps from the root), dedup by sets | n <= 15 |
| `arndt_check.py` | Section 7 | n <= 11 |

Output: `verify.log` ends with `ALL CHECKS PASSED`; `check_gf.gp` prints `1` for both checks;
`animals.out` reproduces 1, 2, 5, ..., 1201917. No discrepancy was found anywhere. No finite case
check is *needed* by the proofs (every statement is proved for all n); the computations are
independent confirmation.

## 9. What is new relative to the OEIS entries (snapshot of 2026-10-01, identical to live)

* **A225034**: the formula "(n+1)a(n) - (2n+3)a(n-1) - 3(n-2)a(n-2) = 0 for n > 1" is labeled
  "Conjecture" (Berselli 2013). It is proved here (Part 5), and it is in fact an immediate
  consequence of the g.f. already labeled "Theorem" in the entry. New formulas (not in the entry):
  a(n) = A005773(n) + A005773(n+1) for n >= 1; a(n) = Sum_{k=0..n-1} (-1)^(n-1-k) C(n-1,k)
  C(2k+3,k+1) (n >= 1); a(n) = Sum_{j=0..n-1} C(n-1,j) C(j+3,n-j) (n >= 1);
  a(n) = [y^n] (1-y+y^2)^(n-1)/(1-y)^(n+2); simplified g.f. (1+x)(sqrt((1+x)/(1-3x)) - 1)/(2x);
  a(n) = A163765(n) for n >= 3. An independent elementary proof of the "Theorem" g.f. Missing
  cross-references: A005773, A163765, A048775, A001700. Arndt's comment should read "length n"
  (Section 7).
* **A163765**: has no formula beyond its definition and no cross-reference besides A048775. New:
  A163765(n) = A225034(n) = A005773(n) + A005773(n+1) for n >= 3 (A163765(1) = 1, A163765(2) = 6);
  g.f. (1+x)(sqrt((1+x)/(1-3x)) - 1)/(2x) - 1 - 2x - x^2; for n >= 3 it counts 101-avoiding binary
  words with n ones and at most n zeros; it satisfies Berselli's recurrence for n >= 5.
* **A005773**: could get the cross-reference A005773(n) + A005773(n+1) = A225034(n), n >= 1.
