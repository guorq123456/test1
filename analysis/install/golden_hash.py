"""Hash of the golden games as this machine plays them (all decisions), to compare old and new code here."""
import hashlib, json, sys
sys.path.insert(0, "."); sys.path.insert(0, "tests")
from golden_search import GAMES, play
for deck, opp, seed, limit in GAMES:
    got = play(deck, opp, seed, limit)
    print(f"{deck}|{opp}|{seed}", len(got), hashlib.sha256(json.dumps(got).encode()).hexdigest())
