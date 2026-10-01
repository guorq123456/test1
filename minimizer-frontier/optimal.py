"""CP-SAT: minimum-density (w,k)-forward scheme over alphabet sigma (exact, all contexts)."""
import sys, time
import numpy as np
from ortools.sat.python import cp_model
from density import density_of, g_sigma, g_prime

def solve_forward(sigma, w, k, time_limit=600, workers=4, local=False, enumerate_all=False, target=None, log=False):
    L = w + k
    nW, nC = sigma ** (L - 1), sigma ** L
    m = cp_model.CpModel()
    # one-hot x[W][i]: window W selects offset i
    x = [[m.NewBoolVar(f"x{W}_{i}") for i in range(w)] for W in range(nW)]
    for W in range(nW):
        m.AddExactlyOne(x[W])
    unch = []
    for C in range(nC):
        pre, suf = C // sigma, C % nW
        if pre == suf:  # constant string a^L : always charged, nothing to do
            continue
        if not local:
            # forward: f(pre) - f(suf) <= 1  ->  forbid x[pre][i] & x[suf][j] with i - j >= 2
            for i in range(2, w):
                for j in range(0, i - 1):
                    m.AddBoolOr([x[pre][i].Not(), x[suf][j].Not()])
        # uncharged iff f(pre) == f(suf) + 1
        u = m.NewBoolVar(f"u{C}")
        ands = []
        for j in range(w - 1):
            a = m.NewBoolVar(f"a{C}_{j}")
            m.AddBoolAnd([x[pre][j + 1], x[suf][j]]).OnlyEnforceIf(a)
            m.AddBoolOr([x[pre][j + 1].Not(), x[suf][j].Not(), a])
            ands.append(a)
        m.AddMaxEquality(u, ands)
        unch.append(u)
    if target is not None:
        m.Add(sum(unch) == nC - target)
    else:
        m.Maximize(sum(unch))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    solver.parameters.log_search_progress = log
    if enumerate_all:
        solver.parameters.enumerate_all_solutions = True
        solver.parameters.num_workers = 1
        sols = []
        class CB(cp_model.CpSolverSolutionCallback):
            def on_solution_callback(self):
                f = np.array([next(i for i in range(w) if self.Value(x[W][i])) for W in range(nW)])
                sols.append(f)
        st = solver.Solve(m, CB())
        return st, sols
    st = solver.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return st, None, None
    f = np.array([next(i for i in range(w) if solver.Value(x[W][i])) for W in range(nW)])
    return st, f, solver.StatusName(st)

if __name__ == '__main__':
    sigma, w = int(sys.argv[1]), int(sys.argv[2])
    ks = [int(a) for a in sys.argv[3].split(',')]
    local = '--local' in sys.argv
    for k in ks:
        t = time.time()
        st, f, name = solve_forward(sigma, w, k, local=local, time_limit=float(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith('-') else 600)
        if f is None:
            print(f"sigma={sigma} w={w} k={k}: {st} no solution"); continue
        d, c, ok = density_of(f, sigma, w, k)
        L = w + k
        g, gp = g_sigma(sigma, w, k), g_prime(sigma, w, k)
        print(f"sigma={sigma} w={w} k={k} L={L} [{name} {time.time()-t:.1f}s] opt charged={c}/{sigma**L} density={d:.5f}  g={g:.5f} ({round(g*sigma**L)})  g'={gp:.5f} ({round(gp*sigma**L)})  tight={'YES' if c==round(gp*sigma**L) else 'no'} forward={ok}")
        np.save(f"opt_s{sigma}_w{w}_k{k}{'_local' if local else ''}.npy", f)
