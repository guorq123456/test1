# The three operations puzzles, taken apart (measurement; nothing wired)

**Condition:** the opponent's deck list is known (deck order and hand unknown).

**Task** (the architecture thread 2026-10-10 08:46Z): the analysis line's d9f691e, analysis/lethal-setup/puzzles/puzzles.md. All three are original Ramp mirror turns of Salem's games: Salem is low on defense and facing a big threat. He removes it with Spilling Red and stabilises with Erntz; the bot doesn't.

**Method** (`ops.py`; rows in data/rows.jsonl, the read in data/read.txt):
- Each position is rebuilt from the record (turn-level step 0's start). The agents determinize the opponent's hand themselves.
- Three specs each play the turn on 8 seeds: level-strong, mcts:1043+plan+learned+phased and mcts:3000+plan+learned+phased.
- At the turn's first decision I read the search's root children: Salem's first action's rank, visits and value, against those of the chosen move.
- The installed evaluation (level-strong's weights, the ENDED model) scores Salem's turn end and the bot's. For the linear model, the features that make the difference are listed too.

## Results

| puzzle | installed evaluation of the turn end: Salem / bot | level-strong (200) | mcts:1043 | mcts:3000 | class |
|---|---|---|---|---|---|
| 1 (k 320) | **0.726** / 0.088 | Erntz, end (8/8) | the same (8/8) | the same (8/8) | **luck**, see below |
| 2 (k 518) | **0.587** / 0.282 | the bot's line (8/8) | **Salem's line** (8/8) | **Salem's line** (8/8) | generation: budget |
| 3 (k 445) | **0.652** / 0.403 | the bot's line (8/8) | **Salem's line, another order** (8/8) | the same (8/8) | generation: budget |

**Puzzle 1.**
- Salem's line rests on a draw. Kimika's Fanfare draws a card, and it drew Sagatsumatsu, whose Fanfare adds the two Spilling Red. Sagatsumatsu is 3 of the 27 cards left (11%), and Spilling Red is not in the deck.
- At the start of the turn there is no way to remove the 11/11 Erntz: Burnite's 9 doesn't kill it, and Normagdala gives −0/−4. So Salem's 0.771 in the re-test is the value of his turn end after the lucky draw, not of a plan anyone could have chosen.
- The search's root has Kimika (Salem's first action) at rank 4–15, with value 0.69 against Erntz's 0.92. It is searched, and averaged over draws it is worse.
- This is not a generation or evaluation failure. A fair re-test would play Kimika with its draw re-dealt. I suggest the analysis line drop this puzzle or re-test it that way.

**Puzzle 2.**
- level-strong plays Erntz in all 8 runs, like Salem, then evolves Erntz into Normagdala, leaving us at 3.
- At that second decision the evolution has 99 visits (0.939) and Salem's Bonus Play Point 37–43 (0.88–0.93).
- Turn ends with more iterations, as installed win probability on 4 seeds (mcts:400 / 600 / 1043 / 3000 on the same seeds):
  - mcts:400: 0.492
  - mcts:600 and up: Salem's line exactly (0.587)
- At equal compute, the existing levers don't find it:
  - +prior: 0.423
  - +alloc=legal:2 / :4: 0.233 / 0.282

**Puzzle 3.**
- level-strong plays Lumiore & Argente, discarding Erntz and Sloth (us at 6).
- At the root, Salem's Spilling Red has the same visits as the chosen move (20 / 20) and a higher value (0.994 vs 0.989). Several of Lumiore's discard pairs tie there too.
- A tie-break by value was tried and reverted: it picks another Lumiore pair.
- mcts:400 and up play Salem's line (Erntz, Bonus Play Point, Spilling Red, in that order; the same turn end in value).
- +prior: 0.492. +alloc: 0.403.

## Judgments (the architecture thread's)

- **J43, right (3 of 3).** The installed evaluation rates Salem's turn end higher in all three puzzles. In puzzle 1 that holds only for the end after the lucky draw.
- **J44, wrong.** No puzzle fails because the planner can't express a choice or a discard. These are non-lethal turns: the planner isn't used, and the search lists every discard choice as a legal move.
  - Puzzles 2 and 3 are search budget. Discard choices multiply the moves: 56 legal moves at puzzle 2's root and 15 at puzzle 3's (Lumiore's pairs), and 200 iterations don't reach Salem's line. 400–600 iterations do, and so do 1043 and 3000.
  - Puzzle 1 is luck.
- **No mechanism to fix generically** here, unlike the flags. The planner's discard step (+discard, 20e1aa2) is for lethal turns and doesn't touch these.

**The bank** (tests/puzzles; tools.puzzles):
- Three positions rebuilt from the descriptions (tests/helpers.py `mirror_position`):
  - `ramp-erntz-normagdala` (puzzle 2): setup, expected: the enemy board empty, us at 11 or more.
  - `ramp-erntz-spilling` (puzzle 3): setup, expected: the enemy board empty, us at 13 or more.
  - `ramp-erntz-kimika` (puzzle 1): open, with the luck noted.
- Scoreboard, seeds 1–3:
  - level-strong: 0 / 6 solved.
  - mcts:600+plan+learned+phased: 5 / 6 (puzzle 2 fails on seed 3).
  - Puzzle 1: every spec plays Erntz and ends.

## +complex: compute moved to complex turns (the architecture thread 08:58Z; not in any level)

- **(a) Merging exactly equivalent moves: nothing to merge.** The search keys a hand card by (card id, cost), so the
  copies of one card already share a child. Puzzle 2's 56 legal moves are 56 children with 9 different cards in
  hand, and puzzle 3's Lumiore pairs are combinations, not orders.
- **(b) Iterations by complexity.** `alloc=complex:K:BETA[:LO:HI]` (search.mcts `_complex_budget`); `+complex` is
  K 21.4, BETA 0.4, LO 50, HI 1500.
  - Formula: clip(K × max(n, BETA × n0)), where n is this decision's legal moves and n0 those at the turn's first
    searched decision.
  - A wide turn keeps a share of its budget on its later, narrower decisions. Puzzle 2 loses at its second decision.
  - Per-turn allocation alone (K × n0, any power) gives puzzle 3 only about 290 iterations: complex turns also have
    more decisions.
- **Calibration.** On 200 step-1 games, the iterations the formula gives equal level-strong's at K 28.25. Each
  iteration costs more in complex positions, so K was set by milliseconds.
  - Whole turns on 300 step-1 starts (turn_cost.py), A ÷ level-strong:
    - K 24.5: 1.156
    - K 22.9: 1.076
    - **K 21.4: 1.023** (iterations 0.817)
  - **20 gate pairs at K 21.4** (seeds 68930000–019, private, not a bank's): total ms **0.993**, per searched
    decision **1.007**.
- **Puzzles 2 and 3 (seeds 1–3):**
  - +complex at K 28.25 / 24.5 / 22.9 / **21.4**: 6/6, 5/6, 6/6, **6/6**
  - level-strong: 0/6
  - mcts:600: 5/6
- **Default unchanged:** golden identical.
