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

**Games and seeds:**
- Shard k is netdata seed S + k. It holds games g = 0 … 999, 1000 games per shard.
- Each game is `learn.netdata.play` and is fixed by (seed, g):
  - deal seed: seed × 100003 + g;
  - agent seeds: seed × 1000 + 2g + i;
  - --deck's seat: g % 2.
- S comes from the analysis line.
- Shards k = 0–9 (10⁴ games) run in the cloud; k = 10–99 run on Salem's computer.

**Files:**
- Each finished game is appended at once to `rec-<seed>.part.jsonl` (the netdata record: the deal and the actions,
  plus the search's view of each decision).
  - "cpu" is the CPU seconds its worker spent on it.
- A complete shard is compressed to `rec-<seed>.jsonl.gz`, about 2.5 MB.
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

Commands are for cmd, run from Salem's own checkout. `<C>` is the commit to run (the one the architecture thread
names) and S the analysis line's seed base.

1. **A worktree of its own** (Salem's checkout stays as it is):
   ```
   git fetch origin ccr-165ad1e7-t2zmqu
   git worktree add ..\svsim-scale <C>
   cd ..\svsim-scale
   ```
2. **Run.** Records go to `..\scale-rec`, outside the worktree. Salem's rules: below normal priority, off CPU0,
   at most 12 processes (11 workers plus the parent):
   ```
   start "" /WAIT /BELOWNORMAL /AFFINITY FFFFE cmd /c "python -m svsim.tools.host svsim.learn.scaledata play --base S --shards 10 100 --workers 11 --out ..\scale-rec > ..\scale-rec.log 2>&1"
   ```
   - It prints one progress line every 50 games: games, wall seconds, CPU seconds per game, games per hour.
   - **Stopped at any point:** run the same line again to go on.
3. **Check:**
   ```
   python -m svsim.learn.scaledata check ..\scale-rec
   ```
   It lists each shard (games, unique g, first-seat wins, CPU seconds per game) and any unfinished part files.
4. **Hand over** the `rec-*.jsonl.gz` files, about 2.5 MB per shard, about 225 MB for 90 shards. Part files are not
   needed.

**Time:** at 3.0 CPU seconds per game (cloud, Linux), 11 workers come to about 13,000 games an hour, so about 7
hours for 90,000. Windows may differ; the log's first lines show the real rate.

**Cross-machine games are not expected to be identical:** cmp_roots differs between Linux (142cc567…2b9adf) and
Windows (755a0bba…96a6). Shards are disjoint, so this does not matter; a game merged from both machines would show
up as a mismatch.
