"""Ramp Dragon opening hands: the expected clock with and without ramp cards in hand."""
import sys, random, time, statistics
sys.path.insert(0, "/home/user/test1")
from multiprocessing import Pool
from svsim.cards import decks
from svsim.core.engine import new_game, apply
from svsim.core.actions import Mulligan
from svsim.core.view import determinize
from svsim.search import race
from svsim.ui.text import card_name
RAMP = {10042310, 10844120}       # 龙之启示, 金银绚烂 (Accelerate) -- for the tally only

def job(seed):
    rhino, ramp = decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON)
    s = new_game(ramp, rhino, seed=seed, first=seed % 2)
    apply(s, Mulligan(())); apply(s, Mulligan(()))
    hand = [c.defn.card_id for c in s.players[0].hand]
    t = time.perf_counter()
    clocks = []
    for k in range(3):
        d = determinize(s, 0, random.Random(seed * 10 + k))
        clocks.append(race.clock(d, 0, horizon=9).turns)
    return seed % 2, sum(c in RAMP for c in hand), [card_name(__import__('svsim.cards.pool', fromlist=['POOL']).POOL[c]) for c in hand], clocks, time.perf_counter() - t

if __name__ == "__main__":
    with Pool(4) as pool:
        rows = pool.map(job, range(80))
    by = {}
    for first, n, hand, clocks, sec in rows:
        by.setdefault(min(n, 2), []).extend(clocks)
    for n in sorted(by): print(f"ramp cards in hand {n}: mean clock {statistics.mean(by[n]):.2f} over {len(by[n])} samples")
    print("seconds per clock:", statistics.mean(r[4] for r in rows) / 3)
    for r in rows[:6]: print(r)
