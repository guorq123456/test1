# Peak-free words and images of 2- and 3-window min/max filters

Files are in `/tmp/claude-0/deep/morphology/`. Every script named below is in that directory.

## 0. Results at a glance

Let `k >= 0` and let `[0,k] = {0,1,...,k}`. Words are 0-indexed.

* **Theorem 1.** Fix `N >= 1`. Count the words of length `N` over `[0,k]` with no interior strict peak. This equals the number of words of length `N+1` over `[0,k]` in which every nonzero letter is `<=` some existing neighbour. An explicit bijection sends `x` to `delta+(k - x)`, where `delta+` is the 2-window max-filter with 0-padding (full mode). The inverse sends `y` to `k - eps-(y)`, where `eps-` is the valid 2-window min-filter.
  In OEIS terms, for all `n >= 1` and `k >= 1`:
  `A200886(n,k) = (column 1 of Hardin's "n X m 0..k arrays with every nonzero element <= some horizontal or vertical neighbor" table)(n+3)`.
  In particular, for all `n >= 1`:
  `A200880(n)=A202882(n+3)`, `A200881(n)=A203094(n+3)`, `A200882(n)=A203184(n+3)`, `A200883(n)=A203050(n+3)`, `A200884(n)=A203059(n+3)`, `A200885(n)=A202909(n+3)`.
  Within the second family, `A202882(n)` (and the others) counts the peak-free words of length `n-1`, for every `n >= 1`.
* **Corollary 1.** Fix `n >= 1`. The number of distinct images of the valid 2-window min-filter `[0,k]^(n+1) -> [0,k]^n` also equals the Theorem 1 count. This proves the statements `A217883(n,2) = A202882(n+1)` and `A217954(n,2) = A203094(n+1)`, which were recorded in OEIS without proof.
* **Theorem 2.** Fix `N >= 1`. Count the words of length `N` over `[0,k]` with neither an interior strict peak nor an interior strict valley. This equals the number of distinct images of the clipped 3-window min-filter on `[0,k]^(N+1)`. An explicit bijection is `eps+` (the 2-window min-filter, full mode, padded with the top value `k`). Its inverse is `delta-` (the valid 2-window max-filter).
  In OEIS terms, for all `n >= 1` and `k >= 1`: `A200871(n,k) = D(n+3,k)`.
  In particular, for `n >= 1`: `A200865(n) = A217450(n+3)` and `A200866(n) = A218051(n+3)`. The same holds for column 1 of A217457, A217645 and A217547, and for column 2 of A217547 (all for `k = 2`). It also holds for column 1 of A218181, A218651 and A218056, and for column 2 of A218056 (all for `k = 3`).
* **Theorem 3 (all k).** The generating function is
  `sum_{N>=0} A(N,k) x^N = b_k(x^2) / (b_k(x^2) - x B_k(x^2))`,
  with Morgan-Voyce polynomials `b_k(y) = sum_j C(k+j,2j) y^j` and `B_k(y) = sum_j C(k+1+j,2j+1) y^j`. Equivalently, for every `k` the generating function of the `n X 1` family is `sum_{n>=1} a(n) x^n = x b_k(x^2)/(b_k(x^2) - x B_k(x^2))`.
  This proves, for every `k`, all the "Empirical" recurrences and generating functions of A200880–A200885, A202882, A203094, A203184, A203050, A203059, A202909, and of the columns of A200886. The recurrence is `A(N) = sum_{j=1}^{2k+1} (-1)^(j+1) C(k+1+floor((j-1)/2), j) A(N-j)` for `N >= 2k+1`.
* **Section 7 (finite but rigorous).** The following are proved by a Cayley–Hamilton argument with explicit linear representations, plus polynomiality in `k`:
  * every "Empirical" column recurrence and g.f. of A200865–A200870, A217450, A218051 and A200871 (`k <= 7`);
  * every "Empirical" row polynomial and conjectured row g.f. or recurrence of A200886, A200871, A200872–A200877 and A200887–A200892.

  In total, `recurrences.py` checks 102 stored formulas and finds 0 failures.

None of the main identities (Theorems 1 and 2) needs a finite verification: the proofs below hold for all `k >= 0` and `N >= 1`. The computations in Section 8 are independent confirmations.

---

## 1. Definitions and the OEIS dictionary

For a word `w` of length `L`, positions are `0..L-1`. A position `i` is *interior* if `1 <= i <= L-2`.

* An interior `i` is a **strict peak** of `x` if `x_i > x_{i-1}` and `x_i > x_{i+1}`.
* An interior `i` is a **strict valley** of `x` if `x_i < x_{i-1}` and `x_i < x_{i+1}`.

The following sets are defined for fixed `k`. The superscript `(k)` is omitted when it is clear.

* `A_N = { x in [0,k]^N : x has no strict peak }`
* `V_N = { x in [0,k]^N : x has no strict valley }`
* `C_N = A_N ∩ V_N`
* `B_M = { y in [0,k]^M : for every i with y_i != 0 there is j in {i-1,i+1} ∩ [0,M-1] with y_i <= y_j }`
* `D_M = { eps3(w) : w in [0,k]^M }`, where `eps3(w)_i = min{ w_j : j in {i-1,i,i+1} ∩ [0,M-1] }`

Write `A(N,k)=|A_N^(k)|`, and similarly `B(M,k)`, `C(N,k)` and `D(M,k)`.

**Operators.** Let `N >= 1`. For `0 <= i <= N` put `S_i = {i-1,i} ∩ [0,N-1]`. This set is nonempty because `N >= 1`.

| operator | maps | definition | name |
|---|---|---|---|
| `delta+` | `[0,k]^N -> [0,k]^(N+1)` | `(delta+ x)_i = max{x_j : j in S_i}`, `i=0..N` | full dilation (0-padding) |
| `eps+` | `[0,k]^N -> [0,k]^(N+1)` | `(eps+ x)_i = min{x_j : j in S_i}`, `i=0..N` | full erosion (top-padding by `k`) |
| `delta-` | `[0,k]^(N+1) -> [0,k]^N` | `(delta- y)_j = max(y_j, y_{j+1})`, `j=0..N-1` | valid dilation |
| `eps-` | `[0,k]^(N+1) -> [0,k]^N` | `(eps- y)_j = min(y_j, y_{j+1})`, `j=0..N-1` | valid erosion |
| `c` | `[0,k]^L -> [0,k]^L` | `c(x)_i = k - x_i` | complement |

Clipping the index set is the same as padding with 0 for `delta+`, and the same as padding with `k` for `eps+`, because all letters lie in `[0,k]`.

**Complement symmetry.** Since `t -> k-t` reverses order, `k - max = min(k - .)`. This gives (C1)–(C3), which are used throughout:

* (C1) `c ∘ delta+ = eps+ ∘ c` and `c ∘ eps+ = delta+ ∘ c`.
* (C2) `c ∘ delta- = eps- ∘ c` and `c ∘ eps- = delta- ∘ c`.
* (C3) `c` maps `A_N` bijectively onto `V_N`, because `x_i > x_{i±1}` is equivalent to `k-x_i < k-x_{i±1}`. Also `c(C_N) = C_N`.

**OEIS dictionary.** Each identification below follows from the `%N` wording. All were confirmed by brute force from the definitions in `defs.py` and `check_brute.py`: 564 stored terms or table entries, 0 failures.

* **A200886** `T(n,k)`: "0..k arrays x(0..n+1) of n+2 elements without any interior element greater than both neighbors". This is `T(n,k) = A(n+2,k)` for `n,k >= 1`.
  * The table is read by antidiagonals `T(1,1),T(1,2),T(2,1),...`.
  * Columns `k=2..7` are A200880–A200885, each `a(n)=A(n+2,k)`.
  * Rows 2..7 are A200887–A200892, each `a(m) = A(L,m)` with `L = 4..9`.
* **A200871** `T(n,k)` is the same with "...or less than both neighbors". This is `T(n,k) = C(n+2,k)`.
  * Columns `k=2..7` are A200865–A200870.
  * Rows 2..7 are A200872–A200877.
* **Hardin's tables** "n X m 0..K arrays with every nonzero element less than or equal to some horizontal or vertical neighbor": A202889 (K=2), A203101 (3), A203191 (4), A203057 (5), A203066 (6), A202916 (7).
  * In an `n X 1` array an entry has no horizontal neighbour. Its vertical neighbours are the entries `i-1` and `i+1` that exist.
  * So column 1 of these tables counts `B_n^(K)`. These columns are A202882, A203094, A203184, A203050, A203059 and A202909, with `a(n) = B(n,K)`, `n >= 1`.
  * Example: `a(1) = 1`, because a single entry has no neighbour and must be 0.
* **Min-filter tables** "Number of n X m arrays of the minimum value of corresponding elements and their *(nbhd)* neighbors in a random 0..K n X m array". The entry is the number of distinct output arrays (see the "All solutions for n=3" examples in A217450 and A218051).
  * In an `n X 1` array, horizontal, diagonal and antidiagonal neighbours do not exist. So column 1 of every such table with vertical neighbours counts `D_n^(K)`. The relevant tables are:

    | neighbourhood | K=1 | K=2 | K=3 |
    |---|---|---|---|
    | horizontal and vertical | A217637 | A217457 | A218181 |
    | horizontal, vertical or antidiagonal | A218084 | A217645 | A218651 |
    | horizontal, vertical, diagonal or antidiagonal | A217982 | A217547 | A218056 |

  * Separate `n X 1` entries: A217450 (K=2) and A218051 (K=3), each `a(n)=D(n,K)`.
  * For the 3x3 neighbourhood (A217982, A217547, A218056), column 2 equals column 1 for a simple reason. In an `n X 2` array every output entry `(i,j)` is `eps3(m)_i` with `m_i = min(w_{i,1}, w_{i,2})`, and every `m` is attained (take `w_{.,1}=w_{.,2}=m`). So the image set is `{(z,z) : z in D_n}`.
* **A217883** (K=2) and **A217954** (K=3) `T(n,w)`: "n-element 0..K arrays with each element the minimum of w adjacent elements of a random 0..K array of n+w-1 elements". Column `w=2` is the number of distinct images of `eps- : [0,K]^(n+1) -> [0,K]^n`.

## 2. Two lattice identities on a chain

For `a,b,c` in a totally ordered set:

* (L1) `max(a, min(b,c)) = min(max(a,b), max(a,c))` and `min(a, max(b,c)) = max(min(a,b), min(a,c))`.
  *Proof.* Without loss of generality `b <= c`. Then `min(b,c)=b`, and `max(a,b) <= max(a,c)`, so the right side is `max(a,b)`. The second identity is the order-dual. ∎
* (L2) `min(max(a,b), max(b,c)) = max(b, min(a,c))` and `max(min(a,b), min(b,c)) = min(b, max(a,c))`.
  *Proof.* This is (L1) applied with `b` as the distinguished element. ∎

Three consequences are used below.

* `max(b, min(a,c)) = b` if and only if `b >= min(a,c)`, that is, if and only if `b` is not a strict valley between `a` and `c`.
* `min(b, max(a,c)) = b` if and only if `b <= max(a,c)`, that is, if and only if `b` is not a strict peak between `a` and `c`.
* If `b` is a strict peak between `a` and `c`, then `min(b, max(a,c)) = max(a,c)`.

## 3. Images of the 2-window operators

**Lemma 1.** Let `N >= 1`.

* (a) For every `u in [0,k]^N` and `0 <= j <= N-1`:
  * `(eps- delta+ u)_j = max(u_j, min(u_{j-1},u_{j+1}))` if `j` is interior;
  * `(eps- delta+ u)_j = u_j` if `j in {0, N-1}`.

  Consequently `eps- delta+ u = u` if and only if `u in V_N`.
* (b) `eps-([0,k]^(N+1)) = V_N`.
* (c) For every `x in [0,k]^N`, `delta- eps+ x` is obtained from `x` by replacing each strict peak `x_j` with `max(x_{j-1},x_{j+1})`. Consequently `delta- eps+ x = x` if and only if `x in A_N`, and `delta- eps+ x <= x` pointwise.
* (d) `delta-([0,k]^(N+1)) = A_N`.

*Proof.*

(a) We have `(delta+ u)_j = max{u_t : t in S_j}` and `(delta+ u)_{j+1} = max{u_t : t in S_{j+1}}`.
* Interior `j` (`1 <= j <= N-2`): here `S_j = {j-1,j}` and `S_{j+1} = {j,j+1}`. So `(eps- delta+ u)_j = min(max(u_{j-1},u_j), max(u_j,u_{j+1})) = max(u_j, min(u_{j-1},u_{j+1}))` by (L2).
* `j = 0` with `N >= 2`: `S_0={0}` and `S_1={0,1}`, so the value is `min(u_0, max(u_0,u_1)) = u_0`.
* `j = N-1 >= 1`: `S_{N-1} = {N-2,N-1}` and `S_N = {N-1}`, so the value is `min(max(u_{N-2},u_{N-1}), u_{N-1}) = u_{N-1}`.
* `N = 1`: `S_0 = S_1 = {0}`, so the value is `u_0`.

The "consequently" part follows from the first consequence after (L2).

(b) "⊇": by (a), every `u in V_N` satisfies `u = eps-(delta+ u)`.
"⊆": let `u = eps- w` and let `j` be interior. Then `u_{j-1} = min(w_{j-1},w_j) <= w_j` and `u_{j+1} = min(w_{j+1},w_{j+2}) <= w_{j+1}`. Hence `min(u_{j-1},u_{j+1}) <= min(w_j,w_{j+1}) = u_j`, so `j` is not a strict valley of `u`.

(c) By (C1) and (C2), `delta- eps+ x = c(eps- delta+ c(x))`. Apply (a) to `u = c(x)` and take complements. Interior entries become `k - max(k-x_j, min(k-x_{j-1}, k-x_{j+1})) = min(x_j, max(x_{j-1},x_{j+1}))`, and boundary entries become `x_j`. By the consequences after (L2), `min(x_j, max(x_{j-1},x_{j+1}))` equals `x_j` unless `j` is a strict peak of `x`, in which case it equals `max(x_{j-1},x_{j+1}) < x_j`.

(d) `delta-([0,k]^(N+1)) = delta-(c([0,k]^(N+1))) = c(eps-([0,k]^(N+1))) = c(V_N) = A_N`, by (C2), (b) and (C3). ∎

**Lemma 2.** Let `N >= 1`.

* (a) `delta+([0,k]^N) ⊆ B_{N+1}`.
* (b) For every `y in [0,k]^(N+1)` and `0 <= i <= N`:
  * `(delta+ eps- y)_i = min(y_i, max(y_{i-1},y_{i+1}))` for `1 <= i <= N-1`;
  * `(delta+ eps- y)_0 = min(y_0,y_1)`;
  * `(delta+ eps- y)_N = min(y_{N-1},y_N)`.

  Consequently `delta+ eps- y = y` for every `y in B_{N+1}`, and `delta+([0,k]^N) = B_{N+1}`.

*Proof.*

(a) Let `y = delta+ x` and fix `i`. Choose `j in S_i` with `x_j = y_i`.
* If `j = i-1`, then `i-1` is a position of `y` and `i-1 in S_{i-1}`, so `y_{i-1} >= x_{i-1} = y_i`.
* If `j = i`, then `i <= N-1`, so `i+1 <= N` is a position of `y` and `i in S_{i+1}`, so `y_{i+1} >= x_i = y_i`.

Either way `y_i` is `<=` an existing neighbour. This holds for every `i`, in particular for the nonzero ones.

(b) `(eps- y)_j = min(y_j,y_{j+1})` for `j = 0..N-1`.
* For `1 <= i <= N-1`: `(delta+ eps- y)_i = max(min(y_{i-1},y_i), min(y_i,y_{i+1}))`, which equals `min(y_i, max(y_{i-1},y_{i+1}))` by (L2).
* For `i = 0`: `S_0 = {0}`, giving `min(y_0,y_1)`.
* For `i = N`: `S_N = {N-1}`, giving `min(y_{N-1},y_N)`.

Now let `y in B_{N+1}`.
* If `y_i = 0`, every one of these expressions equals `0 = y_i`.
* If `y_i != 0` and `1 <= i <= N-1`, then `y_i <= y_{i-1}` or `y_i <= y_{i+1}`, so `y_i <= max(y_{i-1},y_{i+1})` and the value is `y_i`.
* If `y_0 != 0`, its only neighbour is `y_1`, so `y_0 <= y_1` and `min(y_0,y_1) = y_0`. The case `i = N` is symmetric.

Hence `y = delta+(eps- y)` lies in the image of `delta+`. Together with (a) this gives the equality. ∎

## 4. Theorem 1

**Theorem 1.** Let `k >= 0` and `N >= 1`. Define `Phi(x) = delta+(c(x))` on `A_N` and `Psi(y) = c(eps-(y))` on `B_{N+1}`. Then `Phi` maps `A_N` bijectively onto `B_{N+1}`, and `Psi` is its inverse. Hence `A(N,k) = B(N+1,k)`.

The identity `A(N,k) = B(N+1,k)` also holds for `N = 0`: `A_0` contains only the empty word, and `B_1 = {0}`.

*Proof.*

* `Phi(A_N) ⊆ B_{N+1}`: by Lemma 2(a).
* `Psi(B_{N+1}) ⊆ A_N`: `eps- y` lies in `V_N` by Lemma 1(b), and `c(V_N) = A_N` by (C3).
* `Psi(Phi(x)) = x` for `x in A_N`: we have `c(x) in V_N`, so `c(eps- delta+ c(x)) = c(c(x)) = x` by Lemma 1(a).
* `Phi(Psi(y)) = y` for `y in B_{N+1}`: `Phi(Psi(y)) = delta+(c(c(eps- y))) = delta+ eps- y = y` by Lemma 2(b). ∎

**Corollary 1.** For `n >= 1`, the number of distinct images of `eps- : [0,k]^(n+1) -> [0,k]^n` is `|V_n| = |A_n| = B(n+1,k)`, by Lemma 1(b), (C3) and Theorem 1.

**OEIS consequences.**

* `A200886(n,k) = A(n+2,k) = B(n+3,k)` for all `n,k >= 1`. This covers the whole table, so all its rows and columns.
* For `n >= 1`: `A200880(n)=A202882(n+3)`, `A200881(n)=A203094(n+3)`, `A200882(n)=A203184(n+3)`, `A200883(n)=A203050(n+3)`, `A200884(n)=A203059(n+3)`, `A200885(n)=A202909(n+3)`. Equivalently, `A202882(n) = A(n-1,2)` for all `n >= 1`, and so on.
* Rows `r = 2..7` of A200886 are A200887, A200888, A200889, A200890, A200891, A200892. Each row sequence `a(m) = A(r+2, m)` equals the number of `(r+3) X 1` arrays over `0..m` with every nonzero element `<=` some neighbour.
* For `n >= 1`: `A217883(n,2) = A202882(n+1)` and `A217954(n,2) = A203094(n+1)`. These were already recorded in OEIS as plain cross-references. For `n >= 3` they are also `A200880(n-2)` and `A200881(n-2)`.
* For `k=1`, `A(N,1)` is the number of binary words avoiding the factor `010`, which is `A005251(N+3)` (D. Callan's comment there). Hence `B(M,1) = A005251(M+2)`, and `A200886(n,1) = A005251(n+5)`, as stated in A200886.

## 5. Theorem 2

**Lemma 3 (factorisation).** For `N >= 1` and `w in [0,k]^(N+1)`: `eps3(w) = eps+(eps-(w))`.

*Proof.* Let `u = eps- w`, so `u_j = min(w_j,w_{j+1})` for `j=0..N-1`. Then `(eps+ u)_i = min{w_l : l in U_i}` with `U_i = ∪_{j in S_i} {j,j+1}`. We check that `U_i = {i-1,i,i+1} ∩ [0,N]`:

* `i = 0`: `S_0 = {0}` and `U_0 = {0,1}`.
* `i = N`: `S_N = {N-1}` and `U_N = {N-1,N}`.
* `1 <= i <= N-1`: `S_i = {i-1,i}` and `U_i = {i-1,i,i+1}`.

This also covers `N = 1`, where both windows of a length-2 word are the whole word. ∎

By Lemma 3 and Lemma 1(b): **`D_{N+1} = eps+(V_N)`** for `N >= 1`.

**Lemma 4.** Let `N >= 1`.

* (a) For every `z in eps+([0,k]^N)`: `eps+(delta-(z)) = z`.
* (b) For every `u in V_N`, the word `g = delta-(eps+(u))` lies in `C_N` and satisfies `eps+(g) = eps+(u)`.

*Proof.*

(a) Write `z = eps+(u)`. By (C1) and (C2), `eps+ delta- z = c(delta+ eps- c(z))` and `c(z) = delta+(c(u))`. Now `c(z)` lies in `B_{N+1}` by Lemma 2(a), so `delta+ eps- c(z) = c(z)` by Lemma 2(b). Hence `eps+ delta- z = z`.

(b) First, `g` lies in the image of `delta-`, which is `A_N` by Lemma 1(d). Also `eps+(g) = eps+(u)` by (a) applied to `z = eps+(u)`.

It remains to show `g in V_N`. By Lemma 1(c) applied to `x = u`, `g_j = u_j` unless `j` is a strict peak of `u`, in which case `g_j = max(u_{j-1},u_{j+1})`. In all cases `g <= u` pointwise.

Suppose `j` is a strict valley of `g`, so `g_j < g_{j-1}` and `g_j < g_{j+1}`.
* If `j` is not a strict peak of `u`, then `g_j = u_j`. Also `u_{j-1} >= g_{j-1} > u_j` and `u_{j+1} >= g_{j+1} > u_j`. So `j` is a strict valley of `u`, which contradicts `u in V_N`.
* If `j` is a strict peak of `u`, then `g_j = max(u_{j-1},u_{j+1}) >= u_{j-1} >= g_{j-1} > g_j`, which is a contradiction.

Hence `g in A_N ∩ V_N = C_N`. ∎

**Theorem 2.** Let `k >= 0` and `N >= 1`. Define `Theta(x) = eps+(x)` on `C_N`. Then `Theta` maps `C_N` bijectively onto `D_{N+1}`, and its inverse is `z -> delta-(z)`. Hence `C(N,k) = D(N+1,k)`.

The theorem fails for `N = 0`: `C(0,k) = 1` while `D(1,k) = k+1`. This is why the OEIS offsets match only from the right index on.

*Proof.*

* **Into:** if `x in C_N ⊆ V_N`, then `x = eps- w` for some `w` by Lemma 1(b). So `Theta(x) = eps+ eps- w = eps3(w) in D_{N+1}` by Lemma 3.
* **Injective, with left inverse `delta-`:** if `x in C_N ⊆ A_N`, then `delta-(Theta(x)) = delta- eps+ x = x` by Lemma 1(c).
* **Onto:** let `z in D_{N+1}`. Then `z = eps3(w) = eps+(u)` with `u = eps- w in V_N`, by Lemma 3 and Lemma 1(b). By Lemma 4(b), `g := delta-(z)` lies in `C_N` and `Theta(g) = eps+(g) = eps+(u) = z`. Hence the inverse map is `z -> delta-(z)`. ∎

**OEIS consequences.**

* `A200871(n,k) = C(n+2,k) = D(n+3,k)` for all `n,k >= 1`. This covers the whole table, so all its rows and columns.
* For `n >= 1`: `A200865(n) = A217450(n+3)` and `A200866(n) = A218051(n+3)`.
* For `n >= 2`: `A217450(n) = C(n-1,2)` and `A218051(n) = C(n-1,3)`.
* Column 1 of A217457, A217645 and A217547, and column 2 of A217547, equal A217450 (`K=2`). Column 1 of A218181, A218651 and A218056, and column 2 of A218056, equal A218051 (`K=3`).
* For `K=1`, column 1 of A217637, A218084 and A217982 is `D(n,1) = C(n-1,1) = A200871(n-3,1)` for `n >= 4`. This is consistent with the existing cross-references "Column 1 is A006355(n+4)" (A200871) and "Column 1 is A006355(n+1)" (A217637, A218084, A217982).
* Each row `a(m) = C(L,m)` (A200872–A200877, `L=4..9`) equals the number of distinct clipped 3-window min-filter images of length `L+1` over `0..m`.

## 6. Theorem 3: the generating function for every alphabet

Define

* `B_n(y) = sum_{j=0}^{n} C(n+1+j, 2j+1) y^j` and `b_n(y) = sum_{j=0}^{n} C(n+j, 2j) y^j` for `n >= 0`;
* `B_{-1} = 0`.

These are the Morgan–Voyce polynomials. Pascal's rule gives two identities.

* (MV1) `B_{n+1} - B_n = b_{n+1}`. Coefficient of `y^j`: `C(n+2+j,2j+1) - C(n+1+j,2j+1) = C(n+1+j,2j)`.
* (MV2) `b_{n+1} = b_n + y B_n`. Coefficient of `y^j`: `C(n+1+j,2j) = C(n+j,2j) + C(n+j,2j-1)`, and `[y^j] y B_n = C(n+j, 2j-1)`.

Note `b_n(0) = 1`.

**Theorem 3.** For every `k >= 0`, as formal power series,

```
G_k(x) := sum_{N>=0} A(N,k) x^N = b_k(x^2) / (b_k(x^2) - x B_k(x^2)),
F_k(x) := sum_{M>=0} B(M,k) x^M = 1 + x G_k(x).
```

*Proof.*

Let `𝓑_k` be the set of words over `[0,k]` of any length (the empty word included) satisfying the condition defining `B_M`. Let `𝓔_k` be the set of words over `[0,k]` in which *every* letter is `<=` some existing neighbour. Let `F_k` and `E_k` be their length generating functions. For `k = -1` (empty alphabet), `𝓔_{-1}` contains only the empty word and `E_{-1} = 1`.

*Step 1: `F_k = E_{k-1} / (1 - x E_{k-1})` for `k >= 0`.*
Every word `y` over `[0,k]` factors uniquely as `y = W_0 0 W_1 0 ... 0 W_r`, where `r` is the number of zeros and the `W_i` are words over `[1,k]`. Zeros impose no condition in `𝓑_k`. A letter of `W_i` is nonzero. Its neighbours in `y` are letters of `W_i`, or zeros (which are smaller than it), or do not exist. So `y in 𝓑_k` if and only if, for each `i`, every letter of `W_i` is `<=` a neighbour inside `W_i`. Subtracting 1 from every letter, this says `W_i - 1 in 𝓔_{k-1}`. Hence `𝓑_k` is in bijection with `∪_{r>=0} (𝓔_{k-1})^(r+1)`, with length `sum|W_i| + r`, and `F_k = sum_r x^r E_{k-1}^(r+1)`. For `k = 0` every `W_i` is empty, which is consistent with `E_{-1} = 1`.

*Step 2: `E_k = F_k - x` for `k >= 0`.*
Use the same factorisation for words in `𝓔_k`. Nonzero letters are constrained exactly as in `𝓑_k`. A zero is `<=` any letter, so it satisfies the condition if and only if it has a neighbour, that is, if and only if the word has length `>= 2`. The only word of `𝓑_k` that contains a zero and has length 1 is the word "0". Hence `𝓔_k = 𝓑_k \ {"0"}`.

*Step 3: a recurrence for `G_k`.*
Steps 1 and 2 give `F_{k+1} = (F_k - x)/(1 - x F_k + x^2)`. The denominator has constant term 1, so this is valid in `Z[[x]]`. By Theorem 1 (and `A(0)=B(1)=1`), `F_k = 1 + x G_k`. Substituting:

```
G_{k+1} = ((1+x) G_k - x) / ((1 - x + x^2) - x^2 G_k),    G_0 = 1/(1-x).
```

To check `G_0`: `F_0 = 1/(1-x)` because all words over `{0}` lie in `𝓑_0`.

*Step 4: the closed form satisfies the same recurrence.*
Let `R_k = b_k/(b_k - x B_k)` with `y = x^2`. The denominator has constant term 1, and `R_0 = 1/(1-x)` because `b_0 = B_0 = 1`. Write `R_k = p/q` with `p = b_k` and `q = b_k - x B_k`. Then

* numerator: `(1+x)p - x q = b_k + y B_k = b_{k+1}`, by (MV2);
* denominator: `(1-x+y) q - y p = (b_k + y B_k) - x(b_k + B_k + y B_k) = b_{k+1} - x B_{k+1}`, by (MV2) and (MV1).

So `R_{k+1} = ((1+x)R_k - x)/((1-x+x^2) - x^2 R_k)`. The map on the right is well defined on power series with constant term 1. By induction `G_k = R_k` for all `k`. ∎

**Remark.** Step 3 is exactly Mansour–Shattuck's recurrence at `q = 0` (J. Integer Seq. 13 (2010) 10.6.8, Lemma 2.1). There `W_{k+1}(x,0) = G_k` counts words over a `(k+1)`-letter alphabet with no peak `π_j < π_{j+1} > π_{j+2}`. Their lemma together with Steps 1–2 gives a second, algebraic proof of Theorem 1. The proof above does not depend on their result.

**Corollary 3 (recurrences for all k).** Put `Q_k(x) = b_k(x^2) - x B_k(x^2) = sum_{j=0}^{2k+1} (-1)^j C(k+1+floor((j-1)/2), j) x^j`. This polynomial has degree `2k+1`, with `Q_k(0)=1` and leading coefficient `-1`. Since `Q_k G_k = b_k(x^2)` has degree `2k`, for every `N >= 2k+1`:

```
A(N,k) = sum_{j=1}^{2k+1} (-1)^(j+1) C(k+1+floor((j-1)/2), j) A(N-j,k).
```

For `k=1..7` this is the "Empirical" recurrence of A200886 column `k`, and also of A200880–A200885 and A202882, A203094, A203184, A203050, A203059, A202909 (`gf_theorem3_check.py` part (4) compares the coefficients).

For the OEIS indexing:
* `a(n) = A(n+2,k)` satisfies the recurrence for `n >= 2k-1`.
* `a(n) = B(n,k) = A(n-1,k)` satisfies it for `n >= 2k+2`.

In both cases this includes every `n` for which the recurrence refers only to terms `a(m)` with `m >= 1`. The generating functions are

```
sum_{n>=1} B(n,k) x^n = x b_k(x^2) / Q_k(x),
sum_{n>=1} A(n+2,k) x^n = (G_k(x) - 1 - (k+1)x - (k+1)^2 x^2) / x^2.
```

For `k=2,3,4` the first is exactly R. J. Mathar's g.f. in A202882, A203094 and A203184. For example, for `k=4`: `b_4(y) = (1+y)(1+9y+6y^2+y^3)`.

## 7. Remaining stored formulas: finite but rigorous verification

**Lemma CH.** Let `L` be an `m x m` matrix and let `a(n) = u^T L^(n-n0) v` for `n >= n0`. Suppose the relation `a(n) = sum_{i=1}^{d} c_i a(n-i)` holds for `n0+d <= n <= n0+d+m-1`. Then it holds for all `n >= n0+d`.

*Proof.* For `n >= n0+d`, `t(n) := a(n) - sum c_i a(n-i) = u^T L^(n-n0-d) w`, where `w = (L^d - sum c_i L^(d-i)) v`. By Cayley–Hamilton, `s(j) = u^T L^j w` satisfies a linear recurrence of order `m` whose characteristic polynomial (that of `L`) is monic. So `s(0) = ... = s(m-1) = 0` forces `s ≡ 0`. ∎

**Linear representations.**

* `A_N`: classify a word of length `N >= 1` by the state `(x_{N-1}, rise)`, where `rise = [N >= 2 and x_{N-1} > x_{N-2}]`. Appending a letter `w` creates exactly one new interior position, `N-1`. That position is a strict peak if and only if `rise` holds and `w < x_{N-1}`. The new state depends only on `(x_{N-1}, w)`. So `A(N) = 1^T L_A^(N-1) f_1` with `m = 2(k+1)`.
* `C_N`: use the state `(x_{N-1}, s)` with `s in {up, down, flat}`. The forbidden transitions are `up` followed by `w < x_{N-1}` and `down` followed by `w > x_{N-1}`. So `C(N) = 1^T L_C^(N-1) f_1` with `m = 3(k+1)`.

These are exactly the DPs `A_all`, `A_all_fast` and `C_all_fast` in `dp.py`.

**Columns of the Theorem 2 family (k <= 7).**

* For `a(n) = C(n+2,k)` (A200865–A200870 and the columns of A200871), the representation holds from `n0 = 1` with `m = 3(k+1) <= 24`.
* By Theorem 2, `a(n) = D(n,k) = C(n-1,k)` for `n >= 2` (A217450, A218051). So the same `L_C` gives a representation from `n0 = 2`. Any instance of a recurrence that involves `a(1)` is checked directly.
* The orders are `d <= 11`. So Lemma CH needs the recurrence only for `n <= 2+11+24-1 = 36`.
* `recurrences.py` checks every stored recurrence for all `n <= 400`.
* A stored g.f. `P/Q` with `Q(0) != 0` is proved by two checks: the coefficients of `P/Q` agree with `a(n)` for `n <= 400`, and the recurrence encoded by `Q` holds (Lemma CH).
* `recurrences.py` also re-proves the A- and B-side formulas this way, with `m = 2(k+1)`. For B it uses its own DP (`B_all_fast`, state `(last letter, satisfied?)`). This is redundant with Theorem 3 but independent of it.

**Lemma P (rows).** Fix `N >= 1`. Membership of `x in [0,k]^N` in `A_N` or `C_N` depends only on comparisons between letters, that is, on the standardisation `st(x)`. Let `r` be the number of distinct letters of `x`. The map `x -> (st(x), set of letters)` is a bijection onto pairs (surjective word `[0,N-1] -> [0,r-1]`, `r`-subset of `[0,k]`). Hence

```
A(N,k) = sum_{r=1}^{N} p_r C(k+1, r),
```

with `p_r` independent of `k`, and similarly for `C`. This is a polynomial in `k` of degree `<= N`, valid for all integers `k >= 0`; both sides vanish when `r > k+1`.

So a claimed polynomial of degree `<= N` is proved by agreement at `N+1` values of `k`. `recurrences.py` checks `k = 0..N+5`.

Consequences for the row sequences:
* Every recurrence `(1-E^{-1})^(N+1) a = 0` holds for a polynomial of degree `<= N`.
* A g.f. `P/(1-x)^(N+1)` with `deg P <= N+1` has coefficients that are polynomials of degree `<= N` in `n` for all `n >= 1`. So agreement at `n = 1..59` proves it.

This covers:
* rows `n=1..7` of A200886 and A200871 ("Empirical for rows");
* A200887–A200892 and A200872–A200877: the Empirical polynomials, and Colin Barker's conjectured g.f.s and recurrences;
* "Row 1 is A002412(n+1)" (A200886) and "Row 1 is A084990(n+1)" (A200871), which are the `n=1` polynomials.

Result (`recurrences.log`): **102 stored formulas proved, 0 failed.**

## 8. Computations

| script | what it does | range | result |
|---|---|---|---|
| `defs.py`, `check_brute.py` | brute force straight from the `%N` wording (including the 2D definitions) vs stored `%S` terms | search space `<= 3*10^5` per term; 564 terms or table entries of A200865–A200892, A202882, A203094, A203184, A203050, A203059, A202909, A202889/A203101/A203191/A203057/A203066/A202916 (2D entries), A217450, A218051, column 1 (and 2) of the 9 min-filter tables, column 2 of A217883 and A217954 | 0 failures |
| `dp.py`, `extend.py` | exact DPs for A, B and C; D and V via subset construction of the image automaton, which uses no characterisation proved here; compared with all OEIS b-files | 34 b-files: A200865–A200870, A200880–A200885, A202882, A203094, A203184, A203050, A203059, A202909, A217450, A218051 (n <= 210), A200872–A200877, A200887–A200892 (n <= 210), A200886 and A200871 (9999 entries each) | 0 mismatches |
| `extend.py` | identities `A(N)=B(N+1)` (Theorem 1), `A(N)=V(N)` (Corollary 1), `C(N)=D(N+1)` (Theorem 2) | `k <= 7`: `N <= 402`; `8 <= k <= 20`: `N <= 80`; whole A200886 b-file vs B; A200871 b-file entries with `k <= 30` (3783) vs D; rows `n <= 210` (B) and `n <= 40` (D) | all true (53,322 comparisons, 0 failures) |
| `bijection_check.py` | explicit maps `Phi`, `Psi`, `Theta`, `delta-` and all set equalities of Lemmas 1–4, by exhaustive enumeration | all `(k,N)` with `(k+1)^(N+1) <= 3*10^5`, `0 <= k <= 7` (86 cases, e.g. `k=2`: `N<=10`; `k=3`: `N<=8`) | all assertions pass |
| `recurrences.py` | Section 7 | — | 102/102 |
| `gf_theorem3_check.py` | Theorem 3: the block recursion vs B from its definition (`k<=25`, `M<100`); (MV1) and (MV2) for `n<=60`; the closed form vs A (`k<=40`, `N<120`); recurrence coefficients vs A200886 | — | all true |

Extended terms (for example `A(400,k)`, `B(401,k)`, `C(400,k)`, `D(401,k)` for `k<=7`, and the first 61 terms of every family) are in `extended_terms.txt`.

## 9. OEIS pairs resolved, and cross-reference status (snapshot Oct 1 2026, `xref_audit.py`)

| identity (proved here) | cross-referenced in OEIS? |
|---|---|
| A200880(n)=A202882(n+3) | no, in either direction |
| A200881(n)=A203094(n+3) | no (this pair was missing from the triage list) |
| A200882(n)=A203184(n+3) | no |
| A200883(n)=A203050(n+3) | no |
| A200884(n)=A203059(n+3) | no |
| A200885(n)=A202909(n+3) | no |
| A200886(n,k) = column 1 of the `0..k` table (A202889, A203101, A203191, A203057, A203066, A202916 for k=2..7) at n+3 | no |
| A217883(n,2)=A202882(n+1); A217954(n,2)=A203094(n+1) | yes, A217883→A202882 and A217954↔A203094, stated without proof; now proved |
| A217883(n,2)=A200880(n-2), A217954(n,2)=A200881(n-2) (n>=3) | no |
| A200865(n)=A217450(n+3) | no |
| A200866(n)=A218051(n+3) | no |
| A200871 column 2 = column 1 of A217457/A217645/A217547 (and column 2 of A217547) at n+3 | no |
| A200871 column 3 = column 1 of A218181/A218651/A218056 (and column 2 of A218056) at n+3 | no |
| A200871 column 1 = A006355(n+4); column 1 of A217637/A218084/A217982 = A006355(n+1) | yes (via A006355); consistent with Theorem 2 |
| A200886 column 1 = A005251(n+5) | yes |

There are no OEIS partners for the `n X 1` min-filter counts with `K >= 4`. For `n >= 4` and `K = 4,5,6,7` these are `D(n,K) = A200867(n-3)`, `A200868(n-3)`, `A200869(n-3)`, `A200870(n-3)` respectively, by Theorem 2. A search of the snapshot (`col_search.py`, `col_search2.py`) found no other match for any member of these families.

**Errata noticed.**

* (i) A202882's link annotation reads "Mansour–Shattuck, Lemma 2.1, k=3, one peak". By Theorem 1 the correct statement is "no peak", with a shift: `A202882(n) = [x^(n-1)] W_3(x,0)`. Words over a 3-letter alphabet with exactly one peak number 0, 0, 0, 5, 30, 109, ..., which is not A202882. The A203094 annotation ("k=4, no peak") is correct up to the same shift.
* (ii) A203094 says "Also a column of A228461". A228461 is the 3-window **max** table. Its column `k=3` is A217949 = 4, 16, 50, 130, ..., while A203094 has 144 at that position. No row or column of A228461 equals A203094. The intended reference is presumably A217954 (window 2), column 2, which is proved here.

**Full tables.**

* The identities hold for the *entire* tables A200886 (Theorem 1, all `n,k >= 1`) and A200871 (Theorem 2, all `n,k >= 1`), including the row sequences.
* In Hardin's 2D tables (A202889 etc.) only column 1 (`n X 1`) is involved. Columns `m >= 2` are genuinely two-dimensional. There is no analogous statement and no OEIS match.
* In the 2D min-filter tables only column 1, and column 2 of the 3x3-neighbourhood tables (by the trivial reduction in Section 1), are covered.
* The "minimum or maximum" filter entries (A217995, A217999, A220106) are not covered by these theorems.
