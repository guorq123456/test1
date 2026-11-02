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
me, op = s.players[s.active], s.players[1 - s.active]
print("active", s.active, "turn", s.turn, "taken", me.turns_taken, op.turns_taken, "ep", me.ep, me.sep, "hp", me.leader_hp, op.leader_hp)
print("flags cd", [c.countdown for c in me.field])
gk = op.followers[0]; print("gk evolved", getattr(gk, "evolved", None), getattr(gk, "super_evolved", None), gk.keywords)
print("hand costs", [(c.defn.name, c.cost if hasattr(c, 'cost') else None) for c in me.hand])
