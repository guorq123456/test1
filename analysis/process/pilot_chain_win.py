"""One hero's whole pilot line on the new PC, in order: g1, g2, g3, then the move prior from g2/g3 (PRIOR-HAVEN.md's
recipe; the drivers beside this file). Each step is resumable and is skipped when its last line says done, so the
chain can be started again after any stop.

    py analysis/process/pilot_chain_win.py DECK WORKERS        e.g.  py analysis/process/pilot_chain_win.py forest2 10

DECK is a key of pilot_next_win.HEROES (forest2 = bot/T3-FOREST-2, bank 87240000; the WGP comparison report
2026-11-15, section 7). Run from the repo root with PYTHONPATH set to it. Writes runs/pilot-DECK-bot-g1/logs/chain.log
and, at the end, chain.done.
"""
import os
import subprocess
import sys
import time

HEROES = {"forest2": ("bot/T3-FOREST-2", 87240000)}
DECK, W = sys.argv[1], sys.argv[2]
assert DECK in HEROES, "DECK forest2"
if os.name == "nt":
    import ctypes
    k = ctypes.windll.kernel32
    k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)   # below normal; children inherit
HERO, BANK = HEROES[DECK]
RUN = f"runs/pilot-{DECK}-bot-g1"
os.makedirs(f"{RUN}/logs", exist_ok=True)
LOG = open(f"{RUN}/logs/chain.log", "a", encoding="utf-8")  # noqa: SIM115
HERE = os.path.dirname(os.path.abspath(__file__))


def say(s):
    LOG.write(f"== {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {s}\n")
    LOG.flush()


def done(log):
    try:
        lines = [x for x in open(log, encoding="utf-8").read().splitlines() if x.strip()]
    except OSError:
        return False
    return bool(lines) and lines[-1].rstrip().endswith(" done")


STEPS = [(f"{RUN}/logs/pilot-{DECK}-bot-g1.log", ["pilot_gen_win.py", HERO, f"pilot-{DECK}-bot-g1", str(BANK), W]),
         (f"{RUN}/logs/pilot-{DECK}-bot-g2.log", ["pilot_next_win.py", DECK, "2", W]),
         (f"{RUN}/logs/pilot-{DECK}-bot-g3.log", ["pilot_next_win.py", DECK, "3", W]),
         (f"{RUN}/logs/prior-{DECK}-bot.log", ["pilot_prior_win.py", DECK, W])]
say(f"start {DECK} {HERO} bank {BANK} workers {W}")
for log, (script, *args) in STEPS:
    if done(log):
        say(f"skip {script} {' '.join(args)} (done)")
        continue
    say(f"run {script} {' '.join(args)}")
    r = subprocess.run([sys.executable, os.path.join(HERE, script), *args], check=False)
    if r.returncode or not done(log):
        say(f"STOPPED at {script} {' '.join(args)} (exit {r.returncode}); start the chain again to resume")
        sys.exit(1)
open(f"{RUN}/logs/chain.done", "w", encoding="utf-8").write(time.strftime("%Y-%m-%dT%H:%M:%SZ\n", time.gmtime()))
say("done")
