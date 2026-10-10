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

## k 329 and 455 (the architecture thread 09:45Z): evaluation

The same breakdown (`ops.py --ks 329 455`; data/rows_329_455.jsonl, read_329_455.txt).

| start | installed evaluation of the turn end: Salem / bot | G_end re-test: Salem / bot | level-strong / 1043 / 3000 (8 seeds each) | class |
|---|---|---|---|---|
| 329 | 0.651 / **0.690** | 1.000 / 0.854 | the bot's end, 24/24 (0.690) | **evaluation** |
| 455 | 0.272 / **0.32–0.38** | 0.583 / 0.125 | 10+ different ends, none Salem's (mean 0.335 / 0.338 / 0.356) | **evaluation** |

**329.**
- The search does see Salem's first move: Lyria with Enhance is rank 5–6 at the root, with value 0.93–0.95. Its continuations score lower.
- Salem keeps a fuller hand: the 7-cost follower Lyria draws, plus Normagdala. He also leaves a Lyria (Barrier) on the field.
- The bot deals 2 more to the face (the enemy at 9 against 11).
- The evaluation pays more for the face damage than for the hand. Largest differences, Salem − bot: op_hp_sqrt −0.23, op_hp_low −0.22, me_barrier +0.15, me_hand +0.10.
- **J51 right.**

**455.**
- Salem's first move (Roar of Prominence) is rank 10–16 at the root, with value 0.57–0.63.
- His end has the enemy at 6, their board empty, and an evolution point kept. The bot's ends have us at 14 with an evolved Kimika on the field.
- The evaluation prefers our defense and board. Largest differences, Salem − bot: op_hp_sqrt +0.21, me_ep +0.20, me_hp_sqrt −0.17, me_hp −0.15, me_atk −0.14.

**The bank:**
- `ramp-lyria-crest` (329): expected the enemy board empty and 6 or more cards in hand.
- `ramp-saga-lyria` (455): expected the enemy board empty, the enemy at 6 or less, and an evolution point kept. tools.puzzles facts now include ep and sep.
- Seeds 1–3: level-strong 0/6, mcts:1043 0/6.

## mcts-reply against mcts:1043 (the architecture thread 12:28Z; J57)

**Question:** in 329, Salem keeps cards because the opponent can clear the board next turn. Neither the strong nor
the strongest level searches the opponent's turn. At 1043's budget, does spending part of it on the opponent's turn
(mcts-reply) find Salem's line?

**Matching the wall clock** (turn_cost.py, whole turns from step-1 turn starts, A ÷ mcts:1043+plan+learned+phased):
- 100 starts, three runs side by side: N 700 → 0.920, N 850 → 1.031, N 1000 → 1.188.
- **N 810 on 300 starts, run alone: ms 1.016** (1278.0 vs 1257.4 ms per turn); iterations 0.764.
- So they can be matched on the same machine.
- On the four puzzle positions the mean ms per turn is 3227 vs 2966 (1.09): these turns are more complex than
  average.

**Spec:** `mcts-reply:810+plan+learned+phased+lazy+focus`.
- `+lazy`: the opponent's turn is played out (greedily) only from a turn-end leaf's second visit.
- `+focus`: only under the top three first moves, and at most 20 times a decision.

**Puzzle bank, seeds 1–8** (tools.puzzles --only; data/reply/), solved by the bank's expected conditions:

| puzzle | mcts-reply:810 | mcts:1043 |
|---|---|---|
| 329 (ramp-lyria-crest) | **0/8** (the same end every seed: enemy 11, us 9, 5 cards) | 0/8 (the same end) |
| 455 (ramp-saga-lyria) | **0/8** (enemy 4–6, no evolution point kept) | 0/8 (the same kind of ends) |
| puzzle 2 (ramp-erntz-normagdala) | 1/8 (7 ends at us 3–4) | **8/8** |
| puzzle 3 (ramp-erntz-spilling) | 8/8 | 8/8 |

**Reading:**
- **J57 wrong:** mcts-reply finds Salem's line in neither 329 nor 455. In 329 it ends exactly where 1043 does.
- **Puzzle 2 gets worse** (8/8 → 1/8). It needs depth in our own turn, and mcts-reply has 24% fewer of our own
  iterations at the same wall clock.
- **One caveat:** with `+focus`, at most 20 leaves a decision see the opponent's turn, and only through a greedy
  reply. That is a narrow look at "can they clear my board".

## The opponent's turn played out from both turn ends (the architecture thread 13:15Z; J60)

**Script:** `reply_ends.py` (data/reply/reply_ends.txt, .jsonl). Diagnostic only; the search is unchanged.

**Method:**
- Start from Salem's turn end and from each distinct end of the eight mcts:1043 runs: 329 has one; 455 has seven,
  weighted by their runs.
- 16 determinizations. They are the same for every end of a start: the opponent's hand is dealt from their sorted
  unseen pool with seed j.
- The opponent's turn is played to its end by the search's greedy reply, and separately by
  mcts:1043+plan+learned+phased.
- When my turn comes, the installed evaluation scores it for me (the model for the player to move).

**Win probability after the opponent's reply** (mean ± 95%; the difference is paired by determinization):

| | reply | Salem | bot (1043) | Salem − bot | board cleared: Salem / bot |
|---|---|---|---|---|---|
| 329 | greedy | 0.727 ± 0.043 | 0.775 ± 0.036 | −0.048 ± 0.020 | 2/16 / 13/16 |
| 329 | mcts:1043 | 0.715 ± 0.042 | 0.751 ± 0.038 | **−0.036 ± 0.009** | 3/16 / 16/16 |
| 455 | greedy | 0.286 ± 0.039 | 0.311 ± 0.025 | −0.025 ± 0.028 | (no follower) / 14–16 of 16 |
| 455 | mcts:1043 | 0.254 ± 0.029 | 0.262 ± 0.021 | **−0.008 ± 0.022** | (no follower) / 16/16 |

For comparison, at the turn end itself: the installed evaluation gives 329 0.651 / 0.690 and 455 0.272 / 0.32–0.38;
G_end gives 1.000 / 0.854 and 0.583 / 0.125.

**Reading:**
- **J60 wrong.** In neither puzzle does the installed evaluation rank Salem's end first after the reply. 455's
  difference is within its interval, but its point estimate still has the bot ahead.
- **The reply does what Salem expected.** The opponent clears the bot's board almost every time (16/16 at 1043) and
  Salem's rarely (3/16 in 329).
- **The evaluation still prefers the bot's positions after that.** The opponent's mean HP when my turn comes:
  - 329: 10.8 after the bot's line against 12.8 after Salem's (mcts:1043 reply);
  - 455: 9.4 against 8.3, with our HP 11.2 against 7.6.
- So the gap is in how the position is priced, not in seeing the opponent's turn. The evaluation still pays for the
  face damage, and our defense, more than for Salem's hand and the board that survives. G_end prefers Salem's end
  by far.
