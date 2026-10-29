# Shared value net: transfer test T1 (2026-10-29)

Condition: 对手卡表已知（牌序、手牌未知）— the opponent's deck list is known (order and hand not).

Why (the architecture thread 2026-10-29 02:30Z): the deck search has to judge decks by playing them, and the cheap
bot it can afford (mcts:100+plan, the hand-written score) misjudges some decks. A position score shared by every deck
would fix that; the first question is whether a value net already trained on one or two decks helps on set-10 decks it
never saw.

## Set-up

- Tool: `svsim/tools/deckgate.py` (a7a9d62). A pair is one deal of one ordered non-mirror matchup of the field: X plays
  deck a against Y playing b from both seats, then Y plays a against X playing b (4 games, one seed). The 42 ordered
  matchups of the 7 decks in turn, by offset (each block of 7 plays every deck once as a and once as b).
- Field: `fields/B-r1.txt`, search B's 7 incumbents after round 1 (claude/deck-search 241da436), all set-10 pool. Of
  each deck's ~30 distinct cards, 25-33 are new to either net.
- Y = `mcts:100+plan` (hand-written score). X = `mcts:N+plan+setnet=NET+netmid+netany` (+netany: the net scores every
  game, a7a9d62).
- Time match (the gate's rule, once): 12 pairs at N = 100, seeds 85890000 on (`t1/time-*.jsonl`): CPU per searched
  decision X / Y = 1.833 (net-mid-ramp-t) -> N 55, 2.028 (net-nm3g3f-elf-nem) -> N 49. Over the 300 pairs the ratio
  came out 1.14-1.21 (the 12-pair measure under-corrected; the rule adjusts once, so N stayed): X had 14-21% more CPU.
- 300 fixed pairs per arm (1200 games), bank 85800000 + k, the same seeds for every arm (paired).
- The architecture thread's prediction, registered before the run: the better of the two nets 48%-54%; above 52% with
  probability 0.4.

## Results (X's score, 95% interval over pairs)

| arm | X | score | CPU per step X / Y |
|---|---|---|---|
| 1 (registered) | net-mid-ramp-t, N 55 | 22.5% ± 2.1% | 46 / 39 ms |
| 2 (registered) | net-nm3g3f-elf-nem, N 49 | 23.0% ± 2.3% | 44 / 38 ms |
| 3 (added after) | 1 + `+netclip` | 23.0% ± 2.2% | 46 / 38 ms |
| 4 (added after) | 2 + `+netclip` | 25.5% ± 2.3% | 43 / 38 ms |

Paired differences (same seeds): arm 2 - arm 1 +0.5% ± 3.1%; arm 3 - arm 1 +0.5% ± 2.1%; arm 4 - arm 2 +2.5% ± 2.8%.

By the deck X played (arm 1 / 2 / 3 / 4): forest 19 / 16 / 15 / 20%, sword 44 / 47 / 47 / 45%, rune 9 / 16 / 11 / 16%,
dragon 21 / 20 / 23 / 20%, abyss 23 / 8 / 22 / 17%, haven 11 / 15 / 13 / 20%, portal 31 / 39 / 32 / 41% (about 86
pairs each, ± 4-8%). Logs with every line: `t1/*.log`; every game: `t1/*.jsonl`.

Both registered arms are far below the prediction: both nets lose to the hand-written score on unseen decks, by
about 27 points.

## Why +netclip (arms 3, 4)

A card's input is its static row standardized with the training cards' mean and std (learn.setnet). A column that
never varied in training has std ~1e-3, so a new card reads 1000-5000 standard deviations there (craft_sword,
hook_on_engage, countdown, type_amulet for the ramp-t net; craft_sword, hook_on_earth_rite, kw_aura for NM3), against
at most 12 (ramp-t) and 84 (NM3) on the nets' own cards. `+netclip` (c80f691) clips each column to the range of the
net's own cards (its own cards unchanged, bit for bit). It changed nothing measurable: the inputs blowing up is not
why the nets fail here.

## Control: the tool and +netany on the net's own pairing

`fields/control-elf-nem.txt` (elf-t and nemesis-t, the 2026-10-07 lists), seeds 85810000 on:
- C1: X = mcts:49+plan+setnet=net-nm3g3f-elf-nem+netmid (no +netany: its own pairing), 100 pairs: 58.2% ± 4.7%
  (elf-t 50.0%, nemesis-t 66.5%). The net helps on the decks it was trained on, through the same tool.
- C2: the same with +netany, the first 20 pairs: every pair's points and move counts identical to C1 (20 / 20).

So T1's result is the nets', not the tool's.

# S1: a shared net trained on a pool of set-10 decks (2026-10-29)

The architecture thread 2026-10-29 03:33Z. Condition: 对手卡表已知（牌序、手牌未知）.

- Pool: `fields/C-r0-pool.txt`, search C's 112 distinct round-0 candidates (claude/deck-runs-C 5d70c18), 16 per class,
  65% set-10 cards; B-r1 (the test field) is not in it.
- Self-play: `learn.scaledata play --pool`, two different decks per game (same class allowed), both sides
  mcts:100+plan, 20 shards x 1000 games, seeds 85830000 + 2k (k < 20). About 2.4 CPU s a game.
- Hold-out by deck (`s1.py holdout`): one deck per class (smallest label sha256): C-r0-abyss-random8,
  C-r0-dragon-random4, C-r0-forest-random12, C-r0-haven-random12, C-r0-portal-random7, C-r0-rune-random10,
  C-r0-sword-random14; every game drawing one is validation (2467 of 20000), none is in training
  (`train_mid.py --split games:s1/holdout-games.json`).
- Training: `analysis/scaling/train_mid.py --shared --fresh`, turn-end and mid-turn rows (mid rows thinned to the
  turn-end count), the scaling test's settings. net-s1-10k (first 10 shards) and net-s1-20k (all 20).

## Held-out decks: is it a better predictor? (`s1/eval-*.json`)

Log loss on the held-out decks' games (the hand-written score: search.evaluate with the default weights, what
mcts:100+plan searches with, calibrated by a one-variable logistic fit on 600 training games; constant: the base rate):

| | turn ends | mid-turn |
|---|---|---|
| net-s1-10k | 0.592 | 0.584 |
| net-s1-20k | **0.575** | **0.568** |
| hand-written, calibrated | 0.645 | 0.647 |
| constant | 0.693 | 0.693 |

The net predicts results on decks it never saw clearly better than the hand-written score.

## B-r1: does it play better? (`s1/gate/`)

tools.deckgate on B-r1, Y = mcts:100+plan, X = mcts:N+plan+setnet=net-s1-20k+netmid+netany.
- Time match (once): 24 pairs at N = 100, seeds 85891000 on: CPU X / Y 1.772 -> N 56. (24 pairs at N = 100: 32.3% ±
  9.1%.)
- 300 fixed pairs (1200 games), bank 85820000: **X 36.5% ± 2.4%** (95% 34.1%-38.9%).
  - By X's deck: forest 25.3%, sword 55.8%, rune 20.9%, dragon 34.3%, abyss 34.9%, haven 36.0%, portal 48.2% (± 6.5-8.5%).
  - First / second: 37.3% / 35.7%.
  - **CPU per searched decision X 57 ms, Y 46 ms: ratio 1.231, outside 0.97-1.03** (the extra time is X's).
- The architecture thread's prediction, registered before: 45%-56%, above 52% with probability 0.4. The result is
  below the range.

Against T1 (pairing nets, 22.5%-25.5%, bank 85800000) S1 gains about 13 points, but the search with the shared net
still loses to the hand-written score by 13 points on the same field, with more CPU. A better predictor of the result
does not make a better search here (see the report to the architecture thread for what this suggests checking).

## S1 (i): a shared move prior over the hand-written score (`s1/gate/prior-*`)

`analysis/scaling/models/prior-s1-20k.npz`: learn.setpolicy fit on S1's 20 shards' decisions (k < 20, C-r0 pool),
trunk from net-s1-20k, validation the held-out decks' games (`--split games:s1/holdout-games.json`), cards
`cards-all.npz`. Capped at 6 epochs (validation cross-entropy 1.3879, 1.3832, 1.3811, 1.3799, 1.3791, 1.3785: about
0.001 an epoch at the end; early stopping alone would have run many more 40-minute epochs). X =
mcts:N+plan+puct=prior-s1-20k (the hand-written score, the shared prior at the root and in the tree), Y = mcts:100+plan.

- **Timing and BLAS threads.** The first time match (24 pairs at N = 100, seeds 85891100 on, numpy's BLAS threads
  left as they come) gave CPU X / Y 5.967 (X 399 ms, Y 67 ms a searched decision). The same 24 pairs with BLAS on one
  thread (OMP_NUM_THREADS = OPENBLAS_NUM_THREADS = MKL_NUM_THREADS = 1): **1.573 (X 73 ms, Y 46 ms) -> N 64**, the
  same games (43.8% ± 7.4% both times). With 4 workers on 4 cores, BLAS threads oversubscribe the machine and are
  charged to the side that calls numpy; the gate below runs on one thread. The earlier timings in this file (T1, S1)
  were taken with threads as they came. S1's time match again on one thread (`s1/gate/time-100-1thread.*`, the same
  24 pairs, the same games): **1.781 -> N 56**, as before (1.772 -> 56): the value net's small products do not start
  BLAS threads, the prior's larger ones do. S1's gate (36.5%) stands; T1 (value nets of the same size) likewise.
- 300 fixed pairs (1200 games), bank 85820000, X = mcts:64+plan+puct=prior-s1-20k, one thread (`s1/gate/prior-64.*`):
  **X 48.3% ± 2.1%** (95% 46.3%-50.4%), the sequential test H0.
  - By X's deck: forest 44.7%, sword 72.1%, rune 37.8%, dragon 40.1%, abyss 37.8%, haven 48.8%, portal 57.1%
    (± 7.0-8.1%).
  - First / second: 50.0% / 46.7%.
  - **CPU per searched decision X 55 ms, Y 43 ms: ratio 1.284, outside 0.97-1.03** (the extra time is X's: the
    24-pair measure under-corrected, and the rule adjusts once).
- The architecture thread's prediction, registered before: 50%-55%, above 52% with probability 0.4. The result is
  below the range, and with X's 28% more CPU the CPU-adjusted reading is lower still.

The prior with 64 iterations nearly matches the hand-written search with 100 (so it is worth more than its
iterations), but what it costs a decision is about what it saves: at equal CPU it does not help on B-r1. It is far
closer than the shared value net (S1, 36.5% at 23% more CPU).
