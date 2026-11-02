import time, sys
from svsim.learn.setpolicy import SetPolicy
from svsim.tools.deckgate import read_field
from svsim.cards.pool import POOL
from svsim.core.engine import new_game, legal_actions, apply
from svsim.tools.arena import make_agent
pol = SetPolicy.load(sys.argv[1])
f = read_field("analysis/sharednet/fields/B-r1.txt")
st = new_game([POOL[i] for i in f[0][1]], [POOL[i] for i in f[1][1]], seed=1)
a = make_agent("mcts:100+plan", 1)
n=0; T=0.0; C=0.0
while not st.over and n < 60:
    acts = legal_actions(st)
    c0=time.process_time(); t0=time.perf_counter()
    for _ in range(5): pol.priors(st, acts)
    C += time.process_time()-c0; T += time.perf_counter()-t0
    n+=5
    apply(st, a.act(st, acts))
print(sys.argv[1], "priors per call ms cpu %.2f wall %.2f" % (1000*C/n, 1000*T/n))
