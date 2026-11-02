import random, time, traceback
from svsim.cards import portal
from svsim.cards.pool import collectible
from svsim.core.enums import Craft
from svsim.core.script import has_script
from svsim.agents.random_agent import RandomAgent, play_game
from svsim.core.engine import new_game
pool = [c for c in collectible(Craft.PORTAL) if has_script(c.card_id) or c in portal.VANILLA]
print(len(pool))
t=time.time()
for g in range(300):
    rng = random.Random(g)
    deck=[]
    while len(deck)<40:
        c=rng.choice(pool)
        if deck.count(c)<3: deck.append(c)
    rng2 = random.Random(g+5000)
    deck1=[]
    while len(deck1)<40:
        c=rng2.choice(pool)
        if deck1.count(c)<3: deck1.append(c)
    state=new_game(deck, deck1, seed=g)
    try:
        w=play_game(state,[RandomAgent(g,end_turn_weight=0.2),RandomAgent(g+1,end_turn_weight=0.2)])
    except Exception:
        traceback.print_exc(); print('game', g); break
print(time.time()-t)
