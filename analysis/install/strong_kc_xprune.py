"""The install package "strong + lethal-clock evaluator + discard pruning" (the architecture thread 2026-10-11 18:47Z):
level strong's spec from mcts:200+plan+learned+phased to
mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost (the spec of the stacked gate J81, 200 iterations).
The strongest level is left as it is (it reads the installed models, not the package). Prepared only: run it on
Salem's machine once he says so. Replaces section 6's strong_xprune.py package (one or the other, not both).
Condition: the opponent's deck list is known (order and hand not).

    python analysis/install/strong_kc_xprune.py check     strong's and max's specs, the levels' hash, the package's
    python analysis/install/strong_kc_xprune.py apply     make the change (exact text edits, all or nothing)
    python analysis/install/strong_kc_xprune.py revert    undo it

What `apply` edits (each old text must be found exactly once, or nothing is written; it needs strong at its old
spec, so a machine with section 6's package installed reverts that first):
- svsim/ui/session.py: LEVELS["strong"].
- svsim/tools/arena.py: a VERSIONS name for the new spec ("v2skx"), so a record names the bot.
- tests/test_web.py, tests/test_learn.py: the three asserts that pin strong's old spec, and the web build's list of
  model folders it ships (a level naming phased=pkg-kc-ramp-ramp makes the build ship that folder: tools.web).

The package folder svsim/learn/phased_models/pkg-kc-ramp-ramp (analysis/install/make_pkg.py, 3eab414) has to be
on the machine:
- it is every installed model file byte for byte, with only ramp-ramp-ended.json replaced by cand-kc's;
- `check` and `apply` verify its digest: sha256 over the sorted lines "<file name> <file sha256>" of its files (each
  file's CRLF read as LF, so a Windows checkout with converted line endings gives the same digest);
- `apply` stops before any edit if the folder is missing or its digest differs.
The installed models in svsim/learn/phased_models itself are not touched.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strong_xprune as base   # noqa: E402

ROOT = base.ROOT
OLD = "mcts:200+plan+learned+phased"
NEW = "mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
PKG = ROOT / "svsim/learn/phased_models/pkg-kc-ramp-ramp"
PKG_DIGEST = "1e7bc6f82c2515a2d06dfb4803e25997c3324374e4c9ba312d0dc3bf23bc5675"
EDITS = [
    ("svsim/ui/session.py",
     '          "strong": "mcts:200+plan+learned+phased",\n',
     '          # strong + the lethal-clock evaluator (pkg-kc-ramp-ramp: cand-kc\'s Ramp-mirror turn-end model, the\n'
     '          # other pairings as installed) + discard pruning (+xprune=3:3:cost); the stacked gate J81\n'
     '          "strong": "mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost",\n'),
    ("svsim/tools/arena.py",
     '    "v2s": "mcts:200+plan+learned+phased",     # vs mcts:200+plan+learned: 59.7% +- 3.5% over 600 games\n',
     '    "v2s": "mcts:200+plan+learned+phased",     # vs mcts:200+plan+learned: 59.7% +- 3.5% over 600 games\n'
     '    # v2s with cand-kc\'s Ramp-mirror turn-end model (package pkg-kc-ramp-ramp) and discard pruning\n'
     '    # (search.xprune): 53.0% over v2s in the stacked gate (analysis/stack)\n'
     '    "v2skx": "mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost",\n'),
    ("tests/test_web.py",
     'assert LEVELS["normal"] == VERSIONS["v2r5558960"] and LEVELS["strong"] == VERSIONS["v2s"]',
     'assert LEVELS["normal"] == VERSIONS["v2r5558960"] and LEVELS["strong"] == VERSIONS["v2skx"]'),
    ("tests/test_web.py",
     'assert LEVELS["strong"] == "mcts:200+plan+learned+phased" and LEVELS["fast"] == "greedy+plan+learned"',
     'assert LEVELS["strong"] == "mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost" and '
     'LEVELS["fast"] == "greedy+plan+learned"'),
    ("tests/test_web.py",
     '                                                     "svsim/learn/phased_models/ref-5558960"}   # normal\'s frozen models\n',
     '                                                     "svsim/learn/phased_models/ref-5558960",   # normal\'s frozen models\n'
     '                                                     "svsim/learn/phased_models/pkg-kc-ramp-ramp"}   # strong\'s package\n'),
    ("tests/test_learn.py",
     'assert LEVELS["strong"] == VERSIONS["v2s"] == "mcts:200+plan+learned+phased"',
     'assert LEVELS["strong"] == VERSIONS["v2skx"] == "mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"'),
]


def pkg_digest():
    """sha256 over the sorted "<name> <sha256>" lines of the package folder's files (None if it is missing)."""
    if not PKG.is_dir():
        return None
    def sha(p):                                   # CRLF read as LF: a Windows checkout may convert line endings
        return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    lines = sorted(f"{p.name} {sha(p)}" for p in PKG.iterdir() if p.is_file())
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def max_spec():
    """LEVELS["max"] (None if this checkout has no strongest level, i.e. is from before b215e3d)."""
    import subprocess
    code = "import json; from svsim.ui.session import LEVELS; print(json.dumps(LEVELS.get('max')))"
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    digest = pkg_digest()
    pkg = {"folder": str(PKG.relative_to(ROOT)), "digest": digest, "ok": digest == PKG_DIGEST}
    if cmd in ("apply", "revert"):
        if cmd == "apply" and not pkg["ok"]:
            raise SystemExit(f"package folder missing or different, nothing written: {json.dumps(pkg)}")
        before = base.levels()
        base._edit(reverse=cmd == "revert", edits=EDITS)
        after = base.levels()
        print(json.dumps({"done": cmd, "before": before, "after": after, "package": pkg}, ensure_ascii=False,
                         indent=1))
    else:
        spec, levels_digest = base.levels()
        state = "installed" if spec == NEW else "not installed" if spec == OLD else f"other ({spec})"
        print(json.dumps({"strong": spec, "max": max_spec(), "levels_sha256": levels_digest, "state": state,
                          "package": pkg}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
