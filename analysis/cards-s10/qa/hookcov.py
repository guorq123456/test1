"""Which set 10 hooks fire in the random games (games.py decks), per class."""
import collections, random, sys
sys.path[:0] = [".", "tests"]
from svsim.cards import library  # noqa: F401
from svsim.cards.pending import PENDING
from svsim.core import script as S
import games

fired = collections.Counter()
ids = {}
for cid, sc in list(S._SCRIPTS.items()):
    if cid // 100000 in (110, 900) and (cid // 1000 % 10 in (3, 5, 6, 7) or cid == 90061140) and cid >= 11000000 or cid == 90061140:
        ids[cid] = sc
wrapped = set()
for cid, sc in ids.items():
    cls = type(sc)
    for h in S.HOOKS + ("on_card_banished", "on_ally_fuse"):
        f = getattr(cls, h, None)
        if callable(f) and (cls, h) not in wrapped:
            wrapped.add((cls, h))
            def w(self, ctx, _f=f, _key=f"{cls.__name__}.{h}"):
                fired[_key] += 1
                return _f(self, ctx)
            setattr(cls, h, w)
for name in ("rune", "abyss", "haven", "portal"):
    games.main(name, 300)
allkeys = sorted(f"{c.__name__}.{h}" for c, h in wrapped)
print("never fired:", [k for k in allkeys if fired[k] == 0])
print("fired least:", sorted(((fired[k], k) for k in allkeys if fired[k]), key=lambda t: t[0])[:8])
