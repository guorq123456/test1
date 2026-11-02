import random, sys
r = random.Random(195489856)
first = r.randrange(2)
deck = list(range(40)); r.shuffle(deck)
print(sys.version.split()[0], first, deck[:12], r.getrandbits(32), random.Random(5).sample(range(30), 5))
