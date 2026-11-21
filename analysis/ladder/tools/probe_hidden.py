"""Phase-0 checks of pairing, clone contents and determinize (read-only; no games played).

    python analysis/ladder/tools/probe_hidden.py
Seeds: 99000500-99000519, 99000600, 99000700-99001699 (new_game only), 99000800 (phase-0 probe bank)."""
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from svsim.cards.decks import from_hash
from svsim.core.engine import new_game
from svsim.core.view import determinize, observe

lines = [l.strip().split('|') for l in (ROOT / 'analysis/pilot/fields/bot-frozen7.txt').read_text(encoding='utf-8').splitlines()
         if l.strip() and not l.startswith('#')]
D = {n: from_hash(c) for n, c in lines}
names = list(D)


def deal(seed, a, b):
    s = new_game(D[a], D[b], seed=seed)
    return s.first, [[c.defn.card_id for c in p.hand] for p in s.players], [[c.defn.card_id for c in p.deck] for p in s.players]


print('pairing same-seed identical:', all(deal(99000500 + i, names[1], names[4]) == deal(99000500 + i, names[1], names[4]) for i in range(20)))
x, y = deal(99000600, names[1], names[4]), deal(99000600, names[1], names[5])
print('seat-0 deal independent of opponent deck:', x[1][0] == y[1][0] and x[2][0] == y[2][0], 'first same:', x[0] == y[0])
print('first=0 share over 1000 seeds:', sum(new_game(D[names[0]], D[names[1]], seed=99000700 + i).first == 0 for i in range(1000)) / 1000)
s = new_game(D[names[1]], D[names[4]], seed=99000800)
c = s.clone()
print('clone keeps rng state:', c.rng.getstate() == s.rng.getstate())
print('clone keeps opp hand:', [q.defn.card_id for q in c.players[1].hand] == [q.defn.card_id for q in s.players[1].hand])
print('clone keeps deck order:', [q.defn.card_id for q in c.players[1].deck] == [q.defn.card_id for q in s.players[1].deck])
d = determinize(s, 0, random.Random(1))
true = Counter(q.defn.card_id for q in s.players[1].hand + s.players[1].deck)
samp = Counter(q.defn.card_id for q in d.players[1].hand + d.players[1].deck)
print('determinize opponent multiset == true remaining multiset:', true == samp)
print('observe keys:', list(observe(s, 0)), list(observe(s, 0)['opponent']))
