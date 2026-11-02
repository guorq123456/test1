import sys, time
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, "/home/user/test1/tests")
from svsim.cards import decks
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Phase
from svsim.tools.arena import make_agent
from svsim.search import combo
from svsim.search.lethal import LethalSearch, find_lethal
g = 14; seed = 99600000 + g
agents = [make_agent("level-strong", 2 * seed), make_agent("level-strong", 2 * seed + 1)]
st = new_game(decks.build(decks.PIRATE_T), decks.build(decks.PIRATE_T), seed=seed)
seen = set()
while not st.over:
    if st.phase == Phase.MAIN and (st.turn, st.active) not in seen:
        seen.add((st.turn, st.active))
        if st.turn == 19:
            break
    apply(st, agents[st.active].act(st, legal_actions(st)))
s = st.clone()
hp = s.players[1 - s.active].leader_hp
print("hp", hp, "pp", s.players[s.active].pp, "max", s.players[s.active].max_pp, "tickers", combo.tickers_of(s))
print("hand", [c.defn.name for c in s.players[s.active].hand])
print("field", [(c.defn.name, getattr(c, 'atk', None), getattr(c, 'life', None)) for c in s.players[s.active].field])
print("enemy", [(c.defn.name, c.atk, c.life) for c in s.players[1 - s.active].followers])
for kw in [{}, dict(fix=True), dict(fix=True, eot=True), dict(tickers=True), dict(tickers=True, fix=True), dict(tickers=True, fix=True, eot=True)]:
    p = combo.plan(s, 20000, **kw)
    line = combo.realize(s, p.steps, face_first=p.face_first) if p.damage >= hp and p.steps else None
    ok = bool(line) and combo.verify(s, line)
    print(kw, p.damage, p.tickers, ok, p.steps)
for nodes, near in [(2000, (1000, 4)), (3000, (2000, 4))]:
    r = LethalSearch(max_nodes=nodes, screen=200, near=near, seed=0).solve(s.clone())
    print(nodes, r.sure, r.nodes, r.screened)
r = find_lethal(s.clone()); print("find_lethal", r.sure, r.nodes, r.complete)
p = combo.plan(s, 20000, tickers=True)
for n in range(1, len(p.steps) + 1):
    line = combo.realize(s, p.steps[:n], face_first=True)
    print(n, p.steps[n-1][:2], "realized" if line else "FAILS")
    if not line:
        break
line = combo.realize(s, p.steps, face_first=True)
if line:
    from svsim.core.engine import apply
    x = s.clone()
    for a in line:
        apply(x, a)
    print("after line: enemy hp", x.players[1 - s.active].leader_hp, "flags", combo.tickers_of(x), "over", x.over)
    from svsim.core.actions import EndTurn
    apply(x, EndTurn()); print("after end", x.players[1 - s.active].leader_hp, x.winner)
from svsim.cards.pool import POOL
for cid in (10923110, 10922310, 10523310, 90021310, 90021340, 90021350, 90024320):
    print(cid, POOL[cid].name, POOL[cid].cost)
