"""Offline: the lethal search with another move order (spells first, those aimed at the enemy leader before the
rest; then the rest as now) at the agent's settings and a couple of budgets, on every start where find_lethal is
sure (lethal_miss.py's rows of step 1's self-play) and on the Pirate puzzle. Measurement only.
usage: lethal_order.py STEP1_DIR ROWS.jsonl [WORKERS]"""
import json, sys, time
from multiprocessing import Pool
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
S, ROWS = sys.argv[1:3]
sys.path.insert(0, f"{S}/ana")
from svsim.core.actions import Attack, EndTurn, Evolve, PlayCard
from svsim.core.engine import legal_actions
from svsim.search.lethal import LethalSearch


def rank_now(state, a):
    if isinstance(a, Attack):
        if a.target < 0:
            at = state.on_field(a.attacker)
            return (0, -(at.atk if at else 0), 0)
        return (4, 0, 0)
    if isinstance(a, PlayCard):
        return (1, 0, 0)
    if isinstance(a, Evolve):
        return (2, 0, 0)
    if isinstance(a, EndTurn):
        return (5, 0, 0)
    return (3, 0, 0)


def rank_spells(state, a):
    r = rank_now(state, a)
    if isinstance(a, PlayCard):
        c = state.in_hand(state.active, a.uid)
        spell = c is not None and c.defn.is_spell
        face = bool(a.targets) and min(a.targets) < 0
        return (1, 0 if spell and face else 1 if spell else 2, c.cost if c else 0)
    return r


class Ordered(LethalSearch):
    rank = staticmethod(rank_now)

    def _ordered(self, state):
        return sorted(legal_actions(state), key=lambda a: self.rank(state, a))


class Spells(Ordered):
    rank = staticmethod(rank_spells)


SETTINGS = {"agent": dict(max_nodes=2000, screen=200, near=(1000, 4)),
            "near3000": dict(max_nodes=2000, screen=200, near=(3000, 4)), "full": dict(max_nodes=20000)}
GAMES = None


def init():
    global GAMES
    import student_data as SD
    GAMES = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}


def job(row):
    import student_data as SD
    g, at = (int(x[1:]) if x[0] == "g" else int(x[2:]) for x in row["key"].split("|"))
    st = SD._state_at(GAMES[g], at)
    out = {"key": row["key"], "agent": row["agent"]}
    for name, kw in SETTINGS.items():
        for cls in (Ordered, Spells):
            t = time.perf_counter()
            r = cls(seed=0, **kw).solve(st.clone())
            out[f"{cls.__name__}:{name}"] = (r.sure, r.nodes, round((time.perf_counter() - t) * 1000))
    return out


if __name__ == "__main__":
    rows = [json.loads(l) for l in open(ROWS) if l.strip()]
    sure = [r for r in rows if r["src"] == "selfplay" and r.get("full")]
    with Pool(int(sys.argv[3]) if len(sys.argv) > 3 else 4, initializer=init) as pool:
        res = pool.map(job, sure, chunksize=4)
    summary = {}
    for name in SETTINGS:
        for cls in ("Ordered", "Spells"):
            k = f"{cls}:{name}"
            summary[k] = {"finds": sum(1 for r in res if r[k][0]),
                          "finds_where_agent_missed": sum(1 for r in res if r[k][0] and not r["agent"]),
                          "nodes_mean": round(sum(r[k][1] for r in res) / len(res), 1)}
    print(json.dumps({"sure_starts": len(res), "agent_found": sum(1 for r in res if r["agent"]), **summary}, indent=1))
    from svsim.tools.puzzles import puzzles
    build = {n: b for n, b, _ in puzzles()}["pirate-flags-lethal"]
    for name, kw in SETTINGS.items():
        for cls in (Ordered, Spells):
            r = cls(seed=0, **kw).solve(build(1))
            print("pirate puzzle", cls.__name__, name, r.sure, r.nodes)
