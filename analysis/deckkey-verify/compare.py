"""Compare move lists from replay_check.py / extra_cases.py runs, game by game.

    python3 compare.py BEFORE.json AFTER.json [--same 6=7,8=9]

Prints, for each game, whether the move lists are identical and, if not, the
first move where they part. --same pairs cases that must match within AFTER
(game k of case i against game k of case j).
"""
import json
import sys


def first_diff(a, b):
    for k, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return k
    return None if len(a) == len(b) else min(len(a), len(b))


def main():
    before, after = (json.load(open(p)) for p in sys.argv[1:3])
    for key in sorted(set(before) | set(after), key=lambda s: tuple(map(int, s.split("-")))):
        a, b = before.get(key), after.get(key)
        if a is None or b is None:
            print(f"{key}: only in {'after' if a is None else 'before'}")
            continue
        d = first_diff(a, b)
        print(f"{key}: {'identical' if d is None else f'differs from move {d}'} ({len(a)} / {len(b)} moves)")
    if "--same" in sys.argv:
        for pair in sys.argv[sys.argv.index("--same") + 1].split(","):
            i, j = pair.split("=")
            for g in range(10):
                a, b = after.get(f"{i}-{g}"), after.get(f"{j}-{g}")
                if a is None or b is None:
                    continue
                d = first_diff(a, b)
                print(f"after {i}-{g} vs {j}-{g}: {'identical' if d is None else f'differs from move {d}'}")


if __name__ == "__main__":
    main()
