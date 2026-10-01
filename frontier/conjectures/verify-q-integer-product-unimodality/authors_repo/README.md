# Unimodality of $q$-Fibonomial Coefficients

Bergeron–Ceballos–Küstner introduced the $q$-Fibonomial coefficients $\binom{m+n}{n}_F$ and conjectured that they are unimodal. This paper proves the conjecture for $n \leq 3$. For $n = 2$, we give a combinatorial proof via a nearly symmetric saturated chain decomposition on path-domino tilings. For all three cases we give an algebraic proof, and for $n = 3$ we establish a more general unimodality result for certain products of $q$-analogs.

## Code

Computational verification that $\binom{m+n}{n}_F$ is unimodal for all tested $m, n \geq 1$, coded with the assistance of Claude (Anthropic).

- `fibonomial_test.py` — core utilities: Fibonacci numbers, $q$-Fibonomial computation, unimodality check
- `conjecture_test.py` — exhaustive test of Conjecture 2.5 for $m + n \leq 26$ and selected large pairs up to $(m, n) = (17, 16)$

```
python3 conjecture_test.py [max_sum]
```

Requires Python 3 and numpy.
