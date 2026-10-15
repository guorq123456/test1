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

## Step 2: the net's training settings, fixed before any official size is trained

**Fixed settings** (`analysis/scaling/train.py net`, learn.setnet), the same for 10³, 10⁴ and 10⁵:
- **Shape:** phi 64-64, rho 128-64.
- **Optimizer:** Adam, step 1e-3, batch 256 positions, l2 1e-5.
- **Step size and stopping:** the step size halves after each epoch whose validation log-loss is not better; 4 such
  epochs in a row stop the fit (at most 60 epochs); the best epoch's weights are kept.
- **Validation part:** 1 game in 20 of the size's own games (key seed × 100003 + g, key % 20 == 0); the holdout
  is never used for any choice.
- **Threads:** single-threaded BLAS.

**How these were chosen** (a pilot on shards k = 5–9, 5000 games, which are inside the 10⁴ and 10⁵ sets; no
holdout game used):
- The validation part is 4710 positions. "Smoke" is the 200 smoke games (s = 70100200), which are in no set.

| | training part Brier | validation part Brier | smoke Brier | epochs |
|---|---|---|---|---|
| net, constant step 1e-3 | 0.1960 | 0.1953 | 0.1992 | 13 |
| **net, step halved on no improvement (kept)** | **0.1920** | **0.1956** | **0.1967** | 19 |
| installed linear model | 0.2029 | 0.2016 | 0.2045 | – |

- About 15 seconds an epoch for 88,000 positions while 4 self-play processes share the 4 cores, so about 5 minutes
  an epoch at 10⁵.
- The training and validation losses are close, so the net is not overfitting at 5000 games.

## Results at 10³ and 10⁴ (2026-10-15 19:15–20:15Z; 10⁵ waits for Salem's shards)

**Data:**
- Training: shards k = 0–9.
  - k = 0–4: the analysis line, its branch, sha256 checked;
  - k = 5–9: this line.
  - `merge`: 10,000 games, no duplicates, every g unique, 60.4% first-player wins, no draws.
- Holdout: 5000 games, 93,787 turn ends.
  - h = 0–2: this line, data/heldout/;
  - h = 3–4: the analysis line, sha256 checked.
- **Positions:** every turn end, seen by the player who ended the turn; the label is the game's result.
- All models are scored on the same positions (data/holdout-*.npz hold each model's probability at every holdout
  turn end, in the token files' order, with seed / g / turn / result).
- **Brier is the main score;** log-loss is in brackets.

| model | games | training part | validation part (1/20 of the games) | **holdout** |
|---|---|---|---|---|
| installed linear (ramp-t-ramp-t-ended.json) | – | 0.2047 (10³ games) / 0.2043 (10⁴) | – | **0.2038** (0.5894) |
| linear refit | 10³ | 0.2024 (sample) | – | **0.2013** (0.5829) |
| linear refit | 10⁴ | 0.2022 (sample) | – | **0.2004** (0.5805) |
| DeepSets net | 10³ | 0.2260 (0.6411) | 0.2382 | **0.2285** (0.6469) |
| DeepSets net | 10⁴ | 0.1914 (0.5582) | 0.1944 | **0.1937** (0.5643) |

**What each training column means:**
- **Linear refits:** the training column is a sample of about 1000 of their own training games (up to 20,000 turn
  ends, seed 0).
- **Nets:** the training column is the whole training part (17,984 / 178,093 turn ends), the validation part
  is 1,029 / 9,452.
- The holdout probability files hold all five models.
- `installed_matches_token_label`: the replayed installed logit and the token files' label differ by at most
  6e-7, and the holdout positions line up one to one.

**Readings:**
- **From 10³ to 10⁴ games**, the linear refit improves by 0.0009 and the net by 0.035.
- **At 10³** the net is worse than any linear model.
- **At 10⁴** it is better than the linear refit on the same games by 0.0067 Brier (0.0162 log-loss), and better
  than the installed model by 0.0101.
- **Fit:** at 10⁴ the net's training and holdout scores are close (0.1914 against 0.1937), so it is not
  overfitting; the analysis line's reading rule for 10⁵ (close means under-fitting, try a larger net) applies
  there.

### Does a card's part in the net's value depend on the position? (`contrib`, 10⁴ net; data/contrib-10000.json)

**Method:**
- 3000 holdout turn ends (seed 0).
- In each one, one copy of a card is taken out of my hand, my field or the opponent's field, and the net's logit
  is computed again.
- delta = logit with the card − logit without it.
- 19,189 deltas in all; 36 card × zone groups have at least 20 positions.
- A model with a fixed score per card would give every group a spread of 0.

**Result:**
- The median spread (sd of delta) across the groups is 0.17 logit; the largest is 1.58.
- In 12 of the 36 groups the sign itself changes: the card helps in at least 10% and hurts in at least 10% of
  the positions.
- **Examples:**

  | card, zone | positions | mean delta | sd | 5%–95% | share > 0 |
  |---|---|---|---|---|---|
  | 约束的《正义》·伊兰翠, hand | 1641 | +0.318 | 0.170 | +0.05 to +0.57 | 99% |
  | 世界的伙伴·佐伊, hand | 1474 | −0.176 | 0.209 | −0.56 to +0.15 | 19% |
  | 金银绚烂·璐米欧儿&雅尔贞特, hand | 1443 | −0.271 | 0.246 | −0.58 to +0.17 | 20% |
  | 龙之启示, hand | 830 | −0.303 | 0.212 | −0.56 to +0.12 | 13% |
  | 宣扬的龙人, field | 541 | +0.220 | 0.122 | 0.00 to +0.40 | 95% |
  | 断头的斩姬·相枛津, field | 263 | +0.296 | 0.213 | 0.00 to +0.63 | 95% |

- **One exception:** 狐火蜃景 in hand shows delta 0 at all 473 positions. The net gives that card no weight at
  all in hand; its phi output there is zero.
- A negative mean for a card in hand is not "the card is bad". The net sees the position with one card fewer, but
  the same globals (the hand count included), so the comparison is between this card and an empty slot the
  globals still count.

## Step 3: the net inside strong's search (data/timing.json, `timing.py`)

**Method:**
- One process, nothing else running.
- **Per evaluation:** 394 turn ends of 20 holdout games, each timed 5 times.
- **Per decision:** 120 positions, the first decision of turns ≥ 3 of the same games. v2skx and
  v2skx+setnet=models/net-10000.npz choose in turn at each position, seeds fixed, 3 rounds.

**Per evaluation, offline:**
- the net: 0.15–0.19 ms (three runs);
- the installed linear model: 0.05–0.09 ms.
- The net's single-position path is exact: it differs from the batch pass by at most 3e-15. It keeps each pooled
  card's phi output per card, so only hand, field and leader cards go through phi at each call.

**Per decision:**

| | ms per decision |
|---|---|
| v2skx | 97.1 |
| v2skx+setnet (10⁴ net) | 151.2 |
| **ratio** | **1.557** (rounds: 1.547, 1.573, 1.550) |

- **Where the extra 54 ms goes:**
  - the net is called 192.6 times a decision and spends 50.4 ms there (0.26 ms a call inside the search);
  - the linear model would have spent about 16.7 ms on as many calls;
  - the remaining 20.5 ms is the search going elsewhere with the other evaluator.
- **Agent string:**
  `mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-10000.npz`.
  It replaces only the ramp-t mirror's turn-end score; the pruning stays on.
