"""In-gate same-deck time ratio for a pair of gates (A always plays --deck, B plays --opponent).

Deck X's ratio = A's ms per decision on X in the gate where A plays X / B's ms per decision on X in the gate where B
plays X. Decision-weighted (total ms / decisions). Reads only the timing fields, not the points.
"""
import json
import sys


def per_decision(path, key):
    n = t = 0
    for line in open(path):
        for g in json.loads(line)[key]:
            n += g["n"]
            t += g["total"]
    return t / n, n


def main():
    g1, g2, x1, x2 = sys.argv[1:5]  # gate1.jsonl gate2.jsonl deck-of-A-in-gate1 deck-of-A-in-gate2
    for deck, a_gate, b_gate in ((x1, g1, g2), (x2, g2, g1)):
        a, na = per_decision(a_gate, "ms")
        b, nb = per_decision(b_gate, "ms_b")
        print(f"{deck}: A {a:.2f} ms ({na}) / B {b:.2f} ms ({nb}) = {a / b:.3f}")


main()
