"""
Independence Polynomials of Generalized Petersen Graphs
Step 3: Recurrence Verification and Root Analysis
========================================================
Run this and share the output with me.
"""

import networkx as nx
from itertools import combinations
from collections import defaultdict
import cmath
import math

def generalized_petersen_graph(n, k):
    """Construct GP(n, k)."""
    G = nx.Graph()
    G.add_nodes_from(range(2 * n))
    for i in range(n):
        G.add_edge(i, (i + 1) % n)
        G.add_edge(n + i, n + ((i + k) % n))
        G.add_edge(i, n + i)
    return G


def independence_polynomial(G):
    """Compute independence polynomial, return coefficient dict."""
    nodes = list(G.nodes())
    n_nodes = len(nodes)
    counts = defaultdict(int)
    counts[0] = 1
    
    for size in range(1, n_nodes + 1):
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


def find_roots_numpy(coeffs):
    """Find roots of polynomial using numpy."""
    try:
        import numpy as np
        # numpy.roots expects coefficients in descending order
        roots = np.roots(coeffs[::-1])
        return roots
    except ImportError:
        return None


def find_roots_simple(coeffs):
    """
    Simple root finding for small polynomials using companion matrix.
    Returns list of complex roots.
    """
    try:
        import numpy as np
        if len(coeffs) <= 1:
            return []
        # Normalize so leading coeff is 1
        coeffs_normalized = [c / coeffs[-1] for c in coeffs[:-1]]
        n = len(coeffs_normalized)
        # Build companion matrix
        companion = np.zeros((n, n))
        companion[0, :] = [-c for c in reversed(coeffs_normalized)]
        for i in range(1, n):
            companion[i, i-1] = 1
        eigenvalues = np.linalg.eigvals(companion)
        return eigenvalues
    except ImportError:
        return None


if __name__ == "__main__":
    print("=" * 70)
    print("STEP 3: RECURRENCE VERIFICATION AND ROOT ANALYSIS")
    print("=" * 70)
    
    # ===== PART A: Verify recurrence for total independent sets =====
    print("\n" + "=" * 70)
    print("PART A: VERIFYING RECURRENCE a(n) = 2*a(n-1) + a(n-2) + 2*(-1)^n")
    print("=" * 70)
    
    # Compute totals
    totals = {}
    for n in range(3, 14):
        G = generalized_petersen_graph(n, 1)
        counts = independence_polynomial(G)
        totals[n] = sum(counts.values())
    
    print("\nTotal independent sets:")
    for n in sorted(totals.keys()):
        print(f"  a({n}) = {totals[n]}")
    
    print("\nVerifying recurrence a(n) = 2*a(n-1) + a(n-2) + 2*(-1)^n:")
    for n in range(5, 14):
        predicted = 2 * totals[n-1] + totals[n-2] + 2 * ((-1) ** n)
        actual = totals[n]
        match = (predicted == actual)
        sign = "+" if ((-1)**n) > 0 else "-"
        print(f"  a({n}) = 2*{totals[n-1]} + {totals[n-2]} {sign} 2 = {predicted}, actual = {actual}, MATCH = {match}")
    
    # ===== PART B: Independence number formula =====
    print("\n" + "=" * 70)
    print("PART B: INDEPENDENCE NUMBER alpha(GP(n, 1))")
    print("=" * 70)
    
    print("\nChecking if alpha = 2*floor(n/2) = n (even) or n-1 (odd):")
    for n in range(3, 14):
        G = generalized_petersen_graph(n, 1)
        counts = independence_polynomial(G)
        alpha = max(counts.keys())
        formula = 2 * (n // 2)
        formula_alt = n if n % 2 == 0 else n - 1
        print(f"  GP({n}, 1): alpha = {alpha}, 2*floor(n/2) = {formula}, match = {alpha == formula}")
    
    # ===== PART C: Leading coefficient formula =====
    print("\n" + "=" * 70)
    print("PART C: LEADING COEFFICIENT (# of maximum independent sets)")
    print("=" * 70)
    
    print("\nLeading coefficients for GP(n, 1):")
    for n in range(3, 14):
        G = generalized_petersen_graph(n, 1)
        counts = independence_polynomial(G)
        coeffs = get_coefficients(counts, 2*n)
        leading = coeffs[-1]
        # Check if it's 2 for even n, or 2n for odd n
        if n % 2 == 0:
            expected = 2
        else:
            expected = 2 * n
        print(f"  GP({n}, 1): leading_coeff = {leading}, expected (2 if even, 2n if odd) = {expected}, match = {leading == expected}")
    
    # ===== PART D: Root analysis =====
    print("\n" + "=" * 70)
    print("PART D: ROOT ANALYSIS")
    print("=" * 70)
    
    try:
        import numpy as np
        numpy_available = True
    except ImportError:
        numpy_available = False
        print("\nNumPy not available. Skipping root analysis.")
        print("Install with: pip install numpy")
    
    if numpy_available:
        print("\nRoots of I(GP(n, 1), x) - checking if all real:")
        for n in range(3, 12):
            G = generalized_petersen_graph(n, 1)
            counts = independence_polynomial(G)
            coeffs = get_coefficients(counts, 2*n)
            
            roots = find_roots_numpy(coeffs)
            if roots is not None:
                # Check if all roots are real (imaginary part < tolerance)
                tol = 1e-8
                max_imag = max(abs(r.imag) for r in roots)
                all_real = all(abs(r.imag) < tol for r in roots)
                all_negative = all(r.real < tol for r in roots)
                
                print(f"\n  GP({n}, 1): degree = {len(coeffs)-1}")
                print(f"    All roots real: {all_real} (max |Im| = {max_imag:.2e})")
                print(f"    All roots negative: {all_negative}")
                
                # Print roots
                real_roots = sorted([r.real for r in roots if abs(r.imag) < tol])
                complex_roots = [(r.real, r.imag) for r in roots if abs(r.imag) >= tol]
                
                if real_roots:
                    print(f"    Real roots: {[round(r, 4) for r in real_roots]}")
                if complex_roots:
                    print(f"    Complex roots: {[(round(re, 4), round(im, 4)) for re, im in complex_roots]}")
    
    # ===== PART E: Refined palindromicity check =====
    print("\n" + "=" * 70)
    print("PART E: REFINED PALINDROMICITY (excluding endpoints)")
    print("=" * 70)
    
    print("\nFor odd n: checking if [a_1, ..., a_alpha] is palindromic:")
    for n in [5, 7, 9, 11]:
        G = generalized_petersen_graph(n, 1)
        counts = independence_polynomial(G)
        coeffs = get_coefficients(counts, 2*n)
        inner = coeffs[1:]  # Exclude a_0 = 1
        is_palindrome = (inner == inner[::-1])
        print(f"  GP({n}, 1): inner coeffs = {inner}")
        print(f"           palindromic: {is_palindrome}")
    
    print("\nFor even n: checking if [a_1, ..., a_{alpha-1}] is palindromic:")
    for n in [4, 6, 8, 10]:
        G = generalized_petersen_graph(n, 1)
        counts = independence_polynomial(G)
        coeffs = get_coefficients(counts, 2*n)
        inner = coeffs[1:-1]  # Exclude a_0 = 1 and leading coeff
        is_palindrome = (inner == inner[::-1])
        print(f"  GP({n}, 1): inner coeffs = {inner}")
        print(f"           palindromic: {is_palindrome}")
    
    print("\n" + "=" * 70)
    print("END OF STEP 3")
    print("=" * 70)