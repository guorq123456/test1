# Teaching the turn-end model Salem's own choices (cand-sp-ramp-ramp; fit only, not installed)

**Condition:** 对手卡表已知（牌序、手牌未知）.

**Task:** the architecture thread 2026-10-10 16:49Z. The evaluators trained on self-play results don't move towards
Salem's choices (opsgap). Use his own turns to teach the model when to fight over resources.

## 1. Data (`sp_extract.py`; data/turns.jsonl.gz, sha256 668c5683…c9e8 uncompressed)

**Games:** all 47 of his trainer games. All replay on the current engine.
- analysis/salem-games/db-export-2026-10-08: 37 games. They sit on the architecture thread's branch
  (9bb5293) and were read from there.
- db-export-2026-10-08b: 10 games.
- Seat 0 is Salem.

**Per Salem turn** (main phase; the 6 turns he won during are left out):
- The installed search (mcts:1043, the search alone) runs once from the turn's start.
- Every path in its tree to End Turn gives a turn end, replayed on the real position. Where a key isn't legal
  there (the determinization drew another card), the line ends there.
- Ends that are the same position are merged, their End Turn visits summed. The 8 most visited are kept.
- The bot's end: the installed agent (mcts:1043 with the lethal check) plays the turn on the real position.
- Salem's end is added when it isn't among them.
- Every end is read as version 2 + kclock for Salem.

| pairing | turns | used |
|---|---|---|
| Ramp mirror | **243** | fitted and read |
| 破魔虫精灵 vs 跳费龙 | 75 | kept apart, descriptive |
| 机锋 vs 连击妖 | 50 | kept apart |
| 旗皇 vs 连击妖 | 31 | kept apart |

Ramp mirror:
- Salem's end is among the search's 8 most visited in 150 of 243 turns.
- The bot played exactly his end in 76.
- The bot won during the turn in 4.
- Turns with two or more candidates: 231. Turns where Salem's end and the bot's differ: 163.
- 7.6 candidates per turn.

## 2. Fit (`sp_fit.py`)

- **Objective:** cand-kc's (contrast on the step-1 labels, + 0.03 × calibration, + L2 1e-4), plus
  λ × preference.
  - The preference term is the mean over turns of the mean over the turn's other candidates of
    softplus(−(E(Salem) − E(c))).
- **Form and features:** cand-kc's (linear, version 2 + kclock, its standardization, the version-2 signs, stock
  held at zero). No card ids, deck ids or pairing.
- **Training:** start at cand-kc, Adam lr 0.01, 600 iterations.
- **Choosing λ** from {0, 0.003, 0.01, 0.03, 0.1, 0.3}: leave whole games out, 9 folds of 3 Ramp-mirror games.
- **Rule, fixed before fitting:** the highest held-out pairwise accuracy against the bot, among the λ whose held-out
  self-play contrast error is within +3% of λ 0's.

**Cross-validation** (held-out games; 231 turns for top-1, 163 pairs against the bot):

| λ | top-1 | Salem > bot | Salem > each candidate | self-play val contrast error |
|---|---|---|---|---|
| 0 | 36.8% | 23.3% | 77.3% | 0.011136 |
| 0.003 | 37.2% | 23.3% | 77.7% | 0.011112 |
| 0.01 | 37.2% | 23.9% | 76.8% | 0.011077 |
| **0.03 (chosen)** | **38.5%** | **25.8%** | **78.6%** | **0.011146** |
| 0.1 | 40.3% | 29.4% | 80.6% | 0.012720 (+14%, out) |
| 0.3 | 41.1% | 35.6% | 80.5% | 0.020622 (out) |

The final model at λ 0.03, fit on all 27 Ramp-mirror games, is `svsim/learn/phased_models/cand-sp-ramp-ramp`
(ENDED sha256 c728520b…cb76; ACT = installed). Its self-play val contrast error is 0.011140, against cand-kc's
0.011104 (+0.3%).

## 3. Reads

**Held-out games, Ramp mirror** (`sp_read.py`, data/read.json; cand-sp scored by the fold model that left the game
out):

| | top-1 | Salem's end above the bot's |
|---|---|---|
| installed | 31.2% | 8.6% |
| cand-kc | 36.8% | 22.7% |
| cand-sp (held out) | 38.5% | 25.8% |
| **cand-sp − cand-kc** | +1.7 points (−1.4 to +5.1) | **+2.9 points (−1.4 to +7.3)** |

Intervals: 2000 resamples of games.

- **J75 is wrong.** The gain against the bot is 2.9 points, not 5; the self-play contrast error is +0.3%, within the
  limit.
- The other pairings, read descriptively with the Ramp-mirror models: Salem above the bot, cand-kc → cand-sp:
  - 破魔虫精灵 vs 跳费龙: 8.6% → 8.6% (70 pairs);
  - 机锋 vs 连击妖: 31.0% → 28.6% (42);
  - 旗皇 vs 连击妖: 20.8% → 20.8% (24).
- All four operations positions come from Salem's games. Each is also read with the fold model that didn't see that
  game.

**Operations positions** (ENDED logit, Salem's end / the other):

| | installed | cand-kc | cand-sp | cand-sp, game held out |
|---|---|---|---|---|
| 329 (vs step 0's bot line; the 24 runs' ends) | 0.625 / 0.799 ✗ (0/24) | 0.536 / 0.558 ✗ (0/24) | **0.794 / 0.732 ✓ (24/24)** | **0.862 / 0.805 ✓ (24/24)** |
| 455 | −0.985 / −0.737 ✗ | −0.873 / −0.667 ✗ | −0.717 / −0.557 ✗ | −0.737 / −0.576 ✗ |
| puzzle 2 (vs cand-kc 997's end) | 0.287 / −0.375 ✓ | −0.030 / −0.210 ✓ | 0.233 / −0.208 ✓ | 0.247 / −0.200 ✓ |
| puzzle 3 (vs cand-kc 997's end) | 0.811 / 0.514 ✓ | 0.075 / 0.313 ✗ | 0.158 / 0.295 ✗ | 0.162 / 0.334 ✗ |

- **329 is the first time any model ranks Salem's end first,** including the fold model that never saw that game.
  It also puts his end above all 24 search runs' ends.
- 455 and puzzle 3 stay wrong.

**Weights** (standardized coefficient; per raw unit in data/read.json):

| column | installed | cand-kc | cand-sp |
|---|---|---|---|
| me_hp | 0.415 | 0.362 | 0.484 |
| me_hp_sqrt | 0.568 | 0.524 | 0.493 |
| op_hp | −0.281 | −0.469 | **−0.600** |
| op_hp_sqrt | −0.584 | −0.261 | −0.306 |
| me_hand | 0.165 | 0.186 | **0.246** |
| me_followers | 0.063 | 0.064 | **0.100** |
| me_atk | 0.157 | 0.279 | 0.285 |
| me_life | 0.158 | 0.077 | 0.093 |
| me_max_pp | 0.959 | 1.008 | **1.312** |
| op_max_pp | −1.209 | −1.179 | −1.488 |
| me_ep | 0.173 | 0.150 | 0.195 |
| me_sep | 0.451 | 0.366 | 0.379 |

**Reading:** Salem's choices push up the worth of what he keeps: his hand (+32%), his maximum play points (+30%), his
followers (+56%) and his own defense. That is the 329 kind of turn. But they push the enemy's defense up too
(op_hp −0.469 → −0.600). So the puzzle 3 kind of turn, where he gives up face damage to keep his own defense, stays
wrong.

## 4. Refit under the analysis line's nested folds (`sp_nested.py`; cand-sp2-ramp-ramp)

The analysis line's pre-registration (c8a04a0, analysis/lethal-setup/README-sp.md), via the architecture thread
16:50Z.
- **Folds:** outer 5 (all 47 games by id, j mod 5); inner 4 over the outer fold's training games, used only to
  choose λ from the same grid (0 included).
- **λ rule:** the highest inner pairwise accuracy, ties to the smaller. Pairwise means Salem's end against each of
  the installed 1043's top 8, an identical end left out, a tie counted half.
- **Fitting:** the same objective, data (the Ramp-mirror turns only) and form as §2. The other pairings' turns are
  scored, with the Ramp-mirror models, but not fitted.

**λ chosen:** 0.3 in every outer fold, and 0.3 for the final model (inner accuracies in data/nested.json).
- 0.3 is the grid's top, so accuracy may keep rising past it.
- The self-play contrast error rises with λ (no limit in this rule): outer folds 0.0199–0.0224; final 0.020337,
  1.83 × cand-kc's 0.011104.

**The builder's own pooled readings** (outer held-out games; the analysis line's readings are the ones that count):

| | cand-sp2 (outer fold) | cand-kc | installed | pairs / turns / games |
|---|---|---|---|---|
| all | 83.7% | 80.1% | 78.6% | 2664 / 399 / 47 |
| Ramp mirror | 86.1% | 81.7% | 79.5% | 1538 / 243 / 27 |
| other pairings | 80.4% | 78.0% | 77.3% | 1126 / 156 / 20 |

**Handed to the analysis line:** data/nested_scores.jsonl (sha256 baa31db9…ddcd1). One row per turn with its outer
fold and λ, and every candidate's flags (salem, in_top, bot), visits and three scores: cand-sp2 by the outer fold's
model, cand-kc, and the installed Ramp-mirror ENDED.

The final model: svsim/learn/phased_models/cand-sp2-ramp-ramp (ENDED sha256 caf02e3a…c5ab). cand-sp-ramp-ramp (§2)
is kept as it is.
