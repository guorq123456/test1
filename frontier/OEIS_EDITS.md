# 对 OEIS 的修改建议（汇总）

以下内容摘自各深挖结果的「新增内容」字段，原文为英文。尚未提交到 OEIS。

## morphology

- 证明状态：PROVED；复核：SOUND；查新：PARTIALLY_KNOWN
- 证明文件：`theorems/morphology/proof.md`

### What is new / suggested edits

1. None of the following pairs is cross-referenced in OEIS in either direction (checked by xref_audit.py on the Oct 1 2026 snapshot):
   - A200880/A202882, A200881/A203094, A200882/A203184, A200883/A203050, A200884/A203059, A200885/A202909;
   - A200886 vs the n X m tables A202889, A203101, A203191, A203057, A203066, A202916 (column 1);
   - A200865/A217450, A200866/A218051;
   - A200871 vs the column 1 of the min-filter tables A217457, A217645, A217547, A218181, A218651, A218056 (and column 2 of A217547 and A218056);
   - A217883 column 2 vs A200880, and A217954 column 2 vs A200881.
   The triage list omitted the k=3 pair A200881/A203094.

2. Two existing cross-references are now proved: "A217883 column 2 = A202882(n+1)" and "A217954 column 2 = A203094(n+1)". The existing k=1 links (A200886 column 1 = A005251(n+5), and the A006355 links) are consistent with the theorems.

3. Every "Empirical" recurrence and g.f. becomes a theorem:
   - For the peak-free and nonzero <= neighbour families, for ALL k, via a general closed form. Its A-side is equivalent to Mansour-Shattuck Lemma 2.1 at q = 0, which OEIS does not record as a formula.
   - For the peak-and-valley and min-filter families, for k <= 7, plus all the row polynomials and Colin Barker's conjectured row g.f.s.

4. Errata found:
   - A202882's Mansour-Shattuck link says "k=3, one peak". It should be "no peak", with shift: A202882(n) = [x^{n-1}] W_3(x,0).
   - A203094 says "Also a column of A228461". This is false: A228461's column 3 is 4,16,50,130 while A203094 has 144 there, and no row or column matches. The intended reference is A217954, column 2.

5. Full tables: the identities hold for the entire tables A200886 and A200871, all rows and columns. Columns m >= 2 of Hardin's 2D tables have no analogue and no OEIS match.

## harmonic-hex

- 证明状态：PROVED；复核：SOUND；查新：PARTIALLY_KNOWN
- 证明文件：`theorems/harmonic-hex/proof.md`

### What is new / suggested edits

A228016's %F lines list two formulas as '(conjectured)' (Kimberling 2013): the recurrence a(n)=11a(n-1)-11a(n-2)+a(n-3) and the g.f. (-54+55x-5x^2)/(-1+11x-11x^2+x^3). Both are now theorems, via the identity A228016(n)=A087125(n+1). The recurrence holds for n>=4. The g.f. as printed is sum a(n)x^{n-1}; with offset 1 the proper g.f. is x(54-55x+5x^2)/((1-x)(1-10x+x^2)).

Neither entry links A228016 to A087125. A228016 has no closed form and is not linked to the hex/triangular Pell equation. The proof also confirms the %C limits: H(a(n))-H(a(n-1)) tends to log(5+2sqrt6) = 2.29243166956...

The proof shows several errors in the A228016 entry:
- %N has '>' where '<' is meant.
- %C says 'For A227965' where A228016 is meant.
- %C gives the limit of a(n)/a(n-1) as 0.8989794855..., but it is 9.8989794855... = 5+2sqrt6.
- %C says the ratios a(n)/a(n-1) are increasing, but they decrease (9.981, 9.907, 9.8998, ...).

Extended evidence:
- The definition is rigorously brute-forced through a(10) (k up to 5*10^10).
- The multiprecision check now covers n=1..1000, against 100 terms in the b-file.

For A087125, the proof gives a self-contained Pell-equation argument that its g.f. and recurrence describe exactly the hex-triangular indices.

## nonresidue

- 证明状态：PROVED；复核：SOUND；查新：PARTIALLY_KNOWN
- 证明文件：`theorems/nonresidue/proof.md`

### What is new / suggested edits

A112051 has no formula: only 43 data terms and no b-file. A112052 has the comment "From n>=4 onward seems to be squares of primes", which is labeled as empirical. A112049 has Karttunen's comment that the A112051 positions "seem also to be the positions of the first occurrence of each n, and thus the positions of the records", also unproved. A112060's permutation claim is stated "provided ... every prime occurs infinitely many times". This work:
(1) proves A112051(n) = A216244(n) = A084921(n) = (prime(n)^2-1)/2 for n >= 4, and A112052(n) = prime(n)^2 = A001248(n) for n >= 4;
(2) proves the A112049 comment, namely that the first occurrences of 1, 2, 3, ... come in order at A112051(k) and are exactly the record positions of A112049, A112046 and A112050;
(3) shows the A112060 proviso holds (f(m) = 2 for m = 3, 5 mod 8, and f(p^2 r^2) = p for primes r > p), so A112060 is a permutation;
(4) gives a self-contained elementary proof that n(q) < sqrt(q) for all primes q other than 3, 7, 23; this could be added to A053760 or A000229, e.g. as A000229(k) > prime(k)^2 for k >= 4;
(5) provides a b-file for A112051 with n = 1..9592.
Missing cross-references to add: A112051 <-> A216244, A084921 and A053760; A112052 <-> A001248.

## mathar-ca

- 证明状态：REFUTED；复核：SOUND；查新：PARTIALLY_KNOWN
- 证明文件：`theorems/mathar-ca/proof.md`

### What is new / suggested edits

A282297 and A282295 currently carry %F lines "Conjecture: a(n) = A279721(n) for n>=2" and "Conjecture: a(n) = A279720(n) for n>=2" (R. J. Mathar, Jun 21 2025); the live entries checked on 2026-10-01 still have them. Both are false.
- The first counterexample is n = 26, and the pairs differ for every 26 <= n <= 1000.
- The correct statement is agreement for 2 <= n <= 25 only.
- The visible data lines stop at n = 22 and n = 23, but the entries' own b-files already contradict the conjecture at n = 26.
- New here: the mechanism (an isolated ON cell at (3,+-1) at stage 24, where the rules differ via bit 1); a hand-checkable 25-cell certificate; the equivalence of the two conjectures by symmetry; and terms extended to n = 1000.

Suggested edit: replace both %F lines with "a(n) = A279721(n) [resp. A279720(n)] for 2 <= n <= 25, but not for n = 26 (nor any 26 <= n <= 1000)".

## cuboids

- 证明状态：PROVED；复核：SOUND；查新：NEW
- 证明文件：`theorems/cuboids/proof.md`

### What is new / suggested edits

The current A386884 entry (and A386903, of which it is column 4) has only a definition, an example and data; the data runs to n = 49 and was added by Sean A. Irvine. It has no formula, no g.f., no proof and no link to A178312. This work proves A386884(n) = A178312(n-4) = (n-4)*T(ceil((n-4)/2)) for n >= 4, with a(1..4) = 0. It also gives the g.f. x^5(1+x+4x^2)/((1+x)^3(1-x)^4), the explicit polynomial forms m(m-1)(2m-3)/2 for n = 2m+1 and m(m-1)^2 for n = 2m+2, a Berselli-type formula, and the recurrence of order 7.

Suggested edits:
- add these as proved formulas to A386884 and the column-4 formula to A386903;
- add Cf. A178312 to A386884 and Cf. A386884 to A178312;
- optionally add a comment that every 4-tiling of a box is guillotine, which justifies the splitting description in the A384311/A386884 comments for k = 4, and give the explicit structure: two slabs, each cut once.

The stored terms of A386884 contain nothing labelled conjecture or empirical. The new content is the closed form with a complete proof.

## words101

- 证明状态：PROVED；复核：SOUND；查新：PARTIALLY_KNOWN
- 证明文件：`theorems/words101/proof.md`

### What is new / suggested edits

A225034:
- Berselli's formula '(n+1)a(n)-(2n+3)a(n-1)-3(n-2)a(n-2)=0 for n>1' is labeled 'Conjecture'. It is now proved. It is in fact a formal consequence of the g.f. the entry already labels 'Theorem' (Bilotta-Grazzini-Pergola 2013, Prop. 4 with j=1, proved by the ECO method), because that g.f. simplifies to (1+x)(R-1)/(2x), which satisfies the first-order ODE above. The label can be removed.
- That 'Theorem' g.f. now also has an independent, elementary proof from the definition.
- New formulas, none of them in the entry: a(n)=A005773(n)+A005773(n+1) for n>=1; a(n)=Sum_{k=0..n-1}(-1)^(n-1-k)C(n-1,k)C(2k+3,k+1); a(n)=Sum_j C(n-1,j)C(j+3,n-j); a(n)=[y^n](1-y+y^2)^(n-1)/(1-y)^(n+2); the simplified g.f. (1+x)(sqrt((1+x)/(1-3x))-1)/(2x); and a(n)=A163765(n) for n>=3.
- Missing cross-references: A005773, A163765, A048775, A001700.
- Side finding: Arndt's comment says 'length n+1', but the correct statement is length n with n+2 letters. The words in its own example have length n, and length n+1 gives A025565(n+2) instead. The corrected statement is proved in Section 7 of the proof.

A163765:
- The entry has only its definition and a cross-reference to A048775. New: A163765(n)=A225034(n)=A005773(n)+A005773(n+1) for n>=3, with A163765(1)=1 and A163765(2)=6. Its g.f. is A(x)-1-2x-x^2. For n>=3 it therefore counts 101-avoiding words. It satisfies Berselli's recurrence for n>=5.

A005773:
- It could get the cross-reference A005773(n)+A005773(n+1)=A225034(n) for n>=1.

Dependency: the A005773 link uses only the classical directed-animal g.f. (Dhar 1982; Gouyou-Beauchamps-Viennot 1988).

Scripts in /tmp/claude-0/deep/words101/: enum101.c, verify.py (log in verify.log), check_gf.gp, animals.py, arndt_check.py.

## hardin-table

- 证明状态：PROVED；复核：SOUND；查新：NEW
- 证明文件：`theorems/hardin-table/proof.md`

### What is new / suggested edits

Every formula in A253435 and its row, column and diagonal sequences is currently labeled "Empirical". This proves all of them:
- A253435's per-row and per-column closed forms, recurrences and the "summary table of c" (c = 28 for row 1 and column 1, 18 for column 2, 13 for column 3, 12 elsewhere);
- A253428 (diagonal 9*2^n + 12 for n > 3);
- A253152 (column 1);
- A253429-A253434 (columns 2-7: +36 for n > 3, +49 for n > 2, then 9*2^(n-1) + 9*2^(k-1) + 12 for n > 1);
- A253436-A253441 (rows 2-7: +30, +48, +84, +156, +300, +588 for k > 3);
- Colin Barker's empirical g.f.s.

It also gives one uniform formula for the whole table, T(n,k) = 9*2^(n-1) + 9*2^(k-1) + 12 for n >= 2 and k >= 4. That formula is symmetric in n and k even though the rule is not, which is explained by the explicit classification into row type and frozen type. The stated thresholds are shown to be sharp.

The A253435 formula line has a typo: "9*2(n-1)" should be 9*2^(n-1). A253152 is column 1 of A253435 because V3 is vacuous for two-column arrays; no cross-reference states this.
