import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
from sympy.abc import x

# --- SETTINGS FOR BETTER LEGIBILITY ---
plt.rcParams.update({
    'font.size': 18,          # Was 14, make it 18 or 20
    'axes.titlesize': 20,     # Was 16
    'axes.labelsize': 18,     # Was 14
    'legend.fontsize': 16,    # Was 12 <--- This is the most important one
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'lines.markersize': 10    # Make dots slightly bigger too
})

def build_transfer_matrix(k):
    """Builds the Transfer Matrix T for GP(n, k)."""
    num_vars = k + 1
    states = []
    
    for i in range(2**num_vars):
        bin_str = format(i, f'0{num_vars}b')
        state = tuple(map(int, bin_str))
        states.append(state)
        
    dim = len(states)
    T = sp.zeros(dim, dim)
    
    for i, current_state in enumerate(states):
        u_prev = current_state[0]
        v_prev_seq = current_state[1:]
        
        for j, next_state in enumerate(states):
            u_curr = next_state[0]
            v_curr_seq = next_state[1:]
            
            if v_curr_seq[1:] != v_prev_seq[:-1]:
                continue
            
            v_curr = v_curr_seq[0]
            v_oldest = v_prev_seq[-1]
            
            if u_curr == 1 and v_curr == 1: continue
            if u_prev == 1 and u_curr == 1: continue
            if v_curr == 1 and v_oldest == 1: continue
            
            weight = x**(u_curr + v_curr)
            T[j, i] = weight 
            
    return T

def compute_all_roots():
    """Computes roots for all configs and returns them."""
    configs = [
        (30, 1, 'GP(30,1) - Prism'),
        (25, 2, 'GP(25,2) - Petersen'), 
        (20, 3, 'GP(20,3) - Odd k'),  
        (20, 4, 'GP(20,4) - Even k')   
    ]
    
    results = []
    
    for n, k, label in configs:
        print(f"Processing {label}...")
        T = build_transfer_matrix(k)
        
        # Calculate Trace(T^n)
        poly = (T**n).trace()
        
        # Get coefficients and roots
        coeffs = sp.Poly(poly, x).all_coeffs()
        coeffs_float = [float(c) for c in coeffs]
        roots = np.roots(coeffs_float)
        
        results.append((label, roots))
        
    return results

def plot_full_view(data):
    """Generates the zoomed-out view showing large negative roots."""
    plt.figure(figsize=(10, 6), dpi=300)
    
    for label, roots in data:
        plt.scatter(roots.real, roots.imag, label=label, alpha=0.7, s=40, edgecolors='none')

    plt.axhline(0, color='black', linewidth=0.8)
    plt.axvline(0, color='black', linewidth=0.8)
    
    plt.title("Full Distribution of Roots (Zoomed Out)")
    plt.xlabel("Re(z)")
    plt.ylabel("Im(z)")
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # Let matplotlib auto-scale to show the far left roots (e.g. -1600)
    plt.tight_layout()
    plt.savefig('roots_full.png')
    print("Saved roots_full.png")

def plot_zoomed_view(data):
    """Generates the zoomed-in view near the origin."""
    plt.figure(figsize=(10, 8), dpi=300) # Taller aspect ratio for detail
    
    for label, roots in data:
        plt.scatter(roots.real, roots.imag, label=label, alpha=0.7, s=50, edgecolors='none')

    plt.axhline(0, color='black', linewidth=0.8)
    plt.axvline(0, color='black', linewidth=0.8)

    # STRICT ZOOM LIMITS
    plt.xlim(-12, 2)  
    plt.ylim(-8, 8)

    plt.title("Detail of Roots Near Origin")
    plt.xlabel("Re(z)")
    plt.ylabel("Im(z)")
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('roots_zoom.png')
    print("Saved roots_zoom.png")

# --- EXECUTE ---
if __name__ == "__main__":
    print("Computing roots... (this may take 10-20 seconds)")
    all_data = compute_all_roots()
    
    print("Generating plots...")
    plot_full_view(all_data)
    plot_zoomed_view(all_data)
    print("Done!")