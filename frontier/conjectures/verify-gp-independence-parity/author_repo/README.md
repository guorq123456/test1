# Independence Polynomials of Generalized Petersen Graphs

This repository explores independence polynomials for generalized Petersen graphs GP(n, k) through brute-force enumeration, pattern detection, and root analysis. The scripts were used to verify conjectured formulas, symmetry properties, growth rates, and qualitative behaviors (log-concavity, unimodality, root locations).

## Repository Layout
- [steps/step_1.py](steps/step_1.py): Brute-force computation of independence polynomials for small GP(n, k); checks log-concavity and unimodality for k=1,2.
- [steps/step_2.py](steps/step_2.py): Symmetry GP(n, k) vs GP(n, n-k); palindromicity tests; low-degree coefficient formulas; growth rate estimates for k=1.
- [steps/step_3.py](steps/step_3.py): Recurrence verification for total independent sets a(n) with k=1, independence number formulas, leading coefficients, root analysis, refined palindromicity.
- [steps/step_4.py](steps/step_4.py): Detailed study for k=2 (totals, independence number formula floor(4n/5), coefficients, growth ratios) and root visualization; saves a root plot.
- [steps/step_5.py](steps/step_5.py): Additional families (k=3), comprehensive log-concavity sweep across k<=4, coefficient-of-x^2 derivation, and GP(n,2) vs GP(n,3) comparison.
- [plots/roots_plot.png](plots/roots_plot.png): Scatter plots of roots for GP(n,1) and GP(n,2) independence polynomials.
- [LICENSE](LICENSE): MIT License.

## Requirements
- Python 3.10+
- Packages: networkx (all steps); numpy (roots, plotting); matplotlib (plot export in step 4).
- Install into your environment:
  ```bash
  pip install networkx numpy matplotlib
  ```

## How to Run
- From the repo root, execute any step script directly, e.g.:
  ```bash
  python steps/step_1.py
  ```
- Steps are independent; run them in order for the narrative flow. Enumeration is exponential, so current ranges are modest (n up to ~13). Increasing n or k will grow runtime quickly.

## What Each Step Demonstrates
- **Step 1**: Baseline independence polynomials for GP(n,1) and GP(n,2); empirical log-concavity and unimodality.
- **Step 2**: GP(n,k) ≅ GP(n,n−k) symmetry; non-palindromic full coefficients for k=1 but inner-palindromic patterns hinted; closed forms for low-degree coefficients; growth ratios trending to 1+√2.
- **Step 3**: Recurrence a(n)=2 a(n−1)+a(n−2)+2(−1)^n for total independent sets (k=1); independence number α≈2⌊n/2⌋; leading-coefficient rule (2 if n even, 2n if odd); roots mostly negative with small imaginary parts for higher degrees; inner palindromicity confirmed.
- **Step 4**: For k=2, confirms α=floor(4n/5), provides totals, ratios, and log-concavity; generates and saves root plots at plots/roots_plot.png.
- **Step 5**: Extends checks to k=3 and broader k; verifies log-concavity across tested ranges; derives coefficient-of-x^2 formula 2n(n−2); compares GP(n,2) and GP(n,3) polynomials.

## Notes and Next Steps
- Brute-force enumeration is the bottleneck; replacing with dynamic programming over graph structure or transfer-matrix methods would scale to larger n.
- Roots beyond current ranges could be profiled for potential real-rootedness thresholds or bounds on imaginary parts.
- If you rerun plotting, confirm numpy and matplotlib are installed and that plots/ exists (it is created now).
