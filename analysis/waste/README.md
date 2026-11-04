# Resource waste: a search problem or an evaluator problem? (measurement only)

**Condition:** the opponent's deck list is known (deck order and hand unknown).

**The question** (the architecture thread, 2026-10-10 06:27Z). The analysis line's M3 (ca822b5) looked at the 85
stage-0 turns where Salem's line differs from the bot's. Most of them are *conserve* (30) or *mixed* (31): Salem
keeps a card, PP or EP, or builds the same board with less. Is that because the bot doesn't search far enough
(more iterations would close the gap), or because its evaluation prices resources wrongly (even 3000 iterations
still spend)?

**How it was measured** (`waste.py`):
- **Starts:** M3's 85 starts (turn-level step 0, RC 84d735e).
- **Replays:** on each start, the bot's turn is played again on the real position, the way step 0 played its "bot"
  line (`search.candidates.play_turn` with the spec's agent).
- **Specs:** level-strong (`mcts:200+plan+learned+phased`), `mcts:1043+plan+learned+phased` and
  `mcts:3000+plan+learned+phased`, with the same 4 seeds each.
  - Seed j of start k is 65960000 + k + 1000 j. j = 0 is step 0's own seed.
  - Check: level-strong at j = 0 replays step 0's stored bot line step for step on **85/85** starts.
- **Turn-end fields:** read with M3's own snapshot (the analysis line's `direction.py`), as Salem − line.
- **R, the resource gap** (Salem − line), in M3's conserve units: a card in hand, 2 PP left, an EP and a SEP each
  count 1. Positive means Salem kept more.
- **Generic events per turn** (no table per card):
  - evolve_no_kill: an evolution that destroyed no enemy follower, by itself or by that follower's attacks, on a
    turn not won. Split three ways: the follower then hit the leader / it didn't attack / other.
  - overkill: attack beyond the defense of the follower it killed.
  - max_pp_gain: maximum PP gained by cards played (ramp).
  - play_no_change: a card played that changed neither board, nor either leader, nor the maximum PP.
  - Plain counts.

Run: `python3 analysis/waste/waste.py run STEP0 ANA M3_ROWS --out rows.jsonl --seeds 4 --workers 4`.
- `ANA` is the analysis line's `analysis/` folder (`lethal-setup/`, `turn-level/`, `card-value/`; branch
  ccr-da4857cc-rkpgwr).
- `STEP0` is `analysis/turn-level/step0` of local/pairings-20261008.
- Then read with `waste.py read rows.jsonl M3_ROWS --ana ANA`.
- Rows: `data/waste_rows.jsonl.gz`. Full read: `data/waste_read.txt`.
- svsim 715230d, Python 3.11, this container. M3 reproduces exactly here first (85/85 rows identical).

## Results

**All 85 starts** (seed means, then the mean over starts):

| spec | R | M3's conserve rule still holds | same turn end as Salem | ms per turn |
|---|---|---|---|---|
| level-strong, j = 0 only (step 0's line) | +0.70 | 65% | – | – |
| level-strong, 4 seeds | +0.73 | 64% | 0% | 481 |
| mcts:1043 | +0.68 | 61% | 4% | 2181 |
| mcts:3000 | +0.53 | 56% | 5% | 6808 |

Reseeding level-strong does not move it toward Salem: +0.70 at j = 0 against +0.73 over 4 seeds. So the drops
below are not regression to the mean from how the starts were picked.

**Per resource** (Salem − line), and the paired change from strong to 3000. Negative means 3000 is closer to Salem.
Intervals: 2000 resamples of starts, seed 0.

| class | resource | strong | 1043 | 3000 | 3000 − strong [95%] |
|---|---|---|---|---|---|
| conserve (30) | **hand** | +1.07 | +0.71 | +0.57 | **−0.50 [−0.93, −0.14]** |
| conserve | PP left | +0.89 | +0.93 | +0.97 | +0.07 [−0.04, +0.20] |
| conserve | EP | +0.23 | +0.24 | +0.20 | −0.03 [−0.11, +0.02] |
| conserve | SEP | +0.07 | +0.07 | +0.10 | +0.03 [−0.07, +0.17] |
| conserve | R | +1.81 | +1.48 | +1.35 | −0.46 [−0.83, −0.15] |
| mixed (31) | hand | +0.21 | +0.24 | −0.02 | −0.23 [−0.74, +0.23] |
| mixed | PP left | +0.34 | +0.44 | +0.40 | +0.06 [−0.19, +0.34] |
| mixed | EP | +0.29 | +0.30 | +0.29 | +0.00 [−0.16, +0.16] |
| mixed | R | +0.44 | +0.59 | +0.35 | −0.10 [−0.56, +0.36] |
| all 85 | hand | +0.42 | +0.29 | +0.14 | −0.29 [−0.52, −0.06] |
| all 85 | PP left | +0.42 | +0.49 | +0.48 | +0.06 [−0.05, +0.16] |
| all 85 | EP | +0.16 | +0.18 | +0.16 | +0.01 [−0.06, +0.08] |
| all 85 | R | +0.73 | +0.68 | +0.53 | −0.20 [−0.43, +0.03] |

By M3's class, R for strong / 1043 / 3000:
- race (3): −0.50 / 0.00 / −0.50
- clear (2): 0 / 0 / 0
- develop (6): −0.71 / −0.58 / −0.58
- conserve (30): +1.81 / +1.48 / +1.35. 3000 has the smaller R on 9 starts, the larger on 0, the same on 21.
- mixed (31): +0.44 / +0.59 / +0.35. Smaller on 7, larger on 7, the same on 17.
- small (13): about 0.

**What the extra spending is** (mean per turn: Salem / strong / 1043 / 3000):

| event | all 85 | conserve (30) | mixed (31) |
|---|---|---|---|
| evolutions | 0.24 / 0.39 / 0.42 / 0.40 | 0.27 / 0.50 / 0.51 / 0.47 | 0.23 / 0.52 / 0.52 / 0.52 |
| evolve_no_kill | 0.21 / 0.31 / 0.30 / 0.27 | 0.13 / 0.30 / 0.28 / 0.23 | 0.23 / 0.41 / 0.44 / 0.39 |
| ... of which the follower didn't attack | 0.08 / 0.16 / 0.12 / 0.12 | 0.03 / 0.11 / 0.11 / 0.10 | 0.06 / 0.25 / 0.16 / 0.16 |
| cards played | 1.81 / 1.96 / 1.96 / 1.93 | 1.73 / 2.20 / 2.16 / 2.13 | 2.06 / 2.01 / 2.10 / 2.02 |
| PP spent | 7.34 / 7.76 / 7.83 / 7.82 | 6.63 / 7.53 / 7.56 / 7.60 | 8.16 / 8.50 / 8.60 / 8.56 |
| max_pp_gain (ramp) | 0.11 / 0.05 / 0.09 / 0.07 | 0.17 / 0.03 / 0.04 / 0.03 | 0.06 / 0.02 / 0.10 / 0.06 |
| overkill (attack beyond the kill) | 0.85 / 0.77 / 0.91 / 0.96 | 0.53 / 0.98 / 1.01 / 1.13 | 0.97 / 0.74 / 0.72 / 0.73 |
| attacks on followers | 0.62 / 0.38 / 0.44 / 0.48 | 0.73 / 0.37 / 0.43 / 0.53 | 0.52 / 0.29 / 0.32 / 0.35 |

Other fields: more search also builds a bigger board than Salem (own stats −1.05 → −2.06) and leaves the enemy leader
lower (enemy HP +0.23 → +0.55). It isn't converging to Salem's line overall: the same turn end in 5% of cases at
3000.

## How it reads (descriptive; the classes are small)

- **Cards in hand: partly a search problem.**
  - In the conserve class, 3000 iterations close about half of the card gap: +1.07 → +0.57. The interval excludes 0,
    and no start gets worse.
  - The extra card the bot plays is something deeper search learns not to play. Even so, half the gap is left at
    3000.
- **PP left and EP: an evaluator problem.**
  - Neither moves from strong to 3000. The intervals sit on 0, and the PP gap grows slightly.
  - The bot evolves about twice as often as Salem in the conserve and mixed classes (0.50 vs 0.27, 0.52 vs 0.23), at
    every budget.
  - Its extra evolutions are mostly ones that kill nothing, and in the mixed class often ones whose follower doesn't
    attack at all (0.16-0.25 vs 0.06).
  - The evaluation prices an EP (and PP left over) below what it is worth to Salem; more search spends it the same
    way.
- **Mixed: no change with search.** R goes +0.44 / +0.59 / +0.35, with an interval around 0.
- **Ramp: also unchanged by search.** Salem gains maximum PP from ramp cards more often than any spec, especially in
  the conserve class (0.17 vs 0.03-0.04 per turn).
  - In M3's fields a ramp play looks like PP spent with no board change, so part of Salem's "keep a card, spend PP"
    pattern is playing a ramp card instead of a body.
  - Those cards are Dragonsign and Lumiore & Argente, Shining Wings. They were checked on the 6 starts where M3's
    snapshot saw nothing change.
- **Overkill rises with search in the conserve class** (0.98 → 1.13 vs Salem's 0.53). Deeper search trades into
  followers with more attack than it needs. It doesn't explain the resource gap, but it is spending of a kind the
  evaluation doesn't charge for.

**Limits:**
- 85 starts and 4 seeds; the classes have 30 and 31 starts; one deck pairing (Salem's Ramp games).
- 3000 iterations is about 14 times level-strong's budget, not unlimited: "search" here means what 15x buys.
- The opponent's hidden hand is determinized by the bot as in play.
- R weights 2 PP as one card, M3's thresholds rather than a value.
- The tags are generic and blind to what a kept card was worth.
