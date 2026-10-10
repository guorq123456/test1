# Missed lethals: diagnosis and counts (no play changed)

Condition: 对手卡表已知（牌序、手牌未知）. The architecture thread 2026-10-10 02:11Z and 02:13Z (Salem's Pirate
Royal puzzle); M1 as the analysis line pre-registered it (851504d: J30 graded on 6f11111 only, golden as a side table).

## The Pirate puzzle (tests/puzzles/pirate-flags-lethal)

- **Screen.** At the turn start the lethal agent searches. Its settings (LethalAgent: 2000 nodes, `screen=200`,
  `near=(1000, 4)`; +plan tries the resource-flow planner first) against find_lethal's defaults (20000 nodes,
  unscreened):
  - `damage_estimate` = 2 against the enemy's 10 (short by 8, beyond near's 4), so 200 nodes: nothing found;
  - the planner says 5;
  - find_lethal finds the 10 at node 5441 (about 3 s); the smallest budget that finds it is 5441, so even the
    agent's top budget (2000) is short.
- **Mid-turn.** After the bot's first move (Roughwater First Mate's fanfare on the Steelclad Knight) no lethal is
  left. The agent doesn't search again mid-turn (nothing hidden changed), but there would be nothing to find.
- **Cause.** The budget, set by the screen. The damage comes from the Dread Pirate's Flags' Last Words (2 to the
  enemy leader each), advanced one count per spell played. Neither `damage_estimate` (search/lethal.py: each card
  tried on its own) nor the planner's resource model (search/combo.py) sees it, so `LethalSearch.solve` takes the
  screen budget.
  - Not pruning: the lethal search prunes nothing but transpositions.
  - Not a trigger that doesn't fire.
  - Move order matters, though: spells first, those aimed at the leader first, finds it at node 1165 (0.5 s). But
    that order does worse on the Ramp mirror's lethals (below), so it is no general fix.

## How often (lethal_miss.py, lethal_m1.py; data/)

Every own-turn start of step 1's self-play (RC 6f11111: 1000 games of the original Ramp mirror by level-strong,
18,892 starts) and of the golden games (71 starts). Rows:
- `data/lethal_miss.jsonl.gz`: every start, with find_lethal's verdict, nodes and time, the damage estimate, and
  the agent's own check;
- `data/lethal_m1.jsonl`: one row per sure start.

| | starts | find_lethal sure | agent's check at the start misses it | not realized in the record (M1) |
|---|---|---|---|---|
| 6f11111 | 18,892 | 789 | 86 (10.9%) | **27 (3.42%; Wilson 2.36–4.93%)** |
| golden (mcts:30, truncated) | 71 | 1 | 0 | 0 |
| extra: pirate-t mirror, 80 games by level-strong (seeds 99600000+g) | 1,389 | 70 | 13 (18.6%) | not measured |

- Of 6f11111's 27 unrealized lethals:
  - in all 27 the agent's check at the start missed it;
  - 26 were spoiled during the turn and 1 was left standing at the turn's last decision.
- Of the 86 start misses, 59 were realized anyway later in the turn.
- Of the 703 found at the start, 433 were found by the planner and 270 by the screened search.
- 2,428 starts had no sure lethal and an incomplete find_lethal (the budget ran out): there may be uncounted
  lethals among them.

## Fixes, offline (lethal_policies.py, lethal_order.py)

With the same seed and order, a search of budget B finds a lethal exactly when the full search found it within B
nodes, and it spends min(B, the full search's nodes). This model reproduces the agent's verdict on 786 of 789 sure
starts. Cost is per turn start, at 0.416 ms per node (this container).

| policy | Ramp: start misses recovered (of 86) | of them unrealized (of 27) | + ms per turn start | Pirate sample: recovered (of 13) |
|---|---|---|---|---|
| near 1000 within 8 | 4 | 0 | +19 | |
| near 2000 within 4 | 11 | 5 | +10 | 6 |
| **near 2000 within 4, top budget 3000** | **17** | **7** | **+12** | **8** |
| near 3000 within 4, top budget 3000 | 25 | 9 | +21 | 8 |
| no screen, 2000 | 19 | 6 | +219 | |
| no screen, 20000 (find_lethal) | 86 | 27 | +1479 | 13 |

Move order (spells first, leader-aimed ones first) at the agent's settings finds 14 start misses but loses others:
635 searched finds against 680 now (761 against 789 with 20000 nodes).

## Proposed (not wired into any level; a change of play: an equal-compute gate first, and Salem's word to install)

1. **Budget.** LethalAgent `near=(2000, 4)` and `max_nodes=3000`.
   - About +12 ms per turn start (about +3.5% of a level-strong turn, more with the re-searches after draws).
   - Recovers about a fifth of the Ramp mirror's start misses and well over half of the Pirate sample's.
   - The gain is small: about 7 more realized lethals per 1000 games, which a 300-pair gate can't see.
2. **Salem's puzzle** needs the flags understood. The resource-flow planner's model (search/combo.py) would count
   the countdown amulets whose Last Words hit the enemy leader, advanced one count per spell; its lines are checked
   in the engine before they are played, so a model error can't make a wrong play. It costs only when such an
   amulet is on our field (about 50 ms a planner call). This is the fix aimed at the Pirate deck's complex turns.
