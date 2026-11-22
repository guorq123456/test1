"""python tools/probe_period_games.py G REPS PERIODS [PROTECT]   (11-22, Salem 问每期 100 局; LEDGER LD-30)
Made-up games: how well CR separates known strengths when each member plays G games a period.
Rules from ladder/rules.py and ladder/pool.pick_opponent (S2); protection/removal as pool.py; period ends when every
member has G decided games this period (A14), or all short members are isolated (A27)."""
import random, statistics as st, sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[2])]
from ladder import rules, pool as P

class M:
    def __init__(s, mid, craft, strength, base=False):
        s.mid, s.craft, s.strength, s.base = mid, craft, strength, base
        s.cr, s.games, s.period_games, s.full = 1500, 0, 0, False
        s.pts = []
    @property
    def protected(s):
        return s.games < P_PROTECT or not s.full

def prob(a, b):
    return min(0.98, max(0.02, 0.5 + a - b))

def isolated(act):
    return [m for m in act if not any(o is not m and abs(m.cr - o.cr) <= 200 for o in act)]

def run(G, periods, rng, n_new=35, spread=0.05):
    act, n = [], 0
    for c in range(1, 8):                       # 7 baselines, strength 0, long played (CR ~1500)
        b = M(f"b{c}", c, 0.0, True); b.games = 10000; b.full = True; act.append(b)
    out = []
    for per in range(1, periods + 1):
        if per % 2 == 1:                        # deck period: 35 new members (5 players x 7 classes)
            for i in range(n_new):
                n += 1
                act.append(M(f"p{n}", 1 + i % 7, max(-0.15, min(0.2, rng.gauss(0.0, spread)))))
        for m in act:
            m.period_games = 0
        played = 0
        while True:
            short = [m for m in act if m.period_games < G]
            if not short:
                break
            if played % 100 == 0:
                iso = set(map(id, isolated(act)))
                if all(id(m) in iso for m in short):
                    break
            mu = sum(m.cr for m in act) / len(act)
            cands = list(act)
            while True:
                a = rng.choices(cands, weights=[rules.effective_weight(m.cr, mu, m.protected) for m in cands])[0]
                try:
                    b, _ = P.pick_opponent(a, act, mu, rng)
                    break
                except P.NoOpponent:
                    cands.remove(a)
            aw = rng.random() < prob(a.strength, b.strength)
            a.cr, b.cr = rules.settle(a.cr, b.cr, aw)
            for m in (a, b):
                m.games += 1; m.period_games += 1; m.pts.append(m.cr)
            played += 1
            mu = sum(m.cr for m in act) / len(act)
            act = [m for m in act if not rules.to_remove(m.cr, mu, m.protected)] or act
        if per % 2 == 0:
            for m in act:
                m.full = True
        mu = sum(m.cr for m in act) / len(act)
        smean = st.mean(m.strength for m in act)
        rows = []
        for m in act:
            tail = m.pts[-1000:] or [m.cr]
            rows.append((m, m.cr - mu, sum(tail) / len(tail) - mu, (m.strength - smean) * 100))
        out.append({"period": per, "members": len(act), "games": played, "rows": rows})
    return out

def pair_acc(rows, idx, gap_lo, gap_hi):
    """Same class, true gap in [gap_lo, gap_hi) pp: share where the stronger has the higher reading."""
    ok = tot = 0
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if a[0].craft != b[0].craft:
                continue
            g = a[3] - b[3]
            if gap_lo <= abs(g) < gap_hi:
                tot += 1
                ok += (a[idx] - b[idx]) * g > 0
    return ok, tot

def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
        for k, i in enumerate(o): r[i] = k
        return r
    rx, ry = rk(x), rk(y)
    return st.correlation(rx, ry)

if __name__ == "__main__":
    G = int(sys.argv[1]); reps = int(sys.argv[2]); periods = int(sys.argv[3])
    P_PROTECT = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
    res = {}
    for r in range(reps):
        rng = random.Random(f"pg:{G}:{r}")
        for o in run(G, periods, rng):
            d = res.setdefault(o["period"], {"members": [], "games": [], "rho_now": [], "rho_1000": [],
                                             "res_now": [], "res_1000": [], "acc3_now": [0, 0], "acc5_now": [0, 0],
                                             "acc10_now": [0, 0], "acc5_1000": [0, 0], "acc10_1000": [0, 0],
                                             "res_new": []})
            rows = o["rows"]
            d["members"].append(o["members"]); d["games"].append(o["games"])
            for idx, key in ((1, "now"), (2, "1000")):
                d[f"rho_{key}"].append(spearman([x[idx] for x in rows], [x[3] for x in rows]))
                # residual around the rule's line: 8.5 CR per pp
                d[f"res_{key}"].append(st.pstdev([x[idx] - 8.5 * x[3] for x in rows]))
            for lo, hi, k in ((2, 4, "acc3_now"), (4, 6, "acc5_now"), (8, 12, "acc10_now")):
                a, t = pair_acc(rows, 1, lo, hi); d[k][0] += a; d[k][1] += t
            for lo, hi, k in ((4, 6, "acc5_1000"), (8, 12, "acc10_1000")):
                a, t = pair_acc(rows, 2, lo, hi); d[k][0] += a; d[k][1] += t
            newest = [x for x in rows if not x[0].base and x[0].games < 2 * G + 200]
    summary = {}
    for p, d in sorted(res.items()):
        summary[p] = {"members": st.mean(d["members"]), "games": round(st.mean(d["games"])),
                      "rho_now": round(st.mean(d["rho_now"]), 3), "rho_last1000": round(st.mean(d["rho_1000"]), 3),
                      "resid_sd_now_cr": round(st.mean(d["res_now"]), 1),
                      "resid_sd_last1000_cr": round(st.mean(d["res_1000"]), 1),
                      **{k: round(d[k][0] / d[k][1], 3) for k in ("acc3_now", "acc5_now", "acc10_now", "acc5_1000",
                                                                  "acc10_1000") if d[k][1]}}
    print(json.dumps({"G": G, "reps": reps, "protect": P_PROTECT, "by_period": summary}, indent=1))
