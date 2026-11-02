import sys, time
sys.path.insert(0, "/home/user/test1")
if __name__ == "__main__":
    from svsim.cards import decks
    from svsim.ui.session import DECKS
    from svsim.core.engine import new_game, apply, legal_actions
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    d = decks.build(DECKS["ramp"][1]); s = new_game(d, d, seed=3)
    g = make_agent("greedy", 0)
    n = 0
    while n < 40 or len(legal_actions(s)) < 4:
        apply(s, g.act(s, legal_actions(s))); n += 1
    print("legal", len(legal_actions(s)), "turn", s.turn)
    a = make_agent("level-strong+par=4", 1); srch = _search(a)
    t = time.perf_counter(); m1 = srch.choose(s.clone()); t1 = time.perf_counter() - t
    t = time.perf_counter(); m2 = srch.choose(s.clone()); t2 = time.perf_counter() - t
    print("par first (pool start)", round(t1, 2), "s; second", round(t2 * 1000), "ms; iterations", srch.last_iterations, "cpu", round(srch.last_cpu, 3))
    b = make_agent("level-strong+par=4", 1)
    print("same seed same move:", _search(b).choose(s.clone()) == m1)
    c = make_agent("level-strong", 1); sc = _search(c)
    t = time.perf_counter(); sc.choose(s.clone()); print("level-strong", round((time.perf_counter() - t) * 1000), "ms; iterations", sc.last_iterations)
    from svsim.search import parallel; parallel.shutdown()
