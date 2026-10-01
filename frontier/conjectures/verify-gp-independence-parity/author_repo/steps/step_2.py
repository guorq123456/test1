"""
Independence Polynomials of Generalized Petersen Graphs
Step 2: Symmetry and Pattern Analysis
========================================================
Run this and share the output with me.
"""

import networkx as nx
from itertools import combinations
from collections import defaultdict

def generalized_petersen_graph(n, k):
    """Construct GP(n, k)."""
    G = nx.Graph()
    G.add_nodes_from(range(2 * n))
    for i in range(n):
        G.add_edge(i, (i + 1) % n)  # Outer cycle
        G.add_edge(n + i, n + ((i + k) % n))  # Inner star
        G.add_edge(i, n + i)  # Spokes
    return G


def independence_polynomial(G):
    """Compute independence polynomial, return coefficient dict."""
    nodes = list(G.nodes())
    n = len(nodes)
    counts = defaultdict(int)
    counts[0] = 1
    
    for size in range(1, n + 1):
        for subset in combinations(nodes, size):
            is_independent = True
            for i in range(len(subset)):
                for j in range(i + 1, len(subset)):
                    if G.has_edge(subset[i], subset[j]):
                        is_independent = False
                        break
                if not is_independent:
                    break
            if is_independent:
                counts[size] += 1
    
    return dict(counts)


def get_coefficients(counts, max_degree):
    """Extract coefficient list from counts dict."""
    coeffs = [counts.get(i, 0) for i in range(max_degree + 1)]
    while len(coeffs) > 1 and coeffs[-1] == 0:
        coeffs.pop()
    return coeffs


if __name__ == "__main__":
    print("=" * 70)
    print("STEP 2: SYMMETRY AND PATTERN ANALYSIS")
    print("=" * 70)
    
    # ===== PART A: Check GP(n, k) vs GP(n, n-k) symmetry =====
    print("\n" + "=" * 70)
    print("PART A: CHECKING GP(n, k) vs GP(n, n-k) SYMMETRY")
    print("=" * 70)
    
    for n in range(5, 11):
        print(f"\nn = {n}:")
        for k in range(1, n // 2 + 1):
            k2 = n - k
            if k2 != k and k2 < n:
                G1 = generalized_petersen_graph(n, k)
                G2 = generalized_petersen_graph(n, k2)
                
                counts1 = independence_polynomial(G1)
                counts2 = independence_polynomial(G2)
                
                coeffs1 = get_coefficients(counts1, 2*n)
                coeffs2 = get_coefficients(counts2, 2*n)
                
                same_poly = (coeffs1 == coeffs2)
                is_isomorphic = nx.is_isomorphic(G1, G2)
                
                print(f"  GP({n}, {k}) vs GP({n}, {k2}): same_poly={same_poly}, isomorphic={is_isomorphic}")
    
    # ===== PART B: Check palindromicity for GP(n, 1) =====
    print("\n" + "=" * 70)
    print("PART B: PALINDROMICITY CHECK FOR GP(n, 1)")
    print("=" * 70)
    
    for n in range(3, 12):
        G = generalized_petersen_graph(n, 1)
        counts = independence_polynomial(G)
        coeffs = get_coefficients(counts, 2*n)
        
        reversed_coeffs = coeffs[::-1]
        is_palindrome = (coeffs == reversed_coeffs)
        
        print(f"\nGP({n}, 1): n is {'odd' if n % 2 == 1 else 'even'}")
        print(f"  Coefficients: {coeffs}")
        print(f"  Reversed:     {reversed_coeffs}")
        print(f"  Palindromic: {is_palindrome}")
    
    # ===== PART C: Coefficient formulas for GP(n, 1) =====
    print("\n" + "=" * 70)
    print("PART C: COEFFICIENT FORMULAS FOR GP(n, 1)")
    print("=" * 70)
    
    print("\nCoefficient of x (should be 2n):")
    for n in range(3, 12):
        G = generalized_petersen_graph(n, 1)
        counts = independence_polynomial(G)
        coeff_x = counts.get(1, 0)
        expected = 2 * n
        match = (coeff_x == expected)
        print(f"  n={n}: coeff={coeff_x}, 2n={expected}, match={match}")
    
    print("\nCoefficient of x^2 (looking for formula):")
    for n in range(3, 12):
        G = generalized_petersen_graph(n, 1)
        counts = independence_polynomial(G)
        coeff_x2 = counts.get(2, 0)
        # Try some formulas
        formula1 = 2 * n * (n - 2)  # Guess
        formula2 = n * (2*n - 3)    # Another guess
        print(f"  n={n}: coeff={coeff_x2}, 2n(n-2)={formula1}, n(2n-3)={formula2}")
    
    # ===== PART D: Total independent sets and growth rate =====
    print("\n" + "=" * 70)
    print("PART D: TOTAL INDEPENDENT SETS I(GP(n,1), 1)")
    print("=" * 70)
    
    totals = []
    for n in range(3, 13):
        G = generalized_petersen_graph(n, 1)
        counts = independence_polynomial(G)
        total = sum(counts.values())
        totals.append((n, total))
        print(f"  GP({n}, 1): total = {total}")
    
    print("\nRatio of consecutive totals (looking for growth rate):")
    for i in range(1, len(totals)):
        n_prev, t_prev = totals[i-1]
        n_curr, t_curr = totals[i]
        ratio = t_curr / t_prev
        print(f"  I(GP({n_curr},1),1) / I(GP({n_prev},1),1) = {ratio:.6f}")
    
    print("\nNote: 1 + sqrt(2) = 2.414214...")
    
    print("\n" + "=" * 70)
    print("END OF STEP 2")
    print("=" * 70)