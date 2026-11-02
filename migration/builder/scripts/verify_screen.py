import sys, pickle, time
sys.path.insert(0, "/home/user/test1")
from svsim.cards import library  # noqa
from svsim.search.lethal import LethalSearch
rows = pickle.load(open(sys.argv[1], "rb"))
full, screened = LethalSearch(max_nodes=2000), LethalSearch(max_nodes=2000, screen=200)
lethal = missed_full = missed_screen = 0; t_full = t_screen = 0.0
for state, sure, *_ in rows:
    a, b = full.solve(state), screened.solve(state)
    t_full += a.seconds; t_screen += b.seconds
    if sure:
        lethal += 1; missed_full += not a.sure; missed_screen += not b.sure
print(lethal, missed_full, missed_screen, round(t_full, 1), round(t_screen, 1))
