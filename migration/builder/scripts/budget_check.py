import sys, pickle
sys.path.insert(0, "/home/user/test1")
from svsim.cards import library  # noqa
from svsim.search.lethal import find_lethal
positions = pickle.load(open("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/positions.pkl", "rb"))
rows = []
for i, s in enumerate(positions):
    small = find_lethal(s, max_nodes=2000)
    if small.complete:
        continue
    big = find_lethal(s, max_nodes=40000)
    rows.append((i, small.sure, big.sure, big.complete, big.nodes, round(big.seconds, 1), round(big.probability, 2)))
    print(rows[-1], flush=True)
print("incomplete at 2000:", len(rows), "of", len(positions), "| found only with 40000:", sum(b and not a for _, a, b, *_ in rows))
