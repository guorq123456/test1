# Scaling test: does a card-attribute set network keep improving with more strong self-play?

**Condition:** 对手卡表已知（牌序、手牌未知）.

**Task:** the architecture thread 2026-10-15 17:27Z (Salem 17:25Z: 「先测」).
1. Record strong self-play.
2. Train a DeepSets value net on 10³ / 10⁴ / 10⁵ games.
3. Let strong search use the net at turn ends.

## Step 1: the self-play recorder (`svsim/learn/scaledata.py`, `svsim/learn/tokens.py`)

**Who plays:**
- v2skx, `mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost`, on both sides of the ramp-t mirror.
- No exploration.

**Which turn-end model v2skx reads on this mirror:** the installed `ramp-t-ramp-t-ended.json` (extras hand,
hpphase).
- pkg-kc-ramp-ramp carries that file unchanged.
- The package replaces only the original Ramp mirror's `ramp-ramp-ended.json`.
- So on ramp-t, v2skx's evaluator is level strong's installed one; the only difference from v2s here is the
  discard pruning.

**Games and seeds** (the analysis line, 2f981bb):
- Shard k (k = 0 … 99) is netdata seed s_k = 70100000 + 2k. It holds games g = 0 … 999.
- Each game is `learn.netdata.play` and is fixed by (s, g):
  - deal seed: s × 100003 + g;
  - agent seeds: s × 1000 + 2g + i (a stride of 2 keeps neighbouring shards' agent seeds apart);
  - exploration rng: s × 7919 + g, at rate 0;
  - --deck's seat: g % 2.
- **Who plays which shards:**
  - k = 0–4: the analysis line;
  - k = 5–9: this line (the cloud's 10⁴ together with 0–4);
  - k = 10–99: Salem's computer.
- **Sizes:** 10³ = shard 0, 10⁴ = shards 0–9, 10⁵ = all.
- **Smoke:** s = 70100200 (shard index 100), g < 200. Not part of the data.
- **Holdout:** 5 shards of 1000 games, s_h = 70200000 + 2h (h = 0–4): `--base 70200000 --stride 2 --shards 0 5`
  (the architecture thread and the analysis line, 17:45Z). This line plays it after k = 5–9.
- **Gates:** 70300000 / 70400000 / 70500000.

**Files:**
- Each finished game is appended at once to `rec-<seed>.part.jsonl` (the netdata record: the deal and the actions,
  plus the search's view of each decision).
  - "cpu" is the CPU seconds its worker spent on it.
- A complete shard is compressed to `rec-<seed>.jsonl.gz`, about 1.4 MB (1.44 KB a game in the smoke).
- **Resume:** run the same command again. A cut-off last line is dropped and that game is played again; finished
  shards are skipped.
- **Merge:** `merge` puts shards from several machines together, one game per (seed, g). A game found twice must
  be the same record apart from "date" and "cpu", otherwise it is reported.

**What is encoded (`encode`, in the cloud only; it replays the records):**
- **Which positions:** every turn end (netdata.rows phase ENDED, the moment the installed turn-end evaluator
  scores), for the player who ended the turn.
- **Tokens:** each one is one card in one zone. The zones (the side is part of the zone):
  - my hand, field, leader area and deck;
  - the opponent's field and leader area;
  - the opponent's unseen pool, i.e. their hand and deck as one pool, the same pool learn.features counts.
    The opponent's hand itself shows as a count only.
- **A token's own values:** zone, count, and what the card is now (cost, attack, defense, maximum defense,
  evolved, super-evolved, can hit a follower / the leader, attacks left, countdown, counters, current keywords,
  silenced, given abilities or stats, entered this turn).
- **The card's static row** (96 values, `tokens.static`, looked up by card id; the id itself is never an input):
  - printed values, type, craft and keywords;
  - which script hooks it has and its script properties;
  - learn.roles' measured roles and its effect each round on the field;
  - learn.payoff's measured evolve and super-evolve payoff.
- **Globals:** 25 values (both HPs, play points, evolution points, turns, deck and hand counts, bonus point, who
  went first, cemetery, evolutions).
- **Labels:**
  - the game's result for the player who ended the turn;
  - the installed evaluator's logit there (`linear`; it matches `ramp-t-ramp-t-ended.json`'s logit exactly);
  - seed, g, action index, turn, player, and the game's length.

## Salem's computer: shards 10–99 (90,000 games) in a separate worktree

**One line**, in the cmd window Salem normally runs svsim from (venv active), in his own checkout. `<C>` is the
commit the architecture thread names.
```
git fetch origin ccr-165ad1e7-t2zmqu && (if not exist ..\svsim-scale git worktree add --detach ..\svsim-scale <C>) && cd ..\svsim-scale && start "" /WAIT /BELOWNORMAL /AFFINITY FFFFE cmd /c "python -m svsim.tools.host svsim.learn.scaledata play --base 70100000 --stride 2 --shards 10 100 --workers 11 --out ..\scale-rec >> ..\scale-rec.log 2>&1 && python -m svsim.learn.scaledata check ..\scale-rec > ..\scale-check.json"
```
- **What it does:**
  - creates the worktree `..\svsim-scale` at `<C>` (once; Salem's own checkout is not touched);
  - plays the shards there at below-normal priority, off CPU0, 11 workers plus the parent (12 processes);
  - writes `..\scale-check.json`, a summary of each shard.
- **Output:** `..\scale-rec\rec-<seed>.jsonl.gz`, one per finished shard, about 1.4 MB each and about 130 MB for
  all 90. `..\scale-rec.log` gets a progress line every 50 games: games, wall seconds, CPU seconds per game,
  games per hour.
- **Stopped at any point** (closed window, reboot): run the same line again. It skips the worktree, finished shards
  and finished games, and replays only a cut-off last game.
- **Time:** the cloud measured 3.43 CPU seconds a game (Linux, 4 workers). With Salem's machine's per-process
  factor of about 0.73 (analysis/local-runs) and 11 workers, that is about 6 hours for 90,000 games; E-cores may
  stretch it to 8. The log's first lines show the real rate.
- **Getting the shards back to the cloud:** about 130 MB in 90 files of about 1.4 MB, fine for a data branch in git.
  How they are pushed is left to the architecture and coordination lines with Salem.

**Cross-machine games are not expected to be identical:** cmp_roots differs between Linux (142cc567…2b9adf) and
Windows (755a0bba…96a6). Shards are disjoint, so this does not matter; a game merged from both machines would show
up as a mismatch.

## Smoke (200 games, s = 70100200; 2026-10-15 17:40–17:43Z, svsim at 4d7214d)

`play --base 70100000 --stride 2 --shards 100 101 --per-shard 200 --workers 4` (cloud, 4 processes), then `check`
and `encode`. Files in data/smoke/:
- `rec-70100200.jsonl.gz`: 200 games, 295 KB, sha256 9ffa550d…a710;
- `check.json`.

| | |
|---|---|
| games finished | 200 / 200, g 0–199 each once, no draws |
| **CPU seconds per game (one core)** | **3.45** (the earlier timing run, s = 7100: 3.43) |
| wall, 4 processes | 183 s, about 3,900 games an hour |
| first player's wins | 121 / 200 (60.5%) |
| actions per game | 68.2 on average |
| turn-end positions | 3,858 (19.3 a game) |
| tokens per position | 35.5 on average, at most 43 |
| encoding | 2.0 CPU seconds for the 200 games; tokens file 257 KB |
| installed evaluator on these positions | Brier 0.2045, log-loss 0.5892 |

- The installed evaluator's Brier and log-loss are on the smoke games, which are not part of any training set.
- **Projections:**
  - the cloud's k = 5–9 (5,000 games) take about 80 minutes on 4 processes;
  - 10⁵ games are about 1.9 million turn-end positions and 140 MB of record files.
