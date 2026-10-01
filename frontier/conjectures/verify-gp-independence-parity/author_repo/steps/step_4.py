"""
Independence Polynomials of Generalized Petersen Graphs
Step 4: GP(n, 2) Analysis and Root Visualization
========================================================
Run this and share the output with me.
Requires: pip install numpy matplotlib
"""

import networkx as nx
from itertools import combinations
from collections import defaultdict
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


def check_log_concavity(coeffs):
    """Check if coefficient sequence is log-concave."""
    for i in range(1, len(coeffs) - 1):
        if coeffs[i]**2 < coeffs[i-1] * coeffs[i+1]:
            return False
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("STEP 4: GP(n, 2) ANALYSIS AND ROOT VISUALIZATION")
    print("=" * 70)
    
    # ===== PART A: GP(n, 2) coefficient analysis =====
    print("\n" + "=" * 70)
    print("PART A: GP(n, 2) FAMILY ANALYSIS")
    print("=" * 70)
    
    print("\nCoefficients for GP(n, 2):")
    gp2_data = {}
    for n in range(4, 13):
        G = generalized_petersen_graph(n, 2)
        counts = independence_polynomial(G)
        coeffs = get_coefficients(counts, 2*n)
        total = sum(counts.values())
        alpha = max(counts.keys())
        log_conc = check_log_concavity(coeffs)
        gp2_data[n] = {'coeffs': coeffs, 'total': total, 'alpha': alpha, 'log_conc': log_conc}
        
        print(f"\nGP({n}, 2):")
        print(f"  Coefficients: {coeffs}")
        print(f"  Total: {total}, Alpha: {alpha}, Log-concave: {log_conc}")
    
    # ===== PART B: Check known formula for alpha(GP(n, 2)) =====
    print("\n" + "=" * 70)
    print("PART B: INDEPENDENCE NUMBER alpha(GP(n, 2))")
    print("=" * 70)
    
    print("\nKnown: alpha(GP(n, 2)) = floor(4n/5) for n >= 5")
    for n in range(5, 13):
        alpha_computed = gp2_data[n]['alpha']
        alpha_formula = (4 * n) // 5
        match = (alpha_computed == alpha_formula)
        print(f"  GP({n}, 2): alpha = {alpha_computed}, floor(4n/5) = {alpha_formula}, match = {match}")
    
    # ===== PART C: Coefficient formulas for GP(n, 2) =====
    print("\n" + "=" * 70)
    print("PART C: COEFFICIENT FORMULAS FOR GP(n, 2)")
    print("=" * 70)
    
    print("\nCoefficient of x (should be 2n):")
    for n in range(4, 13):
        coeff_x = gp2_data[n]['coeffs'][1]
        expected = 2 * n
        print(f"  n={n}: coeff={coeff_x}, 2n={expected}, match={coeff_x == expected}")
    
    print("\nCoefficient of x^2:")
    for n in range(4, 13):
        coeff_x2 = gp2_data[n]['coeffs'][2]
        # For GP(n,2), the graph has different structure, try some formulas
        formula1 = 2 * n * (n - 2)  # Same as GP(n,1)?
        print(f"  n={n}: coeff={coeff_x2}, 2n(n-2)={formula1}")
    
    # ===== PART D: Growth rate for GP(n, 2) =====
    print("\n" + "=" * 70)
    print("PART D: GROWTH RATE FOR GP(n, 2)")
    print("=" * 70)
    
    print("\nTotal independent sets and ratios:")
    totals = [gp2_data[n]['total'] for n in range(4, 13)]
    for i, n in enumerate(range(4, 13)):
        print(f"  GP({n}, 2): total = {totals[i]}")
    
    print("\nRatios:")
    for i in range(1, len(totals)):
        ratio = totals[i] / totals[i-1]
        print(f"  Ratio {i+4}/{i+3} = {ratio:.6f}")
    
    # ===== PART E: Root analysis for GP(n, 2) =====
    print("\n" + "=" * 70)
    print("PART E: ROOT ANALYSIS FOR GP(n, 2)")
    print("=" * 70)
    
    try:
        import numpy as np
        numpy_available = True
    except ImportError:
        numpy_available = False
        print("\nNumPy not available.")
    
    if numpy_available:
        print("\nRoots of I(GP(n, 2), x):")
        for n in range(4, 11):
            coeffs = gp2_data[n]['coeffs']
            roots = np.roots(coeffs[::-1])
            
            tol = 1e-8
            max_imag = max(abs(r.imag) for r in roots)
            all_real = all(abs(r.imag) < tol for r in roots)
            all_negative = all(r.real < tol for r in roots)
            
            print(f"\n  GP({n}, 2): degree = {len(coeffs)-1}")
            print(f"    All roots real: {all_real} (max |Im| = {max_imag:.2e})")
            print(f"    All roots negative: {all_negative}")
    
    # ===== PART F: Generate root plot data =====
    print("\n" + "=" * 70)
    print("PART F: ROOT PLOT DATA")
    print("=" * 70)
    
    if numpy_available:
        print("\nGenerating root data for plotting...")
        
        # GP(n, 1) roots
        print("\n--- GP(n, 1) roots ---")
        for n in range(3, 12):
            G = generalized_petersen_graph(n, 1)
            counts = independence_polynomial(G)
            coeffs = get_coefficients(counts, 2*n)
            roots = np.roots(coeffs[::-1])
            
            print(f"GP({n}, 1):")
            for r in sorted(roots, key=lambda x: (x.real, x.imag)):
                print(f"  ({r.real:.6f}, {r.imag:.6f})")
        
        # Create plot if matplotlib available
        try:
            import matplotlib.pyplot as plt
            
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Plot GP(n, 1) roots
            ax1 = axes[0]
            colors = plt.cm.viridis([i/9 for i in range(9)])
            for idx, n in enumerate(range(3, 12)):
                G = generalized_petersen_graph(n, 1)
                counts = independence_polynomial(G)
                coeffs = get_coefficients(counts, 2*n)
                roots = np.roots(coeffs[::-1])
                
                ax1.scatter([r.real for r in roots], [r.imag for r in roots], 
                           c=[colors[idx]], label=f'n={n}', alpha=0.7, s=50)
            
            ax1.axhline(y=0, color='k', linewidth=0.5)
            ax1.axvline(x=0, color='k', linewidth=0.5)
            ax1.set_xlabel('Real part')
            ax1.set_ylabel('Imaginary part')
            ax1.set_title('Roots of I(GP(n, 1), x)')
            ax1.legend(loc='upper left', fontsize=8)
            ax1.grid(True, alpha=0.3)
            
            # Plot GP(n, 2) roots
            ax2 = axes[1]
            colors = plt.cm.plasma([i/7 for i in range(7)])
            for idx, n in enumerate(range(4, 11)):
                coeffs = gp2_data[n]['coeffs']
                roots = np.roots(coeffs[::-1])
                
                ax2.scatter([r.real for r in roots], [r.imag for r in roots], 
                           c=[colors[idx]], label=f'n={n}', alpha=0.7, s=50)
            
            ax2.axhline(y=0, color='k', linewidth=0.5)
            ax2.axvline(x=0, color='k', linewidth=0.5)
            ax2.set_xlabel('Real part')
            ax2.set_ylabel('Imaginary part')
            ax2.set_title('Roots of I(GP(n, 2), x)')
            ax2.legend(loc='upper left', fontsize=8)
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('roots_plot.png', dpi=150, bbox_inches='tight')
            print("\nSaved plot to 'roots_plot.png'")
            plt.close()
            
        except ImportError:
            print("\nMatplotlib not available. Install with: pip install matplotlib")
    
    print("\n" + "=" * 70)
    print("END OF STEP 4")
    print("=" * 70)