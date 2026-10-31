# Play net, R1: labels from playing both sibling moves on (2026-10-30)

Condition: 对手卡表已知（牌序、手牌未知）.

Why: six shared play nets (analysis/sharednet/README.md) lost to the hand-written score at matched CPU (34.6%-48.3%).
Their labels were the game's result (a better predictor that ranked a decision's children worse than the hand-written
score: top-1 45.4% against 66.8%) or the recorded mcts:100+plan's choices (at best a copy of the gate's opponent; an
mcts:400+plan teacher changed one decision in ten). Three times the games moved neither recipe.

R1: at a searched decision, the teacher's two most-visited distinct moves are each played on to the end `m` times by
mcts:100+plan on both sides, the j-th playouts of the two children with common random numbers (both decks reshuffled
by one generator, the same engine seed, the same agent seeds); label d = Q(first) - Q(second) for the mover. A
correction on top of the hand-written score (zero at the start; linear first, so nearly free at play time) is then
fitted so that the corrected score orders the two children as d does. The plan, the pilot's registered predictions
and stop lines: the architecture thread's note shadowverse/playnet-redesign-2026-10-30.md (project files).

## Pilot (`r1_labels.py`, runs/r1/pilot.jsonl)

800 decisions (one per game, P3 self-play records, pool decks only), m = 12, seed 85960000, 4 workers.

Registered before the run (the architecture thread, 2026-10-30 16:4xZ):
- mean d (the teacher's first minus its second, win-rate points): +2 to +6;
- spread of the true d (the measured spread less the playouts' own noise): 5-12 points; below 3: stop R1;
- share of decisions whose true d < 0 (the teacher's first is the worse): 25%-40%; below 10%: stop R1;
- correlation of paired playouts: 0.3-0.6;
- where d is clear (|d| > 2 SE), the hand-written score orders the two children as d does: 60%-75%; above 90%: stop R1.

### Pilot result (2026-10-30 18:0xZ; `pilot.json`, `fit-pilot.json`, data `pilot.jsonl.gz`)

1050 games drawn (the pool the script draws from), 753 decisions labelled (297 skipped: a tie at the top of the visits
or a child that ends the game), m = 12, 1.31 CPU s a playout. Win-rate points, 95% bootstrap intervals over decisions.

| | registered | result | stop line |
|---|---|---|---|
| mean d | +2 to +6 | **+3.4** (2.0-4.9) | |
| spread of the true d (tau) | 5-12 | **16.4** (13.9-18.7); split halves (playouts 1-6 against 7-12): 16.4 (13.7-18.8) | < 3 |
| P(true d < 0), normal model | 25%-40% | **41.8%** (38.9%-45.0%) | < 10% |
| paired playouts, correlation within a decision | 0.3-0.6 | **0.30** | |
| hand-written score's order = d's, clear decisions | 60%-75% | **61.8%** (76 clear decisions) | > 90% |

No stop line is crossed. Two predictions missed: the spread is larger than registered, and the normal model's
teacher-wrong share is just above the range. The normal model does not fit: 48% of the decisions have d = 0 exactly
(40% have every paired playout identical: the two moves led to the same result), and the largest 5% of |d| carry 56%
of the squared differences. A reading without the model: of the 154 decisions whose two halves of playouts both give a
nonzero d of one sign, the teacher's first is the worse in 56 (36%), the better in 98; 56 is 7.4% of all decisions.
By the mover's class tau is 9 (rune) to 21 (sword); by the game's stage 10 (own turn 8 or earlier), 18, 24 (after 16).

Is d predictable beyond the hand-written score (`r1_fit.py`, 5-fold cross-validation over decisions, 105 features)?
Held-out correlation with d: the hand-written score alone 0.176, plus the linear correction 0.182 (the penalty chosen
in the folds is the largest offered); the labels' own noise allows 0.82. Of the 23 clear decisions where the teacher's
first is the worse, the hand-written score orders 2 right, with the correction 3. With 753 decisions the generic
position features add nothing measurable. The clearest teacher-wrong decisions are of many kinds (two cards of one
turn, attack or end the turn, engaging Divine Evidence early or late, fusing), which suggests the correction has to
see the cards, not only position totals.

Next: labels on 10000 more decisions at m = 4 (a playout buys more for a fit spread over more decisions when the
model explains little of d), seed 85961000, the pilot's games left out (it stays as a held-out set with low noise).

### Interim: 2741 labelled decisions at m = 4 (`r1_cards.py`, `cards-2741.json`)

Fitted on the m = 4 labels so far, judged on the pilot (753 decisions, m = 12, games not in training). Cards: per
zone (my hand, field, leader area, deck; the opponent's field and leader area) the sum of the cards' static rows
(learn.tokens.static), 576 columns. "Switch": take the second move wherever the model prefers it; gain per decision
over always taking the teacher's first, win-rate points.

| model | held-out corr with d | teacher-wrong clear decisions right | switch rate | switch gain |
|---|---|---|---|---|
| hand-written score | 0.185 | 2 / 23 | 6.1% | +0.21 ± 0.12 |
| + generic (105) | **0.242** | 4 / 23 | 9.7% | +0.22 ± 0.19 |
| + cards (576) | 0.156 | 3 / 23 | 12.5% | +0.07 ± 0.25 |
| + generic + cards | 0.175 | 4 / 23 | 16.5% | +0.06 ± 0.28 |

With 3.6 times the decisions the generic correction begins to predict d (0.185 -> 0.242), but it does not choose
better: the switches it adds gain nothing measurable. The card sums overfit at this size. The labels' noise allows a
correlation of 0.82 on the pilot.

### 10000 decisions at m = 4: R1's linear correction stops here (2026-10-31 01:3xZ; `cards-10000.json`, `labels-m4.jsonl.gz`)

Labels: 10000 decisions (13514 games drawn, the pilot's games left out), m = 4, seed 85961000, 10.1 CPU s a decision.
They repeat the pilot's spread: mean d +3.2 points, tau 16.4.

A fault found on the way and fixed (r1_fit.rebuild): an end of turn's child was rebuilt with the move applied, so the
opponent's turn had begun (their draw, their play points), while the search scores that child, and r1_labels scored
the hand-written part, before the opponent's turn (search.evaluate.after_end_of_turn). Before the fix the generic
correction's switches gained +0.46 ± 0.18 points a decision; most of that was the correction telling the end of turn
apart by the opponent's started turn, which the search never sees.

Fitted on the 10000, judged on the pilot (753 decisions, m = 12), the fault fixed:

| model | held-out corr with d | switch rate | switch gain | paired with the hand-written score alone |
|---|---|---|---|---|
| hand-written score | 0.185 | 3.9% | +0.12 ± 0.10 | |
| + generic (105) | 0.239 | 4.8% | +0.18 ± 0.10 | +0.06 ± 0.08 |
| + cards (576) | 0.211 | 4.2% | +0.14 ± 0.09 | +0.02 ± 0.08 |
| + generic + cards | 0.225 | 4.2% | +0.13 ± 0.09 | +0.01 ± 0.08 |

What the labels would allow: switching wherever the pilot's measured d < 0 gains +3.9 points a decision (biased up by
the labels' noise); the normal model's E[max(0, -d)] is +5.0. A linear correction, generic or by the cards' summed
static rows, predicts d a little better than the hand-written score (0.185 -> 0.239) and chooses no better (+0.06 ±
0.08 points a decision). No gate is run: a correction that does not change the root choice on held-out decisions has
nothing to show the gate. The architecture thread's P(gate above 52%) for R1's linear correction: 0.05.
