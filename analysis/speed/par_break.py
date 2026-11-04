"""Where +par=4's overhead goes: per searched decision, wall of the parallel choose, the trees' mean and max CPU,
the pickled state's size and time, against level-strong's single tree (same starts, first decision of the turn)."""
import json, pickle, sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2])); sys.path.insert(0, sys.argv[1] + "/ana")


def main():
    import student_data as SD
    from svsim.search import parallel
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    d, N = sys.argv[1], int(sys.argv[2])
    games = {r["g"]: r for r in SD._lines(f"{d}/selfplay.jsonl")}
    starts = list(SD._lines(f"{d}/starts.jsonl"))[:N]
    par = _search(make_agent("level-strong+par=4", 1))
    one = _search(make_agent("level-strong", 1))
    s0 = SD._state_at(games[starts[0]["game"]], starts[0]["at"])
    par.choose(s0.clone())                                # pool start
    orig = parallel._tree
    tot = {"par_wall": 0.0, "tree_cpu_mean": 0.0, "tree_cpu_max": 0.0, "one_wall": 0.0, "one_cpu": 0.0,
           "pickle_ms": 0.0, "pickle_kb": 0.0}
    for r in starts:
        s = SD._state_at(games[r["game"]], r["at"])
        t = time.perf_counter(); b = pickle.dumps(s); tot["pickle_ms"] += 1e3 * (time.perf_counter() - t)
        tot["pickle_kb"] += len(b) / 1024
        t = time.perf_counter(); par.choose(s.clone()); tot["par_wall"] += time.perf_counter() - t
        cpus = par.last_tree_cpu
        tot["tree_cpu_mean"] += sum(cpus) / len(cpus); tot["tree_cpu_max"] += max(cpus)
        t, c = time.perf_counter(), time.process_time(); one.choose(s.clone())
        tot["one_wall"] += time.perf_counter() - t; tot["one_cpu"] += time.process_time() - c
    n = len(starts)
    print(json.dumps({k: round(1e3 * v / n, 2) if k not in ("pickle_ms", "pickle_kb") else round(v / n, 2)
                      for k, v in tot.items()}))
    parallel.shutdown()


if __name__ == "__main__":
    main()
