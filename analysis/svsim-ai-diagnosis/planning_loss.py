"""Exp B: within-turn planning loss. With the same evaluation, how close do the
agents get to the best end of turn? The best is found by exhaustive search over
every order of the turn's actions (transposition table on search.lethal.state_key).
It runs on the true position, so lines with draws or random effects are judged
with the real outcome (an upper bound); `chb`/`chm`/`chx` flag those lines so the
deterministic turns can be compared on their own.

Agents: one-step greedy, ISMCTS:200 and :800 (the repo's, centring and pruning on),
and ISMCTS:200 with max backup (variants.MaxISMCTS).

    PYTHONPATH=<svsim checkout>:. python planning_loss.py positions.pkl out.pkl 20000
"""
from svsim.cards import library as _lib, decks as _decks  # register every card script

import pickle, sys, math, random, time
from multiprocessing import Pool
from svsim.core.engine import apply, legal_actions
from svsim.core.actions import EndTurn, Attack, Evolve, PlayCard
from svsim.search.evaluate import evaluate, after_end_of_turn, DEFAULT, WIN
from svsim.search.lethal import state_key
from svsim.learn.model import Learned, deck_craft
from svsim.core.enums import Craft
from svsim.agents.greedy_agent import GreedyAgent
from svsim.agents.mcts_agent import MCTSAgent
from svsim.ui.text import describe
from svsim.search.lethal import hidden_info
from variants import MaxISMCTS, Agent
from svsim.search.mcts import ISMCTS

BUDGET = int(sys.argv[3]) if len(sys.argv) > 3 else 20000

def end_value(s, me, w):
    if s.over:
        return WIN if s.winner == me else -WIN
    e = after_end_of_turn(s)
    return evaluate(e, me, w)

def best_turn(state, w):
    me = state.active
    tt, nodes = {}, [0]
    def dfs(s):
        if s.over or s.active != me:
            return (WIN if s.winner == me else -WIN) if s.over else evaluate(s, me, w), []
        k = state_key(s)
        if k in tt:
            return tt[k]
        nodes[0] += 1
        best = (end_value(s, me, w), [EndTurn()])
        if nodes[0] < BUDGET:
            for a in legal_actions(s):
                if isinstance(a, EndTurn):
                    continue
                t = s.clone(); apply(t, a)
                v, line = dfs(t)
                if v > best[0] + 1e-9:
                    best = (v, [a] + line)
        tt[k] = best
        return best
    v, line = dfs(state.clone())
    return v, line, nodes[0] < BUDGET

CH = [False]           # set when an action on the line changed hidden info (draw, random effect)


def play_turn(state, agent, w, cap=60):
    s, me, line = state.clone(), state.active, []
    for _ in range(cap):
        if s.over or s.active != me:
            break
        a = agent.act(s, legal_actions(s))
        line.append((s.clone(), a))
        if isinstance(a, EndTurn):
            break
        h = hidden_info(s); apply(s, a)
        if hidden_info(s) != h: CH[0] = True
    return end_value(s, me, w), line

def job(arg):
    i, s, wname = arg
    w = Learned(fallback=DEFAULT) if wname == "L" else DEFAULT
    t = time.time()
    vbest, bline, complete = best_turn(s, w)
    tb = time.time() - t
    CH[0] = False; vg, gline = play_turn(s, GreedyAgent(i, weights=w), w)
    CH[0] = False; vm, mline = play_turn(s, MCTSAgent(200, seed=i, weights=w), w); chm = CH[0]
    CH[0] = False; vm8, _ = play_turn(s, MCTSAgent(800, seed=i, weights=w), w); chm8 = CH[0]
    CH[0] = False; vx, xline = play_turn(s, Agent(MaxISMCTS(iterations=200, seed=i, weights=w)), w); chx = CH[0]
    # chance along the best line
    st2 = s.clone(); chb = False
    for a in bline:
        if st2.over or st2.active != s.active or isinstance(a, EndTurn): break
        h = hidden_info(st2); apply(st2, a); chb |= hidden_info(st2) != h
    # immediate one-step values of first actions
    me = s.active
    def one(a):
        if isinstance(a, EndTurn): return end_value(s, me, w)
        t2 = s.clone(); apply(t2, a); return WIN if t2.winner == me else evaluate(t2, me, w)
    first_best = max(legal_actions(s), key=one)
    setup = not (type(first_best) == type(bline[0]) and one(first_best) - one(bline[0]) < 1e-9)
    txt = lambda st_a: [describe(st, a) for st, a in st_a]
    st = s.clone(); bdesc = []
    for a in bline:
        if st.over or st.active != me: break
        bdesc.append(describe(st, a))
        if isinstance(a, EndTurn): break
        apply(st, a)
    return dict(i=i, w=wname, vbest=vbest, vg=vg, vm=vm, vm8=vm8, vx=vx, chm=chm, chm8=chm8, chx=chx, chb=chb, xline=txt(xline), complete=complete, secs=tb, setup=setup,
                best=bdesc, greedy=txt(gline), mcts=txt(mline), turn=s.turn,
                craft=deck_craft(s, me).name)

if __name__ == "__main__":
    rows = pickle.load(open(sys.argv[1], "rb"))
    starts, seen = [], set()
    for r in rows:
        key = (r["game"], r["turn"])
        if key in seen: continue
        seen.add(key)
        starts.append(r)
    rng = random.Random(7)
    rng.shuffle(starts)
    jobs = []
    nr = nd = 0
    for k, r in enumerate(starts):
        s = r["state"]
        if s.players[s.active].max_pp < 3: continue
        craft = deck_craft(s, s.active)
        if craft == Craft.DRAGON and "learned" in r["spec"] and nd < 70:
            jobs += [(k, s, "H"), (k, s, "L")]; nd += 1
        elif craft == Craft.FOREST and nr < 50:
            jobs.append((k, s, "H")); nr += 1
    print("jobs", len(jobs), flush=True)
    res = []
    with Pool(4) as p:
        for out in p.imap_unordered(job, jobs):
            res.append(out)
            if len(res) % 20 == 0: print(len(res), flush=True)
    pickle.dump(res, open(sys.argv[2], "wb"))
    print("done")
