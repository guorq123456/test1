"""
Independence Polynomials of Generalized Petersen Graphs
Step 5: Final Verification and Summary
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


def check_log_concavity(coeffs):
    """Check if coefficient sequence is log-concave."""
    for i in range(1, len(coeffs) - 1):
        if coeffs[i]**2 < coeffs[i-1] * coeffs[i+1]:
            return False
    return True


def check_unimodality(coeffs):
    """Check if coefficients are unimodal."""
    increasing = True
    for i in range(1, len(coeffs)):
        if increasing:
            if coeffs[i] < coeffs[i-1]:
                increasing = False
        else:
            if coeffs[i] > coeffs[i-1]:
                return False
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("STEP 5: FINAL VERIFICATION AND SUMMARY")
    print("=" * 70)
    
    # ===== PART A: GP(n, 3) Family =====
    print("\n" + "=" * 70)
    print("PART A: GP(n, 3) FAMILY")
    print("=" * 70)
    
    print("\nCoefficients for GP(n, 3):")
    for n in range(7, 13):  # Need n > 2k, so n >= 7 for k=3
        G = generalized_petersen_graph(n, 3)
        counts = independence_polynomial(G)
        coeffs = get_coefficients(counts, 2*n)
        total = sum(counts.values())
        alpha = max(counts.keys())
        log_conc = check_log_concavity(coeffs)
        unimodal = check_unimodality(coeffs)
        
        print(f"\nGP({n}, 3):")
        print(f"  Coefficients: {coeffs}")
        print(f"  Total: {total}, Alpha: {alpha}")
        print(f"  Log-concave: {log_conc}, Unimodal: {unimodal}")
    
    # ===== PART B: Comprehensive Log-Concavity Check =====
    print("\n" + "=" * 70)
    print("PART B: COMPREHENSIVE LOG-CONCAVITY CHECK")
    print("=" * 70)
    
    print("\nChecking log-concavity for GP(n, k) with various n, k:")
    all_log_concave = True
    tested_cases = []
    
    for k in range(1, 5):
        for n in range(max(3, 2*k+1), 14):
            G = generalized_petersen_graph(n, k)
            counts = independence_polynomial(G)
            coeffs = get_coefficients(counts, 2*n)
            log_conc = check_log_concavity(coeffs)
            tested_cases.append((n, k, log_conc))
            
            if not log_conc:
                all_log_concave = False
                print(f"  GP({n}, {k}): Log-concave = {log_conc} <-- COUNTEREXAMPLE!")
    
    if all_log_concave:
        print(f"  All {len(tested_cases)} tested cases are log-concave!")
    
    print(f"\nTotal cases tested: {len(tested_cases)}")
    print(f"All log-concave: {all_log_concave}")
    
    # ===== PART C: Coefficient of x^2 Investigation =====
    print("\n" + "=" * 70)
    print("PART C: COEFFICIENT OF x^2 ANALYSIS")
    print("=" * 70)
    
    print("\nThe coefficient of x^2 counts pairs of non-adjacent vertices.")
    print("For GP(n, k), the graph has 2n vertices and 3n edges.")
    print("Total pairs = C(2n, 2) = n(2n-1)")
    print("Adjacent pairs = 3n (number of edges)")
    print("Non-adjacent pairs = n(2n-1) - 3n = 2n^2 - 4n = 2n(n-2)")
    
    print("\nVerifying for GP(n, 1):")
    for n in range(3, 12):
        G = generalized_petersen_graph(n, 1)
        counts = independence_polynomial(G)
        coeff = counts.get(2, 0)
        formula = 2 * n * (n - 2)
        num_edges = G.number_of_edges()
        total_pairs = n * (2*n - 1)
        non_adj = total_pairs - num_edges
        print(f"  GP({n}, 1): coeff={coeff}, 2n(n-2)={formula}, edges={num_edges}, C(2n,2)-edges={non_adj}")
    
    print("\nVerifying for GP(n, 2):")
    for n in range(4, 12):
        G = generalized_petersen_graph(n, 2)
        counts = independence_polynomial(G)
        coeff = counts.get(2, 0)
        formula = 2 * n * (n - 2)
        num_edges = G.number_of_edges()
        total_pairs = n * (2*n - 1)
        non_adj = total_pairs - num_edges
        print(f"  GP({n}, 2): coeff={coeff}, 2n(n-2)={formula}, edges={num_edges}, C(2n,2)-edges={non_adj}")
    
    # ===== PART D: Check GP(n,2) vs GP(n,3) equality =====
    print("\n" + "=" * 70)
    print("PART D: CHECKING IF GP(n, 2) AND GP(n, 3) HAVE SAME POLYNOMIAL")
    print("=" * 70)
    
    for n in range(7, 12):
        G2 = generalized_petersen_graph(n, 2)
        G3 = generalized_petersen_graph(n, 3)
        
        counts2 = independence_polynomial(G2)
        counts3 = independence_polynomial(G3)
        
        coeffs2 = get_coefficients(counts2, 2*n)
        coeffs3 = get_coefficients(counts3, 2*n)
        
        same = (coeffs2 == coeffs3)
        iso = nx.is_isomorphic(G2, G3)
        
        print(f"  GP({n}, 2) vs GP({n}, 3): same_poly={same}, isomorphic={iso}")
        if same:
            print(f"    Polynomial: {coeffs2}")
    
    # ===== PART E: Summary of All Results =====
    print("\n" + "=" * 70)
    print("PART E: SUMMARY OF ALL VERIFIED RESULTS")
    print("=" * 70)