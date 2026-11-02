"""Leave one game out: does the holding value make the player's own moves and turns rank first more often?"""
import sys, random
sys.path.insert(0, "/home/user/test1")
from multiprocessing import Pool
from svsim.tools import records
from svsim.tools.timing import load_games
from svsim.learn.timing import collect, Timed
from svsim.core.actions import EndTurn
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Phase, Craft
from svsim.search.evaluate import after_end_of_turn, DEFAULT
from svsim.agents.random_agent import RandomAgent
from svsim.tools.arena import make_agent
G = "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/db_v4/games"
GRID = [3.0, 5.0, 8.0, 12.0, 20.0]
GAMES = load_games([G])

def after(state, action):
    s = state.clone()
    if isinstance(action, EndTurn):
        return after_end_of_turn(s)
    apply(s, action)
    return s

def line_end(start, agent):
    s = start.clone()
    for _ in range(80):
        if s.over or s.active != 0: break
        a = agent.act(s, legal_actions(s))
        if isinstance(a, EndTurn): break
        apply(s, a)
    return None if s.over else after_end_of_turn(s)

def job(g):
    others = [r for i, r in enumerate(GAMES) if i != g]
    prof = collect(others, "rhino", "ramp")
    evals = [Timed(base=DEFAULT, weight=w, profiles={(Craft.FOREST, Craft.DRAGON): prof}) for w in GRID]
    step_hits, step_n = [0] * len(GRID), 0
    turn_hits, turn_n = [0] * len(GRID), 0
    record = GAMES[g]
    start, turn = None, None
    for k, (state, action) in enumerate(records.steps(record)):
        if state.active != 0 or state.phase != Phase.MAIN:
            continue
        if state.turn != turn:
            turn, start = state.turn, state.clone()
        legal = legal_actions(state)
        if len(legal) >= 2 and action in legal:
            ends = [after(state, a) for a in legal]
            if not any(e.over for e in ends):
                step_n += 1
                for j, ev in enumerate(evals):
                    scores = [ev.score(e, 0) for e in ends]
                    if scores[legal.index(action)] >= max(scores) - 1e-9:
                        step_hits[j] += 1
        if isinstance(action, EndTurn) and start is not None:
            mine = after_end_of_turn(state)
            if not mine.over:
                alts = [after_end_of_turn(start.clone()), line_end(start, make_agent("mcts:100+plan", k))]
                alts += [line_end(start, RandomAgent(31 * k + i, 0.15)) for i in range(3)]
                alts = [a for a in alts if a is not None]
                turn_n += 1
                for j, ev in enumerate(evals):
                    m = ev.score(mine, 0)
                    if all(m >= ev.score(a, 0) - 1e-9 for a in alts):
                        turn_hits[j] += 1
            start = None
    return step_hits, step_n, turn_hits, turn_n

if __name__ == "__main__":
    with Pool(4) as pool:
        out = pool.map(job, range(len(GAMES)))
    sn = sum(o[1] for o in out); tn = sum(o[3] for o in out)
    for j, w in enumerate(GRID):
        sh = sum(o[0][j] for o in out); th = sum(o[2][j] for o in out)
        print(f"持牌权重 {w:3.1f}: 单步命中 {sh}/{sn} = {sh/sn:.0%}   整回合排第一 {th}/{tn} = {th/tn:.0%}")
