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
