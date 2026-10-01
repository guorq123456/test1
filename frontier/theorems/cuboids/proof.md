# Four strict cuboids filling an n x n x n cube: A386884(n) = A178312(n-4)

## Statement

**Theorem.** For every integer n >= 1,

    A386884(n) = (n-4) * T(ceil((n-4)/2)),      T(j) = j(j+1)/2,

equivalently, with m = floor((n-1)/2),

    A386884(n) = C(m,2) + m(m-1)(m-2) + [n even] * C(m,2)
               = m(m-1)(2m-3)/2   if n = 2m+1,
               = m(m-1)^2         if n = 2m+2.

So A386884(n) = 0 for 1 <= n <= 4 and A386884(n) = A178312(n-4) for all n >= 4
(A178312(k) = k*T(ceil(k/2)), offset 0). Consequently A386884 has generating function
x^5 (1 + x + 4x^2) / ((1+x)^3 (1-x)^4) and satisfies
a(n) = a(n-1) + 3a(n-2) - 3a(n-3) - 3a(n-4) + 3a(n-5) + a(n-6) - a(n-7) for n >= 8
(both inherited from A178312, since the sequence is A178312 shifted by 4 with four
leading zeros; the numerator x^5(1+x+4x^2) has degree 7).

The rest of this file defines everything precisely and proves it. The proof has three parts:

1. (Theorem 1, guillotine lemma) every tiling of a box by at most 4 boxes has a
   guillotine plane; the count 4 is used essentially (Remark 1.4).
2. (Theorem 2, structure) every tiling of the n-cube by 4 strict boxes consists of two
   slabs n x n x t and n x n x (n-t), each cut once across; this gives an explicit
   parametrisation of the possible sets of shapes.
3. (Theorem 3, counting) the distinct sets of shapes are counted exactly.

---------------------------------------------------------------------------------------

## 0. Definitions and the reading of the OEIS definition

*Boxes.* A **box** is a set P = [p_1,q_1] x [p_2,q_2] x [p_3,q_3] in R^3 with p_i < q_i
(axis-parallel, closed, non-degenerate). Its **side lengths** are q_i - p_i; its **shape**
is the multiset of its side lengths, written as a sorted triple (x <= y <= z). A box is
**strict** if its three side lengths are pairwise distinct. For a box P we write P_i =
[p_i,q_i] for its i-th interval and int P for its interior (the product of the open intervals).
"Direction i" means the i-th coordinate axis.

*Tilings.* A **tiling** of a box B by boxes P^1,...,P^k is a finite family with
B = P^1 u ... u P^k and int P^a n int P^b = {} for a != b. A **guillotine plane** of the
tiling is a plane H = {x_i = h} with h strictly inside the i-th interval of B such that no
tile interior meets H.

*The sequence.* Following A386884 ("number of distinct four-cuboid combinations that fill
an n X n X n cube using only strict cuboids"), its comment ("sets of distinct four unordered
triplets (x,y,z) with x,y,z different"), and A386903 (of which A386884 is column k=4:
"number of ways to partition n X n X n cube into k noncongruent strict cuboids"), we define

> A386884(n) = number of **sets** S of four pairwise distinct strict shapes with positive
> integer side lengths such that [0,n]^3 has a tiling by four boxes whose shapes are
> exactly the four elements of S.

So a "combination" is the set of shapes (not a geometric placement), and "distinct" means
the four cuboids are pairwise noncongruent. This reading reproduces the A386884 example
(a(6) = 2 with the two listed sets) and every stored term (Section 6), and the same reading
without the word "strict" reproduces A384311 (Section 6).

*Remarks on the model.*
(a) Tiles are taken axis-parallel. This is no restriction: Appendix A proves that in any
tiling of a box by finitely many (possibly rotated) rectangular boxes, every tile is
axis-parallel.
(b) Tile positions are arbitrary reals; nothing below assumes integer positions. (For the
brute-force program it is convenient that positions are then automatically integers:
Appendix B.)
(c) The A384311/A386884 comments also describe the objects via repeated splitting
(x,y,z) -> (x,y,r),(x,y,z-r) of triplets, i.e. hierarchical guillotine decompositions.
By Theorem 1 applied recursively (a sub-box obtained by a guillotine cut contains fewer
than 4 tiles), every tiling by 4 boxes is such a hierarchical decomposition, and every
such decomposition is a tiling, so both readings define the same sets.

Throughout, B = [0,L_1] x [0,L_2] x [0,L_3] is a box; its 8 **corners** are the points of
{0,L_1} x {0,L_2} x {0,L_3}; its 12 **edges** are the segments joining two corners that differ
in exactly one coordinate (an edge "in direction i" if they differ in coordinate i). We say a
tile P is **full in direction i** if P_i = [0,L_i].

---------------------------------------------------------------------------------------

## 1. Two basic lemmas

**Lemma 1.1 (cutting along a guillotine plane).** Let P^1..P^k tile B and let H = {x_i = h},
0 < h < L_i, be a guillotine plane. Then every tile lies in B^- = B n {x_i <= h} or in
B^+ = B n {x_i >= h}; the tiles lying in B^- tile B^-, those lying in B^+ tile B^+; both
groups are non-empty. If a group consists of a single tile, that tile equals B^- (resp. B^+).

*Proof.* For a tile P with p_i < h < q_i, the point with i-th coordinate h and the other
coordinates at the midpoints of P's other intervals lies in int P n H; so for every tile
q_i <= h or p_i >= h, i.e. P subset B^- or P subset B^+. Every point x of B^- with x_i < h lies
in some tile, which cannot be in B^+, so it lies in a tile of the lower group. The points of
B^- with x_i = h are limits of points of B^- with x_i < h (as h > 0), and a finite union of
closed sets is closed, so the lower group covers B^-; it is contained in B^-, and interiors
are disjoint. Hence it tiles B^-. B^- has non-empty interior, so the lower group is non-empty.
Same for B^+. A single tile P with P subset B^- and P superset B^- equals B^-. QED

**Lemma 1.2 (corners).** Let P^1..P^k tile B.
(a) Each corner of B lies in exactly one tile.
(b) If a tile contains two corners that differ in at least two coordinates, or contains at
least three corners, then it is full in two different directions.
(c) If k >= 2 and some tile is full in two different directions, the tiling has a guillotine
plane.

*Proof.* (a) Existence: the tiles cover B. Uniqueness: let corner c lie in tiles P and Q. For
each i, P_i and Q_i are intervals inside [0,L_i] of positive length containing c_i, which is
an endpoint 0 or L_i of [0,L_i]; so with delta = min of the 6 side lengths of P and Q, both
P_i and Q_i contain [0,delta] (if c_i = 0) or [L_i - delta, L_i] (if c_i = L_i). Hence P n Q
contains a box with all sides delta > 0, so int P n int Q != {}, a contradiction.

(b) If P contains corners c, c' with c_i != c'_i, then P_i contains 0 and L_i, so P_i =
[0,L_i]. This proves the first case. For three distinct corners c, c', c'' in P: if two of
them differ in >= 2 coordinates we are done; otherwise c' differs from c in exactly one
coordinate i and c'' differs from c in exactly one coordinate j, and j != i (otherwise both
are obtained from c by changing coordinate i, so c' = c''); then P is full in i and j.

(c) Permute coordinates so that the tile P is full in directions 1 and 2:
P = [0,L_1] x [0,L_2] x [c,d]. Since k >= 2, P != B, so c > 0 or d < L_3; by the symmetry
x_3 -> L_3 - x_3 assume d < L_3. Suppose a tile Q != P has a point y in int Q with y_3 = d.
Then 0 < y_1 < L_1, 0 < y_2 < L_2, and for small epsilon > 0 the point y - epsilon*e_3 lies in
int Q (open set) and in int P (as c < d - epsilon < d). This contradicts int P n int Q = {}.
P itself has P_3 = [c,d], so int P does not meet {x_3 = d} either. So {x_3 = d} with
0 < d < L_3 is a guillotine plane. QED

---------------------------------------------------------------------------------------

## 2. The guillotine lemma for at most four boxes

**Lemma 2.1 (perfect matchings of the cube graph).** Let M be a set of 4 pairwise
vertex-disjoint edges of B covering all 8 corners. Then either
(I) all four edges of M have the same direction (so M is the set of all 4 edges of B in that
direction), or
(II) there is a direction d not used by M, and, writing {i,j} = {1,2,3} \ {d}, one of the two
faces {x_d = 0}, {x_d = L_d} contains two edges of M, both in direction i, and the other face
contains the remaining two edges of M, both in direction j.

*Proof.* Let m_r be the number of edges of M in direction r. Fix r and look at the 4 corners
of the face {x_r = 0}. Each is matched either by an edge in direction r (which has exactly one
endpoint in this face) or by an edge lying inside the face (two endpoints in the face). Hence
4 = m_r + 2*(number of edges of M inside that face), so m_r is even. As m_1 + m_2 + m_3 = 4,
either some m_r = 4 (case I) or {m_1,m_2,m_3} = {2,2,0} as multisets. In the latter case let
m_d = 0. Then every edge of M lies in one of the two faces {x_d = 0}, {x_d = L_d}, and the
4 corners of each face are matched inside that face, so each face contains exactly 2 edges of
M forming a perfect matching of the 4-cycle of that face, i.e. two opposite (parallel) sides.
If both faces used the same direction i, then m_i = 4, contradiction; so one face uses i and
the other j. QED

(The cube graph has exactly 9 perfect matchings, 3 of type I and 6 of type II; this is also
checked by `misc_checks.py`.)

**Theorem 1 (guillotine lemma).** Every tiling of a box B by k boxes with 2 <= k <= 4 has a
guillotine plane.

*Proof.* If some tile is full in two different directions, Lemma 1.2(c) gives a guillotine
plane. Assume from now on that no tile is full in two directions. By Lemma 1.2(b), every
tile then contains at most 2 corners, and if it contains 2 corners these differ in exactly
one coordinate, i.e. they are the endpoints of an edge of B, and the tile contains that edge
(a box is convex). By Lemma 1.2(a) the 8 corners are distributed among the k tiles with each
corner in exactly one tile, so 8 <= 2k <= 8: **k = 4 and each tile contains exactly two
corners** (this is the only place where k <= 4 is used). The 4 edges so obtained are
pairwise vertex-disjoint and cover all corners, so Lemma 2.1 applies. Note: if a tile P
contains an edge of B in direction r, then P is full in direction r, and P is not full in any
other direction (by our assumption); in each other direction s, P_s contains the
s-coordinate (0 or L_s) of that edge and is a proper subinterval of [0,L_s], so it is
[0, u] with 0 < u < L_s or [L_s - u, L_s] with 0 < u < L_s.

*Case I: all four edges in one direction.* Permuting coordinates, the direction is 3, so the
four tiles contain the four vertical edges of B, at (x_1,x_2) = (0,0), (L_1,0), (L_1,L_2),
(0,L_2) respectively. By the note,

    P^1 = [0,a_1]       x [0,b_1]       x [0,L_3],
    P^2 = [L_1-a_2,L_1] x [0,b_2]       x [0,L_3],
    P^3 = [L_1-a_3,L_1] x [L_2-b_3,L_2] x [0,L_3],
    P^4 = [0,a_4]       x [L_2-b_4,L_2] x [0,L_3],      0 < a_r < L_1, 0 < b_r < L_2.

The segment E = [0,L_1] x {0} x {0} is covered by the tiles; P^3 and P^4 contain no point
with x_2 = 0 (since b_3, b_4 < L_2), so E subset P^1 u P^2, giving [0,a_1] u [L_1-a_2, L_1]
= [0,L_1], hence a_1 >= L_1 - a_2. If a_1 > L_1 - a_2, then P^1 n P^2 contains
[L_1-a_2, a_1] x [0, min(b_1,b_2)] x [0,L_3], which has non-empty interior: impossible.
So **a_1 + a_2 = L_1**. In the same way (segments [0,L_1] x {L_2} x {0}, {0} x [0,L_2] x {0},
{L_1} x [0,L_2] x {0}): **a_3 + a_4 = L_1, b_1 + b_4 = L_2, b_2 + b_3 = L_2.**
Volumes add up: since the tiles cover B, vol(B) <= sum vol(P^r); since the interiors are
disjoint subsets of B and vol(int P) = vol(P), sum vol(P^r) <= vol(B). Hence
(a_1 b_1 + a_2 b_2 + a_3 b_3 + a_4 b_4) L_3 = L_1 L_2 L_3. Substituting a_2 = L_1 - a_1,
a_3 = L_1 - a_4, b_4 = L_2 - b_1, b_3 = L_2 - b_2:

    a_1 b_1 + (L_1-a_1) b_2 + (L_1-a_4)(L_2-b_2) + a_4 (L_2-b_1)
      = L_1 L_2 + a_1 b_1 - a_1 b_2 + a_4 b_2 - a_4 b_1 = L_1 L_2 + (a_1 - a_4)(b_1 - b_2),

so **(a_1 - a_4)(b_1 - b_2) = 0**.
* If a_1 = a_4 =: a (0 < a < L_1): P^1, P^4 have first interval [0,a]; P^2 has
  [L_1 - a_2, L_1] = [a_1, L_1] = [a, L_1]; P^3 has [L_1 - a_3, L_1] = [a_4, L_1] = [a, L_1].
  So {x_1 = a} is a guillotine plane.
* If b_1 = b_2 =: b (0 < b < L_2): P^1, P^2 have second interval [0,b]; P^4 has
  [L_2 - b_4, L_2] = [b_1, L_2] = [b, L_2]; P^3 has [L_2 - b_3, L_2] = [b_2, L_2] = [b, L_2].
  So {x_2 = b} is a guillotine plane.

*Case II.* Permuting coordinates we may assume d = 3, the face {x_3 = 0} contains the two
edges of M in direction 1 (namely [0,L_1] x {0} x {0} and [0,L_1] x {L_2} x {0}) and the face
{x_3 = L_3} contains the two edges in direction 2 ({0} x [0,L_2] x {L_3} and
{L_1} x [0,L_2] x {L_3}). By the note the four tiles are

    A^1 = [0,L_1]       x [0,alpha_1]       x [0,h_1],
    A^2 = [0,L_1]       x [L_2-alpha_2,L_2] x [0,h_2],
    C^1 = [0,beta_1]    x [0,L_2]           x [L_3-g_1,L_3],
    C^2 = [L_1-beta_2,L_1] x [0,L_2]        x [L_3-g_2,L_3],

with 0 < alpha_r < L_2, 0 < beta_r < L_1, 0 < h_r, g_r < L_3.
Consider the vertical edge {0} x {0} x [0,L_3] of B. A^2 contains no point with x_2 = 0
(alpha_2 < L_2) and C^2 none with x_1 = 0 (beta_2 < L_1), so this edge is covered by
A^1 u C^1: [0,h_1] u [L_3 - g_1, L_3] = [0,L_3], so h_1 >= L_3 - g_1. If h_1 > L_3 - g_1 then
A^1 n C^1 contains [0,beta_1] x [0,alpha_1] x [L_3-g_1, h_1], with non-empty interior:
impossible. So h_1 = L_3 - g_1. Likewise the edge {L_1} x {0} x [0,L_3] meets only A^1 and C^2
(C^1 has x_1 <= beta_1 < L_1, A^2 has x_2 >= L_2 - alpha_2 > 0), giving h_1 = L_3 - g_2; and the
edge {0} x {L_2} x [0,L_3] meets only A^2 and C^1, giving h_2 = L_3 - g_1. Hence
h_1 = h_2 = L_3 - g_1 = L_3 - g_2 =: h with 0 < h < L_3, and A^1, A^2 subset {x_3 <= h},
C^1, C^2 subset {x_3 >= h}: {x_3 = h} is a guillotine plane. QED

**Remark 1.4 (sharpness; why the count 4 matters).** For k = 5 the statement is false: the
pinwheel tiling of a 3 x 3 square by 5 rectangles, times an interval, is a non-guillotine
tiling of a box by 5 boxes (and `guillotine_check.c` finds 876 non-guillotine 5-tilings
among boxes with sides <= 4, e.g. already for 2 x 2 x 2). In the proof above the count enters
exactly once: with k <= 4 tiles, if no tile is full in two directions, every tile must
contain exactly two corners; with k = 5 a tile may contain no corner at all (the pinwheel's
central square), and the argument breaks down.

---------------------------------------------------------------------------------------

## 3. Structure of tilings of the cube by four strict boxes

**Theorem 2.** Let n >= 1 and let the cube Q_n = [0,n]^3 be tiled by four strict boxes whose
side lengths are positive integers. Then there are integers t, s, s' with

    1 <= t <= n-1,     s, s' in {1,...,n-1} \ {t, n-t},                      (*)

such that the shapes of the four tiles are

    {s, t, n},  {n-s, t, n},  {s', n-t, n},  {n-s', n-t, n}.                   (**)

Conversely, for all integers t, s, s' satisfying (*) there is a tiling of Q_n by four strict
boxes with the shapes (**).

*Proof.* By Theorem 1 (k = 4) there is a guillotine plane; after permuting coordinates it is
{x_3 = t} with 0 < t < n. By Lemma 1.1 the tiles split into two non-empty groups tiling the
slabs B^- = [0,n]^2 x [0,t] and B^+ = [0,n]^2 x [t,n]. Each slab has two sides equal to n, so it
is not strict; by the last sentence of Lemma 1.1 a group consisting of a single tile would
equal its slab, which is impossible since all tiles are strict. So each group has at least 2
tiles, and as there are 4 tiles, **each slab is tiled by exactly 2 tiles**.

Apply Theorem 1 (k = 2) to the tiling of B^- by its two tiles: there is a guillotine plane
{x_j = s} of B^-, and by Lemma 1.1 both sides contain at least one tile, hence exactly one,
which equals that side: the two tiles are B^- n {x_j <= s} and B^- n {x_j >= s}. If j = 3
the tile [0,n]^2 x [0,s] is not strict; so j in {1,2}, 0 < s < n, and the two tiles have side
lengths (in some order) s, n, t and n-s, n, t. In particular t and s are side lengths of
tiles, hence positive integers, with t <= n-1, s <= n-1. Strictness of {s,t,n}: since
s, t < n this means s != t. Strictness of {n-s,t,n}: n - s != t. So s is not in {t, n-t}.
The same argument for B^+, which has thickness n - t, gives a cut position s' with shapes
{s', n-t, n}, {n-s', n-t, n} and s' not in {n-t, n-(n-t)} = {t, n-t}. This proves (*), (**).

Conversely, given (*), the boxes [0,s] x [0,n] x [0,t], [s,n] x [0,n] x [0,t],
[0,s'] x [0,n] x [t,n], [s',n] x [0,n] x [t,n] tile Q_n, have the shapes (**), and are strict
by the computation just made. QED

**Corollary 2.1.** A386884(n) is the number of distinct sets

    Sigma(t,s,s') = { {s,t,n}, {n-s,t,n}, {s',n-t,n}, {n-s',n-t,n} }

over all integer triples (t,s,s') satisfying (*) for which the four shapes in Sigma(t,s,s')
are pairwise distinct.

*Proof.* By definition A386884(n) counts the sets of four pairwise distinct strict shapes
realised by some tiling of Q_n. By Theorem 2 every such realised set is a Sigma(t,s,s') with
(*), and every Sigma(t,s,s') with (*) is realised. QED

---------------------------------------------------------------------------------------

## 4. Counting the sets Sigma(t,s,s')

*Encoding.* Let [n-1] = {1,...,n-1}. Each shape in (**) has the form {x, y, n} with
x, y in [n-1] and x != y; its largest entry is n and it is determined by the 2-element set
{x,y} subset [n-1]. We identify the shape with this 2-set ("edge" {x,y}); this identification is
injective, so we may count sets of edges. Let rho(x) = n - x, an involution of [n-1]. Its
orbits O(x) = {x, n-x} are: the m = floor((n-1)/2) **proper orbits** {x, n-x} with
1 <= x < n/2 (two elements each) and, if n is even, the fixed point n/2. In this language

    E(t,s,s') = { {s,t}, {rho s, t}, {s', rho t}, {rho s', rho t} },

and condition (*) reads: t in [n-1], s, s' in [n-1], s not in O(t), s' not in O(t).

**Lemma 4.1 (distinctness).** Let (t,s,s') satisfy (*). The four edges of E(t,s,s') are
pairwise distinct if and only if

    s != rho(s),  s' != rho(s'),  and  NOT( t = rho(t) and O(s') = O(s) ).

*Proof.* From s not in O(t) we get rho(s) not in O(t) (as rho(s) = t iff s = rho(t), and
rho(s) = rho(t) iff s = t); likewise for s'. Hence each of the four edges has exactly one
endpoint in O(t) = {t, rho t}: e_1 = {s,t} and e_2 = {rho s, t} have it equal to t, and
e_3 = {s', rho t}, e_4 = {rho s', rho t} have it equal to rho t. Two of these edges coincide
iff their O(t)-endpoints coincide and their other endpoints coincide. Thus
e_1 = e_2 iff s = rho s; e_3 = e_4 iff s' = rho s'; and for a in {1,2}, b in {3,4}, e_a = e_b
iff t = rho t and the other endpoints agree, i.e. iff t = rho t and
(s = s' or s = rho s' or rho s = s' or rho s = rho s'), i.e. iff t = rho t and O(s) = O(s').
QED

Let V be the set of triples (t,s,s') satisfying (*) and the condition of Lemma 4.1. Then
A386884(n) = |{ E(v) : v in V }| by Corollary 2.1. For v = (t,s,s') in V, O(s) and O(s') are
proper orbits different from O(t). We split V into three types:

* **Type A:** O(s') = O(s). Then t != rho t (Lemma 4.1), and since {s', rho s'} = {s, rho s},
  E(v) = O(s) (x) O(t), where for sets X, Y we write X (x) Y = { {x,y} : x in X, y in Y }.
* **Type B:** O(s') != O(s) and t != rho t. Then E(v) = ({t} (x) O(s)) u ({rho t} (x) O(s')).
* **Type C:** O(s') != O(s) and t = rho t, i.e. n even and t = n/2. Then
  E(v) = {n/2} (x) (O(s) u O(s')).

View a set E of edges as a graph with vertex set V(E) = union of its edges.

**Lemma 4.2.** (i) The type-A sets E(v) are exactly the sets O_1 (x) O_2 with {O_1, O_2} an
unordered pair of distinct proper orbits, and distinct pairs give distinct sets; there are
C(m,2) of them. Each has 4 vertices.
(ii) The type-B sets E(v) are exactly the sets ({y} (x) phi(y)) u ({rho y} (x) phi(rho y)) where
O_0 = {y, rho y} is a proper orbit and phi is an injective map from O_0 to the set of proper
orbits other than O_0; distinct pairs (O_0, phi) give distinct sets; there are
m(m-1)(m-2) of them. Each has 6 vertices.
(iii) If n is even, the type-C sets E(v) are exactly the sets {n/2} (x) (O_1 u O_2) with
{O_1,O_2} an unordered pair of distinct proper orbits, distinct pairs giving distinct sets;
there are C(m,2) of them. Each has 5 vertices. If n is odd there are no type-C triples.
(iv) Sets of different types are different.

*Proof.* (i) For type A, E(v) = O(s) (x) O(t) with O(s), O(t) distinct proper orbits. Conversely,
given distinct proper orbits O_1, O_2, take s in O_1, t in O_2, s' = s: then s not in O(t),
s != rho s, t != rho t, so (t,s,s) is in V and E = O_1 (x) O_2. The vertex set of O_1 (x) O_2 is
O_1 u O_2 (4 elements), which determines the unordered pair {O_1,O_2} as the set of orbits it
contains. Count: C(m,2).
(ii) For type B with O_0 = O(t), phi(t) = O(s), phi(rho t) = O(s') (injective, values proper orbits
!= O_0) we get exactly the displayed form. Conversely, for such (O_0, phi) and y in O_0, choose
s in phi(y), s' in phi(rho y); then (y, s, s') is in V (s, s' not in O_0, both in proper orbits,
y != rho y) and has type B, and E(y,s,s') is the displayed set. The three orbits O_0, phi(y),
phi(rho y) are distinct, so the set has 6 vertices; y and rho y have degree 2 and all other
vertices degree 1. Hence the set determines O_0 (its vertices of degree 2) and phi (phi(z) is
the neighbourhood of z for z in O_0). Count: m choices of O_0 and (m-1)(m-2) injective maps
from the 2-element set O_0 into the other m-1 proper orbits: m(m-1)(m-2).
(iii) Similar: given distinct proper orbits O_1, O_2 (n even), (n/2, s, s') with s in O_1,
s' in O_2 lies in V (s, s' != n/2, O(s) != O(s')) and has type C. The set has the 5 vertices
{n/2} u O_1 u O_2, and removing n/2 recovers O_1 u O_2, hence {O_1,O_2}. Count C(m,2).
For n odd, rho has no fixed point.
(iv) The numbers of vertices (4, 6, 5) differ. QED

**Theorem 3.** For all n >= 1, with m = floor((n-1)/2),

    A386884(n) = C(m,2) + m(m-1)(m-2) + [n even] C(m,2) = (n-4) T(ceil((n-4)/2)).

*Proof.* The first equality is Corollary 2.1 with Lemma 4.2. For the second:
* n = 2m+1: C(m,2) + m(m-1)(m-2) = m(m-1)(1/2 + m - 2) = m(m-1)(2m-3)/2. Here n-4 = 2m-3 and
  ceil((2m-3)/2) = m-1, so (n-4) T(m-1) = (2m-3)(m-1)m/2. Equal.
* n = 2m+2: 2C(m,2) + m(m-1)(m-2) = m(m-1)(1 + m - 2) = m(m-1)^2. Here n-4 = 2m-2,
  ceil((2m-2)/2) = m-1, (n-4) T(m-1) = 2(m-1) * m(m-1)/2 = m(m-1)^2. Equal.
These polynomial identities hold for every integer m >= 0 (with T(j) = j(j+1)/2 for all
integers j, so T(-1) = T(0) = 0); in particular A386884(n) = 0 for n = 1, 2, 3, 4
(m = 0, 0, 1, 1). For n >= 4, (n-4) T(ceil((n-4)/2)) = A178312(n-4) by the definition of
A178312 (offset 0). QED

*Example (n = 6, m = 2, proper orbits {1,5}, {2,4}, fixed point 3).* Type A:
{1,5} (x) {2,4} = {1,2},{1,4},{5,2},{5,4}, i.e. {(1,2,6),(1,4,6),(2,5,6),(4,5,6)}; type B: none
(needs m >= 3); type C: {3} (x) {1,5,2,4}, i.e. {(1,3,6),(2,3,6),(3,4,6),(3,5,6)}. These are the
two sets in the OEIS example, a(6) = 2.

*Further consequences.* Since A386884(n) = A178312(n-4) for n >= 4 and A386884(1..4) = 0 =
coefficients of x^1..x^4 of x^4 * (x(1+x+4x^2)/((1+x)^3(1-x)^4)), the g.f. of A386884 (offset 1)
is x^5(1+x+4x^2)/((1+x)^3(1-x)^4), and
A386884(n) = (n-4)(2(n-4)(n-1) - (2n-5)(-1)^n + 3)/16 for all n >= 1 (Berselli's formula for
A178312 with n -> n-4; both sides vanish at n = 1..4: checked in `misc_checks.py`).

---------------------------------------------------------------------------------------

## 5. What is used where (checklist for a skeptical reader)

* Theorem 1 uses only: Lemma 1.2 (corners), Lemma 2.1 (matchings, a parity count), the fact
  that the tiles cover B (edge segments are covered), disjointness of interiors, and additivity
  of volume. No integrality of positions or sizes is used. k <= 4 is used exactly where
  indicated (8 corners, each tile with <= 2 corners).
* Theorem 2 uses Theorem 1 twice (k = 4 for the cube, k = 2 for a slab) and Lemma 1.1, and
  integrality only of side lengths (to conclude t, s, s' are integers).
* The counting uses only Corollary 2.1 and finite combinatorics of the involution x -> n-x.
* No finite case check is needed for the proof. Computations (Section 6) are independent
  confirmations.

---------------------------------------------------------------------------------------

## 6. Computations (all in /tmp/claude-0/deep/cuboids/)

None of these is needed for the proof; they are independent confirmations.

1. `brute4.c`, `brute4b.c` -- **direct brute force from the OEIS definition**, no structural
   assumption (brute4b = brute4 with faster data structures; identical outputs, including the
   numbers of volume candidates, for n <= 14). For given n the program enumerates every set of
   4 pairwise distinct shapes (strict, or arbitrary with flag 0) with sides in [1,n] and total
   volume n^3, and decides by exhaustive backtracking on the unit-cell grid whether the cube
   can be tiled with exactly these four pieces (first empty cell in (z,y,x)-lexicographic
   order, every unused piece in every orientation; this is complete for integer-position
   tilings, and every tiling has integer positions by Appendix B). It also prints the
   realised sets (verbose flag); for n = 6 these are exactly the two sets of the OEIS example.
   Strict results, n = 1..20 (log `brute4b_15_20.txt` for n >= 15, `brute_13_14.txt`):

       n     : 1 2 3 4 5 6 7  8  9  10 11 12 13  14  15  16  17  18  19  20
       a(n)  : 0 0 0 0 1 2 9 12 30 36 70 80 135 150 231 252 364 392 540 576
       cands : 0 0 0 0 2 39 52 678 1302 6795 5871 57855 29084 173763 234247 592952
               411722 2594900 1177176 5775283

   ("cands" = number of 4-sets of distinct strict shapes of total volume n^3 that were tested),
   all equal to the stored terms of A386884 and to the formula.
   With flag 0 (shapes not required strict) it gives 0,0,4,12,47,85,183,266 for n = 1..8,
   equal to A384311, confirming the reading "set of noncongruent shapes" of these entries.
2. `structure_count.py` -- enumerates the sets Sigma(t,s,s') of Corollary 2.1 for n <= 90
   and checks equality with the closed form, with the type count of Lemma 4.2, with
   A178312(n-4), with all 49 stored terms of A386884 (n <= 49) and all 45 stored terms of
   A178312, and, for n <= 14, **set by set** with the list of sets found by brute4b
   (log `structure_count_90_14.txt`).
3. `guillotine_check.c` -- exhaustive check of Theorem 1: all tilings (on the integer grid) of
   every box with sides <= 6 by k = 2, 3, 4 boxes (420, 5040, 66920 tilings) have a guillotine
   plane (`guillotine_M6_K4.txt`); for k = 5 and sides <= 4 there are 876 non-guillotine
   tilings among 41128 (`guillotine_M4_K5.txt`), so the checker does detect non-guillotine
   tilings and the bound 4 is sharp.
4. `guillotine_enum.py` -- computes A386884(n) assuming only Theorem 1 (enumerates all
   hierarchical guillotine decompositions of the cube into 4 strict boxes, dedups shape sets);
   agrees with the formula and stored terms for n <= 70 (`guill_enum_1_20.txt`,
   `guill_enum_21_70.txt`). With strict = 0 it reproduces A384311 for n <= 12
   (`guill_enum_A384311_1_12.txt`).
5. `misc_checks.py` (`misc_checks.txt`) -- closed form = type count of Lemma 4.2 for
   n <= 10^5; the 9 perfect matchings of the cube graph and their classification (Lemma 2.1);
   the Berselli-type formula for n <= 10^5; the g.f. for n <= 399; the order-7 recurrence for
   8 <= n < 2000.

---------------------------------------------------------------------------------------


## Appendix A. Tiles in a tiling of a box are automatically axis-parallel

**Lemma A.** Let the axis-parallel box B be tiled by finitely many rectangular boxes
P^1..P^k, each an arbitrary congruent copy of an axis-parallel box (rotated, i.e.
P = v + {sum lambda_i d_i : 0 <= lambda_i <= l_i} with d_1,d_2,d_3 orthonormal). Then every
P^r is axis-parallel (its edge directions are +-e_1, +-e_2, +-e_3).

*Proof.* Let D be the finite set of all edge directions of all tiles together with e_1, e_2,
e_3. Choose w in R^3 with w.d != 0 for all d in D (avoid finitely many planes) and put
f(x) = w.x. For each tile P, writing P = v + {sum lambda_i d_i} with the vertex v chosen so that
w.d_i > 0 for i = 1,2,3 (replace d_i by -d_i and move v along d_i if needed), we get
f(v + sum lambda_i d_i) = f(v) + sum lambda_i w.d_i, so f attains its minimum on P at the unique
vertex v =: v(P), and the tangent cone of P at v(P) is T = cone(d_1,d_2,d_3), with
w.x > 0 for all x in T \ {0}.

Suppose some tile is not axis-parallel; among such tiles choose P with f(v(P)) minimal, and
put v = v(P).
(1) If a non-axis-parallel tile Q contains v, then v = v(Q): otherwise f(v(Q)) < f(v) (unique
minimiser, v in Q), contradicting the choice of P. Hence its tangent cone T_Q at v satisfies
T_Q \ {0} subset {w.x > 0}.
(2) For a polytope R and a point u in R there is r > 0 with R n Ball(u,r) = (u + T_R(u)) n Ball(u,r),
where T_R(u) is the tangent cone (the inactive facet inequalities hold strictly near u).
Choose r > 0 smaller than the distance from v to every tile not containing v and such that
(2) holds for B and for every tile containing v. With K the tangent cone of B at v, we get
(v + K) n Ball(v,r) = B n Ball(v,r) = union over tiles Q containing v of (v + T_Q) n Ball(v,r);
since all these sets are cones, K = union of the T_Q (Q containing v). The T_Q have pairwise
disjoint interiors: if int T_Q n int T_Q' were non-empty it would contain a point x with
|x| < r (cones), and then v + x would lie in int Q n int Q' (because the open set
(v + int T_Q) n openBall(v,r) is contained in Q, hence in int Q), which is impossible.
(3) K and the tangent cones of axis-parallel tiles are products of factors R, [0,inf),
(-inf,0], i.e. unions of closed coordinate orthants O_sigma = {sigma_i x_i >= 0},
sigma in {+-1}^3. Let A be the union of the axis-parallel cones T_Q and W the union of the other
cones T_Q (Q containing v). Since int O_tau meets no orthant other than O_tau, an orthant O_tau
contained in A is one of the orthants making up some axis-parallel cone T_Q', so
int O_tau subset int T_Q'. If int T_Q (Q non-axis-parallel) met such an O_tau, then (O_tau being
the closure of its interior and int T_Q open) it would meet int O_tau subset int T_Q':
impossible. Hence int T_Q, and so T_Q, lies in
the union U of the orthants O_sigma contained in K but not in A. Conversely for such sigma,
int O_sigma meets no orthant other than O_sigma, so int O_sigma is disjoint from A, hence
contained in W, and O_sigma subset W (W closed). So W = U.
(4) By (1), W \ {0} subset {w.x > 0}. If O_sigma subset W then sigma_i e_i in O_sigma gives
sigma_i w_i > 0, so sigma = sigma* := (sign w_1, sign w_2, sign w_3). Since W contains T_P != {0},
W = O_{sigma*}.
(5) Let mu(X) = volume of X n Ball(0,1). Each T_Q with v a vertex of Q is an orthogonal image of an
orthant, so mu(T_Q) = mu(O_{sigma*}) = omega > 0. W is the union of the cones T_Q of the
non-axis-parallel tiles at v, with disjoint interiors and null boundaries, so
omega = mu(W) = omega * (number of such tiles). Hence P is the only one and T_P = W = O_{sigma*}
(T_P subset O_{sigma*}, both closed convex cones of equal positive measure, and O_{sigma*} is the
closure of its interior). The extreme rays of the simplicial cone cone(d_1,d_2,d_3) are
R_+ d_1, R_+ d_2, R_+ d_3, those of O_{sigma*} are R_+ sigma*_i e_i; so each d_i is +-e_j for some
j, i.e. P is axis-parallel: contradiction. QED

## Appendix B. Integer positions (justifies the grid search in brute4.c)

**Lemma B.** In a tiling of [0,n]^3 by axis-parallel boxes with integer side lengths, every tile
has integer coordinates.

*Proof.* It suffices to show every lower endpoint p_1 of a first interval is an integer
(upper = lower + integer; same for other coordinates). If not, pick a tile P with
non-integer p_1, p_1 minimal. Then p_1 > 0. Choose (y_2,y_3) in the open rectangle
(p_2,q_2) x (p_3,q_3) avoiding the finitely many values that are endpoints of second resp.
third intervals of tiles. For small epsilon > 0 the points (p_1 - epsilon, y_2, y_3) are in B and
covered by tiles; some tile Q contains such points for a sequence epsilon -> 0, hence contains
(p_1, y_2, y_3), and by the choice of y_2, y_3 these lie strictly inside Q_2, Q_3. Write
Q_1 = [a, b] with a < p_1 <= b. If b > p_1, then (p_1 + delta, y_2, y_3) lies in int Q n int P for
small delta > 0: impossible. So b = p_1 and a = p_1 - (side length of Q) is a non-integer smaller
than p_1, contradicting minimality. QED

With integer positions, if c is the first (in (z,y,x)-lexicographic order) unit cell not
covered by the already placed tiles of a tiling, then the tile of that tiling covering c has
its minimal corner cell m <= c coordinatewise; m is not covered by placed tiles, so m >= c
lexicographically, whence m = c. So the backtracking in brute4.c (place a piece with minimal
corner at the first empty cell) visits every tiling, and its answer is exact.
