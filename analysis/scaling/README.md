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

### The net's search path made faster, same numbers (the architecture thread 20:57Z)

**Which version J91 and J92 used:**
- J91 and J92 (equal-compute gates, N = 128) ran with the net's search path from before this change.
- In this branch, setnet.py is the same file from 7bb466d to 25e246e.
- b0920c3's earlier path agrees with it to 3e-15 but not to the last bit.
- The analysis line confirms that the two gates, their 20-pair checks, D1 / D2 and the leaf probe all checked
  out **7bb466d**, unchanged (net-1000 989fa1c6…, net-10000 6257b666…).

**The change (learn.setnet.SetNet.logit):**
- No int16 copy or clip for the live tokens.
- No np.unique for the zones.
- Each pooled zone's sum is kept per zone content: card ids with their counts, in order of first appearance. A
  determinized deck with the same cards reuses it.
- The sums are added in the same order as before.

**Check (`speedcheck.py --old 25e246e`):** SetNet.logit before and after is compared with == on 7937 positions:
- every turn end of 100 holdout games (1907);
- every position the search asked the net about in 30 decisions of v2skx+setnet (6030).
- **0 differ.**

**Speed (`timing.py --rounds 5`, the same 120 positions, one process, idle machine):**
- The old version was timed from a worktree at 25e246e, right before the new one.

| | before (25e246e) | after |
|---|---|---|
| v2skx, ms a decision | 96.1 | 94.5 |
| v2skx+setnet (10⁴ net), ms a decision | 151.3 | 132.3 |
| **ratio** | **1.574** (rounds 1.569, 1.554, 1.582, 1.586, 1.582) | **1.400** (rounds 1.504, 1.378, 1.356, 1.358, 1.405) |
| the net's own time inside the search, ms a decision | 50.9 | 35.7 |

- The first round of the new version includes filling its per-zone cache.
- data/timing.json holds the new run.
- **Offline time per evaluation varies a lot between runs** on this machine: the net 0.09–0.18 ms, the linear
  model 0.04–0.09 ms. The interleaved decision ratio is the steadier number.
- **The ratio for equal compute from here on is 1.400.**

### +neteot: a mid-turn position played to its turn end before the net scores it (the architecture thread 21:00Z)

**Why:** the analysis line's leaf probe (7eba5be) found 17.1% of the net's scores falling inside a turn. These
are in-turn leaves (after a move that isn't the turn's end) and the root's center. The net has only seen
positions after the end-of-turn abilities.

**What the option does:**
- With `+neteot` beside `+setnet=PATH`, a position the search scores for a player who is still to act (their own
  turn, `player_moves_next` False) is first put through `search.evaluate.after_end_of_turn` on a copy.
- If the end of turn decides the game, it counts as the win or loss.
- Off by default; off, the search path is the same as before.

**Tests (tests/test_setnet.py):**
- turn-end positions get the same score with and without the option;
- with it, a mid-turn position scores the same as the net on that position's after_end_of_turn;
- without it, it scores as before;
- scores where the player moves next still come from the base.

**In the search:**
- In 12 decisions (holdout game 1, turns ≥ 3), 903 of 2412 net calls (37.4%) were mid-turn positions. This is a
  different sample from the probe's 17.1%.
- Decision ratio (data/timing-neteot.json, 5 interleaved rounds): **1.447** (1.515, 1.48, 1.393, 1.42, 1.429),
  against 1.400 without the option.

**D3's A:** `mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-10000.npz+neteot`.
- **Use for now:** `+neteot` is for D3 only (the architecture thread 21:12Z). Whether a retrained net goes to a
  gate with it waits on D3.

## Generation 2: self-play with the 10⁴ net (set up 21:15Z, before any game; the architecture thread 21:08Z)

**Why:** D1 (the 10⁴ net against v2skx, both at 200 iterations) came to 44.3% (40.7–47.8). The upper end is below
50%, so the net plays its own positions now.

**Agent:** both sides play `mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-10000.npz`,
exactly D1's agent.
- **No +neteot**, so the positions are the ones D1's agent reaches.
- **Code:** d0e498d (its net path gives the same logits as 7bb466d's, to the last bit).
- **Net file:** net-10000.npz, sha256 6257b666….

**Games:**
- ramp-t mirror, no exploration.
- Shard k is s_k = 70800000 + 2k, g = 0–999.
- **Who plays:** k = 0–4 this line, k = 5–9 the analysis line.
- **Command:**
  `scaledata play --base 70800000 --stride 2 --shards K0 K1 --agent "<the agent>" --deck ramp-t --opponent ramp-t`.

**Afterwards:**
1. `merge`.
2. `encode --net analysis/scaling/models/net-10000.npz`, so every turn end carries net_logit: the number the net
   gave the search at that real turn end.
3. Train **net-gen2-20000** with the fixed settings (2cbc3b6) on v2skx's 10⁴ games (k = 0–9 of 70100000) plus
   generation 2's 10⁴. Validation part as before (key % 20 == 0); the holdout is scored once at the end.

### Correction to the decision ratios above, and the encoding cache dropped (23:30Z)

**What was wrong:** `timing.py` repeats the same 120 positions with the same seeds in every round.
- d0e498d's per-zone cache (and e30b882's per-encoding cache) kept what an earlier round had put there, so rounds
  after the first ran partly on warm caches no real game has.
- The ratios **1.400** (without +neteot) and **1.447** (with it) are optimistic for that reason.

**The fix:** `timing.py` now empties every cache of the net at the start of each round. It sets `_table` and
`_memo` to None; with only `_table` reset, the encoding cache was still consulted before the reset could happen.

**Remeasured** (5 interleaved rounds, the same 120 positions, one process, idle machine, 23:05–23:30Z):

| net path | options | ratio | rounds | the net's ms a decision |
|---|---|---|---|---|
| 69e3ad2 (= d0e498d) | — | **1.485** | 1.49, 1.528, 1.465, 1.474, 1.469 | 41.3 |
| 69e3ad2 (= d0e498d) | +neteot | **1.541** | 1.548, 1.539, 1.545, 1.536, 1.532 | 42.0 |
| e30b882 (with the encoding cache) | +neteot | 1.622 | 1.588, 1.639, 1.653, 1.606, 1.627 | 45.5 |
| 25e246e (before the speed change; only a per-card cache, warm after the first calls) | — | 1.574 (measured before the fix) | – | 50.9 |

**What this means:**
- The speed change d0e498d brings 1.574 down to 1.485, not to 1.400.
- The encoding cache makes the search **slower**: building the key costs more than the repeats save in a fresh
  run. The e30b882 cache is taken out again; setnet.py is 69e3ad2's.
- The gates set N from their own 20-pair check on real games, so they are not affected. J100's check measured
  1.219 there.

## 10⁵: where each shard comes from (the architecture thread 23:34Z)

| shards k | games | played on | code | where the files are |
|---|---|---|---|---|
| 0–4 | 5000 | the analysis line, cloud Linux | 4d7214d | its branch, analysis/scaling/data/rec/ |
| 5–9 | 5000 | this line, cloud Linux | 4d7214d | data/rec/ |
| **10–82** | **73,000** | **Salem's computer, Windows** (11 workers, below normal, mask 0xffffe) | 4d7214d | branch `local/scaling-20261015`, 5434c6d, analysis/scaling/rec/ |
| 83–90 | 8000 | the analysis line, cloud Linux (after J98) | play path as 4d7214d | to come |
| 91–99 | 9000 | this line, cloud Linux | 69e3ad2 (play path as 4d7214d) | to come |

**About Salem's computer:**
- Salem stopped the run at 23:31Z. The shard that was open then was not committed; k83–99 are played in the cloud
  instead.
- **Checks on k10–82 (here, 23:40Z):**
  - 73 files, one per s = 70100020 … 70100164;
  - every shard has 1000 games with g = 0–999 once;
  - for every game: deal seed = s × 100003 + g, agent seeds = [s × 1000 + 2g, +1], explore 0, both sides v2skx;
  - no draws; first player won 44,845 (61.4%);
  - 2.62 CPU seconds a game on that machine.

**Why every shard has one source:** cmp_roots differs between Linux (142cc567…2b9adf) and Windows (755a0bba…96a6),
so the same seeds give different games on the two systems. If both systems played the same shard, only one copy
would be kept.

## 10⁵ training: subnormal numbers, and the switch to flushing them (the architecture thread 04:30Z, R1 / R2)

**What happened:** the 10⁵ net's epochs slowed from 234 s to about 990 s, though the batches cost the same.
- At epoch 9, 212,276 of the checkpoint's 323,332 numbers were subnormal (below 2.2e-308), in the weights
  themselves (54,363 of V1's 60,544) and in Adam's moments.
- l2 decay drives unused weights there, and CPU arithmetic on subnormal numbers is many times slower.

**R1 (registered before the trial's numbers):** epoch 10 ran unchanged. Alongside it, a copy of the epoch-9
checkpoint with every subnormal number set to 0 trained epoch 10 too. The rule: switch the main run to flushing
from epoch 11 if
1. every weight ≥ 2.2e-308 is bitwise equal between the two (fallback: max difference ≤ 1e-12), and
2. the two epoch-10 validation Brier scores agree to 6 decimals.

**Result:**
- All 9,915 normal weights are equal to the last bit (max difference 0).
- Validation Brier 0.185074212348 both, log-loss 0.541848559755 both.
- Epoch time 988 s unchanged against 247 s with the copy flushed.
- **So from epoch 11 the run uses `--ftz`:** after every step, subnormal weights and Adam moments are set to 0
  (setnet.SetNet.fit ftz, default off; 142ccdd). The 10⁵ report says so.

**R2 (inference):**

| net | subnormal weights |
|---|---|
| net-1000, net-10000, net-wide-10000 | none |
| net-gen2-20000 | 37,106 of 80,833 |

- **Flushing net-gen2-20000's at load** (`+netftz`, `ftzcheck.py`): 0 of 93,787 holdout logits change, by the
  batch pass and by the search's single-position path.
- One logit takes 0.153 ms instead of 0.261 ms (measured with two trainings running).
- J98 is recorded as it ran. J93 uses `+netftz` (registered by the architecture thread before any J93 data).

## Results at 10⁵ (2026-10-16 02:20–06:30Z)

**Data:** 100 shards, 100,000 games, merged with no duplicates and no mismatches; 1,873,395 turn ends. Shard
sources are in the table above (k10–82 Windows, the rest Linux). Holdout and scores as for 10³ / 10⁴.

**Holdout Brier** (log-loss in brackets), 93,787 turn ends:

| model | 10³ | 10⁴ | **10⁵** |
|---|---|---|---|
| linear refit (installed recipe) | 0.2013 (0.5829) | 0.2004 (0.5805) | **0.2001 (0.5798)** |
| DeepSets net, fixed settings | 0.2285 (0.6469) | 0.1937 (0.5643) | **0.18676 (0.54595)** |
| installed linear model | 0.2038 (0.5894) | | |

**The 10⁵ net (net-100000):**

| | Brier (log-loss) |
|---|---|
| training part (1,778,991 turn ends) | 0.18491 (0.54147) |
| validation part (94,404) | 0.18483 (0.54126) |
| holdout | 0.18676 (0.54595) |

- 27 epochs: 1–10 as registered, 11–27 with `--ftz` (R1).
- The training and holdout scores are close, so under the analysis line's rule the 10⁵ net is under-fitting.
- 71,081 of its 80,833 parameters are exactly 0 after training; this is looked at in the dead-unit diagnostic.

**The linear refit at 10⁵:** a training-game sample (about 1000 games, 19,717 turn ends) scores 0.1972 (0.5724).

**Readings:**
- From 10⁴ to 10⁵ games the linear refit gains 0.0003 and the net 0.0069. From 10³ to 10⁴ it was 0.0009 and 0.035.
- At 10⁵ the net is 0.0134 better than the linear refit on the same games and 0.0170 better than the installed
  model.

**Which nets used `--ftz`** (the architecture thread 06:01Z):
- net-1000, net-10000, net-wide-10000, net-gen2-20000: none.
- net-100000: from epoch 11 on.
- net-wide-100000 and net-gen3-30000: all epochs.

## How much of each net is in use (`deadunits.py`, data/deadunits.json; the architecture thread 04:37Z, description only)

**What is counted:**
- **Dead unit:** a unit that outputs 0 at every holdout turn end (phi: over every token; rho: over every position).
  The same counts come out over each net's own training data.
- **Input always 0:** an input that is 0 throughout the net's training data.
- **Weights:** each array split into exactly 0 / subnormal / normal.

| | net-10000 | net-gen2-20000 | net-100000 |
|---|---|---|---|
| phi layer 1, dead units | 0 of 64 | 1 of 64 | **39 of 64** |
| phi layer 2, dead units | 5 of 64 | 25 of 64 | **40 of 64** |
| rho layer 1, dead units | 62 of 128 | 86 of 128 | **91 of 128** |
| rho layer 2, dead units | 15 of 64 | 18 of 64 | **31 of 64** |
| static inputs always 0 | 50 of 96 | 51 of 96 | 50 of 96 |
| dynamic inputs always 0 | 6 of 23 | 6 of 23 | 6 of 23 |
| rho's pooled inputs always 0 | 197 of 448 | 273 of 448 | 316 of 448 |
| globals always 0 | 0 of 25 | 0 of 25 | 0 of 25 |
| weights: exactly 0 / subnormal / normal | 0 / 0 / 80,833 | 0 / 37,106 / 43,727 | 71,081 / 0 / 9,752 |

**Readings:**
- **Static inputs:** half of them never vary. The ramp-t mirror has 18 card ids, and many properties (hooks,
  keywords, crafts) are the same for all 18, so after standardizing they are 0. That is the data, not the net.
- **Dead units grow with training:** at 10⁵, about 25 of phi's 64 units per layer and 37 of rho's 128 first-layer
  units are alive.
  - Most of rho's pooled inputs that are always 0 follow from phi's dead second layer (7 zones × 40 = 280 of the
    316).
  - The weights into dead units get no gradient and l2 decay drives them to 0 (subnormal at gen2; exactly 0 with
    `--ftz` at 10⁵).
- **So the width actually in use is well below the nominal one,** which fits the under-fitting reading at 10⁵ and
  may be why the wide net gained only 0.0014 at 10⁴.
- Nothing in the test's settings changes; whether a next round uses another activation or decay is a separate
  decision.

### R3, registered before any result (the architecture thread 06:25Z)

**Purpose:** tell "the net is too narrow" apart from "its units die".

**Settings:** 10⁵ data, net-100000's width (phi 64-64, rho 128-64). The only change is ReLU → leaky ReLU with
negative slope 0.01 (`--slope 0.01`; setnet's ReLU path is unchanged, checked bitwise on net-10000's and
net-100000's holdout probabilities). Everything else is as net-100000: Adam 1e-3, batch 256, l2 1e-5, step halving
and stopping, `--ftz`.

**J104:** R3's holdout Brier point estimate is below net-100000's 0.18676 (60%).
- Its dead-unit counts are reported too: a unit whose output is never positive.
- Order: after the wide 10⁵ net, and after net-gen3-30000, which goes first when generation 3's data arrives.
- R3 is a description only; this test's conclusions do not change with it.

## Another pairing: the elf-t mirror (连击妖, preparation and smoke only; the architecture thread 08:18Z)

**The strong level on the elf-t mirror:**
- In this repository `LEVELS["strong"]` is `mcts:200+plan+learned+phased` (v2s). v2skx is the install package
  prepared for Salem's computer.
- On the elf-t mirror both read the installed `elf-t-elf-t-ended.json` and `-act.json`: pkg-kc-ramp-ramp replaces
  only the original Ramp mirror's model.
- So v2s and v2skx differ there only by the discard pruning.
- The installed elf-t turn-end model has the same recipe as ramp-t's (version 2 + hand, hpphase; 87 coefficients;
  fitted on 27,716 positions).

**What carries over unchanged:**
- **Recorder:** `scaledata play --deck elf-t --opponent elf-t`.
- **Token encoding:** generic; static rows come from card definitions, scripts and measured roles.
- **The linear label:** SPEC's turn-end model is picked per pairing by deck name.
- **`after_end_of_turn` and `+neteot`:** generic.
- **SetNetEnded:** scores only the net's own pairing (info deck / opponent).

**What changed:** `train.py` takes `--deck`, `--opponent`, `--base` and `--holdout-base` (defaults: the ramp-t mirror
and its seeds). The net's info pairing, the linear refit's matchup and the installed model it is compared with
follow them.

**Smoke** (temporary seed 7300, not part of any data):
- **Play:** 6 games of v2skx on the elf-t mirror all finished. 4.2 CPU seconds a game, 84.7 actions on average,
  first player 5 of 6.
- **Encode:** 101 turn ends, 20 card ids (ramp-t: 18), 40.2 tokens a position; the linear label is finite
  everywhere.
- **A 2-epoch net** trained with `--deck elf-t --opponent elf-t` names the elf-t pairing.
- **Search with it:** 2 games of v2skx+setnet=that net+neteot finished, with 49,234 net calls between them. A
  ramp-t game with the same net made no call to it.
- **Not done:** no large run, no seeds registered.

## net-gen3-30000 and R3 (2026-10-16 07:55–08:55Z)

**net-gen3-30000:**
- **Data:** v2skx's k = 0–9, generation 2's k = 0–9, generation 3's k = 0–9 (s = 71300000 + 2k: the analysis
  line, 34ae44c; 10,000 games checked game by game, first player 60.5%).
- **Settings:** fixed, with `--ftz` throughout. 20 epochs; no subnormal weight left.

| | Brier (log-loss) |
|---|---|
| training part (519,870 turn ends) | 0.18839 (0.54951) |
| validation part (26,916) | 0.18628 (0.54561) |
| holdout | **0.18920 (0.55236)** |

- For comparison on the holdout: net-gen2-20000 0.1900, net-10000 0.1937, net-100000 0.18676.

**R3 (net-leaky-100000):** leaky ReLU 0.01, otherwise net-100000's settings, `--ftz`; 24 epochs.

| | Brier (log-loss) |
|---|---|
| training part | 0.18434 (0.53999) |
| validation part | 0.18489 (0.54129) |
| holdout | **0.18692 (0.54648)** |

- net-100000 on the holdout: 0.18676 (0.54595). J104 is the analysis line's to read.
- **Units never positive**, R3 against net-100000:

  | layer | R3 | net-100000 |
  |---|---|---|
  | phi layer 1 | 19 of 64 | 39 |
  | phi layer 2 | 0 of 64 | 40 |
  | rho layer 1 | 63 of 128 | 91 |
  | rho layer 2 | 20 of 64 | 31 |

- With leaky ReLU those units still pass gradient: every weight of W2, V1, V2 and v3 is normal; only W1s / W1d
  have exact zeros (3,200 / 384).
- No pooled input is always 0 (net-100000: 316 of 448).

## Generation 4: two nets, two holdouts (registered by the architecture thread 08:53Z, before any gen-4 game)

The analysis line plays generation 4 with net-gen3-30000 as the player, at seeds 71600000 + 2k. Shard k = 9 stays out of
training and becomes the self-play holdout. The net-100000 self-play already played (k = 0–1) is kept as "sp-net100000".
Both nets use the default structure (ReLU, phi 64-64, rho 128-64, `--ftz`). The wide structure is used only if the wide 10⁵
net is at least 0.0035 lower than the default structure on both holdouts.

| net | `--size` | training shards |
|---|---|---|
| net-gen4-39000 | 39000 (10 v2skx shards) | v2skx 10⁴ + `--add 70800000:10 --add 71300000:10 --add 71600000:9` |
| net-all-131000 (`--name all`) | 131000 (100 v2skx shards) | v2skx 10⁵ + the same three `--add` + sp-net100000's two shards |

Every net reports both holdouts. The v2skx holdout (70200000 + 2h) works as before. The gen-4 k = 9 shard goes through
`--extra-holdout selfplay:71600018`, on `net` and on `holdout-net`. That option adds `holdout_selfplay` to the report and
writes data/holdout-selfplay-net-<tag>.npz. It refuses a seed that is among the net's own training shards. Without the
option, output is as before.

Condition: the opponent's deck list is known (order and hand not).

## The wide 10⁵ net, scored from its epoch-17 checkpoint (not converged; the architecture thread 10:37Z)

The wide 10⁵ fit (phi 128-128, rho 256-128, ReLU, `--ftz`) reached the 2-hour background limit after epoch 17. It was not
resumed: its best validation Brier (0.18489, epoch 16) was already level with net-100000's (0.18483). The structure rule
needs it 0.0035 lower, and one or two more epochs at step size 6.25e-5 could not make that up. models/net-wide-100000.npz
holds the checkpoint's best weights (epoch 16 by validation log loss). They came from the same `net` command with
`--epochs 17`, which trains no further epoch. Its report (data/net-wide-100000.json) carries a "not converged" note.

| net | parameters (approx.) | epochs | valid Brier | holdout Brier | holdout log loss |
|---|---|---|---|---|---|
| net-100000 (ReLU 64-64 / 128-64) | 1× | 27 | 0.18483 | 0.18676 | 0.54595 |
| net-leaky-100000 (R3) | 1× | 24 | 0.18489 | 0.18692 | 0.54648 |
| net-wide-100000 (epoch-17 checkpoint) | ≈4× | 17 | 0.18489 | 0.18649 | 0.54534 |

Wide minus default on the holdout is −0.0003, far from the −0.0035 the rule asks for. Generation 4 therefore uses the
default structure (ReLU 64-64 / 128-64, `--ftz`).

Dead units (data/deadunits.json, now 5 nets): units whose output is never positive anywhere on the holdout.

| layer | net-100000 dead | live | net-wide-100000 dead | live |
|---|---|---|---|---|
| phi layer 1 | 39 of 64 | 25 | 104 of 128 | 24 |
| phi layer 2 | 40 of 64 | 24 | 107 of 128 | 21 |
| rho layer 1 | 91 of 128 | 37 | 217 of 256 | 39 |
| rho layer 2 | 31 of 64 | 33 | 81 of 128 | 47 |

Doubling the width left about the same number of live units in the first three layers. The extra units died. With `--ftz`
there are 0 subnormal weights. Pooled rho inputs that are 0 throughout training: 798 of 896 (net-100000: 316 of 448).
This is a description only.

Condition: the opponent's deck list is known (order and hand not).

## Generation 4 results (2026-10-16 13:30Z–)

The v2skx holdout is 70200000 + 2h, h = 0–4, 93787 turn ends. The self-play holdout is gen 4's k = 9 (71600018), 17948
turn ends; it is in no net's training.

| net | v2skx holdout Brier | self-play holdout Brier | self-play log loss |
|---|---|---|---|
| installed linear | 0.2038 | 0.20723 | 0.60109 |
| net-10000 | 0.19369 | 0.20123 | 0.58455 |
| net-gen2-20000 | 0.19004 | 0.19649 | 0.57078 |
| net-gen3-30000 | 0.18920 | 0.19539 | 0.56687 |
| **net-gen4-39000** (21 epochs, 3215 s) | **0.18868** | **0.19303** | **0.56109** |
| net-sp-29000 (self-play only: gen 2, 3, 4 k 0–8; 26 epochs, 3119 s) | 0.19185 | 0.19355 | 0.56236 |
| **net-gen4-59000** (gen4-39000's data + 2×10⁴ extra gen-4 games; 29 epochs) | **0.18832** | **0.19064** | **0.55445** |
| net-100000 | 0.18676 | 0.19550 | 0.56783 |
| net-leaky-100000 | 0.18692 | 0.19587 | 0.56806 |
| net-wide-100000 (not converged) | 0.18649 | 0.19420 | 0.56403 |
| **net-all-131000** (未收敛（第 12 轮）: epoch-14 checkpoint, best epoch 12) | **0.18659** | **0.19230** | **0.55855** |

net-gen4-39000 (models/net-gen4-39000.npz, sha256 1a177260…) was trained with ReLU 64-64 / 128-64 and `--ftz`.

Condition: the opponent's deck list is known (order and hand not).

net-all-131000 (models/net-all-131000.npz, sha256 4e377143…) is the install candidate. It trained on 131 shards: v2skx
10⁵, gen 2, gen 3, gen 4 k = 0–8 and sp-net100000. It uses ReLU 64-64 / 128-64 and `--ftz`, and has 0 subnormal weights.
The fit reached the 2-hour limit after epoch 14. Validation Brier per epoch:

| epoch | 6 | 9 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|
| valid Brier | 0.18659 | 0.18602 | 0.18572 | **0.18569** | 0.18634 | 0.18582 |

At epoch 14 the step size was 1.25e-4. Following the architecture thread (15:28Z, option b), the fit was not resumed. The
file holds the checkpoint's best weights (epoch 12), taken with the same command and `--epochs 14`, which trains no further
epoch. The report carries the note 「未收敛（第 12 轮）」.

net-sp-29000 (models/net-sp-29000.npz, sha256 ee697fa9…; the architecture thread 16:23Z) was trained on self-play only:
gen 2, gen 3 and gen 4 k = 0–8, with no v2skx games (`--size 29000`, 0 v2skx shards). It uses ReLU 64-64 / 128-64 and
`--ftz`. Removing v2skx's 10⁴ games from net-gen4-39000's data made it worse on both holdouts: +0.0032 on v2skx and
+0.0005 on self-play. Dead on the holdout: phi 6 / 31 of 64, rho 86 of 128 / 10 of 64; 0 subnormal weights.
`deadunits.py` now adds to data/deadunits.json instead of rewriting it.

## net-elft-10000: the first net on the elf-t mirror (连击妖; the architecture thread 21:40Z, registered in the analysis line's 26acfd9)

The data is the analysis line's 37252cc. Training uses data/elf-t/rec, 71900000 + 2k (k = 0–9), 1000 games each. The
holdout is data/elf-t/heldout, 72000000 + 2h (h = 0–4), 88311 turn ends. Every file's sha256 matched. The records were
encoded into their own token folder (22 card ids; ramp-t has 18) with the default spec. The 'linear' label is therefore
the installed elf-t turn-end model.

    python analysis/scaling/train.py --deck elf-t --opponent elf-t --base 71900000 --holdout-base 72000000 \
        net --size 10000 --name elft --ftz --tokens TOK-ELFT --checkpoint CKPT

The structure is ReLU 64-64 / 128-64 with `--ftz`. The fit took 16 epochs and 699 s. The model is
models/net-elft-10000.npz (sha256 3278ad1a6ce5c6b576b7ba134f1216def01740fc4711b1dc2cabbb9a7573b1fa); its info pairing is
elf-t / elf-t. The holdout probabilities are in data/holdout-net-elft-10000.npz.

| | valid (8954) | holdout Brier (88311) | holdout log loss |
|---|---|---|---|
| net-elft-10000 | 0.18441 | **0.19086** | 0.55551 |
| installed elf-t linear, same holdout | | 0.20834 | 0.5985 |

The net is 0.0175 below the installed linear model. On the ramp-t mirror, net-10000 was 0.0101 below its linear model
(0.19369 vs 0.2038).

Dead units on the holdout: phi 0 / 2 of 64, rho 57 of 128 / 7 of 64. There are 0 subnormal weights. Pooled rho inputs
that are 0 throughout training: 146 of 448. `deadunits.py` takes `--holdout-base` (the elf-t mirror: 72000000).

Condition: the opponent's deck list is known (order and hand not).

net-gen4-59000 (models/net-gen4-59000.npz, sha256 1adbebb98a4fc82af28eed70bec065115f638ea4f377b9de9182362c35b27835; the
architecture thread 21:40Z) was trained on net-gen4-39000's 39 shards plus the 40 extra gen-4 shards (72300000 + 2k,
500 games each, data/gen4x). The command was `--size 59000 --name gen4 --add 70800000:10 --add 71300000:10 --add
71600000:9 --add 72300000:40 --ftz --extra-holdout selfplay:71600018`; 71600018 is in no net's training. The structure
is unchanged (ReLU 64-64 / 128-64). A container restart stopped the fit after epoch 19. The same command resumed it from
the checkpoint, which holds the RNG state, so the fit equals an unbroken one. It stopped by patience after epoch 29.

Compared with net-gen4-39000, the extra 2×10⁴ games moved the v2skx holdout by −0.0004 (0.18868 → 0.18832) and the
self-play holdout by −0.0024 (0.19303 → 0.19064). net-gen4-59000 is the best net so far on the self-play holdout
(net-all-131000: 0.19230). Dead on the holdout: phi 31 / 38 of 64, rho 85 of 128 / 21 of 64; 0 subnormal weights.

## Input versions v2 and v2kc: net-in2-59000 and net-in2kc-59000 (the architecture thread 2026-10-17 01:30Z)

`learn.tokens` takes an input version (`inputs`); v1, the default, is the encoding every earlier net has, unchanged.
- **v2**: every token has three more columns.
  - share: in my deck, the chance that my next draw is this card; in the opponent's unseen pool, the expected
    copies of it in their hand (hand size × count / pool size), in thousandths.
  - next_pp: the owner's play points next turn.
  - next_evolve: whether the owner can evolve next turn.
  
  Also, a field follower's attack state is read as of its owner's next turn. At a turn end it still described the
  turn just played: attacks are reset only at the owner's turn start.
- **v2kc**: v2 plus the seven lethal-clock globals (`learn.features` kclock).

A net saves its version with its file; a file without one is v1, so every earlier file and its numbers are unchanged.
`scaledata encode --inputs v2|v2kc` writes the tokens.

**Old nets unchanged.** tests/data/setnet_golden_69e3ad2.json holds the logits of gen3-30000, net-elft-10000 and
gen4-59000 on all 71 turn ends of holdout rec-70200000's first 4 games. They were computed in a 69e3ad2 checkout, and
`test_old_nets_give_the_69e3ad2_numbers_bit_for_bit` checks them string for string. Other tests check v2 / v2kc:
single position equals the batch pass, gradients against finite differences, the version kept in the file, and what
share, next-turn values and attack state mean.

**Data.** The same 79 training shards and two holdouts as gen4-59000 (85 record files) were encoded again as v2 and as
v2kc. Each file was checked against v1: same positions, results, linear labels and v1 globals, and every column v2
does not change is identical. 1.4% of the tokens (572020 of 41752217) got the next-turn attack state. The training
command is gen4-59000's with `--name in2` / `--name in2kc` and the v2 / v2kc token folder.

| net | inputs | epochs | valid Brier | v2skx holdout Brier | self-play holdout Brier (log loss) | µs per call | sha256 |
|---|---|---|---|---|---|---|---|
| net-gen4-59000 | v1 | 29 | 0.18754 | 0.18832 | 0.19064 (0.55445) | 131 (1.00×) | 1adbebb9… |
| **net-in2-59000** | v2 | 29 | 0.18633 | **0.18767** | **0.18911** (0.55134) | 160 (1.22×) | c37e82bc… |
| net-in2kc-59000 | v2kc | 22 | 0.18647 | 0.18798 | 0.18920 (0.55121) | 179 (1.37×) | a49cb0dd… |
| net-in2a-59000 | v2a | 24 | 0.18637 | 0.18793 | 0.18928 (0.55103) | 137 (1.23×)¹ | 71f13486… |

The v2 inputs improve both holdouts (−0.0007 and −0.0015) at no extra data. The lethal clock adds nothing on top of
them offline (+0.0003 / +0.0001).

The µs per call column is `analysis/scaling/inputcost.py`. It records the 1608 positions gen4-59000 was called on in
8 search decisions (ramp-t mirror, mcts:200 + neteot) and replays them through each net with cold caches; the figure
is the best of 5 interleaved rounds on the same machine. The net's share of a step was 40% (see the earlier timing),
so a step costs about +9% (v2) and +15% (v2kc).

A first version of the v2 search path rebuilt every pooled card's token row before its phi lookup, at 1.89× per call.
It now builds a row only when that phi is missing. The logits of both nets on 111 turn ends are identical before and
after the change.

Dead units on the v2skx holdout: in2: phi 23 / 32 of 64, rho 84 of 128 / 29 of 64; in2kc: phi 15 / 34, rho 86 / 22.
Both nets have 0 subnormal weights.

Condition: the opponent's deck list is known (order and hand not).

**v2a (the architecture thread 04:21Z, after J116 / J117 found both v2 nets weaker in play).** v2a has v2's three
columns, with v1's attack state (attacks_left, can_hit_*): it tests whether the next-turn attack state is what cost
v2 its strength. v2a has v2's widths, so its token files carry an `inputs` mark. The token files were built from the
v2 files by putting v1's three attack columns back. Three shards (70100000, 72300040, 70200004) encoded with
`--inputs v2a` were identical to them, array for array. The training command is gen4-59000's with `--name in2a`. A
container restart stopped the fit after epoch 3; it was resumed from the checkpoint, which holds the RNG state.
Offline, in2a equals in2 (0.18793 / 0.18928 against 0.18767 / 0.18911). Dead on the holdout: phi 23 / 29 of 64,
rho 90 of 128 / 29 of 64; 0 subnormal weights.

¹ in2a's cost was measured after 33a8495 (the live memo), in a second run of `inputcost.py`. In that run: gen4-59000 111 µs,
in2 139 µs (1.26×), in2kc 176 µs (1.59×: the lethal clock is not memoized), in2a 137 µs (1.23×).

## net-elft-gen2-19500: the elf-t mirror's second generation (registered by the analysis line, J120 / J121)

The data is the elf-t mirror's 10⁴ games (71900000 + 2k, k = 0–9, v2skx) plus its gen-2 self-play k = 0–18
(72800000 + 2k, 500 games each, net-elft-10000 + neteot; data/elf-t2). Gen-2 k = 19 (72800038) is held out. Inputs v1,
ReLU 64-64 / 128-64, `--ftz`:

    python analysis/scaling/train.py --deck elf-t --opponent elf-t --base 71900000 --holdout-base 72000000 \
        net --size 19500 --name elft-gen2 --add 72800000:19 --ftz --tokens TOK-ELFT --checkpoint CKPT \
        --extra-holdout selfplay:72800038

| net | epochs | valid Brier | elf-t holdout Brier (88311) | gen-2 self-play holdout Brier (9361) |
|---|---|---|---|---|
| installed elf-t linear | | | 0.20834 | 0.20518 |
| net-elft-10000 | 16 | 0.18441 | 0.19086 | 0.19310 |
| **net-elft-gen2-19500** | 17 | 0.18502 | **0.19088** | **0.18415** |

The model is models/net-elft-gen2-19500.npz (sha256
e244c577a174f8c43728755f14216750e3307cf59f659be68acaa1a7292cc58f). The holdout probabilities are in
data/holdout-net-elft-gen2-19500.npz and data/holdout-selfplay-net-elft-gen2-19500.npz.

On the v2skx-played holdout the second generation equals the first. On the positions its own player reaches (the
gen-2 self-play holdout) it is 0.0090 lower. Dead on the holdout: phi 0 / 6 of 64, rho 72 of 128 / 16 of 64; 0
subnormal weights.

Condition: the opponent's deck list is known (order and hand not).

## D6: what the lethal agent buys (registered by the analysis line, method B)

The script is analysis/scaling/d6_lethal.py; the outputs are in data/d6.

**Part 1, time split** (ramp-t seed 74000000, elf-t 74000002, 20 games each; split-*.json). Shares of a decision's time:

| mirror | decisions | ms / decision | planner | full | near | screen | rest (search) |
|---|---|---|---|---|---|---|---|
| ramp-t | 1277 | 49.18 | 0.0054 | 0.0079 | 0.0533 | 0.2205 | 0.7129 |
| elf-t | 1910 | 59.73 | 0.0389 | 0.0271 | 0.0493 | 0.1984 | 0.6864 |

**Part 2a, sure-lethal starts** (points-*.json). A point is the first decision of a turn where the planner, or
LethalSearch.solve, is sure of lethal, and its first move is the recorded move. Ramp-t's points come from rec-71600018
plus gen4x (21000 games); elf-t's come from elf-t2 (10000 games). 200 points were sampled from each with
`random.Random(73900000)`.

| mirror | points found | per game | planner | full | near | screen | sample (planner / full / near / screen) |
|---|---|---|---|---|---|---|---|
| ramp-t | 17424 | 0.83 | 64.3% | 13.3% | 12.7% | 9.7% | 140 / 19 / 21 / 20 |
| elf-t | 9167 | 0.917 | 77.7% | 16.0% | 5.1% | 1.3% | 156 / 26 / 14 / 4 |

**Part 2b, conversion by the bare search** (convert-*.json). From each point the bare search (`mcts-raw:160` for
ramp-t with net-gen3-30000, `mcts-raw:140` for elf-t with net-elft-10000, i.e. the equal-compute player without
LethalAgent) plays the rest of the turn (at most 60 steps), three times, with seeds B + 3j + r (B = 73900000 ramp-t,
73950000 elf-t). A run converts if the game is won within that turn.

| mirror | planner | full | near | screen | all (600 runs) | 95% CI (by point) |
|---|---|---|---|---|---|---|
| ramp-t | 359/420 85.5% | 46/57 80.7% | 47/63 74.6% | 60/60 100% | **512/600 85.3%** | 80.5–90.2% |
| elf-t | 423/468 90.4% | 68/78 87.2% | 24/42 57.1% | 6/12 50% | **521/600 86.8%** | 82.3–91.4% |

The outcome is nearly fixed per point: in ramp-t 169 points convert 3/3 and 27 convert 0/3 (4 mixed); in elf-t 170
and 23 (7 mixed). The sample is uniform over points, so the "all" rate estimates the rate over all sure-lethal starts.
Without the lethal agent, about 0.83 × 14.7% ≈ 0.12 (ramp-t) and 0.917 × 13.2% ≈ 0.12 (elf-t) sure-lethal turns per
game are not won that turn (some of these games may still be won later). The cost is 28.7% / 31.4% of decision time,
22.1% / 19.8% of it in the screen alone. The screen's own points (ramp-t 9.7% of points) all converted in ramp-t (20
points, 60/60). Elf-t has only 4 screen points.

J124 (ramp-t bare N160 converts ≥ 90%, probability 35%): 85.3%, below 90%.

**`+screen=0:1000:4` (the architecture thread, after D6).** With no code change it turns off only the far screen. A
position whose estimate falls short by more than 4 gets budget 0. The root's `_search` returns at once (nodes 0, no
line, not sure), and LethalAgent then hands the decision to the tree search, as when 200 nodes find nothing. Near
positions keep 1000 nodes and unscreened ones keep 2000. The lethal search seeds its own `random.Random(seed)` on
each solve and never touches the game's generator, so nothing else moves. tests/test_lethal.py
(`test_screen_budget_zero_skips_only_the_far_screen`) covers this: the spec parses, a far position expands no node,
and near and unscreened positions give the same result as 200:1000:4.

What budget 0 leaves was measured by d6_screen0.py on recorded positions (100 games each; data/d6/screen0-*.json).
These are not agent decisions: every main-phase step of the record counts.

| records | far-screen positions | solve at 200 | solve at 0 | of it damage_estimate | screen lethals at 200 |
|---|---|---|---|---|---|
| ramp-t rec-72300000 | 5553 | 14.2 ms | 0.28 ms | 0.25 ms | 56 |
| elf-t rec-72800000 | 8523 | 23.3 ms | 0.29 ms | 0.24 ms | 10 |

The estimate is paid today as well. Budget 0 adds about 0.04 ms (the root's state_key and the generator), and it
keeps about 1.2–2% of the screen's time. Near and unscreened results were identical at 327 / 360 positions
(probability, line, sure, nodes, complete).

Condition: the opponent's deck list is known (order and hand not).

## net-elft-gen3-29000: the elf-t mirror's third generation (registered by the analysis line, 8a1cf5e; J129 / J130)

The data is the elf-t mirror's 10⁴ games (71900000 + 2k, k = 0–9, v2skx), its gen-2 self-play k = 0–18 (72800000,
data/elf-t2) and its gen-3 self-play k = 0–18 (74100000 + 2k, 500 games each, net-elft-gen2-19500 + neteot;
data/elf-t3). Gen-2 k = 19 (72800038) and gen-3 k = 19 (74100038) are held out. SIZES has 29000 for sp-29000 (self-play
only), so `--base-shards 10` (dab8ce4; default SIZES[size], every earlier command unchanged) takes the 10 v2skx shards.
Inputs v1, ReLU 64-64 / 128-64, `--ftz`, patience 4:

    python analysis/scaling/train.py --deck elf-t --opponent elf-t --base 71900000 --holdout-base 72000000 \
        net --size 29000 --base-shards 10 --name elft-gen3 --add 72800000:19 --add 74100000:19 --ftz \
        --tokens TOK-ELFT --checkpoint CKPT --extra-holdout selfplay:72800038 --extra-holdout selfplay3:74100038

The fit took 17 epochs and 1664 s (best epoch 13). The two earlier nets were scored on the gen-3 holdout with
`holdout-net ... --extra-holdout selfplay3:74100038`; their other numbers are unchanged.

| net | epochs | valid Brier | elf-t holdout Brier (88311) | gen-2 self-play holdout (9361) | gen-3 self-play holdout (9128) |
|---|---|---|---|---|---|
| installed elf-t linear | | | 0.20834 | 0.20518 | 0.20395 |
| net-elft-10000 | 16 | 0.18441 | 0.19086 | 0.19310 | 0.18431 |
| net-elft-gen2-19500 | 17 | 0.18502 | 0.19088 | 0.18415 | 0.17837 |
| **net-elft-gen3-29000** | 17 | 0.17901 | **0.18803** | **0.18125** | **0.17319** |

The model is models/net-elft-gen3-29000.npz (sha256
2102bd023c65ba7cdb612f9be69cf1305e64645afcccbd835b77996c1691ebac); the report is data/net-elft-gen3-29000.json. The
per-position holdout probabilities are data/holdout-net-elft-gen3-29000.npz (elf-t, 72000000:5),
data/holdout-selfplay-net-elft-gen3-29000.npz (72800038) and data/holdout-selfplay3-net-elft-gen3-29000.npz
(74100038).

Unlike gen 2, gen 3 also improves the v2skx-played holdout (−0.0029 against both earlier nets). On the positions its
own player reaches it is 0.0052 below gen 2; on gen 2's positions, 0.0029 below. The valid set is drawn from the
training shards, so it is not comparable across nets. Dead on the holdout: phi 4 / 25 of 64, rho 87 of 128 / 21 of 64;
0 subnormal weights.

Condition: the opponent's deck list is known (order and hand not).

## A move prior, step 1: data, network, offline report (the architecture thread 11:37Z; the analysis line's lines 95dc772 / 42cec2a)

learn/setpolicy.py. A decision is a searched main-phase decision of a self-play record with two distinct moves or
more. Moves that are the same to the search (one `action_key`, such as two copies of a card in hand) share one
child, and the record gives each of them its count. Here they are one move. The target is the root's visits over
the distinct moves; `--tau 0.5` squares them before normalizing.

The position is learn.tokens.encode of the player to act, run through the value net's trunk. A move is three parts:
- its kind and its target's kind;
- eight numbers (cost, play points after it, kills / dies / face for an attack, targets, mode, fused cards);
- phi of the acting card's token and of its first target's token.

No card id, no per-card score. Each mirror has four versions: fine-tuned (`ft`, the trunk starts from the value net
and is fitted too) or frozen (`fz`, head only), at tau 1 or 0.5. Adam, lr 1e-3, l2 1e-5, batch 256, patience 4,
`--ftz`. The validation part is the games with seed·100003 + g a multiple of 20, inside the training shards.

- **elf-t:** 72800000 + 2k and 74100000 + 2k, k = 0–18 (38 shards; 72800038 and 74100038 are in neither); init
  net-elft-gen3-29000.
- **ramp-t:** 72300000 + 2k, k = 0–39 (gen4x); init net-gen4-59000. The holdout is 71600018.

The fits ran in planned chunks (`--epochs 8 / 16 / …` from the checkpoint, which holds the RNG state; a resumed fit
equals an unbroken one, tests/test_setpolicy.py), each under 2 h, until patience stopped them. Three runs were
killed by the container's memory limit at load before any epoch of theirs was lost. The causes were the whole
data kept next to its two parts, then the per-file parts next to their concatenation. Both are fixed: `Decisions.split`
fills arrays allocated once, with the same arrays (test). No chunk hit the 2 h limit.

| prior | file | epochs (best) | valid CE (its own tau) | fit s | sha256 |
|---|---|---|---|---|---|
| elf-t ft | models/prior-elft-ft.npz | 34 (30) | 1.44145 | 12316 | 973ffd83… |
| elf-t fz | models/prior-elft-fz.npz | 31 (27) | 1.47905 | 5639 | c73d915c… |
| elf-t ft τ0.5 | models/prior-elft-ft-t05.npz | 36 (32) | 1.27785 | 13902 | bc086c53… |
| elf-t fz τ0.5 | models/prior-elft-fz-t05.npz | 37 (33) | 1.35753 | 7148 | 03f72b9a… |
| ramp-t ft | models/prior-ramp-ft.npz | 43 (39) | 1.27435 | 9382 | ebb209a5… |
| ramp-t fz | models/prior-ramp-fz.npz | 37 (33) | 1.33356 | 4274 | 8b5f4fdd… |
| ramp-t ft τ0.5 | models/prior-ramp-ft-t05.npz | 38 (35) | 1.09904 | 8639 | 23708146… |
| ramp-t fz τ0.5 | models/prior-ramp-fz-t05.npz | 39 (36) | 1.19230 | 5068 | db963849… |

Training: elf-t 1331969 decisions (valid 70993); ramp-t 889226 (valid 46477). Full sha256 in data/policy/SHA256SUMS.

**Offline report** (analysis/scaling/policy_offline.py; data/policy/offline-*.json; per-decision rows in
data/policy/dump-*.jsonl.gz). The figures:
- top1: the method's first move is a most-visited move (first in legal order on a tie of the prior);
- top2: the visits of its first two;
- KL: KL(π ‖ q) against the recorded visits at tau 1 for every version. The tau-0.5 versions were fitted to a
  sharper target, so a higher KL is by construction.
- end: whether "end the turn" is first, against whether it is the search's most-visited move. Ending is legal at
  every decision.

"order" is the search's expansion order now (`_options` without a prior, the recorded player); "uniform" is the
expected value of a random order. The analysis line's D8: the recorded player searching the same position again
with other seeds agrees on its first move 91.7% (ramp-t) / 86.3% (elf-t).

elf-t, gen-3 holdout 74100038 (500 games, 36399 decisions; 9183 turn-first):

| method | top1 | top2 | KL | end | top1 first / rest | KL first / rest |
|---|---|---|---|---|---|---|
| uniform | 0.2645 | 0.4645 | 0.2297 | 0.7540 | 0.1892 / 0.2900 | 0.1940 / 0.2418 |
| order | 0.4219 | 0.5364 | | 0.9289 | 0.3163 / 0.4575 | |
| ft | 0.6678 | 0.6197 | 0.0646 | 0.9718 | 0.6311 / 0.6802 | 0.0625 / 0.0653 |
| fz | 0.6085 | 0.6014 | 0.1025 | 0.9513 | 0.5931 / 0.6137 | 0.0830 / 0.1091 |
| ft τ0.5 | 0.6690 | 0.6193 | 0.1211 | 0.9727 | 0.6329 / 0.6812 | 0.1195 / 0.1216 |
| fz τ0.5 | 0.6142 | 0.6025 | 0.1313 | 0.9537 | 0.6033 / 0.6179 | 0.1268 / 0.1328 |

ramp-t, holdout 71600018 (1000 games, 46781 decisions; 17132 turn-first). "old" is learn/policies/ramp-ramp.npz:
the old Ramp mirror, card one-hot over 17 cards, 14 of this data's 18. Its probabilities are added per key.

| method | top1 | top2 | KL | end | top1 first / rest | KL first / rest |
|---|---|---|---|---|---|---|
| uniform | 0.2956 | 0.5257 | 0.3368 | 0.7210 | 0.2195 / 0.3395 | 0.3666 / 0.3195 |
| order | 0.4447 | 0.6128 | | 0.8822 | 0.3701 / 0.4878 | |
| old | 0.5148 | 0.6304 | 0.2288 | 0.8878 | 0.4389 / 0.5587 | 0.2761 / 0.2014 |
| ft | 0.7360 | 0.6916 | 0.0695 | 0.9654 | 0.6697 / 0.7743 | 0.0989 / 0.0525 |
| fz | 0.6839 | 0.6785 | 0.1289 | 0.9437 | 0.6229 / 0.7191 | 0.1630 / 0.1092 |
| ft τ0.5 | 0.7474 | 0.6922 | 0.1383 | 0.9677 | 0.6867 / 0.7825 | 0.1760 / 0.1164 |
| fz τ0.5 | 0.6956 | 0.6791 | 0.1653 | 0.9485 | 0.6323 / 0.7322 | 0.2106 / 0.1392 |

elf-t gen-2 holdout 72800038 (reported only; played by net-elft-10000's player, 37284 decisions): ft 0.6634 /
fz 0.5964 / ft τ0.5 0.6654 / fz τ0.5 0.6051 top1, against order 0.4076 and uniform 0.2680.

The pass or fail of each version is the analysis line's (its registered lines). This report only gives the
numbers. Offline agreement is not strength: whether a prior helps is the gate's question, with its cost counted.

Condition: the opponent's deck list is known (order and hand not).

## B: PUCT at every node (search.mcts `puct`, agent option `+puct=PATH[:C[:T]]`; the architecture thread 18:59Z)

A node picks its move by Q + c_puct · P · √(node visits) / (1 + move visits). This replaces UCB1's exploration
term; no move is forced to be tried first. An unvisited move scores Q = the node's value − 0.1, and a node not yet
visited counts as 0.5.

P is the prior (learn.setpolicy) over the node's open moves, one per action key, sharpened by 1 / T. It is computed
once, the first time a move is picked at the node, and kept on the node. A move open in some determinizations only,
with no entry, gets 1 / (open moves). PUCT and the root prior (+prior / +mimic) can't be combined.

Off, the search is unchanged: tests/test_golden_search.py replays bit for bit, and the whole suite passes. Tests
(tests/test_puct.py) check four things: one prior per node over its open moves; a peaked prior takes the visits
and leaves moves untried; the spec option; the temperature.

**Cost** (analysis/scaling/puct_cost.py; data/policy/puct-cost-*.json). It runs on recorded positions, so no game
is played and no seed is drawn: the holdouts' first games, the searched decisions only. Each spec gets a fresh
player per position, and the specs take turns. Each spec is the candidate with `+puct=prior-<mirror>-<ft|fz>.npz:1`.
The prior's trunk is its own (from gen4-59000 / elft-gen3-29000), not the candidate's net.

| mirror | candidate | decisions | base ms | ft ms (×) | fz ms (×) | equal-wall N, ft / fz |
|---|---|---|---|---|---|---|
| ramp-t | gen3-30000 N 120 | 248 | 65.9 | 76.0 (1.15) | 75.6 (1.15) | 96.9 / 96.5 |
| elf-t | elft-gen2-19500 N 105 | 310 | 79.2 | 96.8 (1.22) | 96.7 (1.22) | 74.9 / 75.6 |

The equal-wall N comes from a line through the PUCT spec's times at N 120 and 72 (ramp-t) / 105 and 63 (elf-t),
solved for the base time:
- ramp-t: 23.9 ms + 0.434 ms per iteration (ft);
- elf-t: 35.1 ms + 0.588 ms per iteration (ft).

The chosen priors (the analysis line's O1, 31dd112: ft-t05 in both mirrors) were timed in a second run the same way
(data/policy/puct-cost-*-t05.json). The machine was a little slower than in the first run; the ratios are the same:
- ramp-t: base 73.2 ms, ft-t05 83.6 ms (×1.14), equal-wall N 98.0;
- elf-t: base 85.9 ms, ft-t05 104.2 ms (×1.21), equal-wall N 76.8.

**Read by the gates (the analysis line's a07ba82).** The gates ran at c_puct 2. That costs more per iteration than
the c_puct 1 measured here: at N 97 / 75 the analysis line's 20-pair check found ms ratios of 1.103 / 1.055, and
the gates used N 88 (ramp-t) / 71 (elf-t). Time a PUCT spec at the c_puct it will play with. The gates' results
are the analysis line's.

**A note from the analysis line's check (31dd112).** search.xprune's cache (`XPrune.allowed`) is keyed by hand uids,
which are unique within a game only, so one player object reused across games can hit another game's entry. A game
(arena, the trainer's `start` / `resume`) always makes a new player. policy_offline.py used one player for a whole
shard: 3 of ramp-t's 46781 decisions had another expansion order, 1 of them another first move. It now makes a new
player each game. The "order" figures above are the earlier run's. Run again with a new player each game, they are
the same to 4 decimals, except ramp-t's top2: 0.4625 (turn-first) and 0.6997 (the rest), against 0.4624 / 0.6998. The cache itself is now emptied when a new game
starts (cdc7b6f, the architecture thread 19:11Z; tests/test_xprune_games.py). A game's own calls are unchanged.

Condition: the opponent's deck list is known (order and hand not).

## B: the trainer's install path, ready and not published (the architecture thread 21:01Z)

Nothing a player sees has changed: the levels (svsim/ui/session.py LEVELS), ratings.json, the installed models and
the published page are as they were. A build of the levels as they are gets no new file
(tests/test_web_models.py). The Session already plays any agent spec, `+puct` included, so it needed no change.

**What a level with +setnet / +puct needs in the page, and now has:**
- **The models:** the page ships only text (hosts like claude.ai serve no archives). A model a spec names
  (`+setnet=PATH`, `+puct=PATH[:C[:T]]`) ships as base64 text at `<PATH>.b64` in svsim.json. learn.setnet's
  and learn.setpolicy's `load_cached` read it where the .npz itself is missing. Sizes: ~0.91 MB a value net,
  ~1.06 MB a prior.
- **numpy:** the worker loaded none; the trainer was pure Python until now. When the specs name a model, the build
  writes Pyodide's numpy wheel as base64 JSON (pyodide/numpy.json, 15.9 MB; the wheel comes from the full Pyodide
  release). The worker unpacks it with `pyodide.unpackArchive(…, "wheel")` and imports numpy at boot, so a missing
  numpy fails at boot, not at the AI's first move. Without the file the worker loads as before. numpy.json is just
  under a 16 MB per-file limit; split it before it grows.
- **`python -m svsim.tools.web --build DIR --spec SPEC …`:** carries a candidate spec's models (and its phased
  folder) without naming it in any level.

**One bug the simulation found:** Pyodide's numpy is 32-bit (wasm32). learn.setpolicy's `seg_softmax` passed int64
counts and indices to `np.repeat` / `np.add.reduceat`, which 32-bit numpy refuses. It now passes the platform's
`intp`, which is int64 on 64 bits, so nothing changes there (tests pass).

**The local simulation** (analysis/scaling/web_sim):
- **The worker:** run_worker.js runs the built worker.js in Node against serve.py, a static host that refuses .zip /
  .whl as claude.ai does. It boots (~4 s from local files), loads numpy and both priors, and plays whole games
  through the Session (start / mulligan / act / ai_step) with the four candidate specs (ramp-t / elf-t, base / PUCT).
- **The cost:** run_py.js runs puct_cost.py inside Pyodide on the holdouts' recorded positions (3 games each;
  data/policy/pyodide-cost-*.json).

| mirror | decisions | base ms (Pyodide) | PUCT at the gate's N, ms (×) | PUCT at the base's N, ms (×) |
|---|---|---|---|---|
| ramp-t | 125 | 148.2 (N 120) | 143.6 at N 88 (0.97) | 170.2 at N 120 (1.15) |
| elf-t | 163 | 169.4 (N 105) | 165.0 at N 71 (0.97) | 197.1 at N 105 (1.16) |

Pyodide in Node is about 2× native CPython here. At the gate's N, a decision with the prior costs what the installed
N costs (0.97, as in the gates). The page's cost is the boot: +15.9 MB numpy and ~2 MB of models, once.

## Next round of self-play with the B players (ready, waiting for seeds)

The players, both sides, with c_puct 2, T 1 (the gates' players):
- ramp-t: `mcts:88+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-gen3-30000.npz+neteot+puct=analysis/scaling/models/prior-ramp-ft-t05.npz:2:1`
- elf-t: `mcts:71+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-elft-gen2-19500.npz+neteot+puct=analysis/scaling/models/prior-elft-ft-t05.npz:2:1`

The command, once the analysis line has given the bases and the split:

    python -m svsim.learn.scaledata play --base BASE --stride 2 --shards K0 K1 --per-shard 500 \
        --deck ramp-t --opponent ramp-t --spec "<the ramp-t player>" --workers 4 --out OUT

elf-t is the same with `--deck elf-t --opponent elf-t`. It runs in a worktree at the commit given with the seeds.
The records keep each decision's root visits per legal move, as before (netdata `_thought`; with PUCT a move never
tried has 0). tests/test_web_models.py plays one such game and checks the counts against the legal moves.

Condition: the opponent's deck list is known (order and hand not).

## Next cycle: training the value nets and priors on the PUCT self-play (shard lists fixed before any fit)

The analysis line registered this in 45212fb ("下一圈：训练"). Every fit goes on from the current candidate. Two
options make that possible; both are off by default, so every earlier command is unchanged (tests):
- `train.py net --init NET` starts from NET's weights, card table and standardization. NET's shape and input version
  must be the command's, and every card of the tokens must be in its table with the same static row. The report
  adds the start's valid Brier (`init_valid`) and its sha256.
- `setpolicy fit --prior PRIOR` (instead of `--init VALUE_NET`) starts from all of PRIOR's weights. Its head width
  must be the command's, and its card table the data's cards.npz. The info adds the start's valid CE.

Every value net uses inputs v1, ReLU 64-64 / 128-64, `--ftz`, patience 4, lr 1e-3, decay 0.5 and the valid set
(games with seed·100003 + g a multiple of 20) as before. Every prior is fine-tuned at τ 0.5, `--ftz`, patience 4,
and its valid set is the same rule. Each fit runs in planned chunks of under 2 h from its checkpoint, as before.

**elf-t value net** (`net-elft-gen4-38500`, from net-elft-gen2-19500, sha256 e244c577…). The shards are:
- the 10⁴ v2skx games 71900000 + 2k, k = 0–9;
- gen-2 self-play 72800000 + 2k, k = 0–18;
- gen-3 self-play 74100000 + 2k, k = 0–18;
- this cycle 75500000 + 2k, k = 0–18.

That is 67 shards and 38500 games. 72800038 / 74100038 / 75500038 and the five 72000000 holdouts are in none of
them.

    python analysis/scaling/train.py --deck elf-t --opponent elf-t --base 71900000 --holdout-base 72000000 \
        net --size 38500 --name elft-gen4 --add 72800000:19 --add 74100000:19 --add 75500000:19 --ftz \
        --init analysis/scaling/models/net-elft-gen2-19500.npz --tokens TOK-ELFT --checkpoint CKPT \
        --extra-holdout selfplay:72800038 --extra-holdout selfplay3:74100038 --extra-holdout selfplay4:75500038

**ramp-t value net** (`net-gen5-68500`, from net-gen3-30000). The shards are net-gen4-59000's 79 (70100000 k 0–9,
70800000 k 0–9, 71300000 k 0–9, 71600000 k 0–8, 72300000 k 0–39), plus this cycle's 75400000 + 2k, k = 0–18. That is
98 shards and 68500 games. 71600018, 75400038 and the five 70200000 holdouts are in none of them. "All the data so
far" here means the lists the candidate's line was trained on (net-gen3-30000's 30 shards are all in
net-gen4-59000's). The 10⁵ v2skx shards (70100020 onward, the all-131000 net's) are not taken.

    python analysis/scaling/train.py net --size 68500 --name gen5 --add 70800000:10 --add 71300000:10 \
        --add 71600000:9 --add 72300000:40 --add 75400000:19 --ftz --init analysis/scaling/models/net-gen3-30000.npz \
        --tokens TOK --checkpoint CKPT --extra-holdout selfplay:71600018 --extra-holdout selfplay5:75400038

**elf-t prior** (`prior-elft-gen4-ft-t05`, from prior-elft-ft-t05, sha256 bc086c53…). The shards are the earlier
prior's 38 (72800000 + 2k and 74100000 + 2k, k = 0–18) plus 75500000 + 2k, k = 0–18. That is 57 shards and about
2.09 million decisions.

    python -m svsim.learn.setpolicy fit --data DEC --cards CARDS --shards <the 57> \
        --prior analysis/scaling/models/prior-elft-ft-t05.npz --tau 0.5 --ftz --checkpoint CKPT --out OUT

**ramp-t prior** (`prior-ramp-gen5-ft-t05`, from prior-ramp-ft-t05, sha256 23708146…). The shards are the earlier
prior's 40 (72300000 + 2k, k = 0–39) plus 75400000 + 2k, k = 0–18. That is 59 shards.

Holdouts, reported and not judged (the analysis line's registration):
- the value nets' Brier on every earlier holdout and on this cycle's k = 19;
- the priors' top1 and KL (policy_offline.py, O1's measure) on 74100038 / 71600018 and on this cycle's k = 19.

Order: the elf-t fits first; its data is all in (data/elf-t4, 455b6f0). ramp-t follows once the analysis line has
pushed its shards.

Condition: the opponent's deck list is known (order and hand not).

### Next cycle: the four fits (2026-10-18 01:02–06:40Z; the shard lists above, unchanged)

Every fit went on from its candidate with `--init` / `--prior`. None has a subnormal weight. Each chunk ran under 2 h
from its checkpoint, until patience stopped it. No chunk was killed and no load ran out of memory. The two value
nets' dead units are in data/deadunits.json (description only).

| model | from | shards | train / valid | epochs (best) | fit s | valid at the start → end | sha256 |
|---|---|---|---|---|---|---|---|
| models/net-elft-gen4-38500.npz | net-elft-gen2-19500 | 67 | 667582 / 35521 turn ends | 18 (14) | 2407 | Brier 0.18106 → 0.17664 | 381c8f2d… |
| models/net-gen5-68500.npz | net-gen3-30000 | 98 | 1175048 / 61131 turn ends | 25 (21) | 4771 | Brier 0.18956 → 0.18654 | 417571af… |
| models/prior-elft-gen4-ft-t05.npz | prior-elft-ft-t05 | 57 | 1988790 / 105961 decisions | 35 (31) | 4868 + 5774 + 5920 + 496 | CE 1.20829 → 1.19134 | 7c5d15b2… |
| models/prior-ramp-gen5-ft-t05.npz | prior-ramp-ft-t05 | 59 | 1302270 / 67936 decisions | 30 (26) | 4483 + 4493 | CE 1.03554 → 1.02275 | 1b7cdfef… |

The full sha256 sums are in data/policy/SHA256SUMS. Each "valid" is its own fit's set, drawn from its training shards,
so it is not comparable across fits.

**Value nets, holdout Brier** (reported, not judged). The earlier nets were scored on this cycle's holdouts with
`holdout-net ... --extra-holdout selfplay4:75500038` / `selfplay5:75400038`, from a tokens folder holding only that
file. Their other numbers and files are unchanged; the reports only gained the new key.

| elf-t | v2skx 72000000 (88311) | gen 2 72800038 (9361) | gen 3 74100038 (9128) | this cycle 75500038 (9195) |
|---|---|---|---|---|
| installed linear | 0.20834 | 0.20518 | 0.20395 | 0.19939 |
| net-elft-gen2-19500 (the candidate) | 0.19088 | 0.18415 | 0.17837 | 0.16803 |
| net-elft-gen3-29000 | 0.18803 | 0.18125 | 0.17319 | 0.16246 |
| **net-elft-gen4-38500** | **0.18678** | **0.17913** | **0.17294** | **0.16074** |

| ramp-t | v2skx 70200000 (93787) | gen 4 71600018 (17948) | this cycle 75400038 (8925) |
|---|---|---|---|
| installed linear | | 0.20723 | 0.20906 |
| net-gen3-30000 (the candidate) | 0.18920 | 0.19539 | 0.19371 |
| net-gen4-59000 | 0.18832 | **0.19064** | 0.19066 |
| **net-gen5-68500** | **0.18830** | 0.19071 | **0.19007** |

The elf-t net is the lowest of the three on every holdout. The ramp-t net is below its start on every holdout. It
equals net-gen4-59000 (the same shards less this cycle's 19), within 0.0006 either way.

**Priors, offline report** (policy_offline.py, O1's measure; data/policy/offline2-*.json, per-decision rows in
dump2-*.jsonl.gz). The earlier prior's figures on 74100038 / 71600018 are those of the step-1 report to the digit.
Each table is a first decision over all decisions.

| holdout (played by) | decisions | order top1 | ft-t05 top1 / KL | new top1 / KL |
|---|---|---|---|---|
| elf-t 74100038 (mcts:200, gen2 net, UCB1) | 36399 | 0.4219 | 0.6690 / 0.1211 | **0.6727** / 0.1866 |
| elf-t 75500038 (this cycle's PUCT player) | 36413 | 0.3648 | **0.9194** / 0.0441 | 0.8974 / **0.0266** |
| ramp-t 71600018 (mcts:200, gen3 net, UCB1) | 46781 | 0.4447 | 0.7474 / 0.1383 | **0.7520** / 0.1977 |
| ramp-t 75400038 (this cycle's PUCT player) | 22902 | 0.3873 | **0.9485** / 0.0497 | 0.9231 / **0.0330** |

This cycle's holdouts were played by a search whose prior was ft-t05 itself. That prior shaped those visits, so its top1
there (0.92 / 0.95) is no fair comparison: it is the self-reinforcement the registration names. On them the new prior's
KL to the visits is lower. On the older UCB1 holdouts the new priors pick the most-visited move slightly more often
(+0.004 / +0.005), and their KL is higher, being sharper. Offline agreement is not strength; that is the gates' question.

Condition: the opponent's deck list is known (order and hand not).

## The value net's mid-turn branch (the architecture thread 2026-10-18 07:53Z; code 0b15872; lists fixed before any fit)

Under +neteot, a leaf inside the scored player's own turn is first played to its turn end (after_end_of_turn on a
copy) and then scored by a net that has seen turn ends only. The cards still playable, the play points left and the
attacks not made all count as wasted. Here one net learns both kinds of position, and a flag tells it which.

- **Net.** `SetNet(flag=True)`: rho reads one more global, the flag (1 inside the mover's own turn, 0 at a turn end).
  `SetNet.flagged_from(candidate)` starts from the candidate's weights, card table and standardization, with V1 one
  zero row longer. At the start, then, it is the candidate at flag 0, and the candidate on the raw position at flag 1.
  A net without the flag, and its file, are as before (tests/test_midrows.py; the golden numbers still hold).
- **Rows.** The turn-end rows are learn.scaledata's tok- files (flag 0). The mid-turn rows (learn.midrows mid- files,
  flag 1) are the move prior's decisions (setpolicy.decisions: searched main-phase decisions with two distinct moves
  or more, the mover to act). They are encoded from the mover's view and labelled with the game's result from the
  mover's view. There is no deck id and no card id, as before.
- **Weight of the two kinds.** Both kinds weigh the same. The mid-turn rows are thinned to about the turn-end rows'
  number: each is kept with probability n_end / n_mid, from a generator seeded per shard. A turn has several
  decisions and one end, so the thinning also keeps the data's size near a turn-end net's. Training and validation
  are split file by file into arrays allocated once (midrows.phase_split), against the memory problems seen before.
- **Settings.** The same as every scaling-test net: inputs v1, ReLU 64-64 / 128-64, Adam, lr 1e-3, decay 0.5,
  patience 4, l2 1e-5, batch 256, `--ftz`. The valid part is the games with seed·100003 + g a multiple of 20. Fits
  run in planned chunks of under 2 h from a checkpoint.
- **Switch.** Agent option `+netmid` (with `+setnet=` a flagged net). A leaf inside the scored player's own turn is
  scored as it is by the flag-1 branch, with no turn end played. Every other position is scored by the flag-0
  branch. Off, nothing changes (tests).

**ramp-t** `net-mid-ramp-t`, from net-gen3-30000:
- turn-end rows: bbc694a's 98 shards (70100000 k 0–9, 70800000 k 0–9, 71300000 k 0–9, 71600000 k 0–8, 72300000
  k 0–39, 75400000 k 0–18);
- mid-turn rows: the prior's 59 (72300000 k 0–39, 75400000 k 0–18);
- holdouts: the five 70200000 shards (turn ends only), 71600018 and 75400038.

**elf-t** `net-mid-elf-t`, from net-elft-gen2-19500:
- turn-end rows: bbc694a's 67 shards (71900000 k 0–9, 72800000 / 74100000 / 75500000 k 0–18);
- mid-turn rows: the prior's 57 (72800000 / 74100000 / 75500000 k 0–18);
- holdouts: the five 72000000 shards (turn ends only), 72800038, 74100038 and 75500038.

    python analysis/scaling/train_mid.py --deck ramp-t --opponent ramp-t --init analysis/scaling/models/net-gen3-30000.npz \
        --tokens TOK --end 70100000:10 --end 70800000:10 --end 71300000:10 --end 71600000:9 --end 72300000:40 \
        --end 75400000:19 --mid-dir MID --mid 72300000:40 --mid 75400000:19 \
        --holdout 70200000 70200002 70200004 70200006 70200008 71600018 75400038 --name mid-ramp-t --checkpoint CKPT

elf-t is the same with its lists (`--deck elf-t --opponent elf-t --init .../net-elft-gen2-19500.npz --name mid-elf-t`).
The script refuses a holdout seed that is in the training lists.

**Report** (mid_report.py), per holdout:
- turn ends: the new net (flag 0) against the candidate;
- mid-turn decisions: the new net (flag 1) against "end the turn now and score with the candidate", which is
  +neteot's number (after_end_of_turn, a finished game 1 / 0). The new net's turn-end branch after that turn end
  and the candidate on the raw position are also given;
- for each: Brier, log-loss and calibration in 10 bins of the prediction (rows, mean prediction, win rate, ece).

The step cost is measured against today's +neteot player on recorded positions (puct_cost.py).

Order: ramp-t first, then elf-t. At most one elf-t process loads at a time. No games are played.

Condition: the opponent's deck list is known (order and hand not).

## R1: the ramp-t prior refitted on decisions searched again by A's scorer (the analysis line's 96c5b24; lists fixed before the fit)

The data is data/r1-ramp/rec/: gen4x 72300000 + 2k, k = 0–39, ft-t05's training records. About half of their
decisions were searched again by A's scorer without a prior (see that folder's README; the builder line did 30 shards
and the analysis line 10). learn.setpolicy encode reads the 40 shards as it reads self-play shards. Their decisions
are the re-searched ones (466481 in all), and the targets are the new visits.

    python -m svsim.learn.setpolicy fit --data DEC --cards CARDS --shards 72300000 72300002 ... 72300078 \
        --prior analysis/scaling/models/prior-ramp-ft-t05.npz --tau 0.5 --ftz --checkpoint CKPT \
        --out analysis/scaling/models/prior-ramp-r1.npz

Every other setting is ft-t05's: head 64, Adam, lr 1e-3, decay 0.5, patience 4, l2 1e-5, batch 256. The valid part
is the games with seed·100003 + g a multiple of 20. CARDS is ft-t05's cards.npz, whose card table `--prior` checks.
The fit runs in planned chunks of under 2 h from its checkpoint. The training shards are these 40 only. 71600018 and
this cycle's 75400038 are in neither list.

Condition: the opponent's deck list is known (order and hand not).

### +netmid in the trainer's install path (the architecture thread 12:01Z; ready, not published)

Nothing a player sees has changed: the levels, ratings.json, the installed models and the published page are as they
were. The install path built for +setnet / +puct (above) needed no change for +netmid. The flag net is one more .npz
the spec names. It ships as `<path>.b64`, and SetNet.load reads its "flag" key there as from the file, in both
the 64-bit and the 32-bit numpy (the flag is a float appended to the globals).

- **Build.** `python -m svsim.tools.web --build DIR --spec A --spec B` at efc64cb. A is the gate's
  `mcts:83+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-mid-ramp-t.npz+netmid+puct=analysis/scaling/models/prior-ramp-ft-t05.npz:2:1`
  and B is today's candidate + prior. svsim.json carries net-mid-ramp-t, net-gen3-30000 and prior-ramp-ft-t05 as
  .b64, and pyodide/numpy.json as before.
- **A whole game in the page's worker** (web_sim/run_worker.js, Node). The worker boots in 3.1 s and loads numpy.
  The Session plays ramp-t mirror with A as the AI and the other side picking legal moves by a fixed generator. The
  game ran to its end at turn 16 with 29 AI steps, a mean of 106 ms a step, and no error.
- **Step cost inside Pyodide** (web_sim/run_py.js running puct_cost.py; data/mid/pyodide-cost-ramp-t.json). On
  75400038's first 3 games (113 decisions), B at N 88 took 140.4 ms a decision and A at N 83 took 142.7 ms, ×1.02.
  The native figure is ×0.99 (the gate's own was 0.988). The page's cost of A is that of today's B, and the boot
  is as before (numpy, and ~0.9 MB per model).

Condition: the opponent's deck list is known (order and hand not).

**prior-ramp-r1** (the fit above, 2026-10-18 15:3x–16:5xZ). The model is models/prior-ramp-r1.npz (sha256
cf3e0de2242fb0a9891ae2eecae2d1093e75c16676ce5a7973a80d325f1fcf4a), from prior-ramp-ft-t05 (23708146…). It had 443253
training and 23228 valid decisions over the 40 shards (info "shards", exactly 72300000 + 2k, k = 0–39). Valid CE at
τ 0.5 against the new visits went from 1.20699 at the start (ft-t05 itself) to 1.07395. It ran 42 epochs (best 38)
in two chunks: 3728 s, then 190 s from the checkpoint. It has 0 subnormal weights. The log is
data/policy/fit-ramp-r1.log. The offline O1 against D10's A-UCB visits and the gate are the analysis line's.

Condition: the opponent's deck list is known (order and hand not).

**The elf-t new bot in the install path** (the architecture thread 15:45Z; ready, not published). The bot is
`mcts:71+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-mid-elf-t.npz+netmid+puct=analysis/scaling/models/prior-elft-ft-t05.npz:2:1`
(N 71 as in the elf-t gate's start; the gate's timing check may move it). The build at d00ab33 carries
net-mid-elf-t and prior-elft-ft-t05 as .b64, and numpy.json.
- **A whole game in the Node worker:** it booted in 3.7 s. The elf-t mirror with the new bot as the AI ran to its
  end at turn 10 with 22 AI steps, a mean of 103 ms a step, and no error.
- **Pyodide step cost** (data/mid/pyodide-cost-elf-t.json; 75500038's first 3 games, 221 decisions): the installed
  strong level `mcts:200+plan+learned+phased` took 218.8 ms a decision and the new bot 209.8 ms, ×0.96.

Condition: the opponent's deck list is known (order and hand not).

## Where a new candidate's decision time goes (the architecture thread 17:17Z; report only, nothing changed)

`analysis/scaling/profile_cost.py`; data/profile/. The bots are the two new candidates: ramp-t A (net-mid-ramp-t +
`+netmid` + ft-t05 PUCT, N 83) and the elf-t bot of 3928895 (net-mid-elf-t + `+netmid` + prior-elft-ft-t05, N 71).
They play the first 3 games of this cycle's holdouts, 75400038 / 75500038. Each side's agent decides at every
main-phase step, and the game goes on by the recorded move. There is one agent per side and game, so what an
agent keeps between decisions is kept as in play; no game is played and no seed is drawn. That covers 151 / 271
steps. The run is native, and in Pyodide 0.26.4 in Node, using the builds of 4ee2855 / 3928895
(web_sim/profile_in_pyodide.py).

Timers wrap a few methods (inclusive wall, without the profiler). The figures are ms per main-phase step.
GameState.clone and determinize overlap the others: the lethal search clones too.

| | ramp-t native | ramp-t Pyodide | elf-t native | elf-t Pyodide |
|---|---|---|---|---|
| wall per step | 38.1 | 90.8 | 52.7 | 115.5 |
| lethal search (LethalSearch.solve) | 12.6 (33%) | 32.3 (36%) | 16.8 (32%) | 42.3 (37%) |
| value net (SetNet.logit) | 6.1 (16%) | 17.8 (20%) | 7.0 (13%) | 18.1 (16%) |
| prior (SetPolicy.priors) | 4.7 (12%) | 12.0 (13%) | 6.8 (13%) | 16.6 (14%) |
| determinize | 3.0 (8%) | 6.0 (7%) | 3.1 (6%) | 5.7 (5%) |
| GameState.clone (all callers) | 4.1 (11%) | 10.7 (12%) | 5.2 (10%) | 13.9 (12%) |

The rest, about a third, is the tree search's own work: moves applied in the iterations, legal moves, selection and
backup, and search.xprune.

Under cProfile, own time by where the code lives, with a C function's time given to its callers, puts the
simulator (rules, moves) at 41% / 39%, state copy at 9%, the value net at 17% / 14%, the prior at 4%, mcts.py at
9% / 7%, and lethal and plans at 11% / 21%. The profiler's overhead falls mostly on many small Python calls, so these
shares are a guide only. The lethal search runs 0.4 / 0.3 times a step: the agent skips it while the turn and the
hidden information are the same. Most runs are screened, with a budget of 200 nodes, and run to that budget. That
is about 280–300 µs a node, each node being moves, clones and sampled draws.

The positions mode (`--mode positions`: a fresh agent at each searched decision, as puct_cost.py does) loses that
skip, so it puts the lethal search at 34–42%. That overstates it for play, so the table above uses play order.

**What exact (bit-for-bit) changes could save: estimates, nothing tried.** Each change is meant to leave every
decision, every random draw and every number as it is, checked by the golden replays (the 3-game replays and the
logit dumps) before any use.

| change | where | est. share of the part | est. share of the step |
|---|---|---|---|
| lethal: compute hidden_info once per search level, not per node, and a cheaper state_key (per-card keys built once per card state) | search/lethal.py (state_key, hidden_info, _card_key were ~25% of the lethal time under the profiler) | 20–30% | 7–10% |
| value net: fewer Python tuples on the live tokens (the rows and the memo key are built per leaf; logit's own Python time is ~45% of it) | learn/setnet.py logit, tokens._live | 25–40% | 3–6% |
| prior: the move arrays and token encoding vectorized, the trunk's live-token memo as in the value net (forward is ~40% of priors()) | learn/setpolicy.py priors | 30–40% | 4–5% |
| determinize: shuffles from a dedicated Random, no getstate / seed round trip (the same draws) | core/view.py _inline_shuffle (getstate + seed ~0.35 of its time) | ~40% | 2–3% |
| state copy: cheaper per-card copy (515k card copies in 151 steps) | core/state.py copy | 20–30% | 2–3% |

That totals about 18–27% of a step: ×1.2–1.4 the iterations in the same time, or the same play ~20% sooner.
That is not 2×. The larger savings change results, and are therefore not on this list: a smaller lethal screen
budget, fewer sampled draws in the lethal search, or batching the net's leaf evaluations (which changes BLAS's
summation order). Whether ×1.3 is worth the work is D12's question (2N against N); this table only gives the price.

Condition: the opponent's deck list is known (order and hand not).

## D13 preparation: the opponent's real hand in the search (`+oracle`), and what the guess at their hand uses (the architecture thread 17:44Z)

**The switch already exists.** `+oracle` came in f90f60e (2026-10-08) as an experiment, off by default and in no
level. With it, every determinization of the tree search (search.mcts, core.view.determinize(..., oracle=True))
gives the opponent their real hand, and only the order of their deck (and of one's own) is guessed. Off,
determinize draws exactly as before: tests/test_learn.py::test_oracle_sees_the_opponent_s_real_hand_and_off_draws_as_before
checks the uids and the random numbers against the definition from before the switch. For D13 the spec is A's with
`+oracle` added. Two things it does not touch:
- The value net never sees which unseen cards are in the hand. tokens pools the opponent's hand and deck into one
  zone (op_unseen), so with the switch the net scores the same cards in the same pooled zone. Only the simulated
  play differs: what the opponent can play in the tree.
- The lethal agent's macro / burst / dig lines determinize on their own and stay unaided, but A uses none of them.
  The lethal search itself looks only at the searcher's own turn.

New here: `web --build` refuses a spec with `+oracle` (svsim/tools/web.py _specs; test in
tests/test_web_models.py), so the diagnostic cannot reach the page. No game is played by this change, and the
search's code is untouched.

**What the guess at the opponent's hand uses now** (core.view.determinize, without `+oracle` or `+infer`). The pool
is the opponent's real hand plus their real deck. With the deck list known, that is exactly the deck list less
every card seen leave it: played, on the field, in the cemetery, banished, discarded. It is shuffled uniformly,
and the first len(hand) cards become the hand. So:

| information | used? |
|---|---|
| the deck list (the condition of every result) | yes, the pool is the cards not yet seen |
| cards played, destroyed, discarded, banished | yes, they are out of the pool |
| the hand's size | yes |
| the mulligan | nothing public to use (only the number swapped, which the hand's size already gives) |
| when a card was drawn | not used, and nothing about which card a draw was |
| **cards put into the hand by an effect** (add_to_hand, add_copy_to_hand: Fairy, Deepwood Bounty, Spilling Red, Depths of the Eld Blades …) | **not used**: they are public and certainly in the hand, but they are pooled with the deck. A guess can put one in the deck and a deck card in the hand, a world that cannot be |
| **cards returned to the hand from the field** (return_to_hand) | **not used**: public and in the hand, pooled the same way |
| cards drawn by a condition (draw_matching: "draw a follower") | not used: the hand holds a card meeting it (public as a condition, not as the card) |
| what the opponent could have played and did not (search.infer, `+infer=...`) | off in A; a weighting, not a certainty |

How often it matters, on the first 20 games of this cycle's holdouts at the searched decisions: in ramp-t 254 of 964
decisions (25%), the opponent's hand holds at least one card from no deck list slot (386 of 4633 hand cards: Spilling
Red 267, Depths of the Eld Blades 119). In elf-t it is 407 of 1423 (29%) (515 of 6330: Fairy 330, Deepwood Bounty
185). Returned cards come on top of that and are not counted here. Keeping such known cards in the hand, and
drawing only the rest from the pool, would use information that is public by the rules. It is a candidate change
of its own, so it is listed here, not made.

Condition: the opponent's deck list is known (order and hand not).

## The opponent-hand zone: an omniscient net and its control (the architecture thread 17:47Z; code 08c2952; set before either fit)

**Code.** `SetNet(ophand=True)` adds a zone of the opponent's real hand, card by card. Each card is a live token of
the existing card features (learn.tokens._live), with no card id and no score per card. Its phi sum enters rho
through rows of its own: `U @ V1 + P_hand @ V1h`. `SetNet.with_ophand_from(net)` starts with V1h = 0. Until it is
trained, the net then gives every position the same number as `net`, to the last bit, in both the batch and the
search's single-position path (tests/test_ophand.py). Off, nothing changes: no other net, file or test differs.
`midrows encode-hand` writes, beside each tok- / mid- file, the opponent's hand at its positions. Their game and
action index are checked against the file's when they are loaded. In the search, the zone sees the hand as the
state has it: a guess, or the real one with `+oracle`. This is a diagnostic only, and no player or level uses it.

**Two fits, the same in everything but the zone.** Both start from net-mid-ramp-t (sha256 4232818e…). Both use its
data: the 98 turn-end shards and 59 mid-turn shards of its list. The mid-turn rows are thinned with the same rate and
seed, so the rows are the same. The valid part is the same games (seed·100003 + g a multiple of 20). The settings
are the same: lr 1e-3, decay 0.5, l2 1e-5, batch 256, `--ftz`. Both run exactly 12 epochs: `--patience 100`, so
neither stops early, and each keeps its best valid epoch.
- **omniscient** `net-midoph-ramp-t`: with the zone (`--hand-dir`);
- **control** `net-midc-ramp-t`: without it, net-mid-ramp-t trained on for the same 12 epochs.

    python analysis/scaling/train_mid.py --deck ramp-t --opponent ramp-t --init analysis/scaling/models/net-mid-ramp-t.npz \
        <net-mid-ramp-t's --end / --mid / --holdout lists> --epochs 12 --patience 100 --name midoph-ramp-t --hand-dir HAND
    (the control: the same without --hand-dir, --name midc-ramp-t)

The screen is the analysis line's: holdout Brier, omniscient against control. Below 0.005 better, this line stops.

**Starting-point check (before either fit's result).** `SetNet.with_ophand_from(net-mid-ramp-t)` (V1h = 0, sha256
39d2c922…) was run through mid_report.py on the holdouts with `--hand-dir`, so it read the recorded real hand. Its
dumps (data/mid/dump-midoph-start-ramp-t) equal data/mid/dump-mid-ramp-t field by field, to the last bit: turn ends of
v2skx (70200000–70200008), selfplay (71600018) and selfplay5 (75400038), and mid-turn decisions of the last two. The
mid-turn baseline columns go through the single-position path (`logit`), so that path is covered too. The test is
tests/test_ophand.py::test_added_at_zero_it_scores_as_the_net_to_the_last_bit. The holdouts' hand files are in
data/mid/hand-ramp-holdout (SHA256SUMS). They are re-made by `python -m svsim.learn.midrows encode-hand --kind end|mid
--records DIR --out DIR` from the holdout records.

**The two fits (files only; the screen is the analysis line's).** Both ran 12 epochs. The omniscient net kept
epoch 12 and the control kept epoch 10.
- `models/net-midoph-ramp-t.npz`, sha256 a5f29bca…. Info: data/net-midoph-ramp-t.json. Log:
  data/mid/train-midoph-ramp-t.log. Holdout: data/mid/report-midoph-ramp-t.json and dump-midoph-ramp-t, read with
  the recorded real hand (`--hand-dir`).
- `models/net-midc-ramp-t.npz`, sha256 26ea8ccb…. Info: data/net-midc-ramp-t.json. Log:
  data/mid/train-midc-ramp-t.log. Holdout: data/mid/report-midc-ramp-t.json and dump-midc-ramp-t.

The omniscient net reads the opponent's real hand. It is for measurement only, not for play, and `+oracle` never goes
into an installed spec (tools/web.py refuses it).

Condition: the opponent's deck list is known (order and hand not).

## D14: new inputs and a wider net on the ramp-t mid net (the architecture thread 19:38Z; code 62aac43; set before either fit)

Both fits start from net-mid-ramp-t (sha256 4232818e…) and score as it does, to the last bit, until they are
trained. They use net-midc-ramp-t's data, mid-turn thinning rate and seed, valid games, 12 epochs at `--patience 100`
and its settings, and each keeps its best valid epoch. The control is net-midc-ramp-t, which is not trained again.

**D14a, `net-midv2a-ramp-t` (`train_mid.py --v2a`).** The inputs are v2a's (net-in2a-59000's): v1's columns plus
share, next_pp and next_evolve (learn.tokens V2_EXTRA). `SetNet.with_v2a_from` (option xcols) keeps v1's columns
going through W1d as before and gives the three new columns rows of their own, W1x (3 × 64), 0 at the start. Their
product is added after v1's, so every product the old net makes is made as before. Making W1d three rows longer
instead would change the inner size of a product, and BLAS can then sum in another order. The data was encoded
again as v2a (`scaledata encode --inputs v2a`, `midrows encode --inputs v2a`). All 166 files (105 turn-end, 61
mid-turn, holdouts included) were checked against the v1 files: v1's token columns and every other array are
identical. So the rows, results, thinning and valid split are the same.

**D14b, `net-midwide-ramp-t` (`train_mid.py --wide`, learn.widenet).**
- **Width.** Twice the width: phi 128-128, rho 256-128 (64 / 64 / 128 / 64 new units).
- **Old units.** They keep their weights. The new units reach an old unit only through blocks of their own (new
  inputs to old outputs, and the new last-layer units to the output). These blocks start at 0, are trained, and are
  added after the old net's own term.
- **New units.** Their input weights (from old and new units) start random: He, from the constructor's fixed
  generator, not a game seed. So they compute from the first step and their output weights get gradient.
- **Activation.** A PReLU, max(z, 0) + a·min(z, 0), on every unit, old and new (option 1 of the analysis line's two;
  the architecture thread prefers it). There is one slope a per layer (phi 1, phi 2, rho 1, rho 2). The slopes start
  at 0, where the activation is the old ReLU to the last bit, and are trained with the weights, without l2. So the
  dead old units can come back too.
- **Fit in chunks.** Its epochs are slower, so it goes in chunks of under 2 hours from its checkpoint. The checkpoint
  holds the whole state, the shuffling generator included, so the result is the same as an unbroken fit.

**Starting-point check.** The same as D13′'s: both starts' holdout dumps against data/mid/dump-mid-ramp-t, field by
field. The tests are tests/test_v2a_grow.py and tests/test_widenet.py: the start equals the net bitwise in the batch
and in the single-position path, at turn ends and mid-turn. Trained, the single-position path matches the batch, and
the gradients match finite differences.

**The screen is the analysis line's:** either variant ≥ 0.010 lower than net-midc-ramp-t mid-turn goes to a gate.
Otherwise this line stops.

Condition: the opponent's deck list is known (order and hand not).

### D14 fits (files; the screen is the analysis line's)

| net | sha256 | epochs (best) | fit | info / log | holdout |
|---|---|---|---|---|---|
| net-midv2a-ramp-t (D14a) | e16da389… | 12 (11) | 4442 s, one run | data/net-midv2a-ramp-t.json, data/mid/train-midv2a-ramp-t.log | report-midv2a-ramp-t.json, dump-midv2a-ramp-t |
| net-midwide-ramp-t (D14b) | 6fb58358… | 12 (12) | 12609 s of epochs in four chunks (1, 2–6, 7–10, 11–12) | data/net-midwide-ramp-t.json (its fit_s is the last chunk's), data/mid/train-midwide-ramp-t.log | report-midwide-ramp-t.json, dump-midwide-ramp-t |

- D14b's learned slopes are, phi 1 to rho 2: 0.0014, 0.0003, −0.038, −0.090. The largest weight of the new last-layer
  units (v3_n) is 0.0027.
- **Step cost, native** (puct_cost.py, data/mid/cost-d14-ramp-t.json): 469 decisions of rec-75400038's first 10
  games. A's spec (N 83, +netmid, prior ft-t05) with each net, the three taking turns position by position. The
  figures are ms per decision:

| net | ms per decision | × net-midc-ramp-t |
|---|---|---|
| net-midc-ramp-t | 59.90 | 1.00 |
| net-midv2a-ramp-t | 62.66 | 1.05 |
| net-midwide-ramp-t | 145.43 | 2.43 |

Condition: the opponent's deck list is known (order and hand not).

## NM1 preparation: ramp-t vs elf-t, a non-mirror pairing (the architecture thread 2026-10-19 00:34Z; named NM1 at 00:40Z, D15 being the analysis line's reply diagnostic)

The scoring-net line stops (D14, the analysis line c3379a2). The same recipe moves to a non-mirror pairing, ramp-t
against elf-t first. Below is what the trainer's bots use there today, what the new candidates do there, and the
plan. Nothing a player sees has changed.

### 1. The trainer: decks, pairings, and what each level scores with

**Decks.** The page (web/index.html, ui.session.DECKS) offers nine decks on either side, so 81 ordered pairings: the
five early decks (破魔虫精灵 rhino, 跳费龙 ramp, 海盗皇家 pirate, 连击精灵 combo, 快攻龙 face) and the four
tournament decks (elf-t, nemesis-t, ramp-t, pirate-t). The AI plays the deck picked as "AI 的卡组". The CR
calibration (ratings.json, version 23) measures the four tournament decks, each against the ruler's four.

**Levels** (ui.session.LEVELS): fast `greedy+plan+learned`; normal
`mcts:115+plan+learned+phased=ref-5558960+reuse+mull=default`; strong `mcts:200+plan+learned+phased`; max
`mcts:1043+plan+learned+phased`; original `mcts:100+plan+learned+phased=orig-f631e14+noalias+screen=200+mull=default`.

**Which model scores**: analysis/scaling/pairing_probe.py builds each bot as the trainer does and asks it to
score a dealt position of the pairing (no game played, no seed drawn). Output: data/pairing/probe-levels.json.
- *Per-pairing linear models* (learn.phased): a model is filed under the ordered pair (deck, opponent deck) and the
  moment (ended / act). There are installed models for 12 ordered pairs: elf-t–elf-t, elf-t–nemesis-t, elf-t–ramp-t,
  nemesis-t–elf-t, nemesis-t–ramp-t, pirate-t–elf-t, pirate-t–pirate-t, ramp-ramp, ramp-t–elf-t, ramp-t–nemesis-t,
  ramp-t–pirate-t and ramp-t–ramp-t.
- *Per-deck linear models* (learn.model Learned, svsim/learn/weights): every other pairing falls back to the deck's
  class model (dragon.json, forest.json, …) or to ramp-ramp.json.

| bot | ramp-t (AI) vs elf-t | elf-t (AI) vs ramp-t |
|---|---|---|
| fast | weights/dragon.json | weights/forest.json |
| normal | ref-5558960/ramp-t-elf-t-{ended,act}.json | ref-5558960/elf-t-ramp-t-{ended,act}.json |
| strong, max | phased_models/ramp-t-elf-t-{ended,act}.json | phased_models/elf-t-ramp-t-{ended,act}.json |
| original | weights/dragon.json (its folder has the Game8 mirror only) | weights/forest.json |
| v2skx (`phased=pkg-kc-ramp-ramp`) | pkg-kc-ramp-ramp/ramp-t-elf-t-{ended,act}.json | pkg-kc-ramp-ramp/elf-t-ramp-t-{ended,act}.json |

- **The four ramp-t vs elf-t files are the same in all three folders, byte for byte** (sha256 ramp-t-elf-t-ended
  b2f24b13…, -act 9fea10f1…, elf-t-ramp-t-ended 8be505d7…, -act df7e7bff…). Normal, strong, max and v2skx
  therefore score ramp-t vs elf-t with the same weights.
- **pkg-kc-ramp-ramp is mirror-only in effect.** It is the installed folder copied byte for byte, with
  ramp-ramp-ended.json replaced (README of the package). Outside the original Ramp mirror, v2skx differs from strong
  only by `+xprune=3:3:cost`.
- **The four files.** Each is a version-2 linear model of one side and moment. They were fitted on the 2000 v2
  self-play games of elf-t vs ramp-t (2026-10-08, per-pairing fits). The turn-end models used about 14 800 turn
  ends each, the in-turn models 52 904 and 70 361 positions.
- **For comparison, the mirrors:**
  - the ramp-t mirror: normal falls back to ramp-ramp (the alias, since ref-5558960 has no ramp-t–ramp-t), while
    strong and v2skx use ramp-t–ramp-t;
  - the elf-t mirror: elf-t–elf-t at every searching level.

### 2. The new candidates in ramp-t vs elf-t

The candidates are the ramp-t mirror's A (`net-mid-ramp-t+netmid+puct=prior-ramp-ft-t05`, N 83) and the elf-t new
bot (`net-mid-elf-t+netmid+puct=prior-elft-ft-t05`, N 71).
- **They run.** On the first 2 recorded games of that set (111 main-phase decisions, both sides), each spec decided
  at every step without an error (profile_cost.py, data/pairing/probe-candidates-ramp-t-elf-t.json). The records
  were replayed; no seed was drawn.
- **Their value net is never used** (SetNet.logit 0 calls per decision). SetNetEnded answers only for its own pairing
  (info deck / opponent: ramp-t–ramp-t, elf-t–elf-t). Every position goes to the model under it, which is v2skx's,
  i.e. the installed ramp-t–elf-t / elf-t–ramp-t linear models above. +netmid changes nothing there.
- **Their move prior is used** (SetPolicy.priors 12.2 and 10.7 calls per decision). The prior checks no pairing.
  Cards it never saw get their static rows on the fly, but it was trained on its mirror's decisions only.
- So in this pairing a candidate is v2skx's evaluation with a mirror-trained prior at a smaller N (83 / 71 against
  200), not the bot that passed its mirror's gate.

### 3. Plan for ramp-t vs elf-t (the mirror's recipe)

- **Data.**
  - Who plays: v2skx on both sides (`scaledata play --deck ramp-t --opponent elf-t`). The first player is
    random per game, so each deck is first and second, and every game gives turn ends and decisions from both
    sides.
  - How much: 10⁴ games in 10 shards of 1000 for training, and 5 shards held out. This is the mirror's first
    generation (70100000 + 2k, holdout 70200000 + 2h).
  - Why not the new candidates: they would add only a mirror prior to the same evaluation (§2), so the data would be
    v2skx's at a smaller N.
  - Seeds come from the analysis line.
  - Cost: about 4–5 CPU s a game, so about 1.1 h a shard with 4 workers. It is played in runs of under 2 hours.
- **Value net.**
  - One net, learning both sides' views. Each turn end is scored from the side that ended the turn, as in the
    mirror. Both views share the card features, so one net sees twice the data.
  - The net knows no deck or pairing number: its inputs are each card's features and state, never a card id, and no
    card gets a fixed score.
  - It has the mid-turn branch: flag, mid-turn rows from the decisions of both sides, and the mirror's thinning and
    valid split.
  - Start: net-mid-ramp-t or net-mid-elf-t, whichever has the lower valid Brier on the new data before training
    (both kinds of row). This rule is set before either is scored.
  - A card the start never saw is added to its table by its static row, as SetNet does in play, with the start's
    standardization unchanged. So on the cards it knows, the start scores as before.
  - Training: as gen 4 / the mid nets (lr 1e-3, decay 0.5, l2 1e-5, batch 256, --ftz, patience 4). The epochs go
    in chunks of under 2 hours.
- **Move prior.**
  - Each side's own mirror prior, prior-ramp-ft-t05 and prior-elft-ft-t05, is fine-tuned on that side's decisions
    in the new data (`setpolicy fit --prior`, τ 0.5).
  - Before the fine-tune, the valid CE of the mirror prior as it is is reported next to it.
- **Code needed (default off, the mirrors bit for bit as now):**
  - SetNetEnded answers for a net whose info names both orders of a pairing;
  - `train_mid.py` / `scaledata` take the non-mirror pairing's shards and the start's table extension;
  - `setpolicy encode/fit` keeps one side's decisions (`--deck`).
- **The gate is the analysis line's to register.** The new bot plays v2skx with seats swapped, time-matched. The new
  bot on the ramp-t side and on the elf-t side are two arms or one, as it registers.

Condition: the opponent's deck list is known (order and hand not).

## +netreply: a +reply leaf scored by the value net (the architecture thread 2026-10-19 00:37Z; the analysis line's D15 finding)

`mcts-reply` plays the opponent's next turn out greedily at a turn-end leaf. It then scores the leaf with
`player_moves_next` True, and SetNetEnded passed every such score to the linear model under it, so one tree mixed two
scales (the analysis line, c66d599).
- **The moment.** The engine starts the next turn inside the opponent's EndTurn (core.engine._end_turn calls
  _start_turn: play points refilled, turn-start abilities, the draw). So the leaf as it was is the start of the own
  turn, not the opponent's turn end the nets were trained on.
- **With +netreply** (off by default), where the net answers for the opponent's side of its pairing
  (SetNetEnded.answers_reply), the play-out stops at the opponent's EndTurn: search.mcts takes after_end_of_turn,
  the end-of-turn abilities resolved and the own turn not started, the moment of a turn-end row. The score is then
  SCALE × minus the net's turn-end logit for the opponent.
- **Other pairings**, and the switch off, go on into the own turn as before and are scored by the in-turn model.
- **Tests:** tests/test_netreply.py checks that the score is −SCALE × net.logit(position, opponent). It also checks
  that with the switch the scored leaves are before the own turn starts (turns_taken not advanced), and without it
  after. The agent option is tested too. The full suite passes: 1249 passed, 4 skipped. The old nets' golden numbers
  are unchanged with the switch off.

Condition: the opponent's deck list is known (order and hand not).

### NM1 value net: two arms, and the choice between them (the architecture thread 03:15Z; set before either fit)

The start rule (the lower valid Brier) picked net-mid-ramp-t: 0.304 on the valid games of the 9 shards then
played, against net-mid-elf-t's 0.363 (data/nm1/start-choice.json). Both are worse than a constant 0.5 (0.25)
on this pairing. The architecture thread reads this as calibration that did not carry over: in a mirror both sides
are alike, here one side is favoured. So two arms are trained, on the same data with the same settings.
- **Main arm `net-nm1-ramp-elf` (start).** From net-mid-ramp-t, its card table grown to the pairing's cards
  (`--extend-cards`), the flag kept.
- **Control arm `net-nm1f-ramp-elf` (fresh).** A new flagged net of the default structure (phi 64-64, rho
  128-64, ReLU), from the constructor's fixed seed 0. Its card table and standardization come from the training data,
  as train.py's nets (`--fresh`).
- **Both arms.**
  - Data: the 10 training shards' turn ends (tok-) and mid-turn rows (mid-), thinned to the turn ends' count.
    Valid games: seed·100003 + g a multiple of 20.
  - Views: one net for both sides' views, answering for both orders (`--pairs ramp-t:elf-t elf-t:ramp-t`).
  - Settings: lr 1e-3, decay 0.5, l2 1e-5, batch 256, `--ftz`, patience 4, at most 60 epochs, the best valid epoch
    kept.
- **Which goes to the gate.** The arm with the lower valid Brier, both kinds of row together, at its kept epoch. The
  holdout shards (78000000 + 2h) are not read before that choice. After it they are the analysis line's.
- **The commands** (TOK, MID: the NM1 token and mid-row folders):

      python analysis/scaling/train_mid.py --deck ramp-t --opponent elf-t --pairs ramp-t:elf-t elf-t:ramp-t \
          --tokens TOK --end 77900000:10 --mid-dir MID --mid 77900000:10 \
          --holdout 78000000 78000002 78000004 78000006 78000008 \
          (--init analysis/scaling/models/net-mid-ramp-t.npz --extend-cards --name nm1-ramp-elf | --fresh --name nm1f-ramp-elf) \
          --epochs 60 --patience 4 --checkpoint CKPT

  (train_mid.py always fits with `--ftz`, SetNet.fit ftz=True.)

Condition: the opponent's deck list is known (order and hand not).

**The two arms, and the choice** (2026-10-19 03:46–04:13Z; the rule above). Both fits ran on 10 shards: 319 970
training and 15 996 valid rows, mid-turn rows thinned at 0.32.

| arm | sha256 | epochs (kept) | valid Brier, both kinds | turn end | mid-turn |
|---|---|---|---|---|---|
| start, net-nm1-ramp-elf | b6e525eb… | 10 (6) | 0.17422 | 0.17669 | 0.17174 |
| fresh, **net-nm1f-ramp-elf** | cae8324a… | 16 (12) | **0.17109** | 0.17520 | 0.16698 |

- **The fresh arm goes to the gate.** Its valid Brier is the lower one.
- Both arms answer for both orders of the pairing (info pairs).
- The holdout shards were not read for this choice. They are the analysis line's from here on.
- Logs: data/nm1/train-nm1{,f}-ramp-elf.log. Info: data/net-nm1{,f}-ramp-elf.json.

Condition: the opponent's deck list is known (order and hand not).

### NM1 priors, the new bot's two specs and N₀ (2026-10-19 04:10–05:15Z)

**Priors.** Each side's mirror prior was fine-tuned on that side's decisions in the 10 training shards (`setpolicy
encode --deck`, `fit --prior … --extend-cards --tau 0.5 --ftz`). Their info still names the mirror pairing (deck /
opponent); the prior checks no pairing.

| prior | from | train / valid decisions | valid CE start → end | epochs (best) | sha256 |
|---|---|---|---|---|---|
| prior-nm1-ramp-t | prior-ramp-ft-t05 | 188 450 / 10 014 | 1.31714 → 1.15019 | 40 (36) | 4f023f95… |
| prior-nm1-elf-t | prior-elft-ft-t05 | 283 215 / 15 067 | 1.45271 → 1.25591 | 30 (26) | db18c4b6… |

**The new bot, one spec per deck it plays:**
- ramp-t: `mcts:99+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm1f-ramp-elf.npz+netmid+puct=analysis/scaling/models/prior-nm1-ramp-t.npz:2:1`
- elf-t: `mcts:91+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm1f-ramp-elf.npz+netmid+puct=analysis/scaling/models/prior-nm1-elf-t.npz:2:1`

**N₀, matched to v2skx's wall time per decision** (puct_cost.py with `--deck`, native).
- *Positions.* The recorded decisions of that side in games 0–29 of training shards 77900006, 77900008 and
  77900010: 1876 ramp-t and 2711 elf-t decisions. No game was played and no seed was drawn.
- *Method.* v2skx and the new bot at N 90, 100 and 110 took turns position by position. The new bot's
  ms per decision was fitted linearly in N, and N₀ is where the fit meets v2skx's time.
- *Result.*

  | side | v2skx | N 90 | N 100 | N 110 | N₀ |
  |---|---|---|---|---|---|
  | ramp-t | 83.28 | 79.45 | 82.78 | 88.52 | 99.3 → **99** |
  | elf-t | 100.42 | 100.47 | 104.03 | 110.56 | 90.9 → **91** |

- *Earlier, smaller runs.* Runs of 20–30 games on single shards scattered by about ±10% (data/nm1/cost-*.json),
  which is why the pooled run above sets N₀.

Condition: the opponent's deck list is known (order and hand not).

**NM1 gates (the analysis line, 80c7437).** New bot against v2skx, 300 pairs per gate:

| gate | new bot plays | win rate (95% CI) | CR |
|---|---|---|---|
| 1 | ramp-t | 58.3% (54.5–62.2) | +79 |
| 2 | elf-t | 58.8% (55.0–62.7) | +84 |
| both, 600 pairs | | 58.6% (55.9–61.3) | +82 |

- Both gates passed: the lower bound of the 600 pairs is above 50%.
- **N₀ was corrected inside the gates.** The gates' own checks timed whole games and found the N₀ above off by about
  5% each way, so they ran with corrected N:
  - ramp-t: ratio 1.052, gate N 94, in-gate ratio after the fix 1.015;
  - elf-t: ratio 0.953, gate N 95, in-gate ratio after the fix 1.000.
- **Next time.** For a non-mirror pairing, N₀ should come from whole-game timing like the gates', or from many more
  positions.
- **Installing** is Salem's call.

Condition: the opponent's deck list is known (order and hand not).

## NM2 preparation: ramp-t vs nemesis-t (the architecture thread 2026-10-19 05:28Z; set before any game)

**What the trainer's bots score this pairing with** (pairing_probe.py, data/pairing/probe-nm2.json). It is as in
NM1:

| bot | ramp-t (AI) vs nemesis-t | nemesis-t (AI) vs ramp-t |
|---|---|---|
| fast, original | weights/dragon.json | weights/portal.json |
| normal | ref-5558960/ramp-t-nemesis-t-{ended,act}.json | ref-5558960/nemesis-t-ramp-t-{ended,act}.json |
| strong, max | phased_models/ramp-t-nemesis-t-{ended,act}.json | phased_models/nemesis-t-ramp-t-{ended,act}.json |
| v2skx | pkg-kc-ramp-ramp/ramp-t-nemesis-t-{ended,act}.json | pkg-kc-ramp-ramp/nemesis-t-ramp-t-{ended,act}.json |

- The four per-pairing files are byte for byte the same in the three folders (sha256 0e76127c…, 719ddf12…,
  a16ecfe4…, daafbf1b…). They are version-2 linear models, fitted on the 2000 v2 self-play games of the 2026-10-08
  per-pairing fits (about 15 600 turn ends a side).
- No net answers here: neither the mirror nets nor NM1's, whose pairs are ramp-t–elf-t.

**The card table.** nemesis-t has 38 distinct cards; net-nm1f-ramp-elf and net-mid-ramp-t know 1 of them. The others
are added by their static rows (setnet.extend_table, `--extend-cards`) when a start that lacks them is grown. The
cards themselves are in the simulator (the tournament decks' registration).

**Plan (NM1's recipe):**
- **Data:** v2skx on both sides, `scaledata play --deck ramp-t --opponent nemesis-t`. 10 training shards of 1000 games
  and 5 holdout shards of 1000; seeds from the analysis line.
- **Value net, two arms:** fresh (constructor seed 0), and from net-nm1f-ramp-elf (it has seen the ramp-t side;
  `--init … --extend-cards`). Both have the mid-turn branch and one net for both views
  (`--pairs ramp-t:nemesis-t nemesis-t:ramp-t`), with NM1's settings. **The arm with the lower valid Brier, both kinds
  of row together, goes to the gate.** The holdout shards are not read before that choice.
- **Priors:**
  - ramp-t side: from prior-nm1-ramp-t (`--prior … --extend-cards`).
  - nemesis-t side: there is no nemesis prior. It is made as the mirrors' `ft` priors were: the trunk from the chosen
    NM2 value net (`setpolicy fit --init NET`), fine-tuned with its head at τ 0.5. That trunk has seen nemesis-t's
    cards, and a mirror prior's trunk has not. The chosen net has the mid-turn flag, so its trunk is taken at flag 0
    (a turn end): the flag's row of V1 is left out. This is the one code change, off for unflagged nets.
  - Both sides: τ 0.5 on that side's decisions (`setpolicy encode --deck`).
- **N₀:** by whole-game timing (NM1's gates found per-decision timing ±5% off), or many more positions than NM1's.
  Given to the analysis line before the gate.

Condition: the opponent's deck list is known (order and hand not).

**NM2 value net, the two arms and the choice** (2026-10-19 08:42–09:2xZ; the rule above). Both fits ran on 10 shards:
318 021 training and 16 828 valid rows, mid-turn rows thinned at 0.337.

| arm | sha256 | epochs (kept) | valid Brier, both kinds | turn end | mid-turn | at the start |
|---|---|---|---|---|---|---|
| start, net-nm2-ramp-nem (from net-nm1f-ramp-elf) | 9c8fb308… | 11 (7) | 0.19081 | 0.19209 | 0.18955 | 0.232 / 0.232 |
| fresh, **net-nm2f-ramp-nem** | e2866368… | 13 (9) | **0.18835** | 0.18983 | 0.18689 | 0.402 / 0.396 |

- **The fresh arm goes to the gate**, as in NM1. The start inherited something: it began far better (0.23
  against 0.40). But it stopped at a worse epoch.
- The holdout shards (78800000 + 2h) were not read for the choice.
- The nemesis-t prior takes its trunk from net-nm2f-ramp-nem (`setpolicy fit --init`).

Condition: the opponent's deck list is known (order and hand not).

**Whole-game timing on recorded games does not match the gates either** (game_cost.py, NM1's specs; data/nm1/
gamecost-*.json). The positions were games 0–29 of shards 77900006 / 08 / 10, with one agent per game and side kept
through the game, the specs rotating game by game. Ratios are the new bot's ms per decision over v2skx's:

| side | N | game_cost.py | the gate's own whole-game timing |
|---|---|---|---|
| ramp-t | 99 | 1.121 | 1.052 |
| ramp-t | 94 | 1.035 | 1.015 |
| elf-t | 91 | 1.141 | 0.953 |
| elf-t | 95 | 1.122 | 1.000 |

- **Why it misses.** On recorded games the agent follows v2skx's moves. The positions it meets, and what it keeps
  between decisions (a reused tree, the lethal stamp), are not those of its own games. So this is worse than the
  per-position fit, which was off by about 5%.
- **What sets N.** The offline N₀ is only a start. The N of a gate is set by the gate's own check games (whole-game
  timing in play), as in NM1. For NM2 the start is the pooled per-position fit, as NM1's was.

Condition: the opponent's deck list is known (order and hand not).

### NM2 priors, the new bot's two specs and N₀ (2026-10-19 09:2x–10:4xZ)

| prior | from | train / valid decisions | valid CE | epochs (best) | sha256 |
|---|---|---|---|---|---|
| prior-nm2-ramp-t | prior-nm1-ramp-t (`--prior --extend-cards`) | 201 495 / 10 522 | 1.2333 → 1.10376 | 32 (28) | 45abda4f… |
| prior-nm2-nemesis-t | the trunk of net-nm2f-ramp-nem at flag 0 (`--init`), a new head | 270 677 / 14 366 | 1.29994 (epoch 1) → 1.23206 | 42 (38) | 8e074cc1… |

**The new bot:**
- ramp-t: `mcts:88+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm2f-ramp-nem.npz+netmid+puct=analysis/scaling/models/prior-nm2-ramp-t.npz:2:1`
- nemesis-t: `mcts:86+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm2f-ramp-nem.npz+netmid+puct=analysis/scaling/models/prior-nm2-nemesis-t.npz:2:1`

**N₀**, NM1's pooled per-position fit (puct_cost.py `--deck`). The positions are games 0–29 of training shards
78700006 / 08 / 10: 1925 ramp-t and 2629 nemesis-t decisions. The table is ms per decision (data/nm2/cost-*-fit.json):

| side | v2skx | N 90 | N 100 | N 110 | N₀ |
|---|---|---|---|---|---|
| ramp-t | 90.77 | 92.01 | 94.74 | 100.05 | 88.0 → **88** |
| nemesis-t | 101.06 | 103.30 | 106.81 | 112.97 | 86.3 → **86** |

This N₀ is a start (see above): the gate's own check games set the N, as in NM1.

Condition: the opponent's deck list is known (order and hand not).

## NM1 generation 2: the plan (set before the gen-2 data is read)

- **Data.** The NM1 new bot played both sides (`--opponent-spec`): training 78300000 + 2k (k = 0–9) and holdout
  78400000 + 2h (h = 0–4), 1000 games each; the analysis line played all but k = 9.
- **Value net `net-nm1g2-ramp-elf`.**
  - Start: net-nm1f-ramp-elf, its table and flag kept, both orders.
  - Training rows: generation 1's 10 training shards plus generation 2's 10. Both kinds of row, mid-turn rows thinned
    to the turn ends' count over all 20 shards. Valid games: seed·100003 + g a multiple of 20 in both generations.
  - Settings: NM1's (lr 1e-3, decay 0.5, l2 1e-5, batch 256, `--ftz`, patience 4, at most 60 epochs), the best valid
    epoch kept.
  - One arm only: the step is a continuation. The holdout shards of both generations are the analysis line's.
- **Priors `prior-nm1g2-ramp-t` / `prior-nm1g2-elf-t`.** Each side's from prior-nm1-* (`--prior`), on that side's
  decisions in the same 20 shards, τ 0.5.
- **Generation 1's data stays in.** Generation 2's games come from a stronger player, but 10⁴ of them alone is half
  the rows. Keeping both is how the mirrors' later generations were trained (gen4-59000, the mid nets).
- **N₀.** The gate (gen 2 against gen 1) puts two new bots side by side with the same structure, so their cost
  differs only by the priors and nets. The start is the pooled per-position fit, and the gate's check games set N.

Condition: the opponent's deck list is known (order and hand not).

## NM3 preparation: elf-t vs nemesis-t (the architecture thread 2026-10-19 10:38Z; set before any game)

**What the trainer's bots score this pairing with** (pairing_probe.py, data/pairing/probe-nm3.json):

| bot | elf-t (AI) vs nemesis-t | nemesis-t (AI) vs elf-t |
|---|---|---|
| fast, original | weights/forest.json | weights/portal.json |
| normal | ref-5558960/elf-t-nemesis-t-{ended,act}.json (sha256 f3b4ebee…, 7da583ee…) | ref-5558960/nemesis-t-elf-t-{ended,act}.json |
| strong, max, v2skx | phased_models (= pkg-kc-ramp-ramp)/elf-t-nemesis-t-{ended,act}.json (e9a27705…, ca6a4f2f…) | phased_models (= pkg-kc-ramp-ramp)/nemesis-t-elf-t-{ended,act}.json (85a74b7f…, 3ff16f20…) |

- **One difference from NM1 and NM2: the elf-t side's models.** Since C2 (the hand feature set, 2026-10-08; gated at
  the strong level only), strong, max and v2skx have the C2 models fitted on the c2gen self-play (13 016 / 62 706
  positions). Normal keeps Version 15's frozen ones.
- The nemesis-t side's files are the same in all three folders (14 341 / 67 348 positions, the 2000-game pairs set).
- No net answers in this pairing.

**Card table.** net-nm2f-ramp-nem knows nemesis-t's cards and not elf-t's. net-nm1f-ramp-elf knows elf-t's and not
nemesis-t's. A start's missing cards are added by their static rows (`--extend-cards`).

**Plan (NM1's recipe):**
- **Data:** v2skx on both sides, `scaledata play --deck elf-t --opponent nemesis-t`: 10 training shards of 1000 and 5
  holdout shards of 1000; seeds from the analysis line.
- **Value net, two arms:** fresh (constructor seed 0), and from net-nm2f-ramp-nem (`--init … --extend-cards`). Both
  have the mid-turn branch and one net for both views (`--pairs elf-t:nemesis-t nemesis-t:elf-t`), with NM1's
  settings. **The arm with the lower valid Brier, both kinds of row together, goes to the gate.** Nothing is assumed
  from NM1 and NM2. The holdout shards are not read before the choice.
- **Priors:** elf-t side from prior-nm1-elf-t, nemesis-t side from prior-nm2-nemesis-t. Both use `--prior
  --extend-cards`, on that side's decisions, τ 0.5.
- **N₀:** the pooled per-position fit as a start; the gate's check games set N.
- **Order:** NM1 generation 2's continuation goes first when its data is in (about 12:35Z); NM3's fits come after.

Condition: the opponent's deck list is known (order and hand not).

**NM2 gates (the analysis line, 29f9cd0).** New bot against v2skx, 300 pairs per gate. The check games corrected N:

| gate | new bot plays | N₀ → N (check ratio) | in-gate ratio | win rate (95% CI) | CR |
|---|---|---|---|---|---|
| 1 | ramp-t | 88 → 94 (0.940) | 0.982 | 54.0% (50.0–58.0) | +38 |
| 2 | nemesis-t | 86 → 77 (1.114) | 1.0305 | 58.3% (54.5–62.2) | +79 |
| both, 600 pairs | | | | 56.2% (53.3–58.9) | +59 |

- Both gates passed: the lower bound of the 600 pairs is above 50%.
- The per-position N₀ was off by 6% (ramp-t) and 11% (nemesis-t). This is NM1's lesson again: the check games set N.
- Installing is Salem's call.

Condition: the opponent's deck list is known (order and hand not).

### NM1 generation 2: the fits, the specs and N₀ (2026-10-19 10:5x–12:2xZ)

| model | from | data | valid | epochs (best) | sha256 |
|---|---|---|---|---|---|
| net-nm1g2-ramp-elf | net-nm1f-ramp-elf | gen 1 + gen 2, 602 228 / 31 847 rows | Brier: turn end 0.17681 → 0.16971, mid-turn 0.16721 → 0.16000 | 13 (9) | 34f53da0… |
| prior-nm1g2-ramp-t | prior-nm1-ramp-t | 383 994 / 20 224 decisions | CE 1.10149 → 1.05866 | 31 (27), two chunks | 4b276d1e… |
| prior-nm1g2-elf-t | prior-nm1-elf-t | 570 378 / 30 356 decisions | CE 1.18051 → 1.14379 | 31 (27), two chunks | c7db9f78… |

The "→" pairs are the start (the gen-1 model on the new valid part) and the fit.

**The gen-2 bot:**
- ramp-t: `mcts:94+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm1g2-ramp-elf.npz+netmid+puct=analysis/scaling/models/prior-nm1g2-ramp-t.npz:2:1`
- elf-t: `mcts:95+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm1g2-ramp-elf.npz+netmid+puct=analysis/scaling/models/prior-nm1g2-elf-t.npz:2:1`

**N₀.** Generation 1's in-gate N, 94 and 95. The two generations have the same structure. At the same N, gen 2 against
gen 1 cost 0.980 (ramp-t, 519 decisions) and 1.003 (elf-t, 790), per-position on 25 games of 78300018
(data/nm1g2/cost-g2-*.json). The gate's check games set N.

Condition: the opponent's deck list is known (order and hand not).

**NM1 generation-2 gates (the analysis line, f960c05).** Gen 2 against gen 1, 300 pairs per gate. The check games kept N:

| gate | gen 2 plays | N₀ → N (check ratio) | in-gate ratio | win rate (95% CI) | CR |
|---|---|---|---|---|---|
| 1 | ramp-t | 94 → 94 (1.021) | 1.024 | 57.2% (53.2–61.1) | +68 |
| 2 | elf-t | 95 → 95 (0.971) | 0.980 | 54.0% (50.2–57.8) | +38 |
| both, 600 pairs | | | | 55.6% (52.8–58.4) | +53 |

- Both gates passed: the lower bound of the 600 pairs is above 50%.
- Keeping gen 1's N held here. The two generations have the same structure, and the gates' same-deck ms ratios,
  gen 2 over gen 1, were 1.008 (ramp-t) and 0.995 (elf-t). The per-position reading above was 0.980 / 1.003.
- Installing is Salem's call.

Condition: the opponent's deck list is known (order and hand not).

### NM3 self-play: the builder's training shards (2026-10-19 10:4x–14:0xZ)

v2skx on both sides (`scaledata play --deck elf-t --opponent nemesis-t`), the builder's half of the training shards:
79100000 + 2k, k = 5–9 (data/nm3/rec, SHA256SUMS-build). The analysis line plays k = 0–4 and the holdout.

| k | shard | games | draws | first player wins | elf-t wins | elf-t in seat 0 | elf-t first |
|---|---|---|---|---|---|---|---|
| 5 | 79100010 | 1000 | 0 | 572 | 453 | 500 | 511 |
| 6 | 79100012 | 1000 | 0 | 553 | 456 | 500 | 497 |
| 7 | 79100014 | 1000 | 0 | 557 | 462 | 500 | 487 |
| 8 | 79100016 | 1000 | 0 | 554 | 439 | 500 | 507 |
| 9 | 79100018 | 1000 | 0 | 547 | 454 | 500 | 491 |

- Every shard has 1000 distinct g.
- "First player wins" is winner == first. An earlier message to the analysis line counted winner == 0 by mistake, and
  the analysis line caught it.
- k = 9 was stopped after 279 games on purpose, to add workers, and resumed from its part file. Games 277–282 replay
  identically.

Condition: the opponent's deck list is known (order and hand not).

### NM3: the value net, the priors, the specs and N₀ (2026-10-19 14:5xZ–17:1xZ)

The data is the 10 training shards 79100000 + 2k, k = 0–9: the analysis line's k = 0–4 (SHA256SUMS-analysis on
its branch) and the builder's k = 5–9. 19 of the analysis line's games were replayed, all identical, including
four around k = 2's resume point. The validation part is (seed·100003 + g) % 20 == 0, as in NM1 and NM2.

**Value net, two arms** (valid: 8952 turn-end and 9051 mid-turn rows of 500 games):

| arm | model | epochs (best) | valid Brier: turn end / mid-turn / both | start on the valid part | sha256 |
|---|---|---|---|---|---|
| fresh | net-nm3f-elf-nem | 11 (7) | 0.19776 / 0.19370 / **0.19572** | — | 30846733… |
| from net-nm2f-ramp-nem, `--extend-cards` (21 cards added) | net-nm3-elf-nem | 6 (2) | 0.20231 / 0.20018 / 0.20124 | 0.23922 / 0.23444 | 0cda54b6… |

- **The fresh arm goes to the gate.** It has the lower valid Brier, both kinds of row together, as in NM1 and NM2.
  The holdout was not read before the choice.
- **The choice holds on the valid part alone.** Paired over the valid games (2000 resamples of games), start − fresh
  is +0.0055, sd 0.0023, 95% +0.001 to +0.010. The fresh arm's own valid Brier has an sd of 0.006 over games.
- **Every valid game has the pairing's first deck in seat 0.** 100003 ≡ 3 (mod 20) and the shards' seeds are even,
  so the chosen g are all even, and play() seats the deck at g % 2. The net has no seat input (only went_first and
  the like). The valid games' first-player share, first-player wins, elf-t wins and length are those of the training
  games, within noise. The same holds for NM1 and NM2.
- **The architecture thread's decision (16:53Z):** lines continued from an earlier net keep this split. From-scratch
  nets of new pairings get a seat-free split (for example hash(seed, g) % 20 == 0), and this README says which line
  uses which. Earlier results are not recomputed.

**Priors** (both `--prior --extend-cards`, τ 0.5, on that side's decisions):

| prior | from | train / valid decisions | valid CE | epochs | sha256 |
|---|---|---|---|---|---|
| prior-nm3-elf-t | prior-nm1-elf-t | 319 125 / 17 151 | 1.373 → 1.23115 | 51 (6675 s) | ab41e9ad… |
| prior-nm3-nemesis-t | prior-nm2-nemesis-t | 324 735 / 17 161 | 1.39392 → 1.23071 | 32 (4239 s) | 7c9da4f9… |

**A fix to the priors' info (9b28ed9).** With `--extend-cards`, `setpolicy fit --prior` kept the start prior's own
provenance in the info: its init, its shards, its deck and opponent. Now it writes the fields a plain `--prior`
writes: the prior and its sha256, the shards and τ. `--deck` / `--opponent` set the side; they are info only, and
default to the prior's.
- The two NM3 priors' info was rewritten to these fields after the fit, and their weights were checked identical.
- prior-nm2-ramp-t, prior-nm1g2-ramp-t and prior-nm1g2-elf-t keep the stale fields. Their weights, and so their play
  in the gates, are as gated.
- No search reads these fields. pairing_probe.py prints a prior's deck and opponent.

**The new bot:**
- elf-t: `mcts:88+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm3f-elf-nem.npz+netmid+puct=analysis/scaling/models/prior-nm3-elf-t.npz:2:1`
- nemesis-t: `mcts:86+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm3f-elf-nem.npz+netmid+puct=analysis/scaling/models/prior-nm3-nemesis-t.npz:2:1`
- Both were checked to build and to search with the set N. The net answers both orders. Each prior is its own
  side's.

**N₀**, the pooled per-position fit as in NM2: puct_cost.py `--deck` on games 0–29 of training shards
79100006 / 08 / 10. The table gives ms per decision (data/nm3/cost-*-fit.json).

| side | decisions | v2skx | N 90 | N 100 | N 110 | N₀ |
|---|---|---|---|---|---|---|
| elf-t | 2952 | 99.52 | 100.96 | 103.73 | 109.92 | 88.1 → **88** |
| nemesis-t | 3037 | 113.44 | 116.08 | 119.97 | 126.46 | 85.7 → **86** |

The same fit on NM2's file gives its 86.3 back. This N₀ is a start: as in NM1 and NM2, the gate's check games set N.

Condition: the opponent's deck list is known (order and hand not).

### The validation split: `--split key|hash` (the architecture thread 2026-10-19 16:53Z)

`learn.setnet.in_valid` picks the validation games for train_mid.py, train.py net and `setpolicy fit`.
- **`key`** is the default and every net's split so far: (seed·100003 + g) % 20 == 0. With even shard seeds it picks
  g of one parity only, so one seat (see the NM3 section).
- **`hash`** is splitmix64 of the same key, % 20 == 0. It picks the same share of games with no tie to g's parity.
  On NM3's 10 training shards it picks 533 games, 47.5% of them with g even.
- With `key` the parts are those of before. On NM3's data the counts are 335 737 / 18 003 rows and 319 125 /
  17 151 decisions, and net-nm3f-elf-nem's valid Brier is 0.19572 again. A model's info has `"split": "hash"` only
  when it was fitted with hash.

**Which line uses which:**

| line | split |
|---|---|
| every net and prior up to and including NM3 | key |
| continued lines (NM1 gen 3, NM2 gen 2, and the like) | key |
| from-scratch nets of new pairings, from the next one on | hash |

Condition: the opponent's deck list is known (order and hand not).

**NM3 gates (the analysis line, 6ef8368).** New bot against v2skx, 300 pairs per gate:

| gate | new bot plays | N₀ → N (check ratio) | in-gate ratio | win rate (95% CI) | CR |
|---|---|---|---|---|---|
| 1 | elf-t | 88 → 88 (1.027) | 0.984 | 52.7% (48.7–56.7) | +25 |
| 2 | nemesis-t | 86 → 78 (1.105) | 1.046 (out of band, noted) | 67.5% (64.0–71.0) | +172 |
| both, 600 pairs | | | | 60.1% (57.3–62.8) | +97 |

- Both gates passed: the lower bound of the 600 pairs is above 50%.
- **The nemesis-t side ran slower than the per-position fit both times:** check ratio 1.114 in NM2 and 1.105 in NM3.
  Even after the fix, the in-gate ratio was 1.03–1.05.
- **The architecture thread's rule (18:02Z):** from now on, a nemesis-t side's N₀ is divided by 1.10 before it goes
  to the analysis line's check.
- Installing is Salem's call.

Condition: the opponent's deck list is known (order and hand not).

### NM1 generation 3 self-play: the builder's training shards (2026-10-19 18:0x–19:5xZ)

Both sides are the gen-2 bot with their own specs (`scaledata play --deck ramp-t --opponent elf-t --spec R
--opponent-spec E`). The N are the architecture thread's: ramp-t 89 (corrected by the gen-2 direct test), elf-t 95.
- R = `mcts:89+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm1g2-ramp-elf.npz+netmid+puct=analysis/scaling/models/prior-nm1g2-ramp-t.npz:2:1`
- E = `mcts:95+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm1g2-ramp-elf.npz+netmid+puct=analysis/scaling/models/prior-nm1g2-elf-t.npz:2:1`

The builder plays training shards 79700000 + 2k, k = 3–9 (data/nm1g3/rec, SHA256SUMS-build), and holdout h = 3, 4.
The analysis line plays k = 0–2 and holdout h = 0–2. k = 3, 4 and h = 3, 4 moved to the builder at 19:54Z.
The builder checked the analysis line's k = 0–2: SHA256SUMS, the stats, and 12 of 12 replayed games identical
(g 0, 1, 500, 999 of each shard).

| k | shard | games | draws | first player wins | ramp-t wins | ramp-t in seat 0 | ramp-t first |
|---|---|---|---|---|---|---|---|
| 3 | 79700006 | 1000 | 0 | 587 | 490 | 500 | 501 |
| 4 | 79700008 | 1000 | 0 | 631 | 530 | 500 | 513 |
| 5 | 79700010 | 1000 | 0 | 611 | 530 | 500 | 487 |
| 6 | 79700012 | 1000 | 0 | 574 | 512 | 500 | 514 |
| 7 | 79700014 | 1000 | 0 | 584 | 508 | 500 | 502 |
| 8 | 79700016 | 1000 | 0 | 616 | 540 | 500 | 520 |
| 9 | 79700018 | 1000 | 0 | 576 | 527 | 500 | 517 |

- Every shard has 1000 distinct g. Each has two `ai` strings, one per seat order.
- No shard was stopped or resumed.
- "First player wins" counts winner == first.
- This is a continued line, so its fits use `--split key`.

Condition: the opponent's deck list is known (order and hand not).

### NM1 generation 3: the fits, the specs and N₀ (2026-10-19 20:4xZ–23:5xZ)

The data is gen 1, gen 2 and gen 3's training shards, 30 in all: 77900000 / 78300000 / 79700000 + 2k, k = 0–9.
The split is `--split key`, as for a continued line.

**Value net, two arms** (the architecture thread 19:52Z). The valid part is 23 987 turn-end and 24 080 mid-turn rows
of 1500 games:

| arm | model | epochs (best) | valid Brier: turn end / mid-turn / both | sha256 |
|---|---|---|---|---|
| from net-nm1g2-ramp-elf | net-nm1g3-ramp-elf | 13 (9) | 0.16857 / 0.15935 / **0.16395** | 7885e137… |
| fresh | net-nm1g3f-ramp-elf | 17 (13) | 0.16911 / 0.16010 / 0.16460 | 92de25d9… |

- **The continued arm goes to the gate.** Its valid Brier is the lower.
- **Start:** net-nm1g2-ramp-elf scores 0.16636 on the same valid part (0.1707 / 0.16203).
- **The difference is within noise.** Paired over the valid games (2000 resamples), fresh − continued is +0.00065,
  sd 0.00063, 95% −0.0005 to +0.0020.
- **By generation** (continued / fresh):

  | valid rows | continued | fresh |
  |---|---|---|
  | gen 1 | 0.16560 | 0.16705 |
  | gen 2 | 0.15977 | 0.16089 |
  | gen 3 | 0.16642 | 0.16584 |

  The fresh arm is lower on gen 3's own rows.
- **On the gen-3 holdout (the analysis line, 1194793) the fresh arm is about 0.001 better on both kinds of row.**
  Both arms beat the gen-2 net there. The gate uses the continued arm, as registered.

**Priors** (each from its gen-2 prior, `--prior --extend-cards --deck --opponent`, τ 0.5, that side's decisions in
the 30 shards):

| prior | train / valid decisions | valid CE | epochs | sha256 |
|---|---|---|---|---|
| prior-nm1g3-ramp-t | 588 354 / 30 965 | 0.98571 → 0.96885 | 37 | 913be133… |
| prior-nm1g3-elf-t | 871 727 / 45 994 | 1.06246 → 1.04815 | 31 | 9a92361f… |

- Both ran in two planned chunks. Each was stopped at 23:07Z, before its 2 h limit, and resumed from its checkpoint.
  The epochs carry on in order, so the fit is the one an unbroken run gives.
- Their info is written by the fixed `fit` (9b28ed9): the gen-2 prior and its sha256, the 30 shards and the side.

**The gen-3 bot:**
- ramp-t: `mcts:89+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm1g3-ramp-elf.npz+netmid+puct=analysis/scaling/models/prior-nm1g3-ramp-t.npz:2:1`
- elf-t: `mcts:95+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm1g3-ramp-elf.npz+netmid+puct=analysis/scaling/models/prior-nm1g3-elf-t.npz:2:1`
- Both were checked: they build and search with their N, the net answers both orders, and each prior is its side's.

**N₀:** gen 2's N, 89 and 95, as for gen 2 against gen 1. Per position at the same N, on 25 games of 79700018
(data/nm1g3/cost-g3-*.json), gen 3 against gen 2 costs:

| side | decisions | ms per decision (gen 2 → gen 3) | ratio |
|---|---|---|---|
| ramp-t | 521 | 87.65 → 86.56 | 0.988 |
| elf-t | 720 | 95.22 → 95.01 | 0.998 |

The gate's check games set N.

Condition: the opponent's deck list is known (order and hand not).

**NM1 generation-3 gates (the analysis line, 999a37f): not passed.** Gen 3 against gen 2, 300 pairs per gate:

| gate | gen 3 plays | N₀ → N (check ratio) | in-gate ratio | win rate (95% CI) | CR |
|---|---|---|---|---|---|
| 1 | ramp-t | 89 → 92 (0.969) | 0.990 | 53.2% (49.3–57.2) | |
| 2 | elf-t | 95 → 98 (0.965) | 1.059 (out of band, noted) | 47.7% (43.8–51.5) | |
| both, 600 pairs | | | | 50.4% (47.6–53.2) | +4 |

- **Not passed:** the lower bound of the 600 pairs is below 50%. Gen 2 stays NM1's bot.
- **Both checks found gen 3 about 3% cheaper** than the per-position readings (0.988 / 0.998) said, so N was raised by
  3 on each side.
- **The gate used the continued arm, as registered.** On the gen-3 holdout the fresh arm was about 0.001 better on
  both kinds of row; the gate does not say whether that would have mattered.
- **What NM1 does next is the architecture thread's call.**

Condition: the opponent's deck list is known (order and hand not).

### NM2 generation 2: self-play, the fits, the specs and N₀ (2026-10-19 21:3xZ – 2026-10-20 02:3xZ)

**Self-play.** NM2 bots on both sides with their own specs: ramp-t mcts:94 and nemesis-t mcts:75 (the install N),
both with net-nm2f-ramp-nem and that side's NM2 prior. Training shards are 80100000 + 2k, holdout 80200000 + 2h.
- The builder played k = 7–9 and h = 3, 4 (data/nm2g2/rec and /hold, SHA256SUMS-build). The analysis line played the
  rest.
- The builder checked the analysis line's k = 0–6: SHA256SUMS 7 of 7, the stats, and 21 of 21 replays.
- ramp-t won 4483 of the 10 000 training games.

| k | shard | first player wins | ramp-t wins |
|---|---|---|---|
| 7 | 80100014 | 560 | 430 |
| 8 | 80100016 | 563 | 463 |
| 9 | 80100018 | 573 | 463 |

**Value net, two arms.** Gen 1 + gen 2, 20 shards, `--split key`. The valid part is 16 503 turn-end and 16 708
mid-turn rows of 1000 games.

| arm | model | epochs (best) | valid Brier: turn end / mid-turn / both | sha256 |
|---|---|---|---|---|
| from net-nm2f-ramp-nem | net-nm2g2-ramp-nem | 9 (5) | 0.18736 / 0.18139 / 0.18436 | e0b75bc7… |
| fresh | net-nm2g2f-ramp-nem | 16 (12) | 0.18383 / 0.18041 / **0.18211** | ac8bd599… |

- **The fresh arm goes to the gate.**
- **Start:** net-nm2f-ramp-nem scores 0.19171 on the same valid part.
- **Paired over the valid games:** continued − fresh is +0.00225, sd 0.00099, 95% +0.0003 to +0.0042.
- **By generation** (continued / fresh): gen 1 0.18777 / 0.18661, gen 2 0.18093 / 0.17758.
- **Holdout (the analysis line, 9d746a7):** gen-1 net 0.1974 / 0.1939, continued 0.1866 / 0.1812, fresh
  0.1834 / 0.1783. Fresh − continued is −0.0031 / −0.0029, the same way as on valid.
- **The arm rule from NM3 gen 2 on (the architecture thread 01:23Z):** with the paired valid interval clear of 0, the
  better arm; with it across 0, the fresh arm.

**Priors** (each from its NM2 prior, `--prior --extend-cards --deck --opponent`, τ 0.5):

| prior | train / valid decisions | valid CE | epochs | sha256 |
|---|---|---|---|---|
| prior-nm2g2-ramp-t | 401 108 / 21 060 | 1.05003 → 1.01124 | 31 | 847e24f5… |
| prior-nm2g2-nemesis-t | 551 233 / 29 103 | 1.17205 → 1.13477 | 26 | b672ed41… |

**The gen-2 bot:**
- ramp-t: `mcts:94+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm2g2f-ramp-nem.npz+netmid+puct=analysis/scaling/models/prior-nm2g2-ramp-t.npz:2:1`
- nemesis-t: `mcts:74+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm2g2f-ramp-nem.npz+netmid+puct=analysis/scaling/models/prior-nm2g2-nemesis-t.npz:2:1`
- Both were checked: they build and search with their N, the net answers both orders, and each prior is its side's.

**N₀.** Gen 1's N times gen 1 / gen 2 per position, at the same N, on 25 games of 80100018 (data/nm2g2/cost-g2-*.json):

| side | decisions | ms per decision (gen 1 → gen 2) | ratio | N₀ |
|---|---|---|---|---|
| ramp-t | 549 | 91.66 → 91.40 | 0.997 | 94 |
| nemesis-t | 822 | 108.82 → 110.04 | 1.011 | 75 / 1.011 → **74** |

- **The 1/1.10 rule for nemesis-t is not applied on top.** That rule came from new bots against v2skx: different
  structures, where per-position timing read the nemesis-t side about 10% low (NM2 1.114, NM3 1.105).
- Here both bots have the same structure, and B's N 75 is already an in-gate N. NM1 gen 2's same-structure checks were
  1.021 / 0.971.
- With the rule taken literally, the start would be 74 / 1.10 → 67.
- **The architecture thread agreed (02:15Z): the start is 74.** The rule now reads: a nemesis-t side's N₀ is divided
  by 1.10 only when B is v2skx, a different structure. The gate's check games set N.

Condition: the opponent's deck list is known (order and hand not).

**NM2 generation-2 gates (the analysis line, bb56f17): passed.** Gen 2 against gen 1, 300 pairs per gate:

| gate | gen 2 plays | N₀ → N (check ratio) | in-gate ratio | win rate | CR |
|---|---|---|---|---|---|
| 1 | ramp-t | 94 → 85 (1.106) | 0.984 | 50.0% | +0 |
| 2 | nemesis-t | 74 → 77 (0.962) | 0.963 (out of band, noted) | 59.5% | +91 |
| both, 600 pairs | | | | 54.8% (52.1–57.3) | +45 |

- Both gates passed: the lower bound of the 600 pairs is above 50%.
- **The per-position N₀ missed on both sides,** though both bots have the same structure:
  - ramp-t was about 10% too high (the check ratio was 1.106);
  - nemesis-t was about 4% too low (0.962).
- **The install N (the architecture thread 02:45Z):** ramp-t 85, nemesis-t 80.
- Installing is Salem's call.

Condition: the opponent's deck list is known (order and hand not).

### NM3 generation 2: self-play, the fits, the specs and N₀ (2026-10-20 02:5xZ–09:4xZ)

**Self-play.** NM3 bots on both sides with their own specs: elf-t mcts:88, nemesis-t mcts:75 (the install N), both
with net-nm3f-elf-nem and that side's NM3 prior. Training shards are 80500000 + 2k, holdout 80600000 + 2h.
- The builder played training k = 5–9 and holdout h = 4 (data/nm3g2/rec and /hold, SHA256SUMS-build). The analysis
  line played the rest, h = 3 included.
- **Resumes after container restarts:** the builder's k = 6 (after game 765; g 763–767 replay identically), and the
  analysis line's k = 2 (after game 190) and h = 0 (after game 864).
- **Cross-machine check of h = 3:** the builder's 17 games of h = 3 from before it stopped (g 0–16) are identical to
  the analysis line's.
- The builder checked the analysis line's k = 0–4: SHA256SUMS 5 of 5, the stats, and 14 of 14 replays.
- elf-t won 4285 of the 10 000 training games.

| k | shard | first player wins | elf-t wins |
|---|---|---|---|
| 5 | 80500010 | 556 | 441 |
| 6 | 80500012 | 540 | 427 |
| 7 | 80500014 | 572 | 419 |
| 8 | 80500016 | 558 | 437 |
| 9 | 80500018 | 550 | 433 |

**Value net, two arms.** Gen 1 + gen 2, 20 shards, `--split key`. The valid part is 17 354 turn-end and 17 374
mid-turn rows of 1000 games.

| arm | model | epochs (best) | valid Brier: turn end / mid-turn / both | sha256 |
|---|---|---|---|---|
| from net-nm3f-elf-nem | net-nm3g2-elf-nem | 9 (5) | 0.18765 / 0.18115 / 0.18440 | dc184732… |
| fresh | net-nm3g2f-elf-nem | 12 (8) | 0.18617 / 0.18010 / **0.18313** | 67cb052a… |

- **Start:** net-nm3f-elf-nem scores 0.19097 on the same valid part.
- **Paired over the valid games:** continued − fresh is +0.00127, sd 0.00095, 95% −0.0007 to +0.0032. The interval
  crosses 0, so the 01:23Z rule picks the fresh arm. Its point estimate is also the lower.
- **By generation** (continued / fresh): gen 1 0.19423 / 0.19125, gen 2 0.17396 / 0.17450.
- **Holdout (the analysis line, 3253ab6):** gen-1 net − fresh is +0.0108 / +0.0112. Fresh − continued is
  −0.0008 / +0.0004, so the two do not separate. On the elf-t side's mid-turn rows the continued arm is better by
  +0.0015 (+0.0003 to +0.0027).

**Priors** (each from its NM3 prior, `--prior --extend-cards --deck --opponent`, τ 0.5, `--split key`):

| prior | train / valid decisions | valid CE | epochs | sha256 |
|---|---|---|---|---|
| prior-nm3g2-elf-t | 630 516 / 33 403 | 1.15454 → 1.12266 | 22 | 9317eb6a… |
| prior-nm3g2-nemesis-t | 645 599 / 33 819 | 1.16011 → 1.12602 | 36 | b14dc2ad… |

Both ran in two planned chunks. Each was stopped at 07:51Z, before its 2 h limit, and resumed from its checkpoint;
the epochs carry on in order.

**The gen-2 bot:**
- elf-t: `mcts:88+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm3g2f-elf-nem.npz+netmid+puct=analysis/scaling/models/prior-nm3g2-elf-t.npz:2:1`
- nemesis-t: `mcts:75+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-nm3g2f-elf-nem.npz+netmid+puct=analysis/scaling/models/prior-nm3g2-nemesis-t.npz:2:1`
- Both were checked: they build and search with their N, the net answers both orders, and each prior is its side's.

**N₀.** Gen 1's N times gen 1 / gen 2 per position, at the same N, on 25 games of 80500018
(data/nm3g2/cost-g2-*.json). There is no 1/1.10 for nemesis-t: B is the same structure.

| side | decisions | ms per decision (gen 1 → gen 2) | ratio | N₀ |
|---|---|---|---|---|
| elf-t | 805 | 159.48 → 159.36 | 0.999 | 88 |
| nemesis-t | 821 | 146.91 → 147.80 | 1.006 | 75 / 1.006 → 75 |

Both timings ran beside other fits, but the specs take turns position by position, so the drift falls on both alike.
The gate's check games set N.

Condition: the opponent's deck list is known (order and hand not).

**NM3 generation-2 gates (the analysis line, 70111a0): not passed.** Gen 2 against gen 1, 300 pairs per gate:

| gate | gen 2 plays | N₀ → N (check ratio) | in-gate ratio | win rate (95% CI) | CR |
|---|---|---|---|---|---|
| 1 | elf-t | 88 → 80 (1.095) | 1.026 | 44.5% (40.5–48.5) | −52 |
| 2 | nemesis-t | 75 → 75 (1.007) | 0.953 (out of band, noted) | 60.3% (56.4–64.2) | +99 |
| both, 600 pairs | | | | 52.4% (49.5–55.2) | +23 |

- Not passed: the lower bound of the 600 pairs is below 50%.
- **The two sides went opposite ways.** The gen-2 elf-t side is clearly worse than gen 1; the nemesis-t side is
  clearly better.
- **The per-position ratio missed again on the elf-t side:** 0.999 against a check of 1.095.
- **The registered "if the elf-t side is still weak, look into it" condition is met.** The analysis line put three
  routes to the architecture thread:
  - (a) a same-N control;
  - (b) swapping the net and the prior apart;
  - (c) replacing only the nemesis-t side.
- The NM3 model files are left as they are until it decides.

Condition: the opponent's deck list is known (order and hand not).

### NM3 generation 2: why the elf-t side fell back — the prior and the timing (the architecture thread 2026-10-20 10:31Z)

Report only. No game is played and no seed is drawn. The NM3 model files are left as they are.

**(1) The two elf-t priors on the gen-2 holdout's elf-t decisions.** The script is `nm3g2_prior_cmp.py`, and the
output is `data/nm3g2/diag/prior-cmp-elf-t.json`.

- The holdout is h = 0–4 (80600000 + 2h), encoded with `setpolicy encode --deck elf-t`: 164 016 decisions.
- The search targets come from the gen-1 bots that played those shards. That search ran with the gen-1 prior, so "top-1
  vs search" leans towards gen 1.
- A rerun differs from the first run in one decision, an argmax near-tie under threaded BLAS. The file holds the rerun.

| | gen-1 prior | gen-2 prior |
|---|---|---|
| CE to the search, τ 0.5 | 1.07897 | 0.98003 |
| top-1 = the search's top | 80.87% | 81.69% |
| mass on the search's top | 0.448 | 0.523 |

The two priors' top-1 picks agree on 86.4% of decisions. By the kind of move the search chose:

| search's top | decisions | gen 1 hits | gen 2 hits | g1 = g2 |
|---|---|---|---|---|
| play (no target) | 71 358 | 80.95% | 82.44% | 87.0% |
| attack → leader | 20 574 | 87.49% | 87.89% | 88.6% |
| **attack → enemy card** | 17 897 | 85.75% | **82.07%** | 86.3% |
| **play → enemy card** | 16 140 | 69.66% | **67.10%** | 77.9% |
| evolve | 8 821 | 82.61% | 84.90% | 87.8% |
| super-evolve | 8 162 | 82.05% | 84.56% | 88.2% |
| end turn | 7 399 | 91.39% | 93.99% | 94.5% |
| play → hand card | 6 222 | 50.13% | 59.48% | 75.4% |
| bonus | 5 794 | 87.49% | 88.87% | 91.2% |

- **Gen 2 is the better prior overall** (CE −9%) and in every turn band.
- **It is worse in one place: picking an enemy card to hit**, whether by attacking it or by playing a card at it. That is
  trading and removal: 34 037 decisions, about a fifth of elf-t's.
- When the two priors disagree, about half the time both pick a "play" move but a different card or target (10 402 of
  22 339). Next most common: gen 1 plays and gen 2 attacks (2 475); then both attack, at different targets (2 176).

**(3) Timing.** The script is `gate_ratios.py`, and the output is `data/nm3g2/diag/gate-ratios.json`. The four-spec
per-position file is `data/nm3g2/diag/cost-split-elf-t.json`.

- **What the check compares.** A gate's check ratio is A's ms per decision over B's, in the same games. In a non-mirror
  gate, A and B sit on opposite decks. Recomputed from each ncheck.jsonl, it reproduces all 16 scaling checks exactly.
- **What N₀ compared.** The gen-2 N₀ compared gen 2 with gen 1 on the same deck. It cannot predict a check of
  gen-2 elf-t against gen-1 nemesis-t.
  - The gen-1 install Ns (elf-t 88, nemesis-t 75) were each set against v2skx, never against each other.
  - So 0.999 and 1.095 measure different things.
- **The check is noisy.** A pair bootstrap of each 300-pair gate gives the SD of what a 20-pair check would read. It is
  0.034–0.051, wider than the ±0.03 band. NM3 gen-2 gate 2 is one example: it read 1.007 at its check and 0.953 over
  its 600 games, at the same N.
- **The gen-2 elf-t side is not slower.**
  - In the check games at N 88: gen 2 97.88 ms per decision (gate 1), gen 1 97.25 (gate 2). Decisions per game: 34.8
    and 34.0.
  - Per position at N 88, on the N₀'s 805 elf-t positions, each spec relative to gen 1 (156.24 ms):

    | gen-2 net | gen-2 prior | ratio |
    |---|---|---|
    | | | 1 |
    | yes | | 0.986 |
    | | yes | 0.999 |
    | yes | yes | 1.004 |

  - Neither the net nor the prior makes a decision slower. Neither do longer turns: the decisions per game above are
    much the same.
- **Gate 1's elf-t side was not short of time.** Over its 600 games at N 80 it ran at 1.026 of its gen-1 nemesis-t
  opponent's time per decision.

**The 16 checks and their gates** (ratio = A ms per decision / B ms per decision):

| gate | check N | check ratio | gate N | gate ratio (600 games) | 20-pair SD |
|---|---|---|---|---|---|
| nm1 gate1-ramp | 99 | 1.052 | 94 | 1.015 | 0.047 |
| nm1 gate2-elf | 91 | 0.953 | 95 | 1.000 | 0.042 |
| nm1g2 direct elf-t | 95 | 0.985 | 95 | 0.998 | 0.049 |
| nm1g2 direct ramp-t | 94 | 1.027 | 94 | 1.061 | 0.048 |
| nm1g2 gate1-ramp | 94 | 1.021 | 94 | 1.024 | 0.043 |
| nm1g2 gate2-elf | 95 | 0.971 | 95 | 0.980 | 0.044 |
| nm1g3 gate1-ramp | 89 | 0.969 | 92 | 0.990 | 0.040 |
| nm1g3 gate2-elf | 95 | 0.965 | 98 | 1.059 | 0.047 |
| nm2 gate1-ramp | 88 | 0.940 | 94 | 0.982 | 0.039 |
| nm2 gate2-nem | 86 | 1.114 | 77 | 1.030 | 0.051 |
| nm2g2 gate1-ramp | 94 | 1.106 | 85 | 0.984 | 0.049 |
| nm2g2 gate2-nem | 74 | 0.962 | 77 | 0.964 | 0.045 |
| nm3 gate1-elf | 88 | 1.027 | 88 | 0.984 | 0.034 |
| nm3 gate2-nem | 86 | 1.105 | 78 | 1.046 | 0.039 |
| nm3g2 gate1-elf | 88 | 1.095 | 80 | 1.026 | 0.037 |
| nm3g2 gate2-nem | 75 | 1.007 | 75 | 0.953 | 0.036 |

- The 600-game ratios run from 0.953 to 1.061, with a mean of 1.006.
- The "N₀ misses" in NM2 and NM3 were checks of A against the opposite deck, plus the check's own noise. Gen 2 was not
  slower.
- For a gen-vs-gen gate, N₀ is better estimated as A's side against B's side, with both on their own decks' positions
  in the same games.

**Reading them together.** The elf-t fall-back is not a timing artefact. What differs is how the gen-2 prior chooses
targets on enemy cards. The analysis line's b1 and b2 half-gates swap the net and the prior, and they will say which
one carries the loss.

Condition: the opponent's deck list is known (order and hand not).

**Afterwards (the analysis line c577c03, c9d85c3).** The premise of this section was withdrawn.
- A single gate's score holds the two decks' matchup, so it is read against the previous generation's self-play rate
  for that deck, not against 50%.
- Read that way, the elf-t side did not fall back:
  - gen 2 against gen 1: +1.7;
  - the half-gates: b1 (gen-2 net) +3.4, b2 (gen-2 prior) +2.2, a (gen 2 at N 88) +6.9.
- The seat split was withdrawn (the architecture thread 10:57Z). The NM3 candidate is the gen-1 bot again.

### Same-deck N against v2skx for the install candidates (the architecture thread 2026-10-20 10:55Z / 10:57Z)

The rule from the next gate on: a seat's N is matched to v2skx playing the same deck. Here it is recomputed for each
install candidate's seats, offline, with no game and no seed.

**Method.** The script is `samedeck_fit.py`, and the data are in `data/samedeck/`.
- *Positions.* Each line's gen-1 N₀ positions: games 0–29 of three v2skx training shards per line, 90 games.
- *Timing.* puct_cost.py `--deck`, with v2skx and the candidate at three N, taking turns position by position.
- *Fit.* A linear fit in N; the N is where the fit meets v2skx's time.
- *The two runs.*
  - 2026-10-20: three seats ran in parallel, N 75/90/105.
  - 2026-10-19: the gen-1 fits. Converted to gen 2 with the gen-2 / gen-1 per-position ratio at the same N (0.980,
    1.003, 0.997, 1.011). NM3's gen-1 bot needs no conversion.

| seat | gate N | install N | same-deck N, 10-19 fit | same-deck N, 10-20 fit |
|---|---|---|---|---|
| NM1 gen 2 ramp-t | 94 | 89 | 103 | 88 |
| NM1 gen 2 elf-t | 95 | 95 | 90 | **81** |
| NM2 gen 2 ramp-t | 85 | 85 | 89 | 83 |
| NM2 gen 2 nemesis-t | 77 | 80 | 84 | 75 |
| NM3 gen 1 elf-t | 88 | 88 | 88 | |
| NM3 gen 1 nemesis-t | 78 | 75 | 86 | |

- **The two runs disagree by 6–15% in N, on the same positions.**
  - *What moved.* The new bot's time per decision against v2skx's, at the same N, moved by 2–8% between the runs.
  - *What held.* Gen 2 against gen 1 stayed within about 1%: same structure, same run.
  - *How it amplifies.* Time per decision is flat in N: the elasticity is 0.39–0.59, so 10% more N is only about 4–6%
    more time. A few percent of timing drift therefore becomes 5–15% in N.
- *Solo control on 30 of the 90 games, run alone.* At N 90, gen 1 and gen 2 against v2skx:
  - elf-t: 1.136 and 1.138;
  - nemesis-t: 1.136 and 1.132.

  The generations match, but the level is far above both fits (about 1.00–1.09).
- So a time match between a net bot and v2skx, two different structures, depends on the host and its state at the
  10% level. A same-structure match does not.
- **The flag (a same-deck N more than 10% below the gate N).**
  - NM1 gen 2 elf-t is flagged in the 10-20 fit (81 against 95), but not in the 10-19 fit (90).
  - Nothing else is flagged in either run.
  - NM3 gen 1 nemesis-t goes the other way: its gate N is below the same-deck N.
- **For the NM2 gen-2 gate against v2skx:** the same fit, run on the gate's own host just before the gate, sets N₀
  better than either run here. Its seats come out at ramp-t 83–89 and nemesis-t 75–84.

Condition: the opponent's deck list is known (order and hand not).

**Afterwards (the architecture thread 2026-10-20 11:59Z).**
- A gate against v2skx now gets its same-deck N measured on the analysis line's machine, under the gate's load, just
  before the gate. A gen-vs-gen gate is matched as before.
- **The install N is not taken from these offline numbers.** The trainer runs in the browser (Pyodide), where timing
  differs from both machines. Once Salem chooses to install, the same-deck N against v2skx is measured once in the
  browser. Until then, a candidate's N in the lists here is a reference only.
- The NM2 positions for that fit are `data/samedeck/rec-cost-nm2.jsonl.gz`: the first 30 games of 78700006 / 08 /
  10, in that order, 90 records. The file is checked equal, record by record, to the committed shards (sha256
  70e59868b19f64e7…).

Condition: the opponent's deck list is known (order and hand not).

## Strong's net bots by matchup: the install, and N from real games in the page's runtime (2026-10-23)

**Salem, in this session:** 「装档」, then 「非镜像也装，那几个nm都装吧」.

**What changes.** `ui.session.MATCHUPS` / `level_spec` picks strong's bot by (the player's deck, the AI's deck) in 8
matchups. Every other matchup, and every other level, is unchanged.

| matchups | bot |
|---|---|
| the ramp-t mirror | net-mid-ramp-t + prior-ramp-ft-t05 |
| the elf-t mirror | net-mid-elf-t + prior-elft-ft-t05 |
| ramp-t vs elf-t (NM1 gen 2, both seats) | one net; the prior is the AI's deck's |
| ramp-t vs nemesis-t (NM2 gen 2, both seats) | one net; the prior is the AI's deck's |
| elf-t vs nemesis-t (NM3 gen 2, both seats) | one net; the prior is the AI's deck's |

**The page.** It ships 13 models (5 nets and 8 priors), about 13.5 MB of base64. These go in `models-N.json`, each
about 6 MB, and svsim.json `_more` lists them for worker.js. numpy (about 16 MB) comes too. All of it downloads once,
the first time the page opens. Nothing is published yet.

**N from real games.** The script is `selfplay_time.py`, run in Pyodide through `web_sim/selfplay_time_in_pyodide.py`
and `run_py.js` on the build's own bundle. The data are in `data/install-time/`.
- Each seed is one game, played twice: the new bots on both sides, and the reference on both sides.
- The two take turns seed by seed, in a rotating order.
- The time of every agent.act is summed per deck.
- Seeds, timing only (the analysis line 0e9038c / 8c19c27): the mirrors 82500000–09 and 82600000–09; NM1 83500000–09,
  NM2 83600000–09, NM3 83700000–09.
- In Pyodide the games replayed move for move as natively.

| matchup, deck the AI plays | N | reference | new ms / reference ms per decision | ratio |
|---|---|---|---|---|
| ramp-t mirror | 83 | v2s | 122.33 / 124.24 | 0.985 |
| ramp-t mirror | 83 | v2skx | 114.58 / 118.77 | 0.965 |
| elf-t mirror | 73 | v2s (= v2skx on elf-t) | 148.31 / 151.20 | 0.981 |
| NM1, ramp-t | 94 | v2skx | 146.30 / 134.25 | 1.090 |
| NM1, elf-t | 95 | v2skx | 143.54 / 140.99 | 1.018 |
| NM2, ramp-t | 76 | v2skx | 127.90 / 139.48 | 0.917 |
| NM2, nemesis-t | 63 | v2skx | 155.14 / 150.83 | 1.029 |
| NM3, elf-t | 76 | v2skx | 159.36 / 135.40 | 1.177 |
| NM3, nemesis-t | 75 | v2skx | 159.76 / 144.13 | 1.108 |

- Each row is 10 games per side: 270–690 decisions. Read the ratios as about ±5–8%.
- **The reference waits on where the trainer runs.**
  - The web page (version 23) has strong = v2s.
  - Salem's Windows install (673e2c1, 10-13) has strong = v2skx.
  - The architecture thread proposes bringing the page to the Windows state (v2skx in the unchanged matchups, plus
    最强), which would make v2skx the reference.
- **N, by the gates' rule:** inside 0.97–1.03, N stays; outside, N = round(N / ratio), once. Against v2skx:

  | seat | N |
  |---|---|
  | ramp-t mirror | 83 → 86 |
  | elf-t mirror | 73 |
  | NM1 | 94 → 86 / 95 |
  | NM2 | 76 → 83 / 63 |
  | NM3 | 76 → 65 / 75 → 68 |

  Against v2s, the mirrors stay at 83 / 73.

Condition: the opponent's deck list is known (order and hand not).

**Against v2s, and the installed N** (the architecture thread 14:38Z).
- The page keeps version 23's strong (v2s) in every other matchup; v2skx and 最强 are not added.
- So the N is matched to v2s. The non-mirror pairings were retimed against v2s on the same seeds:

| matchup, deck the AI plays | gated N | new ms / v2s ms per decision | ratio | installed N |
|---|---|---|---|---|
| ramp-t mirror | 83 | 122.33 / 124.24 | 0.985 | 83 |
| elf-t mirror | 73 | 148.31 / 151.20 | 0.981 | 73 |
| NM1, ramp-t | 94 | 142.67 / 132.12 | 1.080 | 87 |
| NM1, elf-t | 95 | 141.79 / 136.66 | 1.038 | 92 |
| NM2, ramp-t | 76 | 130.58 / 123.13 | 1.061 | 72 |
| NM2, nemesis-t | 63 | 152.91 / 152.84 | 1.000 | 63 |
| NM3, elf-t | 76 | 157.07 / 126.23 | 1.244 | 61 |
| NM3, nemesis-t | 75 | 155.79 / 133.52 | 1.167 | 64 |

- The new bots replay their games identically in both runs (the same seeds). Their own times moved by 1–3% between
  the runs: the machine.
- The analysis line's round 8 measured these cells at the gated N (83 / 73 / 89 / 95 / 85 / 80 / 88 / 75). It notes
  every cell whose installed N is more than 15% away.

Condition: the opponent's deck list is known (order and hand not).
