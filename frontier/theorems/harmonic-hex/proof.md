# A228016(n) = A087125(n+1): Kimberling's harmonic greedy sequence is the hex-triangular index sequence

All files referred to below are in `/tmp/claude-0/deep/harmonic-hex/`.

## 0. Definitions and statement

Throughout, `H(0) = 0` and `H(k) = 1 + 1/2 + ... + 1/k` for integers `k >= 1`.
`H` is strictly increasing on the non-negative integers.

**A228016** (offset 1). Name of the entry, with `(x,y) = (1,5)`:

* `a(1)` = least `k` such that `1/1+...+1/5 < H(k) - H(5)`, i.e. `H(5) - H(0) < H(k) - H(5)`;
* `a(2)` = least `k` such that `H(a(1)) - H(5) < H(k) - H(a(1))`;
* for `n > 2`, `a(n)` = least `k` such that `H(a(n-1)) - H(a(n-2)) < H(k) - H(a(n-1))`.

(The entry's %N line prints `>` in the third clause. Read literally ("least `k` with
`H(a(n-1)) - H(a(n-2)) > H(k) - H(a(n-1))`") this would give `k = 1` for every `n`, which
contradicts the data. The %C line states the rule with `<`. The Mathematica program, which
produced the data and the b-file, takes `Ceiling` of the real root `w` of
`H(w) = 2H(a(n-1)) - H(a(n-2))`, and that is the `<` reading. So `<` is what is meant, and Section 5
shows that both the `<` and the `<=` readings, and the program's `Ceiling`, give the same sequence.)

The three clauses become one rule if we put `c_{-1} = 0` and `c_0 = 5`. Then for `n >= 1`

    c_n = min { k >= 1 : H(k) > T(c_{n-1}, c_{n-2}) },   where T(p, q) := 2 H(p) - H(q),      (0.1)

and `A228016(n) = c_n` for `n >= 1`. Indeed `H(y) - H(x-1) < H(k) - H(y)` with `x = 1`, `y = 5` is
`H(k) > 2H(5) - H(0)`.

**A087125** (offset 0): the indices `k >= 0` for which the hex number `3k(k+1)+1` is triangular,
in increasing order.

**The sequence e.** Define integers `e_0 = 0`, `e_1 = 5`, and `e_n = 10 e_{n-1} - e_{n-2} + 4` for `n >= 2`.
So `e = 0, 5, 54, 539, 5340, 52865, 523314, ...`

> **Theorem.**
> (a) `A087125(n) = e_n` for all `n >= 0`.
>
> (b) For every `n >= 2`,
>
>        H(e_n - 1)  <  2 H(e_{n-1}) - H(e_{n-2})  <  H(e_n)        (strict on both sides).
>
> (c) `A228016(n) = e_{n+1} = A087125(n+1)` for every `n >= 1`.
>
> **Corollaries** (Section 6). For `n >= 4`, `A228016(n) = 11 A228016(n-1) - 11 A228016(n-2) + A228016(n-3)`.
> Also `sum_{n>=1} A228016(n) x^(n-1) = (54 - 55x + 5x^2)/(1 - 11x + 11x^2 - x^3)`, which is Kimberling's g.f.
> `(-54 + 55x - 5x^2)/(-1 + 11x - 11x^2 + x^3)`. Both are listed as "conjectured" in A228016 and are
> now proved. Moreover
> `A228016(n) = ((2+sqrt6)(5+2sqrt6)^(n+1) + (2-sqrt6)(5-2sqrt6)^(n+1) - 4)/8`,
> `A228016(n)/A228016(n-1) -> 5+2sqrt6` and `H(A228016(n)) - H(A228016(n-1)) -> log(5+2sqrt6)`.

Proof outline. Part (a) is a Pell-equation computation. Part (c) follows from (b) by induction.
Part (b) is the analytic core. We write `b_n = e_n + 1/2`, which satisfies `b_{n-1}^2 - b_n b_{n-2} = 3`,
and we use two-sided bounds, with explicit constants and valid for every `m >= 0`, on
`H(m) - log(m + 1/2) - gamma`. Only the single case `n = 2` (the triple `0, 5, 54`) is checked by
direct exact computation, and Section 4 also gives a hand verification of it.

---

## 1. Part (a): the hex-triangular indices (Pell equation)

Let `k >= 0`. The hex number `3k(k+1)+1` is triangular iff `3k(k+1)+1 = m(m+1)/2` for some integer `m >= 0`.
Multiply by 8 and add 1. Since `24k^2 + 24k + 9 = 6(2k+1)^2 + 3`, this is equivalent to

    (2m+1)^2 - 6 (2k+1)^2 = 3.                                              (1.1)

Conversely, suppose `X^2 - 6Y^2 = 3` with `X, Y >= 1` and `Y` odd. Then `X^2 = 6Y^2 + 3` is odd, so `X` is odd.
Putting `m = (X-1)/2 >= 0` and `k = (Y-1)/2 >= 0` gives a solution of (1.1). So the hex-triangular
indices are exactly the numbers `(Y-1)/2`, where `(X, Y)` runs over the positive integer solutions of
`X^2 - 6Y^2 = 3` with `Y` odd.

**Lemma 1.1.** Let `S = {(X,Y) in Z_{>0}^2 : X^2 - 6Y^2 = 3}`. Define `(X_0, Y_0) = (3, 1)` and
`(X_{j+1}, Y_{j+1}) = (5X_j + 12Y_j, 2X_j + 5Y_j)`. Then `S = {(X_j, Y_j) : j >= 0}`.

*Proof.* Write `N(X,Y) = X^2 - 6Y^2`. The map `(X,Y) -> (5X+12Y, 2X+5Y)` is multiplication of `X + Y sqrt6` by
`5 + 2 sqrt6`, and `N(5,2) = 1`. Directly, `(5X+12Y)^2 - 6(2X+5Y)^2 = X^2 - 6Y^2`. So every `(X_j, Y_j)` lies in `S`,
because the coordinates stay positive integers.

Conversely, let `(X, Y) in S` with `Y >= 2`. The values `Y = 2, 3` would need `X^2 = 27` or `X^2 = 57`, which are
not squares, so `Y >= 4`. Put `X' = 5X - 12Y` and `Y' = 5Y - 2X`. The inverse map also preserves `N`, so
`N(X', Y') = 3`. Moreover:

* `X' > 0`, because `25X^2 = 150Y^2 + 75 > 144Y^2`;
* `Y' > 0`, because `25Y^2 > 4X^2 = 24Y^2 + 12` is equivalent to `Y^2 > 12`, which holds for `Y >= 4`;
* `Y' < Y`, because this is `2Y < X`, and `4Y^2 < 6Y^2 + 3 = X^2`.

So `(X', Y') in S`, `Y' < Y`, and `(X, Y) = (5X' + 12Y', 2X' + 5Y')`. Repeating this step strictly decreases the
positive integer `Y`, so after finitely many steps we reach an element of `S` with `Y = 1`. That element is
`(3, 1)`. Hence `(X, Y) = (X_j, Y_j)` for some `j`. (If `Y = 1` from the start, then `X = 3` and `j = 0`.) ∎

From the recursion, `Y_{j+1} = 2X_j + 5Y_j > Y_j`, and `Y_{j+1} ≡ Y_j (mod 2)`, so every `Y_j` is odd.
Also `2X_{j+1} = 10X_j + 24Y_j = 5(Y_{j+1} - 5Y_j) + 24Y_j`, which gives `Y_{j+2} = 10Y_{j+1} - Y_j`,
with `Y_0 = 1` and `Y_1 = 11`.

Put `k_j = (Y_j - 1)/2`. Then `k_0 = 0`, `k_1 = 5`, and `k_{j+2} = 10k_{j+1} - k_j + 4`, so `k_j = e_j`. The `k_j`
are strictly increasing and, by the discussion above, they are exactly the hex-triangular indices.
Hence `A087125(n) = e_n` for all `n >= 0`. This proves (a). ∎

(`hex_brute.c` checks this from the definition for all `k <= 2*10^9`. It finds exactly
`0, 5, 54, 539, 5340, 52865, 523314, 5180279, 51279480, 507614525`.)

---

## 2. The shifted sequence `b_n = e_n + 1/2`

Put `b_n = e_n + 1/2 = Y_n / 2`. Then

    b_0 = 1/2,  b_1 = 11/2,  b_2 = 109/2,  b_n = 10 b_{n-1} - b_{n-2}  (n >= 2).        (2.1)

Indeed `e_n + 1/2 = 10(b_{n-1} - 1/2) - (b_{n-2} - 1/2) + 4 + 1/2 = 10b_{n-1} - b_{n-2}`.

**Lemma 2.1 (invariant).** For all `n >= 2`, `b_{n-1}^2 - b_n b_{n-2} = 3`.

*Proof.* Let `Q_n = b_n^2 - b_{n+1} b_{n-1}` for `n >= 1`. Using (2.1),

    Q_{n+1} - Q_n = b_{n+1}^2 - (10b_{n+1} - b_n) b_n - b_n^2 + b_{n+1} b_{n-1}
                  = b_{n+1}(b_{n+1} - 10 b_n + b_{n-1}) = 0,

and `Q_1 = 121/4 - (109/2)(1/2) = 3`. ∎

**Lemma 2.2 (ratios).** Let `rho_n = b_n / b_{n-1}` for `n >= 1`. Then `rho_1 = 11`, and
`9 < rho_n <= 11` for all `n >= 1`. Moreover `rho_n < 10` for `n >= 2`. In particular all `b_n > 0`, the
sequence `(b_n)` is increasing, and `b_n >= 11/2` for `n >= 1`.

*Proof.* `rho_1 = (11/2)/(1/2) = 11`. If `rho_{n-1} > 9`, then `b_{n-1} > 0`, and (2.1) gives
`rho_n = 10 - 1/rho_{n-1}`, which lies in `(10 - 1/9, 10)`, a subset of `(9, 10)`. Induction finishes the proof. ∎

(Also, `rho_n` decreases to `r := 5 + 2 sqrt6 = 9.898979...`. This is the fixed point of `x -> 10 - 1/x`
that exceeds 9, and the map is increasing. This fact is used only in Corollary 6.4.)

---

## 3. Two-sided bounds for harmonic numbers

For an integer `k >= 1` let

    g(k) := log((k + 1/2)/(k - 1/2)) - 1/k .

With `t = 1/(2k)`, which lies in `(0, 1/2]`, we have `(k+1/2)/(k-1/2) = (1+t)/(1-t)` and `1/k = 2t`. The series
`log((1+t)/(1-t)) = 2 sum_{j>=0} t^(2j+1)/(2j+1)` holds for `|t| < 1`, so

    g(k) = 2 sum_{j>=1} t^(2j+1)/(2j+1) = 2 t^3 sum_{j>=0} t^(2j)/(2j+3) > 0.        (3.1)

For integers `0 <= m < M`, telescoping gives

    [H(m) - log(m + 1/2)] - [H(M) - log(M + 1/2)] = sum_{k=m+1}^{M} g(k).            (3.2)

Indeed `H(M) - H(m) = sum_{k=m+1}^{M} 1/k` and `log(M+1/2) - log(m+1/2) = sum_{k=m+1}^{M} log((k+1/2)/(k-1/2))`.

Let `phi(x) = 1/(24 x^2)` and `psi(x) = 1/(24 x^2) - 1/(120 x^4)` for `x > 0`.

**Lemma 3.1.** For every integer `k >= 1`,

    psi(k - 1/2) - psi(k + 1/2)  <  g(k)  <  phi(k - 1/2) - phi(k + 1/2).

*Proof.* Let `t = 1/(2k)`, which lies in `(0, 1/2]`. Then `k ± 1/2 = (1 ± t)/(2t)`, and a direct computation
(machine-checked in `lemmas_check.py`, items (L1) to (L3)) gives

    phi(k-1/2) - phi(k+1/2) = k / (12 (k^2 - 1/4)^2) = (2/3) t^3 / (1 - t^2)^2,
    1/(k-1/2)^4 - 1/(k+1/2)^4 = 16 t^4 [ (1+t)^4 - (1-t)^4 ] / (1-t^2)^4 = 128 t^5 (1 + t^2)/(1 - t^2)^4,
    psi(k-1/2) - psi(k+1/2) = (2/3) t^3/(1-t^2)^2 - (16/15) t^5 (1+t^2)/(1-t^2)^4.

*Upper bound.* `(2/3) t^3/(1-t^2)^2 = 2 t^3 sum_{j>=0} ((j+1)/3) t^(2j)`. Compare coefficients with (3.1).
For `j = 0` they are equal (`1/3 = 1/3`). For `j >= 1`, `(j+1)/3 >= 2/3 > 1/5 >= 1/(2j+3)`. Since `t > 0`,
this gives `g(k) < phi(k-1/2) - phi(k+1/2)`.

*Lower bound.* By (3.1), dropping the terms with `j >= 2`, `g(k) > (2/3) t^3 + (2/5) t^5`. So it suffices to show

    (2/3) t^3 + (2/5) t^5  >=  (2/3) t^3/(1-t^2)^2 - (16/15) t^5 (1+t^2)/(1-t^2)^4 .

Divide by `t^3 > 0`, put `s = t^2` (which lies in `(0, 1/4]`), and multiply by `15(1-s)^4 > 0`. The inequality
becomes `P(s) >= 0`, where

    P(s) = (10 + 6s)(1-s)^4 - 10(1-s)^2 + 16 s (1+s) = 2s + 42 s^2 - 4 s^3 - 14 s^4 + 6 s^5

(the expansion is item (L4) of `lemmas_check.py`). For `0 < s <= 1/4`,
`P(s) >= s (2 + 42s - 4s^2 - 14s^3) > s (2 - 4/16 - 14/64) > 0`. ∎

**Lemma 3.2 (bounds for D).** The limit `C := lim_{M->oo} (H(M) - log(M + 1/2))` exists. (It equals Euler's
constant, but this is not used.) For every integer `m >= 0` put `D(m) := H(m) - log(m + 1/2) - C`. Then

    D(m) = sum_{k > m} g(k),                                                         (3.3)

and, with `beta = m + 1/2`,

    1/(24 beta^2) - 1/(120 beta^4)  <  D(m)  <  1/(24 beta^2).                         (3.4)

Moreover `D(m) > 0`, and `D` is strictly decreasing: `D(m-1) - D(m) = g(m) > 0`.

*Proof.* By Lemma 3.1, `0 < g(k) < phi(k-1/2) - phi(k+1/2)`. The right-hand sides telescope to a finite sum,
because `phi(x) -> 0`. So `sum_k g(k)` converges, and by (3.2), `H(M) - log(M+1/2)` converges as `M -> oo`.
Letting `M -> oo` in (3.2) gives (3.3).

Sum the strict inequalities of Lemma 3.1 over `k = m+1, ..., M` and let `M -> oo`. The telescoping sums equal
`phi(m+1/2) - phi(M+1/2)` and `psi(m+1/2) - psi(M+1/2)`, which tend to `phi(m+1/2)` and `psi(m+1/2)`. The
termwise differences `phi(k-1/2) - phi(k+1/2) - g(k)` and `g(k) - psi(k-1/2) + psi(k+1/2)` are positive, so the
limiting inequalities stay strict, and (3.4) follows. The last two claims follow from (3.3) and `g > 0`. ∎

(`lemmas_check.py` also checks (3.4) numerically, as a sanity check: for every `m <= 20000`, and for
`m = 10^6, 10^9, 10^15, 10^30`. The actual expansion is `D(m) = 1/(24 beta^2) - 7/(960 beta^4) + ...`, and
`7/960 < 1/120`.)

---

## 4. The key two-sided inequality (Part (b))

For `n >= 2` put `T_n := 2H(e_{n-1}) - H(e_{n-2})`.

**Proposition 4.1.** For every `n >= 2`, `H(e_n - 1) < T_n < H(e_n)`.

*Proof for `n = 2`* (the triple `e_0, e_1, e_2 = 0, 5, 54`). Here `T_2 = 2H(5) - H(0) = 137/30`. Exact rational
arithmetic (`exact_small.py`) gives

    H(54) - 137/30 = 479812184179176959849 / 54749786241679275146400  > 0,
    137/30 - H(53) = 1602218238666873295253 / 164249358725037825439200 > 0.

(Hand check of the same case using Lemma 3.2: `H(54) - H(5) = log(109/11) + D(54) - D(5) > log(109/11) - 1/726 = 2.29207...`,
which is greater than `H(5) = 137/60 = 2.28333...`. Also `H(53) - H(5) = log(107/11) + D(53) - D(5) < log(107/11) + 1/(24 * 53.5^2) = 2.27494...`,
which is less than `137/60`.)

*Proof for `n >= 3`.* Write `u = b_{n-2}`, `v = b_{n-1}` and `w = b_n`. Since `n - 2 >= 1`, Lemma 2.2 gives
`u >= 11/2`, `v >= 109/2`, `rho := v/u = rho_{n-1}` with `9 < rho <= 11`, and `w = rho_n v` with `rho_n < 10`.
By Lemma 2.1, `uw = v^2 - 3`. By the definition of `D`, `H(e_j) = C + log(b_j) + D(e_j)` for each `j`. Hence

    H(e_n) - T_n = log(u w / v^2) + D(e_n) + D(e_{n-2}) - 2 D(e_{n-1})
                 = log(1 - 3/v^2) + D(e_n) + D(e_{n-2}) - 2 D(e_{n-1}).               (4.1)

*Right inequality, `T_n < H(e_n)`.* For `0 <= x < 1`, `-log(1-x) = sum_{j>=1} x^j/j <= x/(1-x)`. With
`x = 3/v^2 < 1`, this gives `log(1 - 3/v^2) >= -3/(v^2 - 3)`. By Lemma 3.2,
`D(e_n) > 0`, `D(e_{n-2}) > 1/(24u^2) - 1/(120u^4)` and `D(e_{n-1}) < 1/(24 v^2)`. So by (4.1),

    H(e_n) - T_n > 1/(24u^2) - 1/(120u^4) - 1/(12 v^2) - 3/(v^2 - 3).

Multiply by `24u^2 > 0` and substitute `v = rho u`:

    24u^2 (H(e_n) - T_n) > 1 - 1/(5u^2) - 2/rho^2 - 72/(rho^2 - 3/u^2).

Now `u >= 11/2` and `rho > 9` give `1/(5u^2) <= 4/605`, `2/rho^2 < 2/81`, and
`rho^2 - 3/u^2 > 81 - 12/121 > 0`, so `72/(rho^2 - 3/u^2) < 72/(81 - 12/121) = 8712/9789`. Therefore

    24u^2 (H(e_n) - T_n) > 1 - (4/605 + 2/81 + 8712/9789) = 1 - 147315962/159903315 > 0.0787 > 0.

*Left inequality, `H(e_n - 1) < T_n`.* `H(e_n - 1) = H(e_n) - 1/e_n`, so by (4.1)

    T_n - H(e_n - 1) = 1/e_n - [ log(1 - 3/v^2) + (D(e_n) - D(e_{n-1})) - D(e_{n-1}) + D(e_{n-2}) ].

In the bracket, `log(1 - 3/v^2) < 0`. Also `D(e_n) - D(e_{n-1}) < 0`, because `D` is strictly decreasing and
`e_n > e_{n-1}`, and `-D(e_{n-1}) < 0`. Finally `D(e_{n-2}) < 1/(24u^2)` by (3.4). Hence

    T_n - H(e_n - 1) > 1/e_n - 1/(24 u^2).

Now `e_n < b_n = w = rho_n rho_{n-1} u < 10 * 11 * u = 110 u`, and `110u <= 24 u^2` because `u >= 11/2 > 110/24`.
So `e_n < 24 u^2`, which gives `1/e_n > 1/(24u^2)`, and so `T_n - H(e_n - 1) > 0`. ∎

(All the rational constants above are machine-checked in `lemmas_check.py`, item (C1). The lemmas about `b_n`
are re-checked there in exact arithmetic for `n <= 2000`, item (C2).)

*Remark.* Asymptotically, `H(e_n) - T_n ~ 1/v^2` and `T_n - H(e_n - 1) ~ 1/e_n`. So the root `w*` of
`H(w*) = T_n` (with `H` the real-analytic harmonic function) satisfies `e_n - w* ~ r/b_{n-1}`, where
`r = 5 + 2 sqrt6`. It lies just below `e_n`, at a distance tending to 0. The multiprecision run `verify.gp`
shows exactly this pattern of gaps.

---

## 5. Part (c): induction

Let `c_n` be defined by (0.1), so that `A228016(n) = c_n` for `n >= 1`, with `c_{-1} = 0 = e_0` and
`c_0 = 5 = e_1`.

*Claim.* `c_n = e_{n+1}` for all `n >= -1`.

This holds for `n = -1, 0`. Let `n >= 1` and assume `c_{n-1} = e_n` and `c_{n-2} = e_{n-1}`. Then
`T(c_{n-1}, c_{n-2}) = 2H(e_n) - H(e_{n-1}) = T_{n+1}`, and Proposition 4.1 (for the index `n+1 >= 2`) gives
`H(e_{n+1} - 1) < T_{n+1} < H(e_{n+1})`. `H` is strictly increasing on the integers. So every `k >= e_{n+1}`
satisfies `H(k) > T_{n+1}`, and every `k <= e_{n+1} - 1` satisfies `H(k) < T_{n+1}`. Hence the least `k` with
`H(k) > T_{n+1}` is `e_{n+1}`, i.e. `c_n = e_{n+1}`. ∎

Since both inequalities are strict, the answer is the same if `>` in (0.1) is replaced by `>=`. The same holds
for the Mathematica program in the entry: the real increasing function `w -> H(w)` takes the value `T_{n+1}` at a
point strictly inside `(e_{n+1} - 1, e_{n+1})`, so its `Ceiling` is `e_{n+1}`. Combining with Part (a),

    A228016(n) = c_n = e_{n+1} = A087125(n+1)   for all n >= 1.   ∎

---

## 6. Corollaries (the "conjectured" formulas of A228016)

Write `a(n) = A228016(n) = e_{n+1}`.

**6.1 Recurrence.** For `m >= 3`, subtracting `e_{m-1} = 10e_{m-2} - e_{m-3} + 4` from
`e_m = 10e_{m-1} - e_{m-2} + 4` gives `e_m = 11e_{m-1} - 11e_{m-2} + e_{m-3}`. With `m = n+1`, this is
`a(n) = 11a(n-1) - 11a(n-2) + a(n-3)` for all `n >= 4`, which is the smallest `n` where all three of
`a(n-1), a(n-2), a(n-3)` are defined.

**6.2 Generating function.** Let `A(x) = sum_{n>=1} a(n) x^n`. In `(1 - 11x + 11x^2 - x^3) A(x)`, the coefficient
of `x^n` vanishes for `n >= 4` by 6.1. The coefficients for `n = 1, 2, 3` are `54`, `539 - 594 = -55` and
`5340 - 5929 + 594 = 5`. Hence

    sum_{n>=1} a(n) x^n = x (54 - 55x + 5x^2)/(1 - 11x + 11x^2 - x^3).

Equivalently `sum_{n>=1} a(n) x^(n-1) = (-54 + 55x - 5x^2)/(-1 + 11x - 11x^2 + x^3)`, which is the formula in the
entry. That formula therefore uses the offset-0 convention: its constant term is `a(1)`.

**6.3 Closed form.** The characteristic roots of `b_n = 10b_{n-1} - b_{n-2}` are `r^{±1}`, where
`r = 5 + 2 sqrt6`. Matching `b_0 = 1/2` and `b_1 = 11/2` gives
`b_n = ((2+sqrt6) r^n + (2-sqrt6) r^{-n})/8`. Hence

    a(n) = ((2+sqrt6)(5+2sqrt6)^(n+1) + (2-sqrt6)(5-2sqrt6)^(n+1) - 4)/8.

**6.4 Limits stated in the %C line.** `a(n)/a(n-1) -> r = 5 + 2sqrt6 = 9.8989794855663561963945681494...`
(the entry prints `0.8989794855...`, which drops the leading 9). And by (3.4),

    H(a(n)) - H(a(n-1)) = log(b_{n+1}/b_n) + D(e_{n+1}) - D(e_n) -> log r = 2.29243166956117768780078...,

which agrees with the value in the entry. Contrary to the comment's wording, `a(n)/a(n-1)` is *decreasing*:
`9.981..., 9.907..., 9.8998..., ...`. Indeed
`e_{m}/e_{m-1} = rho_m + (rho_m - 1)/(2b_{m-1} - 1)`, and both terms decrease. The differences
`H(a(n)) - H(a(n-1))` do increase, by construction.

---

## 7. Computations (independent of the proof)

All in `/tmp/claude-0/deep/harmonic-hex/`:

| script | what it does | result |
|---|---|---|
| `compare_bfiles.py` | compares A228016 data (19 terms) and its b-file (n = 1..100), and the A087125 b-file (n = 0..1000), with `e_n` | all equal: `A228016(n) = e_{n+1}` for n <= 100, `A087125(n) = e_n` for n <= 1000 |
| `brute.c` | **rigorous brute force of the definition of A228016**. Scans `k = 1, 2, 3, ...` once. Encloses `2^120 H(k)` in `[L_k, L_k + k]`, where `L_k = sum floor(2^120/j)`, using exact 128-bit integers. Every comparison of `H(k)` with the threshold `2H(c_{n-1}) - H(c_{n-2})` must be certified, or the program aborts. Assumes nothing about the answer. | `a(1..10) = 54, 539, ..., 49741043219` (all k <= 5*10^10 scanned; see `brute_out.txt`) |
| `hex_brute.c` | brute force of the definition of A087125: `24k^2+24k+9` a perfect square, for `k <= 2*10^9` | exactly `0, 5, 54, 539, 5340, 52865, 523314, 5180279, 51279480, 507614525` |
| `exact_small.py` | exact rational check (binary splitting) of Proposition 4.1 for n = 2..6 | true. Only n = 2 is used by the proof. |
| `verify.gp` | PARI/GP at 2600 digits, `H(k) = psi(k+1) + Euler`. Finds the least `k` with `H(k) > T` by local search from a crude guess, for n = 1..1000, and compares with `e_{n+1}` | all 1000 terms agree. Gaps above/below the threshold are about `1/a(n-1)^2` and `1/a(n)`, far above the working precision. |
| `lemmas_check.py` | sympy verification of identities (L1)-(L4) and of the series of `g`; exact checks of the constants (C1) and of the `b_n` facts (C2); numerical sanity checks of (3.4); hand check of n = 2 | all pass |

The proof needs only one direct computation: Proposition 4.1 at `n = 2`, i.e.
`H(53) < 137/30 < H(54)`. It is verified in exact rational arithmetic by `exact_small.py`, and by hand in Section 4.
Every other case `n >= 3` is covered by the analytic argument, which uses only Lemma 2.1, Lemma 2.2 and the
inequalities (3.4), all with explicit constants.

## 8. Notes on the OEIS entry A228016

* %N: the third clause has `>` where `<` is meant (see Section 0).
* %C: "For A227965" should refer to this sequence (A228016). The limit of `a(n)/a(n-1)` is
  `9.8989794855... = 5 + 2sqrt6`, not `0.8989794855...`. The ratios decrease to this limit.
* %F: both formulas marked "(conjectured)" are now theorems (Section 6). The g.f. as printed is
  `sum_{n>=1} a(n) x^(n-1)`; with the entry's offset 1, the standard g.f. is
  `x(54 - 55x + 5x^2)/((1-x)(1-10x+x^2))`.
* Suggested cross-reference: `A228016(n) = A087125(n+1)`.
