"""For each optimal P(nu) solution (restricted SAT), test whether it is a threshold function of the
alternating-flipped bits (LP feasibility, margin 1)."""
import sys, numpy as np
from ortools.linear_solver import pywraplp
from w2 import solve
from pnu import alt_vec, excess

def is_threshold(h, nu):
    s = pywraplp.Solver.CreateSolver('GLOP')
    a = [s.NumVar(-100, 100, f'a{i}') for i in range(nu)]
    th = s.NumVar(-100, 100, 'th')
    for W in range(1 << nu):
        v = alt_vec(W, nu)
        expr = sum(a[i] * v[i] for i in range(nu))
        if h[W]: s.Add(expr >= th + 1)
        else: s.Add(expr <= th - 1)
    s.Minimize(sum(a))
    st = s.Solve()
    if st in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return [round(x.solution_value(), 3) for x in a], round(th.solution_value(), 3)
    return None

nu = int(sys.argv[1]); cap = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
# restricted solutions of k'=nu : c over (nu+1)-bit windows ignoring last bit -> h over nu bits
sols = solve(nu, True, enumerate_all=True, cap=cap)
found = 0
for c in sols:
    h = np.array([c[W << 1] for W in range(1 << nu)])
    assert excess(h, nu) == 0
    r = is_threshold(h, nu)
    if r is not None:
        found += 1
        if found <= 12: print(f"  threshold solution: weights={r[0]} theta={r[1]}")
print(f"nu={nu}: {len(sols)} solutions, {found} are alternating-threshold functions")
