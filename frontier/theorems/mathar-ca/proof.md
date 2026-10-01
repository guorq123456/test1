# Refutation of R. J. Mathar's conjectures A282297 = A279721 and A282295 = A279720 (n >= 2)

**Verdict: both conjectures are FALSE.** The smallest counterexample is n = 26, and the two
readouts also differ for every n with 26 <= n <= 1000. The discrepancy already appears in the
b-files stored in the OEIS entries themselves (Robert Price's own Mathematica output). The
%S/%T/%U data lines stop at n = 22 (A282297) and n = 23 (A282295), which is presumably why the
coincidence looked like it held.

All files are in `/tmp/claude-0/deep/mathar-ca/`. `run_all.sh` reproduces every computational
claim below in about 20 seconds.

---

## 1. Statement

**Theorem.**

(a) A282297(26) = 111100000000000111111111111 and A279721(26) = 111000000000000111111111111.
These are different.

(b) A282295(26) = 111111111111000000000001111 and A279720(26) = 111111111111000000000000111.
These are different.

(c) For 2 <= n <= 25: A282297(n) = A279721(n) and A282295(n) = A279720(n). For n = 1 and for
every n with 26 <= n <= 1000, both pairs differ. So n = 26 is the first counterexample to each
conjecture "a(n) = ... for n >= 2".

(d) The two conjectures are equivalent to each other for each fixed n (Lemma 3). This explains
why they fail at exactly the same values of n.

Parts (a), (b) and the minimality in (c) for n <= 126 can be read directly from the OEIS b-files:
line 26 of `b282297.txt` and line 26 of `b279721.txt` differ, and so do line 26 of `b282295.txt`
and line 26 of `b279720.txt`. Section 5 also gives a short hand-checkable certificate for (a)
and (b).

---

## 2. Exact definitions (decoded from the Mathematica programs in the entries)

All four entries use the same program. Only `code` (193 or 451) and the final `Range` change.

* `CAStep[rule_, a_] := Map[rule[[10 - #]] &, ListConvolve[{{0,2,0},{2,1,2},{0,2,0}}, a, 2], {2}]`.
  `ListConvolve[ker, a, 2]` is the cyclic convolution with the kernel's centre element (2,2)
  aligned to each cell. The kernel is invariant under 180-degree rotation, so convolution equals
  correlation. At cell z the value is
  `v(z) = c + 2 s`, where `c` = state of z and `s` = number of ON cells among the 4 von Neumann
  neighbours of z. So v is in {0, ..., 9}.
* `rule = IntegerDigits[code, 2, 10]` is (d_9, d_8, ..., d_0), the 10 binary digits of `code`
  with the most significant digit first. So `rule[[10 - v]]` = d_v = bit v of `code`.
  **Local rule:** new state = T_code(c, s) := bit_{c+2s}(code).
* 193 = 2^7 + 2^6 + 2^0, so its set bits are {0, 6, 7}.
  451 = 2^8 + 2^7 + 2^6 + 2^1 + 2^0, so its set bits are {0, 1, 6, 7, 8}.
  Since v = 0, 1, 6, 7, 8 correspond to (c,s) = (0,0), (1,0), (0,3), (1,3), (0,4):
  * T_193(c,s) = 1  iff  (c = 0 and s = 0) or s = 3;
  * T_451(c,s) = 1  iff  s = 0 or s = 3 or (c = 0 and s = 4).
  The two rules therefore differ only on the inputs **(c,s) = (1,0)** (an isolated ON cell) and
  **(c,s) = (0,4)** (an OFF cell whose 4 neighbours are all ON). On both inputs rule 451 gives 1
  and rule 193 gives 0.
* Grid: a torus Z_g x Z_g with g = 2*128 + 1 = 257. Stage 0 has a single ON cell at the centre
  (the origin). `ca` collects stages 0, 1, ..., 129. Then the list is trimmed: entry n (1-based)
  is stage n-1, restricted to the (2n-1) x (2n-1) window centred at the origin.
* Readouts. The output index is i = 1..127, which is stage n = i - 1 for n = 0..126.
  `Part[ca[[i]][[i]], Range[i, 2i-1]]` is the middle row of the window, columns 0..n relative to
  the origin. That gives A282297 (code 451) and A279721 (code 193): the digits of cells
  (0,0), (1,0), ..., (n,0), read as a decimal number (`FromDigits[..., 10]`).
  `Range[1, i]` gives columns -n..0. That gives A282295 (code 451) and A279720 (code 193).

Notation: R_code(n) is the 0/1 string s_0 s_1 ... s_n of length n + 1, where s_x is the state of
(x,0) at stage n. L_code(n) is the string for cells (-n,0), ..., (0,0). The OEIS term is the
integer whose decimal digits are this string, so leading zeros are dropped.

---

## 3. Lemmas

**Lemma 1 (the plane evolution is well defined; background).** Consider the evolution on the
infinite plane Z^2 from a single ON cell. At stage t the configuration equals a constant
background b_t everywhere except on a finite set contained in the diamond {|x|+|y| <= t}.
For both rules, b_t = t mod 2.

*Proof.* We have b_0 = 0. A background cell whose neighbours are all background has
(c,s) = (b, 4b). T(0,0) = bit_0 = 1 for both codes, and T(1,4) = bit_9 = 0 for both codes
(193, 451 < 512). So b_{t+1} = 1 - b_t. The state of z at stage t+1 depends only on the closed
neighbourhood of z at stage t. So if every cell in that neighbourhood is background at stage t,
then z is background at stage t+1. Induction on t gives the diamond bound. QED

**Lemma 2 (the torus program equals the plane evolution on the readout cells).** For both codes
and for every 0 <= n <= 126 and |x| <= n, the state of (x,0) at stage n in Price's 257-torus
equals its state in the plane evolution of Lemma 1.

*Proof.* The torus evolution lifts to the plane evolution started from the periodic
configuration with ON cells exactly at gZ^2. This holds because the rule is
translation-invariant and g >= 3, so neighbourhoods lift bijectively. The state of z at stage n
depends only on initial states in the Manhattan ball B(z,n). Take z = (x,0) with |x| <= n <= 126
and a lattice point p = g(a,b) != 0. Then
||p - z||_1 >= g(|a|+|b|) - |x| >= 257 - 126 = 131 > n.
So B(z,n) contains no seed except the origin. On B(z,n) the periodic and single-seed initial
configurations agree, and therefore so do the states of z at stage n. QED

(The C simulator in Section 6 works directly on the plane and needs no such argument. It holds a
boundary ring at the background value b_t, which is exact by Lemma 1.)

**Lemma 3 (symmetry; the two conjectures are equivalent).** For each code and each stage n, the
plane configuration is invariant under the dihedral group D4 (x -> -x, x <-> y, ...). Hence
L_code(n) is the reversal of R_code(n). Also, the readout does not depend on whether "x-axis"
means a row or a column of the Mathematica matrix. Consequently, for every n:
A282295(n) = A279720(n)  iff  A282297(n) = A279721(n).

*Proof.* T_code(c,s) depends on the neighbours only through the count s, and D4 permutes the
four von Neumann neighbours. The stage-0 configuration is D4-invariant, so by induction every
stage is D4-invariant. Reflection x -> -x maps (x,0) to (-x,0), which gives the reversal. The
strings R(n) and L(n) have fixed length n + 1, so equal integers mean equal strings, even with
leading zeros dropped. Hence A282295(n) = A279720(n) iff L_451(n) = L_193(n), iff
R_451(n) = R_193(n), iff A282297(n) = A279721(n). QED

**Lemma 4 (why the conjecture looked right).** At stage 1 the two configurations differ only at
the origin. At stage 2 they are identical. From then on, the two evolutions can separate only at
a cell whose (c,s) is (1,0) or (0,4).

*Proof (by hand).* Stage 0 has the origin ON and the background 0.

Stage 1, background 1:
* The origin has (c,s) = (1,0). It becomes 0 under rule 193 and 1 under rule 451.
* Each of the four neighbours of the origin has (c,s) = (0,1), index 2. Bit 2 is 0 for both
  codes, so these become 0.
* Every other cell has (c,s) = (0,0) and becomes 1.

Stage 2, background 0:
* Origin, rule 193: (c,s) = (0,0), so it becomes 1. Rule 451: (c,s) = (1,0), so it becomes 1.
* (1,0), rule 193: (c,s) = (0,3), so it becomes 1. Rule 451: (c,s) = (0,4), so it becomes 1.
* (2,0): (1,3) under both rules, so it becomes 1.
* (1,1): (1,2), index 5, so it becomes 0 under both rules.
* Every remaining cell z has 2 <= |z|_1, so its stage-1 closed neighbourhood does not contain
  the origin. That neighbourhood is therefore the same under both rules. Its centre is ON at
  stage 1 (c = 1), and at most two of its neighbours are OFF (only (+-1,0) and (0,+-1) are OFF),
  so s >= 2. The input (1,s) with s >= 2 is not in {(1,0),(0,4)}, so both rules give the same
  output. (The cells (+-1,0), (0,+-1) are handled by the (1,0) line above together with D4
  symmetry.)

So the stage-2 configurations coincide. After that, the same configuration fed into T_451 and
T_193 gives the same output at every cell except those with (c,s) in {(1,0), (0,4)}. QED

So the conjecture would hold for all n if the common evolution never produced an isolated ON
cell or a fully surrounded OFF cell. It does produce one. At stage 16, the common configuration
has isolated ON cells at (+-2, +-2). Here is the stage-16 configuration for |x|,|y| <= 16, with
y = 16 in the top row and '#' = ON:

```
................#................
................#................
................#................
...............###...............
..............#####..............
.............#######.............
............#########............
...........####.#.####...........
..........####.....####..........
.........#####.....#####.........
........######.....######........
.......#######.....#######.......
......########.....########......
.....#########.....#########.....
....####......#.#.#......####....
...####........###........####...
########......#####......########
...####........###........####...
....####......#.#.#......####....
.....#########.....#########.....
......########.....########......
.......#######.....#######.......
........######.....######........
.........#####.....#####.........
..........####.....####..........
...........####.#.####...........
............#########............
.............#######.............
..............#####..............
...............###...............
................#................
................#................
................#................
```

As a result, the full configurations differ at stage 17, in exactly those 4 cells. The number of
differing cells in the whole plane at stages 0..30 is:

| stage | 0 | 1 | 2-16 | 17 | 18-20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| #differing cells | 0 | 1 | 0 | 4 | 0 | 12 | 8 | 0 | 16 | 28 | 60 | 132 | 140 | 100 | 217 |

These counts come from `transparent.py` and agree with `diffscan.py`. The early differences
heal (stages 18 and 23 are identical again). From stage 24 on they persist and spread, and they
reach the x-axis at stage 26.

---

## 4. Main computational facts (three independent implementations plus the stored b-files)

**Fact A (the stored data).** The OEIS b-files (n = 0..126; downloaded copies are
`b282297.txt`, `b279721.txt`, `b282295.txt`, `b279720.txt`) give:
* A282297 vs A279721 differ exactly at n in {1} ∪ {26, ..., 126}, which is 102 values.
* A282295 vs A279720 differ exactly at the same set.
* At n = 26 the values are the ones in Theorem (a), (b).

**Fact B (my implementations reproduce every stored term).** Each of the following reproduces
all 4 x 127 stored b-file terms:
1. `repro.py`: a line-by-line numpy re-implementation of the Mathematica program (257-torus,
   index c + 2s, bit lookup). All 127 terms of each of the 4 sequences match.
2. `plane.c`: an independent C simulator on the plane. It has an explicit background b_t, a
   box of half-width N + 1, and a ring held at b_t. It reproduces all 127 terms of all four
   b-files and agrees with `repro.py` for n <= 126. The left readouts use Lemma 3.
3. `transparent.py`: a deliberately naive implementation. It stores the plane as (background,
   set of exceptional cells) and writes the rules as the Boolean formulas of Section 2, decoded
   by hand rather than by bit lookup. It matches all four b-files for n <= 40, including left
   readouts computed directly with no symmetry assumption.

**Fact C (extension to n = 1000).** Using `plane.c` with N = 1000 (`r451.txt`, `r193.txt`;
extended tables in `ext_b*.txt`, n = 0..1000):
R_451(n) = R_193(n) exactly for n in {0} ∪ {2, ..., 25}. They differ for n = 1 and for all
26 <= n <= 1000, which is 976 values. By Lemma 3 the same holds for the left readouts.

---

## 5. Hand-checkable certificate for the counterexample at n = 26

By Lemma 3 it is enough to show that the cell (3,0) at stage 26 is ON under rule 451 and OFF
under rule 193. That is digit x = 3 of R(26): `1111...` versus `1110...`.

The state of (3,0) at stage 26 depends only on stage-23 states in the diamond
D = {(x,y) : |x-3| + |y| <= 3}. That diamond has 25 cells.

**Input (computed; Facts B.1–B.3 agree).** The stage-23 configurations of the two rules are
identical everywhere (0 differing cells in the table above). On D they are as follows, with
columns x = 0..6 from left to right and rows y = 3..-3 from top to bottom:

```
y= 3:          0
y= 2:      1   0   0
y= 1:  0   0   0   0   0
y= 0:  0   0   0   0   1   1   1      (x = 0..6)
y=-1:  0   0   0   0   0
y=-2:      1   0   0
y=-3:          0
```

The y = 0 row agrees with the stored term A282297(23) = A279721(23) = 11111111000000000000,
which is the string 000011111111000000000000 for x = 0..23.

**Stage 24 (radius-2 diamond). Both rules give the same result here, because no cell has (c,s)
in {(1,0), (0,4)}.**

| cell | c | neighbours (W,E,N,S) | s | index c+2s | bit, both codes |
|---|---|---|---|---|---|
| (3,2) | 0 | (2,2)=1,(4,2)=0,(3,3)=0,(3,1)=0 | 1 | 2 | 0 |
| (2,1) | 0 | (1,1)=0,(3,1)=0,(2,2)=1,(2,0)=0 | 1 | 2 | 0 |
| (3,1) | 0 | 0,0,0,0 | 0 | 0 | 1 |
| (4,1) | 0 | (3,1)=0,(5,1)=0,(4,2)=0,(4,0)=1 | 1 | 2 | 0 |
| (1,0) | 0 | 0,0,0,0 | 0 | 0 | 1 |
| (2,0) | 0 | 0,0,0,0 | 0 | 0 | 1 |
| (3,0) | 0 | (2,0)=0,(4,0)=1,0,0 | 1 | 2 | 0 |
| (4,0) | 1 | (3,0)=0,(5,0)=1,0,0 | 1 | 3 | 0 |
| (5,0) | 1 | (4,0)=1,(6,0)=1,0,0 | 2 | 5 | 0 |

The cells with y < 0 follow by the symmetry y -> -y: (3,-1) = 1, and (2,-1) = (4,-1) = (3,-2) = 0.

**Stage 25 (radius-1 diamond).**
* (3,1): c = 1, and its neighbours (2,1), (4,1), (3,2), (3,0) are all 0, so s = 0. This is an
  **isolated ON cell**, index 1. Rule 451 (bit_1 = 1) gives **1**. Rule 193 (bit_1 = 0) gives **0**.
  The same holds for (3,-1).
* (2,0): c = 1, neighbours (1,0)=1, (3,0)=0, (2,1)=0, (2,-1)=0, so s = 1 and the index is 3.
  Both rules give 0 (bit 3 is 0 in both codes).
* (3,0): c = 0, neighbours (2,0)=1, (4,0)=0, (3,1)=1, (3,-1)=1, so s = 3 and the index is 6.
  Both rules give 1.
* (4,0): c = 0, all four neighbours 0, so the index is 0. Both rules give 1.

**Stage 26, cell (3,0):** c = 1 under both rules.
* Rule 451: neighbours (2,0)=0, (4,0)=1, (3,1)=1, (3,-1)=1, so s = 3 and the index is 7.
  bit_7(451) = 1, so the cell is **ON**.
* Rule 193: neighbours (2,0)=0, (4,0)=1, (3,1)=0, (3,-1)=0, so s = 1 and the index is 3.
  bit_3(193) = 0, so the cell is **OFF**.

So digit x = 3 of R(26) is 1 for rule 451 and 0 for rule 193. Therefore
A282297(26) ≠ A279721(26). By Lemma 3, digit x = -3 of L(26) differs too, so
A282295(26) ≠ A279720(26). This is consistent with Fact A. `diamond.py` prints this certificate
and asserts every intermediate value against the full simulation. QED (Theorem (a), (b))

Minimality (Theorem (c)) is the finite check of Facts A, B and C: the readouts agree for
2 <= n <= 25.

---

## 6. Scripts (all in /tmp/claude-0/deep/mathar-ca/)

* `run_all.sh`: runs everything below. Its output is in `run_all.out`.
* `repro.py`: exact replica of Price's Mathematica program, checked against the b-files.
* `plane.c` / `plane`: independent plane simulator. `./plane CODE N` prints R_CODE(n) for
  n = 0..N.
* `compare.py`: cross-checks `plane` against the b-files and `repro.py`, and compares the rules
  for n <= 1000.
* `transparent.py`: naive set-based simulator with hand-decoded Boolean rules. It reports the
  full-plane difference counts per stage.
* `diamond.py`: the stage-23 to stage-26 local certificate of Section 5.
* `certificate.py` → `certificate.txt`: pictures of stages 16, 25, 26 and the lists of differing
  cells for stages 16..26.
* `ext_b282297.txt`, `ext_b282295.txt`, `ext_b279721.txt`, `ext_b279720.txt`: terms n = 0..1000
  (n <= 126 identical to the OEIS b-files).

Side remark (consistent with the triage note). Rule 449 = 193 + 2^8 differs from 193 only on
(0,4). Its x-axis readout first differs from rule 193 at n = 30 (n >= 2), and from rule 451 at
n = 26. This matches the mechanism above: the first effect that reaches the axis, at n = 26,
comes from the isolated-ON-cell input (1,0), where rule 449 behaves like 193.

## 7. Suggested OEIS correction

Replace the %F lines with comments of this form:
"a(n) = A279721(n) for 2 <= n <= 25, but a(26) != A279721(26) (and a(n) != A279721(n) for
26 <= n <= 1000); the conjecture of R. J. Mathar is false."
Similarly for A282295 / A279720.
