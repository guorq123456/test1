# Closed form for every entry of Hardin's table A253435

All scripts and outputs are in `/tmp/claude-0/deep/hardin-table/`.

## 0. The definition and its reading

A253435: T(n,k) = number of (n+1) X (k+1) 0..1 arrays "with every 2X2 subblock diagonal minus
antidiagonal sum nondecreasing horizontally, vertically and ne-to-sw antidiagonally", for n, k >= 1.
The OEIS entry lists it by antidiagonals: a(1)=T(1,1), then T(1,2), T(2,1), then T(1,3), T(2,2), T(3,1), and so on.
In each antidiagonal n goes up from 1.

**Notation.** The array is x = (x(i,j)), with rows 0 <= i <= n and columns 0 <= j <= k. For 0 <= i <= n-1 and 0 <= j <= k-1 put

    D(i,j) = [x(i,j) + x(i+1,j+1)] - [x(i,j+1) + x(i+1,j)]      (diagonal minus antidiagonal)

so D is an n X k matrix with entries in {-2,...,2}. The array is called **valid** when all three of these hold:

* (V1) horizontally: D(i,j) <= D(i,j+1), whenever both entries exist;
* (V2) vertically: D(i,j) <= D(i+1,j), whenever both entries exist;
* (V3) ne-to-sw: D(i,j+1) <= D(i+1,j), whenever both entries exist. Going one step from the NE cell to the SW cell does not decrease D.

T(n,k) is the number of valid arrays.

**This reading matches the data.** `brute.c` enumerates every 0/1 array of a given size and tests (V1)-(V3).
* It reproduces every term with (n+1)(k+1) <= 26, listed in `brute_out.txt`. That is 40 entries, including the asymmetric pairs T(2,3)=70 vs T(3,2)=73 and T(2,4)=102 vs T(4,2)=108.
* Two other readings of (V3) fail. The opposite direction (sw-to-ne, mode 1) gives the transposed table. The other diagonal (nw-to-se, mode 2) gives T(2,2)=72, not 58.

## 1. Main result

**Theorem.** For all n, k >= 1:

| range | T(n,k) |
|---|---|
| n >= 2, k >= 4 | 9*2^(n-1) + 9*2^(k-1) + 12 |
| n = 1, k >= 4 | 9*2^(k-1) + 37 |
| k = 1, n >= 4 | 9*2^(n-1) + 37 |
| k = 2, n >= 4 | 9*2^(n-1) + 36 |
| k = 3, n >= 3 | 9*2^(n-1) + 49 |
| n, k <= 3 | rows n=1,2,3: (16, 39, 69), (39, 58, 70), (69, 73, 85) |

The table covers every pair (n,k) with n, k >= 1. In particular T(n,k) = 9*2^(n-1) + 9*2^(k-1) + 12 for all n, k >= 4, which is the claim that was asked about, and in fact for all n >= 2, k >= 4.

The proof also classifies the valid arrays (Section 5).

## 2. Elementary facts

**(F1) Rectangle sums.** For 0 <= a < b <= n and 0 <= c < d <= k,

    sum_{i=a}^{b-1} sum_{j=c}^{d-1} D(i,j) = x(a,c) - x(a,d) - x(b,c) + x(b,d).

*Proof.* Write D(i,j) = e(i+1,j) - e(i,j), where e(i,j) = x(i,j+1) - x(i,j). Summing over i telescopes, giving sum_j [e(b,j) - e(a,j)]. Summing over j then telescopes as well. []

The right-hand side adds two 0/1 numbers and subtracts two 0/1 numbers, so **every rectangle sum of D lies in [-2, 2].**

Let P = {(i,j) : D(i,j) >= 1} and N = {(i,j) : D(i,j) <= -1}.

**(F2) Row/column restriction.** For any valid array (any n, k >= 1):
* every (i,j) in P has i >= n-2 and j >= k-2;
* every (i,j) in N has i <= 1 and j <= 1.

*Proof.* Take (i,j) in P.
* By (V1), D(i,j') >= D(i,j) >= 1 for every j' >= j. The rectangle {i} x [j, k-1] then has sum >= k-j, and by (F1) that sum is <= 2. So j >= k-2.
* In the same way, (V2) and the rectangle [i, n-1] x {j} give n-i <= 2.

The statement for N is symmetric. (V1) gives D(i,j') <= -1 for j' <= j, and (F1) bounds the sum over {i} x [0, j] below by -2, so j+1 <= 2. (V2) gives i <= 1 in the same way. []

## 3. Lemma 1: where P and N can be

**Lemma 1.** Assume (H): n >= 1, k >= 2 and max(n,k) >= 4. Then every valid array has

    N ⊆ C- := {(0,0),(0,1)}    and    P ⊆ C+ := {(n-1,k-2),(n-1,k-1)}.

Under (H) the sets C- and C+ are disjoint. If n >= 2 they lie in different rows. If n = 1 then k >= 4, so k-2 >= 2.

*Proof.* **Case n = 1.** (F2) gives N ⊆ {(0,0),(0,1)} and P ⊆ {(0,k-2),(0,k-1)} directly.

**Case n >= 2.** By (F2), N ⊆ {0,1} x {0,1} and P ⊆ {n-2,n-1} x {k-2,k-1}. Four cells remain to be excluded.

* **(b) (1,1) is not in N.** Suppose D(1,1) <= -1. Then:
  * D(1,0) <= D(1,1) by (V1);
  * D(0,1) <= D(1,1) by (V2);
  * D(0,0) <= D(0,1) by (V1).
  
  All four entries of the rectangle {0,1} x {0,1} are <= -1, so its sum is <= -4. This contradicts (F1).

* **(b') (n-2,k-2) is not in P.** Suppose D(n-2,k-2) >= 1. Then:
  * D(n-2,k-1) >= 1 by (V1);
  * D(n-1,k-2) >= 1 by (V2);
  * D(n-1,k-1) >= D(n-1,k-2) >= 1 by (V1).
  
  The rectangle {n-2,n-1} x {k-2,k-1} then has sum >= 4. This contradicts (F1).

* **(c) (1,0) is not in N.** Suppose D(1,0) <= -1. Then:
  * D(0,0) <= D(1,0) <= -1 by (V2);
  * D(0,1) <= D(1,0) <= -1 by (V3) with (i,j) = (0,0).
  
  The rectangle {0,1} x {0,1} has sum >= -2 by (F1), so D(1,1) >= -2 + 3 = 1. Hence (1,1) is in P. By (F2), 1 >= n-2 and 1 >= k-2, that is n <= 3 and k <= 3. This contradicts max(n,k) >= 4.

* **(c') (n-2,k-1) is not in P.** Suppose D(n-2,k-1) >= 1. Then:
  * D(n-1,k-1) >= 1 by (V2);
  * D(n-1,k-2) >= D(n-2,k-1) >= 1 by (V3) with (i,j) = (n-2,k-2).
  
  The rectangle {n-2,n-1} x {k-2,k-1} has sum <= 2, so D(n-2,k-2) <= 2 - 3 = -1. Hence (n-2,k-2) is in N. By (F2), n <= 3 and k <= 3, which again contradicts (H). []

## 4. Proposition 2: an exact characterization

**Proposition 2.** Assume (H). An array x is valid if and only if both of these hold:

* (Z) D(i,j) = 0 for every (i,j) outside C- ∪ C+;
* (Ch) D(0,0) <= D(0,1) <= 0 <= D(n-1,k-2) <= D(n-1,k-1).

*Proof.* (=>) Lemma 1 says D >= 0 outside C- and D <= 0 outside C+. Since C- and C+ are disjoint, this gives (Z), D <= 0 on C- and D >= 0 on C+. (V1) supplies D(0,0) <= D(0,1) and D(n-1,k-2) <= D(n-1,k-1).

(<=) Under (Z) and (Ch):
* D(g) <= 0 for every g outside C+;
* D(g) >= 0 for every g outside C-.

Take any inequality D(a) <= D(b) required by (V1), (V2) or (V3). If a is outside C+ and b is outside C-, then D(a) <= 0 <= D(b). So only the instances with a in C+ or b in C- need checking.

* **a in C+.** Then a lies in row n-1.
  * (V2) and (V3) would need b in row n, so they give no instance.
  * (V1) with a = (n-1,k-2) gives b = (n-1,k-1); this is D(n-1,k-2) <= D(n-1,k-1), part of (Ch).
  * (V1) with a = (n-1,k-1) would need column k, so it gives nothing.
* **b in C-.** Then b lies in row 0.
  * (V2) and (V3) have b in row i+1 >= 1, so they give no instance.
  * (V1) with b = (0,0) is impossible.
  * (V1) with b = (0,1) gives a = (0,0); this is D(0,0) <= D(0,1), part of (Ch). []

`check_char.c` tests Lemma 1 and Proposition 2 exhaustively over all arrays for 23 sizes (21 of them satisfy (H)). For every size satisfying (H) there are no mismatches.
* (n,k) in {(1,4..11), (2,4..7), (3,4..5), (4,2..4), (5,2..3), (6,2), (7,2)}.
* (3,3) is outside (H), yet the equivalence still holds there.
* (4,1) is a deliberate control outside (H), where k = 1 makes the test meaningless; it reports mismatches, as expected.

## 5. Counting by rows

Write R_0, ..., R_n in {0,1}^(k+1) for the rows, and d_i = R_{i+1} - R_i in {-1,0,1}^(k+1). Then

    D(i,j) = d_i(j+1) - d_i(j),

so row i of D is the forward difference of d_i. Write 0^ and 1^ for the constant rows.

### 5.1 How (Z) and (Ch) read in terms of the d_i

**Case n >= 2.** Row 0 meets C- ∪ C+ only in C-, and row n-1 meets it only in C+. So (Z) and (Ch) are equivalent to three conditions:

* (T) d_0 has *TL shape*: d_0(2) = d_0(3) = ... = d_0(k) =: e, and with p = d_0(1) - d_0(0) and q = e - d_0(1) we have p <= q <= 0.
* (M) d_i is a constant vector for every 1 <= i <= n-2.
* (B) d_{n-1} has *BR shape*: d(0) = ... = d(k-2) =: e, and with u = d(k-1) - e and v = d(k) - d(k-1) we have 0 <= u <= v.

**Case n = 1.** There is a single difference vector d = d_0, and (Z) and (Ch) say:
* d(2) = ... = d(k-2) =: e;
* (d(0), d(1), e) satisfies the TL inequalities;
* (e, d(k-1), d(k)) satisfies the BR inequalities.

### 5.2 Lemma 3: the TL patterns

**Lemma 3.** Consider triples (d0, d1, e) in {-1,0,1}^3 with

    d1 - d0 <= e - d1 <= 0.

There are exactly 7 of them:
* the six triples (a, b, b) with b <= a;
* the triple (1, 0, -1).

*Proof.*
* If e = d1, the condition reduces to d1 <= d0.
* If e < d1, then d0 - d1 >= d1 - e >= 1, so d0 - e >= 2. In {-1,0,1} this forces d0 = 1 and e = -1, and then d1 = 0. That triple, (1,0,-1), satisfies the condition with p = q = -1. []

**BR as a mirror image.** The vector d has BR shape exactly when its reversal d~(j) = d(k-j) has TL shape. Indeed,

    d~(1) - d~(0) = -v    and    d~(2) - d~(1) = -u,

so -v <= -u <= 0 is the same as 0 <= u <= v.

### 5.3 The completion counts f and g

For W in {0,1}^(k+1) define:
* f(W) = #{R : W - R has TL shape}, the number of possible R_0 when R_1 = W;
* g(W) = #{R : R - W has BR shape}, the number of possible R_n when R_{n-1} = W.

**Lemma 4.** Let k >= 2 and W = (w0, w1, W') with W' = (w2, ..., wk). Then:

* If W' is not constant, f(W) = 1 + w0.
* If W' ≡ c, f(W) = A_c[w0][w1], where A_0 = [[3,1],[5,3]] and A_1 = [[1,1],[2,3]] (rows indexed by w0).
* g(W) = f(W~), where W~(j) = 1 - W(k-j).

In particular f(0^) = f(1^) = g(0^) = g(1^) = 3.

*Proof.* Each TL pattern (d0, d1, e) from Lemma 3 gives at most one R = W - d, and gives one exactly when every entry w - δ lies in {0,1}. With w in {0,1} and δ in {-1,0,1}, the entry w - δ is in {0,1} exactly when δ is in {w-1, w}. This leads to the following.

* **W' contains both values.** Then e must be 0, leaving the patterns (0,0,0) and (1,0,0). Here d1 = 0 is always allowed, and d0 = 1 is allowed only when w0 = 1. So f(W) = 1 + w0.

* **W' ≡ 0.** Then e is in {-1, 0}, leaving 6 patterns: (-1,-1,-1), (0,-1,-1), (1,-1,-1), (0,0,0), (1,0,0), (1,0,-1). The patterns compatible with (w0, w1) are:

  | (w0, w1) | compatible patterns | count |
  |---|---|---|
  | (0,0) | (-1,-1,-1), (0,-1,-1), (0,0,0) | 3 |
  | (0,1) | (0,0,0) | 1 |
  | (1,0) | (0,-1,-1), (1,-1,-1), (0,0,0), (1,0,0), (1,0,-1) | 5 |
  | (1,1) | (0,0,0), (1,0,0), (1,0,-1) | 3 |

* **W' ≡ 1.** Then e is in {0, 1}, leaving the patterns (0,0,0), (1,0,0), (1,1,1). The patterns compatible with (w0, w1) are:

  | (w0, w1) | compatible patterns | count |
  |---|---|---|
  | (0,0) | (0,0,0) | 1 |
  | (0,1) | (0,0,0) | 1 |
  | (1,0) | (0,0,0), (1,0,0) | 2 |
  | (1,1) | all three | 3 |

* **g.** The map R -> R~, with R~(j) = 1 - R(k-j), is a bijection. It satisfies (W~ - R~)(j) = (R - W)(k-j), so R - W has BR shape exactly when W~ - R~ has TL shape. Hence g(W) = f(W~). []

Explicitly, R_0 in {0^, 1^, 01^k} when R_1 is constant, and R_n in {0^, 1^, 0^k1} when R_{n-1} is constant.

`check_fg.py` checks by brute force over all R, for every W and 2 <= k <= 10, both the 7 patterns and every value given by Lemma 4.

### 5.4 Lemma 5: the middle rows

**Lemma 5.** Let m >= 1. A sequence R_1, ..., R_m of 0/1 rows has constant consecutive differences exactly when one of these holds:
* (i) all R_i are equal to one non-constant row W;
* (ii) every R_i is in {0^, 1^}.

The two cases are disjoint, and case (ii) contains 2^m sequences.

*Proof.* Suppose R_i is non-constant and R_{i+1} - R_i = c·1^ with c ≠ 0. If c = 1, then R_i + 1^ is a 0/1 row, which forces R_i = 0^. If c = -1, it forces R_i = 1^. Both contradict non-constancy, so c = 0 and R_{i+1} = R_i. The same argument with R_{i-1} - R_i shows R_{i-1} = R_i. By induction every row equals R_i. If no R_i is non-constant we are in case (ii). The converse is clear. []

### 5.5 Lemma 6: the sums S_k

Define S_k = sum of f(W)·g(W) over the non-constant W in {0,1}^(k+1).

**Lemma 6.** S_2 = 36, S_3 = 49, and S_k = 9·2^(k-1) + 12 for k >= 4.

*Proof for k >= 4.* Write V = (w0, ..., w_{k-2}). Since (W~)' = (1 - w_{k-2}, ..., 1 - w0), Lemma 4 gives:

* g(W) = 2 - w_k when V is not constant;
* g(W) = A_{1-c}[1-w_k][1-w_{k-1}] when V ≡ c.

Let E be the set of W for which W' or V is constant. For W outside E, f(W)·g(W) = (1+w0)(2-w_k). Over all W,

    sum_W (1+w0)(2-w_k) = 2^(k-1) · 3 · 3 = 9·2^(k-1).

Since k >= 4, the windows W' and V share position 2. So W' ≡ c and V ≡ c' together force c = c' and W constant. Therefore E consists of the two constant words and 12 further distinct words:

* **W' ≡ c, (w0, w1) ≠ (c, c).** Here V is non-constant (it contains w2 = c and differs from c in w0 or w1). So f = A_c[w0][w1] and g = 2 - c.
* **V ≡ c, (w_{k-1}, w_k) ≠ (c, c).** Here W' is non-constant (it contains w_{k-2} = c). So f = 1 + c and g = A_{1-c}[1-w_k][1-w_{k-1}].

| family | words | f·g | sum f·g | baseline (1+w0)(2-w_k) | sum baseline |
|---|---|---|---|---|---|
| W' ≡ 0 | (w0,w1) = 01, 10, 11 | 1·2, 5·2, 3·2 | 18 | 2, 4, 4 | 10 |
| W' ≡ 1 | (w0,w1) = 00, 01, 10 | 1·1, 1·1, 2·1 | 4 | 1, 1, 2 | 4 |
| V ≡ 0 | (w_{k-1},w_k) = 01, 10, 11 | 1·1, 1·2, 1·1 | 4 | 1, 2, 1 | 4 |
| V ≡ 1 | (w_{k-1},w_k) = 00, 01, 10 | 2·3, 2·1, 2·5 | 18 | 4, 2, 4 | 10 |
| constant | 0^, 1^ | (excluded from S_k) | — | 2, 2 | 4 |

So S_k = 9·2^(k-1) - (10+4+4+10+4) + (18+4+4+18) = 9·2^(k-1) + 12.

*Proof for k = 2.* Here W = (w0, w1, w2), W' = (w2) and V = (w0), so f = A_{w2}[w0][w1] and g = A_{1-w0}[1-w2][1-w1]. The six non-constant words give:

| W | 001 | 010 | 011 | 100 | 101 | 110 |
|---|---|---|---|---|---|---|
| f·g | 1·1 | 1·2 | 1·1 | 5·3 | 2·1 | 3·5 |

The sum is 1 + 2 + 1 + 15 + 2 + 15 = 36.

*Proof for k = 3.* Here W' = (w2, w3) and V = (w0, w1). Lemma 4 gives, for the 14 non-constant words:

| W | f·g | W | f·g |
|---|---|---|---|
| 0001 | 1·1 | 1000 | 5·2 |
| 0010 | 1·2 | 1001 | 2·1 |
| 0011 | 1·1 | 1010 | 2·2 |
| 0100 | 1·2 | 1011 | 2·1 |
| 0101 | 1·1 | 1100 | 3·3 |
| 0110 | 1·2 | 1101 | 2·1 |
| 0111 | 1·1 | 1110 | 2·5 |

The sum is 49. []

`check_fg.py` recomputes S_k by brute force for 2 <= k <= 10, together with F = f(0^)+f(1^) = 6, G = g(0^)+g(1^) = 6 and f(0^)g(0^) + f(1^)g(1^) = 18. For 4 <= k <= 9 it also confirms that |E| = 14, that the 12 non-constant words of E have sum of f·g equal to 44, and that the baseline sum over E is 32.

## 6. Proof of the Theorem

**(a) n >= 3, k >= 2, max(n,k) >= 4.** Proposition 2 and 5.1 apply. A valid array is a choice of:
* the middle rows R_1..R_{n-1}, satisfying (M);
* R_0, with f(R_1) choices;
* R_n, with g(R_{n-1}) choices.

By Lemma 5 with m = n-1 >= 2:

    T(n,k) = sum over non-constant W of f(W)g(W)
             + sum over (R_1..R_{n-1}) in {0^,1^}^(n-1) of f(R_1)g(R_{n-1})
           = S_k + 2^(n-3)·(f(0^)+f(1^))·(g(0^)+g(1^))
           = S_k + 2^(n-3)·36
           = S_k + 9·2^(n-1).

Lemma 6 then gives:
* 9·2^(n-1) + 9·2^(k-1) + 12 for n >= 3, k >= 4;
* 9·2^(n-1) + 36 for k = 2, n >= 4;
* 9·2^(n-1) + 49 for k = 3, n >= 4.

**(b) n = 2, k >= 4.** (M) is empty and R_1 = W is arbitrary, so

    T(2,k) = S_k + f(0^)g(0^) + f(1^)g(1^) = S_k + 18 = 9·2 + 9·2^(k-1) + 12.

**(c) n = 1, k >= 4.** By 5.1 the count runs over d in {-1,0,1}^(k+1). Each d comes from 2^(number of zeros of d) pairs (R_0, R_1). The weight of a TL pattern is the product over d0, d1 of m(d), with m(0) = 2 and m(±1) = 1. Grouped by e, the total TL weights are:
* e = -1: 1 + 2 + 1 + 2 = 6;
* e = 0: 4 + 2 = 6;
* e = 1: 1.

The BR side, its mirror image, has the same weights. There are k-3 >= 1 middle positions, each equal to e. So

    T(1,k) = 6·6·1 + 6·6·2^(k-3) + 1·1·1 = 9·2^(k-1) + 37.

`check_fg.py` also confirms this by direct enumeration for 4 <= k <= 10.

**(d) k = 1, n >= 4.** With a single D column, (V1) and (V3) are vacuous and validity means "D column nondecreasing". With a single D row (n = 1), validity means "D row nondecreasing". Transposition x -> x^T maps (n+1) X 2 arrays to 2 X (n+1) arrays. It preserves D, since the diagonal and the antidiagonal of each 2X2 block are mapped to themselves. So it turns (V2) into (V1), and T(n,1) = T(1,n) = 9·2^(n-1) + 37.

**(e) The remaining cases.** These are n, k <= 3. `brute.c` enumerates them exhaustively, giving 16, 39, 69 / 39, 58, 70 / 69, 73, 85. T(3,3) = 85 = 9·4 + 49, so the k = 3 formula also holds at n = 3.

Every pair (n,k) is covered:
* k >= 4: by (a), (b) or (c);
* k in {2, 3}: n >= 4 by (a), n <= 3 by (e);
* k = 1: n >= 4 by (d), n <= 3 by (e). []

**Classification.** For n >= 3, k >= 2 and max(n,k) >= 4, every valid array is exactly one of two kinds:

* **Row type.** R_1..R_{n-1} are constant rows, R_0 is in {0^, 1^, 01^k} and R_n is in {0^, 1^, 0^k1}. There are 9·2^(n-1) of these.
* **Frozen type.** R_1 = ... = R_{n-1} = W with W non-constant. R_0 = W - d with d a TL pattern, and R_n = W + d' with d' a BR pattern (Lemma 4). There are S_k of these.

The table is symmetric for n, k >= 4 even though the rule is not invariant under transposition. That happens because S_k - 12 = 9·2^(k-1) equals the row-type count with n replaced by k.

## 7. Consequences for the OEIS entries

Every formula below is marked "Empirical" in OEIS, and each follows from the Theorem.

* **A253435.**
  * All closed forms for rows 1..7, columns 1..7 and the diagonal.
  * The whole "summary table of c": c = 28 for row 1 and column 1, 18 for column 2, 13 for column 3, and 12 elsewhere in the eventual range.
  * The recurrences.
  * The entry's typo "9*2(n-1)" should read 9*2^(n-1).
* **A253152** (column 1). 9·2^(n-1) + 37 for n > 3.
* **A253429, A253430** (columns 2, 3). +36 for n > 3 and +49 for n > 2.
* **A253431–A253434** (columns 4–7). 9·2^(n-1) + 9·2^(k-1) + 12, which gives +84, +156, +300, +588 for n > 1.
* **A253436, A253437** (rows 2, 3). +30 and +48 for k > 3.
* **A253438–A253441** (rows 4–7). +84, +156, +300, +588 for k > 3.
* **A253428** (diagonal). 9·2^n + 12 for n > 3.
* **Recurrences.** Every a(n) = 3a(n-1) - 2a(n-2) with its stated threshold.
* **Barker's g.f.s.** Each is checked against the Theorem on 60 coefficients. Both sides satisfy the recurrence from n >= 6, so the g.f.s agree for all n.

`check_gf.py` (output in `check_gf.out`) checks each of these formulas against the Theorem for 400 terms. Every stated threshold is also sharp: the formula fails at the threshold itself.

## 8. Independent computations

* **`brute.c`** enumerates all 2^((n+1)(k+1)) arrays for every size with at most 26 cells (40 entries, `brute_out.txt`). It is also used to compare the readings of the definition.
* **`check_char.c`** checks Lemma 1 and Proposition 2 exhaustively on the 23 sizes listed in Section 4.
* **`check_fg.py`** checks the 7 TL patterns, f, g, g = f∘~, S_k, F, G and the n = 1 count, by brute force for 2 <= k <= 10.
* **`dp.cpp`** is a transfer matrix over rows; its state is the pair of the last two rows, and the next row is generated by a pruned DFS.
  * Mode 0 gives columns.
  * Mode 1, the mirrored rule on the transposed array, gives rows.
  * Widths 2..24 were run in both modes, up to 60 rows for widths <= 22 and 30 rows for widths 23–24 (`dpout/`). Width 24 has 37,748,773 states (9·2^22 + 37 = T(1,23), as predicted).
* **`dp_big.py`** is an independent Python big-integer transfer matrix for widths 2..8, up to 210 rows (`dpbig/`).
* **`compare_all.py`** (output in `compare_all.out`) compares everything with the Theorem:
  * 4211 distinct (n,k) are computed: all entries with min(n,k) <= 23, and max(n,k) up to 30, 60 or 210 depending on the width. 1047 of them are computed by two independent runs. There are **0 mismatches** with the Theorem.
  * All 1101 b-file terms of A253435, which cover every entry with n+k <= 47, are recomputed independently and agree.
  * All 210-term b-files of A253152, A253429–A253434 and A253436–A253441, and the A253428 b-file, agree with the Theorem.
