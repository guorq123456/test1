"""Salem's four positions (claude/deck-search analysis/resource-value/acceptance.py) scored by a value net, as
reported for the DFM rune pilot: turn-end branch = net.logit(EV.after_end_of_turn(state), seat) after the line,
mid-turn branch = net.logit(state, seat, mid=True) right after the line; each the mean over acceptance.score's 40
reseeded copies (k=40), Salem's line passes when it scores higher. Ran from the deck-search worktree (its code).

    cd <deck-search worktree> && python <this file> <net.npz>
"""
import sys
sys.path.insert(0, "/home/claude/test1/.wt/ds/analysis/resource-value")
import acceptance as A
from svsim.search import evaluate as EV
from svsim.learn.setnet import load_cached
net = load_cached(sys.argv[1])
print("info:", {k: net.info.get(k) for k in ("shared", "name")}, "flag:", net.flag)
print("== 回合结束分支（先把回合打完再评）")
A.run(lambda t, p: net.logit(EV.after_end_of_turn(t), p))
print("== 回合中分支（不打完回合，直接评）")
A.run(lambda t, p: net.logit(t, p, mid=True))
