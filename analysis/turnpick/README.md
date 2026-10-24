# Whole-turn pick (agents.turnpick_agent): code, tests, cost; no gate

Condition: 对手卡表已知（牌序、手牌未知）. Assigned by the architecture thread 2026-10-09 23:00Z, on the analysis
line's diagnosis 7b8bd0c (picking among the generator's plans by the installed ENDED model halves the regret T
measures, mostly via race and second). The parameters are not fixed yet: the analysis line first runs an
independent check with G_end (V and T share the evaluator), and the gate opens only after that.

## The agent

Option `+pick[dD][iI][mM][zZ][k<letters>]` on an mcts agent, e.g. `v2s+pick` = `mcts:200+plan+learned+phased+pick`.

| letter | parameter | default |
|---|---|---|
| D | number of shared determinizations | 8 |
| I | iterations of the plans' own searches | 100 |
| M | margin | 0 |
| Z | paired standard errors | 1 |
| letters | kinds besides "bot": s second, t third, r race, k keep a card, p keep the bonus PP, e don't evolve | str |

At the first decision of an own turn, when it has more than one legal action:

1. **Plans.** `search.candidates.generate` runs on a determinization of the position, so no plan sees the hidden
   cards. Plans are deduped by turn end, with the bot's plan first. The plans' searches use I iterations and the
   base's evaluator.
2. **Scores.** Each plan's actions, written as action keys, are replayed on D new determinizations; every plan uses
   the same D. Where a key no longer matches (a draw or random effect came out differently), the plan's own policy
   finishes the turn: the continuation search, under the plan's restriction, or "end" ends the turn. Each plan
   gets V = the mean of σ(ENDED(turn end)); a game won during the turn counts 1, a loss 0.
3. **Switch rule.** The agent switches only when V(best) − V(bot) > M and > Z paired standard errors. Otherwise the
   turn belongs to the base agent, step for step: the plans use their own agents and random numbers, so the base
   agent sees the same calls it would see without the wrapper.
4. **Following a picked plan.** The plan is followed key by key on the real position. When a key doesn't match,
   the base search plays the rest of the turn. A restriction kind keeps its veto on the base search for the whole
   turn, and the lethal search outside reads it (`LethalAgent._veto`).

Tests: tests/test_turnpick.py (6). They cover:
- plans are deduped, the bot's comes first, and the keys replay to the same turn end;
- a turn that isn't switched matches the base agent step for step;
- a restriction's veto reaches the lethal search and is cleared at the next turn;
- a game won during the turn scores its result;
- the switch rule;
- the `+pick` option.

## Cost (tp_cost.py, cost.log)

The first 20 training starts of step 1 (RC 6f11111 starts.jsonl, split train). Each agent plays the mover's whole
turn on the real position, with seed 7, one process and one thread. A "search decision" is a decision with more
than one legal action. The ratios are against level-strong.

| agent | ms per turn (mean / median) | ms per search decision | ratio, per turn | ratio, per search decision | of which the pick, ms per turn | switched |
|---|---|---|---|---|---|---|
| level-strong `v2s` | 342 / 356 | 137 | 1 | 1 | 0 | – |
| `v2s+pickd8i50` | 675 / 686 | 270 | 1.97 | 1.97 | 468 | 5 / 20 (race 2, third 2, second 1) |
| `v2s+pick` (d8 i100) | 930 / 836 | 351 | 2.72 | 2.56 | 712 | 4 / 20 (second 3, race 1) |
| `v2s+pickd8i200` | 1466 / 1269 | 553 | 4.29 | 4.04 | 1170 | 2 / 20 (race 1, second 1) |

Search decisions per turn: level-strong 2.50, the picks 2.50 to 2.65 (a switched turn goes a different way). Two
of the 20 turns made no pick: a lethal, or only one legal action.

Note: the plans' "bot" is the plan-search's turn (I iterations), not the base's 200. At I = 200 the plans are the
generator the analysis line's diagnosis used; with fewer iterations the bot plan the others are compared with is
weaker, and the switch rate goes up (above: 5 at i50, 2 at i200).
