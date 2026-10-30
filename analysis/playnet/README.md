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
