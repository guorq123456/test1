"""Before D13 (architecture 17:44Z): can the current candidate read the opponent's hand at all? On A-vs-A positions
(D11's records), the same state determinized twice with the same random numbers - once as usual, once with +oracle's
real hand (core.view.determinize) - and scored by A's scorer; then whole searches with and without +oracle on the
same seed, root visits compared. Condition: in this check one side knows the opponent's hand; otherwise the opponent's
deck list is known (order and hand not).

    cd <checkout> && PYTHONPATH=. python3 oracle_channel.py REC.jsonl.gz SPEC [games]
"""
import gzip, json, random, sys
from svsim.core.engine import legal_actions
from svsim.core.view import determinize
from svsim.learn.netdata import _search
from svsim.learn.setpolicy import decisions
from svsim.tools.arena import make_agent

rec_path, spec = sys.argv[1:3]
games = int(sys.argv[3]) if len(sys.argv) > 3 else 6
recs = [json.loads(l) for l in gzip.open(rec_path, "rt") if l.strip()][:games]
agent = make_agent(spec, 0)
sc = _search(agent).weights
n = same_hand = 0
dmax = 0.0
searches = same_visits = same_move = 0
for rec in recs:
    for j, (i, state, legal, reps, group, pi, start) in enumerate(decisions(rec)):
        me = state.active
        for k in range(4):
            a = determinize(state, me, random.Random(1000 * i + k))
            b = determinize(state, me, random.Random(1000 * i + k), oracle=True)
            same_hand += sorted(c.uid for c in a.players[1 - me].hand) == sorted(c.uid for c in b.players[1 - me].hand)
            dmax = max(dmax, abs(sc.score(a, me) - sc.score(b, me)))
            n += 1
        if j % 4 == 0:
            res = []
            for opt in ("", "+oracle"):
                ag = make_agent(spec + opt, 77 + i)
                se = _search(ag)
                se.last_root = None
                x = state.clone()
                act = ag.act(x, legal_actions(x))
                root = se.last_root
                res.append((repr(act), sorted((repr(k2), c.visits) for k2, c in root.children.items()) if root else None))
            searches += 1
            same_move += res[0][0] == res[1][0]
            same_visits += res[0][1] == res[1][1]
print(f"{rec_path.split('/')[-1]}: {n} determinization pairs, same opponent hand {same_hand}, max |score diff| {dmax:.3e}; "
      f"{searches} searches: same move {same_move}, same root visits {same_visits}")
