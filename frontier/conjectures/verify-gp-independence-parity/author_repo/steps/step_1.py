"""
Independence Polynomials of Generalized Petersen Graphs
Step 1: Basic computation for small cases
========================================================
Run this and share the output with me.
"""

import networkx as nx
from itertools import combinations
from collections import defaultdict

def generalized_petersen_graph(n, k):
    """
    Construct the generalized Petersen graph GP(n, k).
    
    Vertices 0, 1, ..., n-1 form the outer cycle.
    Vertices n, n+1, ..., 2n-1 form the inner "star polygon".
    Outer vertex i connects to inner vertex n+i.
    Inner vertices form a cycle where n+i connects to n+((i+k) mod n).
    """
    G = nx.Graph()
    G.add_nodes_from(range(2 * n))
    
    # Outer cycle: 0-1-2-..-(n-1)-0
    for i in range(n):
        G.add_edge(i, (i + 1) % n)
    
    # Inner star polygon: n+i connects to n+((i+k) mod n)
    for i in range(n):
        G.add_edge(n + i, n + ((i + k) % n))
    
    # Spokes: i connects to n+i
    for i in range(n):
        G.add_edge(i, n + i)
    
    return G


def independence_polynomial_bruteforce(G):
    """
    Compute the independence polynomial by brute force enumeration.
    I(G, x) = sum over all independent sets S of x^|S|
    
    Returns: (polynomial_string, coefficient_dict)
    """
    nodes = list(G.nodes())
    n = len(nodes)
    
    # Count independent sets of each size
    counts = defaultdict(int)
    counts[0] = 1  # Empty set
    
    for size in range(1, n + 1):
        for subset in combinations(nodes, size):
            # Check if subset is independent (no edges within it)
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
    
    # Build polynomial string
    terms = []
    for k in sorted(counts.keys(), reverse=True):
        if counts[k] == 0:
            continue
        if k == 0:
            terms.append("1")
        elif k == 1:
            terms.append(f"{counts[k]}*x")
        else:
            terms.append(f"{counts[k]}*x^{k}")
    
    poly_str = " + ".join(terms) if terms else "0"
    
    return poly_str, dict(counts)


def get_coefficients(counts, max_degree):
    """Extract coefficient list [a_0, a_1, ..., a_max] from counts dict."""
    coeffs = [counts.get(i, 0) for i in range(max_degree + 1)]
    # Remove trailing zeros
    while len(coeffs) > 1 and coeffs[-1] == 0:
        coeffs.pop()
    return coeffs


def check_log_concavity(coeffs):
    """Check if coefficient sequence is log-concave: a_i^2 >= a_{i-1} * a_{i+1}"""
    for i in range(1, len(coeffs) - 1):
        if coeffs[i]**2 < coeffs[i-1] * coeffs[i+1]:
            return False
    return True


def check_unimodality(coeffs):
    """Check if coefficients increase then decrease (unimodal)."""
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
    print("INDEPENDENCE POLYNOMIALS OF GENERALIZED PETERSEN GRAPHS")
    print("Step 1: Basic Computation")
    print("=" * 70)
    
    # Test GP(n, 1) family
    print("\n--- GP(n, 1) Family ---")
    for n in range(3, 10):
        G = generalized_petersen_graph(n, 1)
        poly_str, counts = independence_polynomial_bruteforce(G)
        coeffs = get_coefficients(counts, 2*n)
        log_conc = check_log_concavity(coeffs)
        unimodal = check_unimodality(coeffs)
        
        print(f"\nGP({n}, 1):")
        print(f"  Vertices: {2*n}, Edges: {G.number_of_edges()}")
        print(f"  Polynomial: {poly_str}")
        print(f"  Coefficients: {coeffs}")
        print(f"  Log-concave: {log_conc}, Unimodal: {unimodal}")
    
    # Test GP(n, 2) family
    print("\n\n--- GP(n, 2) Family ---")
    for n in range(4, 10):
        G = generalized_petersen_graph(n, 2)
        poly_str, counts = independence_polynomial_bruteforce(G)
        coeffs = get_coefficients(counts, 2*n)
        log_conc = check_log_concavity(coeffs)
        unimodal = check_unimodality(coeffs)
        
        print(f"\nGP({n}, 2):")
        print(f"  Vertices: {2*n}, Edges: {G.number_of_edges()}")
        print(f"  Polynomial: {poly_str}")
        print(f"  Coefficients: {coeffs}")
        print(f"  Log-concave: {log_conc}, Unimodal: {unimodal}")
    
    print("\n" + "=" * 70)
    print("END OF STEP 1")
    print("=" * 70)