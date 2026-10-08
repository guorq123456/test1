# Universal bot, step 1: a deck described by what its cards do (2026-10-07)

Plan: /mnt/project-files/shadowverse/universal-bot-plan.md (project files; the player approved it 21:48Z).
Code: `svsim/learn/deckrep.py` (`card_vector`, `deck_static`), check: `nn_check.py`, output `nn_check_2026-10-07.txt`.

## What was checked
133 tournament lists (JCS season 3 + pro league, the meta research's decoded hashes; the G8 lines left out), 14 archetype labels.
Leave-one-out nearest neighbour over the standardized deck vector (85 dimensions after the engine measurement below) (no card id, no name, no class):

| description | class not given | within class |
|---|---|---|
| measured (deckrep), first version | 122/132 = 92.4% | 122/132 = 92.4% |
| measured + engine (below) | 123/132 = 93.2% | 123/132 = 93.2% |
| card ids (reference) | 123/132 = 93.2% | 123/132 = 93.2% |

- Never once confused across classes, though the vector holds no class: the classes' mechanics (Fanfare/Engage/Fuse/Ambush/Invoke...) separate them.
- Every miss is a pair the labels themselves hardly separate: ramp dragon vs drag58 (6), exp vs witch (4, the same Fuse deck under two labels), wrinkle-witch vs spell (1). The card-id reference misses the same pairs.
- Distinctive dimensions read like the meta doc: cut (机锋) = most singletons + Ambush + Invoke + Skybound; bishop = amulets, Engage, Crystallize, heal; pirate = Storm, Enhance, tokens; dragon = face and evolution face payoff, draw at 7+.

## Gap found
42 of 516 Rotation cards (8%) measure zero in all six roles, all with abilities: conditional amulets and spells (buffs, countdown amulets that act when the count ends, deck-condition spells), e.g. World of Games (combo elf core), Spilling Red, Encroached World. The roles sandbox plays a card once on an almost empty board for one round, so enablers that need allies, a countdown or a condition read as nothing. Their tags (listener, turn, cast) still carry some of it.

`engine(defn)` (6 more card dimensions): the card played with two more allied followers and three cards in hand, then four rounds of turns, against the same rounds without it. Zero-role cards: 42 -> 24. Still zero: cards that need the deck's own other plays (combo counts, cards played or destroyed this turn), e.g. World of Games (countdown 5, shortened by plays), Encroached World, Majestic Conquest, Reaper's Due. A card alone can't show those; they belong to the deck-level measurement (the goldfish half of the plan, or the same card's marginal effect inside its own deck's goldfish games).

## What this does not show
Separating lists only says the description is distinct; whether weights built on it play well is step B (shared evaluator vs specialist, equal compute) and C (leave one deck out).

## Goldfish profiles (`svsim/learn/goldfish.py`, `goldfish_run.py`; greedy agent, 300–400 games per deck)

- **Plain goldfish is useless here**: against an opponent that does nothing, all seven decks (four tournament standards, three Game8 builds) kill on own turn 5–6 (means 5.4–6.3; `goldfish_greedy_400.json`). An unopposed board kills before any deck's plan matters.
- **Wall** (enemy leader at 200, ten own turns; `goldfish_greedy_wall.json`): ramp shows its play points (5.6 at turn 5, 8.9 at turn 8 vs 5.0 / 8.0) and the biggest single turn (28.6), but board snowballing still dominates.
- **Wall + wipe** (the opponent destroys the deck's followers every turn, so a turn brings only what comes from hand; `goldfish_greedy_wipe.json`): the decks separate. Damage by turn 10: pirate-t 18.5 (burst 9.8), elf-t 7.9, nemesis-t 8.0, ramp-t 7.6 (+0.7 play points from turn 5). Cards played a turn at turn 8: elf-t 2.7, nemesis-t 2.1, pirate-t 1.8, ramp-t 1.3.
- **The agent's blind spot shows directly**: elf-t (tournament combo elf) and combo(G8) get the same profile; the greedy agent doesn't play the combo turn, so the combo deck's reach reads as 8. This is the risk the plan names: a profile is only as good as the agent playing it. Next: the same wipe profile with the v2 search (mcts:100+plan+learned+phased).
- **With the v2 search** (mcts:100+plan+learned+phased, 100 games per deck, wall + wipe; `goldfish_v2_wipe.json`) the profile changes a lot: ramp-t reaches 7.1 play points at turn 5 and 9.9 at turn 8 (greedy: 5.7 / 8.7), damage by turn 10 rises for every deck (pirate-t 23.4, ramp-t 15.9, elf-t 12.1, nemesis-t 9.4). elf-t still shows no combo-sized turn (largest turn 6.3), so either the search misses it or the tournament elf's damage comes from its board, which the wipe removes; this run can't tell which.
- **Conclusion for the plan**: a goldfish profile depends on the agent as much as on the deck (ramp's turn-5 play points +1.4 from greedy to v2). It must be measured with the agent that will use it and re-measured when the agent changes, and it can't stand alone: the static half (deckrep) is the part that doesn't move with the agent.

## Held-out log loss, one evaluator per pairing vs shared linear (2026-10-08, holdout_2026-10-08.txt)

On the 11 pairing self-play sets (v2, 100 level; one game in five held out; 100k positions per moment). Seen decks: shared linear
(one model for all, or additive w0+a_me+b_op) is within 0.01 of the per-pairing specialist (ENDED 0.5759 / 0.5857 / 0.5847; ACT
0.5797 / 0.5864 / 0.5792). With ramp-t never seen ("-noramp", scored only on ramp-t pairings) the shared linear models fall to
0.67–0.72, about a coin flip (0.693): a linear evaluator learnt on four decks says nothing useful about a fifth. That is what the
deck descriptions in the shared MLP (X1) and the leave-one-deck-out gates are for.

## X1 on a pairing it never saw (2026-10-08, gates/x1loo_elframp.*)

X1 retrained without the elf-t vs ramp-t data (phased_models/cand-mlp-x1-loo-elframp-20261008), elf-t side, 200 level, fixed
300 pairs, seeds 37000000+: A = mcts:188+plan+learned+phased=<that folder> vs B = v2s (the specialist linear fitted on that
pairing), both against C = v2s on ramp-t (its ramp-t-elf-t models are byte-identical to ruler-20261008, so C is the ruler).
A 51.2% ± 4.1% (47.1–55.2), CR +11 (−27..+50); A first 64.3%, second 42.0%; B first 64.3%, second 39.7%. Against the ruler:
A 53.2%, B 52.0% (600 games each). The shared MLP that never saw this pairing ties the specialist that was fitted on it,
same as X1 with the data (49.5% ± 4.1%). One cell; the pooled non-inferiority bar of the plan (lower bound ≥ 47.5%) needs more cells.
