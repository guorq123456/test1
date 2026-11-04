"""At each Accelerate chance the Ramp bot had: its turn vs Accelerate first (then the bot) vs ending, by impact."""
import json, glob, sys, time
sys.path.insert(0, "/home/user/test1")
from multiprocessing import Pool
from svsim.tools import records
from svsim.core.actions import PlayCard, EndTurn
from svsim.core.engine import legal_actions, play_form, apply
from svsim.core.enums import Phase
from svsim.tools.arena import make_agent
from svsim.search import impact
G = "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/db_v3/games/"
LUM = 10844120
SPEC = "mcts:200+plan+learned"

def finish(s, agent, first=None):
    played = 0
    if first is not None:
        apply(s, first); played += 1
    for _ in range(60):
        if s.over or s.active != 1: break
        a = agent.act(s, legal_actions(s))
        if isinstance(a, EndTurn): break
        played += isinstance(a, PlayCard); apply(s, a)
    return s, played

def job(args):
    tag, state = args
    t = time.perf_counter()
    bot_end, bot_n = finish(state.clone(), make_agent(SPEC, 3))
    acc = next(a for a in legal_actions(state) if isinstance(a, PlayCard) and state.in_hand(1, a.uid).defn.card_id == LUM)
    acc_end, acc_n = finish(state.clone(), make_agent(SPEC, 3), acc)
    if bot_end.over or acc_end.over: return tag, None, 0
    out = impact.assess(state, [bot_end, acc_end, state], ["bot", "accelerate", "end"], [bot_n, acc_n, 0],
                        samples=6, seed=1, opponent="mcts:50+plan")
    return tag, {i.label: {k: i[k] for k, _, _ in impact.DIMENSIONS} for i in out}, time.perf_counter() - t

if __name__ == "__main__":
    jobs = []
    for f in sorted(glob.glob(G + "*.json")):
        r = json.load(open(f))["record"]; seen = set()
        for state, action in records.steps(r):
            if state.active != 1 or state.phase != Phase.MAIN or state.turn in seen: continue
            p = state.players[1]
            lum = [c for c in p.hand if c.defn.card_id == LUM]
            if lum and (form := play_form(p, lum[0])) is not None and form.alt is not None:
                seen.add(state.turn); jobs.append((f"{f[-18:-5]} t{state.turn}", state.clone()))
    print(len(jobs), "chances", flush=True)
    with Pool(4) as pool:
        for tag, rows, sec in pool.imap(job, jobs):
            if rows is None: print(tag, "skip"); continue
            print(f"{tag:22s} {sec:5.1f}s " + "  ".join(f"{k}: clock {v['my_clock']:.1f} opp {v['their_clock']:.1f} race {v['race']:.2f} val {v['value']:.2f}" for k, v in rows.items()), flush=True)
