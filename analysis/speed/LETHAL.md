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

## The packaged change: `+lethal2` (the architecture thread 04:57Z; not in any level)

`+lethal2` on an mcts agent = `+tick` and a deeper screen (LethalAgent `near=(2000, 4)`, `max_nodes=3000`).

**`+tick`**: the resource-flow planner models allied countdown amulets that hit the enemy leader (search/combo.py,
"countdown amulets").
- **Tickers, measured in the sandbox like the rest of the planner** (no table per card), `ticker_profile`: how far
  one play of a spell, a follower or an amulet advances the count, and the damage to the enemy leader when the
  amulet is destroyed. Dread Pirate's Flag measures as spell 1, follower 0, amulet 0, pop 2. Demo Totem (a countdown
  that doesn't hurt the leader) is no ticker.
- **Summons, measured too** (`summons`, `evolve_summons`): Roughwater First Mate's Fanfare and Evolve summon a flag.
  Field slots decide which plays are possible: a full field blocks a summon, and a ticker that pops frees its slot.
- **The search** (`_Tickers`, a subclass of the plain search) works on the plain position plus the tickers.
  - After every play, the play's kind advances the tickers; one at 0 pops (its damage counts, its slot frees).
  - What a play or an evolution summons takes a free slot, and a summoned ticker joins in.
  - Cards are measured at the play points actually there (`profile_at`): Enhance is forced when affordable, so a
    0-cost card with Enhance (1) costs 1 when a play point is there. The plain `profile` measures at 10 play points
    and so takes the Depths of the Eld Sword's enhanced 3 damage as free.
  - `realize(face_first=True)`: a ticker plan's play that hits no enemy follower takes the enemy leader as its
    target (a Gilded Blade aimed at the leader). The plain realize takes the first target listed.
- **Scope.** Used only with the flag, and only when a ticker is on the mover's field. Everything else is the plain
  planner: the golden record is identical, cmp_roots is still 142cc567…, the full suite passes. The plan is checked
  in the engine before it is played, as always.
- **On the puzzle bank:**
  - pirate-flags-lethal: planned (10) and verified in about 70 ms; level-strong+tick and +lethal2 win it on seeds
    1-3, level-strong doesn't;
  - pirate-flags-setup: the ticker planner's most is 9, no lethal; the turn played is level-strong's.

**Offline evaluation** (lethal2_eval.py; output in data/lethal2_eval.log). Pirate is measured directly: the same 80
games replayed (all 70 sure starts matched) and both checks timed on each real position. Ramp uses the budget model:
neither the Ramp deck's cards nor what they summon are tickers, so only the budget differs there.

| | pirate-t mirror, 80 games | Ramp mirror, 6f11111 |
|---|---|---|
| turn starts | 1,389 (804 with a ticker on the mover's field) | 18,892 |
| find_lethal sure | 70 | 789 |
| missed by level-strong's check at the start | 13 | 86 |
| not realized in play | 4 (all 4 missed at the start) | 27 (all missed at the start) |
| **+lethal2 recovers, of the start misses** | **12 of 13** (none lost) | **17 of 86** |
| **... of the unrealized** | **4 of 4** | **7 of 27** |
| added ms per turn start: mean / p90 | **+5.3 / +13.3** (level-strong's check: 78.0 / 133.5) | **+12.0 / 0** (3.2% of starts pay, up to +416; p99 +416) |

In the Pirate mirror the ticker planner finds 14 lethals the plain check found by search or not at all. That is why
its added time is low: a planned lethal costs less than the search it replaces.

## The Ramp misses +lethal2 leaves, and +plannerfix / +eot (the architecture thread 05:58Z; not in any level)

### What the 20 are (ramp_misses.py; data/ramp_misses.jsonl)

6f11111 has 27 unrealized lethals; +lethal2 recovers 7. For each of the other 20, find_lethal's line was followed
step by step (where the enemy leader's defense went), next to the damage estimate and the planner's figure.

| cause, described generically | count | generic fix |
|---|---|---|
| The planner measures cards at 10 play points, so an Enhance card does its enhanced effect for free and Overflow always holds; the plan it builds fails in the engine (a card it can't pay, an effect it doesn't get) | **9** | **+plannerfix** recovers all 9 |
| End-of-turn ability of an allied follower that hits the enemy leader (Erntz, evolved: 8). Neither the planner nor the estimate sees end-of-turn effects, and the search tries EndTurn last (2,200-10,000 nodes) | **5** | **+eot** recovers all 5 |
| A spell that needs a card in hand to discard as a cost (Spilling Red: discard + destroy, used to clear Ward before a Storm attack). The planner's sandbox has an empty hand, so the card has no legal play there and the planner never plays it | 3 | not done: the planner would need a discard step (which card to give up) |
| Other gaps of the planner's model (its line fails in the engine for other reasons) | 3 | not done |

Budget alone: all 20 need more than +lethal2's budgets (2,200-19,000 nodes); the smallest budget per case is in the
rows.

### The fixes (search/combo.py; flags +plannerfix and +eot on an mcts agent)

- **`+plannerfix`.** The plain planner's two latent inaccuracies, fixed behind the flag.
  - Cards are measured at the play points left *and* the maximum (`profile_at(defn, fused, pp, cap)`): Enhance is
    forced when affordable, and Overflow reads the maximum.
  - Its plan is realized face first: a planned play that hits no enemy follower aims at the enemy leader.
  - While evaluating, measuring with the maximum set to the play points left lost Sloth of the Crestpetal's Overflow
    damage. The cap fixed that, and the same correction now applies to the ticker search (+tick / +lethal2).
- **`+eot`.** Ending the turn counts what allied followers' end-of-turn abilities deal to the enemy leader
  (`end_turn_damage(defn, evo)`, measured in the sandbox over two random seeds, the smaller kept). It is a final
  step `("end",)` that realize plays as EndTurn.
- **Default unchanged:** golden identical, cmp_roots 142cc567…, full suite 1143 passed.

### Offline, at every turn start (plannerfix_eval.py, plannerfix_agent.py; data/plannerfix*.log, .jsonl.gz)

The planner step of the lethal agent (plan, realize, verify) in three modes at each start, read at the agent's level:
the agent finds a lethal by its planner, or failing that by its screened search, which the flags don't change.

| | Ramp 6f11111, 18,892 starts | Pirate-t sample, 1,389 starts |
|---|---|---|
| agent finds, plain | 755 | 60 |
| **+plannerfix**: finds / gained (find_lethal sure) / gained beyond find_lethal / lost | 843 / 41 / 47 / **0** | 66 / 6 / 0 / **0** |
| of the 27 unrealized | 13 | – |
| **+plannerfix+eot**: finds / gained / beyond / lost | 902 / 74 / 73 / **0** | 66 / 6 / 0 / **0** |
| of the 27 unrealized | **19** | – |
| same verdict, other line (+plannerfix / +plannerfix+eot) | 6 / 52 | 2 / 2 |
| added ms per turn start (+plannerfix / +plannerfix+eot) | +0.2 / +0.05 | −1.5 / −3.9 |

"Beyond find_lethal": verified lethals (checked in the engine, on 16 deck orders and random outcomes when luck is
involved) at starts where find_lethal at its defaults found none within 20,000 nodes. On the pirate sample one start
loses its planner lethal under the fix, but the screened search still finds it, so the agent loses nothing.

Re-run of +lethal2 with the corrected measurement (data/lethal2_eval.log): pirate sample unchanged in verdicts (12/13
recovered, 4/4 unrealized, 0 lost); added time +7.8 / +23.0 ms mean / p90 (this run shared the machine with tests).

## +lethal3: the package (the architecture thread 2026-10-10 06:27Z; not in any level)

**Condition:** the opponent's deck list is known (deck order and hand unknown).

- **Spec:** `level-strong+lethal3` (any mcts spec + `lethal3`). It is +lethal2 (the planner's countdown amulets,
  near-lethal 2000 nodes within 4, 3000 unscreened) with +plannerfix and +eot, behind one flag. It sets its own
  screen, so `screen=` with it is an error.
- **Fallback, found while measuring.** On the pirate sample one start was lost (g14 turn 19). The ticker search
  planned 10 through the flags, and the engine can't play that line: Roughwater First Mate dies striking the Golden
  Knight, so Severed Ties has no ally to take. Meanwhile the plain plan (Beltezore, 12) checks. +lethal2 had the
  same loss; it went uncounted because find_lethal wasn't sure there (incomplete at 20,000 nodes).
  - Fix: `combo.planned_lethal`. A ticker plan that doesn't realize or check falls back to the planner without
    tickers. Without tickers on the field it is one plan, as before. LethalAgent uses it, so +tick and +lethal2 get
    it too.
  - Test: the position is rebuilt in tests/test_lethal3.py.
- **Tests** (tests/test_lethal3.py):
  - the flag sets the package;
  - the puzzle bank on seeds 1-3: pirate-flags-lethal is solved, and pirate-flags-setup still has none played;
  - an end-of-turn lethal (Erntz) is played by the agent and missed by the plain planner;
  - the fallback;
  - with step 1's data: the 20 Ramp misses replayed. +lethal3's check finds exactly the 14 classified as planner
    measurement (9) or end of turn (5); the plain check finds none of the 20.

### Offline, directly at every turn start (lethal3_eval.py; data/lethal3_eval.log, data/lethal3.jsonl.gz)

Both checks run on the real position as LethalAgent runs them (planner, realize, verify, else the screened search),
and both are timed. This is no budget model.

| | Ramp 6f11111, 18,892 starts | Pirate-t sample, 1,389 starts |
|---|---|---|
| sure (find_lethal 20000) | 789 | 70 |
| found: level-strong's check / +lethal3 | 755 / **904** | 60 / **76** |
| gained, find_lethal sure / gained beyond it | 76 / 73 | 12 / 4 |
| **lost** | **0** | **0** |
| sure lethals still missed: now / +lethal3 | 86 / 10 | 13 / 1 |
| unrealized in play: recovered / missed by both | **21 / 6** of 27 | **4 / 0** of 4 |
| by the planner: now / +lethal3 | 485 / 862 | 32 / 56 |
| ms per turn start, now: mean / p90 | 58.2 / 107.1 | 84.1 / 142.5 |
| ms per turn start, +lethal3: mean / p90 | 63.3 / 104.6 | 91.0 / 141.6 |
| **added ms per turn start: mean / p90** | **+5.1 / +8.1** | **+6.9 / +21.8** |

The 6 unrealized Ramp lethals still missed are the unfixed classes above: 3 discard-cost spells and 3 other planner
gaps. Timing was measured with 3 workers on 4 cores. The pirate cell's re-run (after the fallback) shared the
machine with the resource-waste diagnostic (analysis/waste), so its milliseconds are noisier.

### The two remaining Ramp classes (the architecture thread 07:06Z, low priority)

- **The 3 other planner gaps.**
  - **g127, fixed.** Four identical Dragonewt Promoters. The plan's evolution went to one that had already
    attacked, because realize matched followers by card and stats only. The fixed realize (the one +plannerfix,
    +tick, +lethal2 and +lethal3 use) now also matches the attacks a follower has left and its reach. The plain
    realize is unchanged. Test: tests/test_lethal3.py.
  - **g109, not fixed.** The line is right on the real position. Sloth of the Crestpetal's damage to an enemy
    follower is random, though, so on other random outcomes the fixed attack target is already dead and verify
    rejects the line. Fixing it needs plan-level verification: realize again on each sample, and re-realize while
    playing.
  - **g546, not fixed.** The lethal needs Sagatsumatsu's fanfare to cut a hand card's cost (Depths 2 → 1). The
    planner doesn't model effects that target hand cards.
- **Discard-cost spells (3), not done.** Measuring with a hand in the sandbox is easy. The planner would then need a
  discard step that chooses which card to give up, which is not cheap.
- **+lethal3 re-run with the fixed realize** (data/lethal3_realize.log, .jsonl.gz):
  - Ramp: 905 found (+1, g127), 77 gained where find_lethal is sure, 73 gained beyond it, 0 lost, 22/27
    unrealized recovered, +5.0 / +7.5 ms.
  - Pirate: unchanged in verdicts (76 found, 0 lost, 4/4). Its milliseconds are not usable from this run: the
    machine was busy with the evaluator fit, p90 +63.6. Use the earlier +6.9 / +21.8.
