"""The install package "strong + discard pruning" (the architecture thread 2026-10-10 21:09Z): level strong's spec
from mcts:200+plan+learned+phased to mcts:200+plan+learned+phased+xprune=3:3:cost. The iterations, the evaluator
files and the strongest level stay as they are. Prepared only: run it on Salem's machine once he says so.
Condition: the opponent's deck list is known (order and hand not).

    python analysis/install/strong_xprune.py check     the current strong spec and the levels' hash
    python analysis/install/strong_xprune.py apply     make the change (exact text edits, each checked)
    python analysis/install/strong_xprune.py revert    undo it

What `apply` edits (each old text must be found exactly once, or nothing is written):
- svsim/ui/session.py: LEVELS["strong"].
- svsim/tools/arena.py: a VERSIONS name for the new spec ("v2sx"), so a record names the bot.
- tests/test_web.py, tests/test_learn.py: the three asserts that pin strong's old spec.

The levels' hash is sha256 over json.dumps(LEVELS, sort_keys=True). It is the same on every machine (no line
endings involved).
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD, NEW = "mcts:200+plan+learned+phased", "mcts:200+plan+learned+phased+xprune=3:3:cost"
EDITS = [
    ("svsim/ui/session.py",
     '          "strong": "mcts:200+plan+learned+phased",\n',
     '          # strong + discard pruning (+xprune=3:3:cost; analysis/xprune, gates 52.4% pooled over level-strong)\n'
     '          "strong": "mcts:200+plan+learned+phased+xprune=3:3:cost",\n'),
    ("svsim/tools/arena.py",
     '    "v2s": "mcts:200+plan+learned+phased",     # vs mcts:200+plan+learned: 59.7% +- 3.5% over 600 games\n',
     '    "v2s": "mcts:200+plan+learned+phased",     # vs mcts:200+plan+learned: 59.7% +- 3.5% over 600 games\n'
     '    # v2s with discard choices pruned (search.xprune; analysis/xprune): 52.4% pooled over v2s, two gates\n'
     '    "v2sx": "mcts:200+plan+learned+phased+xprune=3:3:cost",\n'),
    ("tests/test_web.py",
     'assert LEVELS["normal"] == VERSIONS["v2r5558960"] and LEVELS["strong"] == VERSIONS["v2s"]',
     'assert LEVELS["normal"] == VERSIONS["v2r5558960"] and LEVELS["strong"] == VERSIONS["v2sx"]'),
    ("tests/test_web.py",
     'assert LEVELS["strong"] == "mcts:200+plan+learned+phased" and LEVELS["fast"] == "greedy+plan+learned"',
     'assert LEVELS["strong"] == "mcts:200+plan+learned+phased+xprune=3:3:cost" and LEVELS["fast"] == "greedy+plan+learned"'),
    ("tests/test_learn.py",
     'assert LEVELS["strong"] == VERSIONS["v2s"] == "mcts:200+plan+learned+phased"',
     'assert LEVELS["strong"] == VERSIONS["v2sx"] == "mcts:200+plan+learned+phased+xprune=3:3:cost"'),
]


def levels():
    """(strong's spec, the levels' hash), read by a fresh interpreter."""
    code = ("import hashlib, json; from svsim.ui.session import LEVELS; "
            "print(json.dumps([LEVELS['strong'], hashlib.sha256(json.dumps(LEVELS, sort_keys=True).encode())"
            ".hexdigest()]))")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def _edit(reverse: bool):
    texts = {}
    for path, old, new in EDITS:
        a, b = (new, old) if reverse else (old, new)
        text = texts.get(path) or (ROOT / path).read_text(encoding="utf-8")
        if text.count(a) != 1:
            raise SystemExit(f"{path}: expected the text once, found {text.count(a)}; nothing written\n{a}")
        texts[path] = text.replace(a, b)
    for path, text in texts.items():
        with open(ROOT / path, "w", encoding="utf-8", newline="") as fh:   # keep the file's own line endings
            fh.write(text)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd in ("apply", "revert"):
        before = levels()
        _edit(reverse=cmd == "revert")
        after = levels()
        print(json.dumps({"done": cmd, "before": before, "after": after}, ensure_ascii=False, indent=1))
    else:
        spec, digest = levels()
        state = "installed" if spec == NEW else "not installed" if spec == OLD else "unknown"
        print(json.dumps({"strong": spec, "levels_sha256": digest, "state": state}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
