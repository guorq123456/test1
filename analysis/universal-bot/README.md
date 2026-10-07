# Universal bot, step 1: a deck described by what its cards do (2026-10-07)

Plan: /mnt/project-files/shadowverse/universal-bot-plan.md (project files; the player approved it 21:48Z).
Code: `svsim/learn/deckrep.py` (`card_vector`, `deck_static`), check: `nn_check.py`, output `nn_check_2026-10-07.txt`.

## What was checked
133 tournament lists (JCS season 3 + pro league, the meta research's decoded hashes; the G8 lines left out), 14 archetype labels.
Leave-one-out nearest neighbour over the standardized 79-dimension deck vector (no card id, no name, no class):

| description | class not given | within class |
|---|---|---|
| measured (deckrep) | 122/132 = 92.4% | 122/132 = 92.4% |
| card ids (reference) | 123/132 = 93.2% | 123/132 = 93.2% |

- Never once confused across classes, though the vector holds no class: the classes' mechanics (Fanfare/Engage/Fuse/Ambush/Invoke...) separate them.
- Every miss is a pair the labels themselves hardly separate: ramp dragon vs drag58 (6), exp vs witch (4, the same Fuse deck under two labels), wrinkle-witch vs spell (1). The card-id reference misses the same pairs.
- Distinctive dimensions read like the meta doc: cut (机锋) = most singletons + Ambush + Invoke + Skybound; bishop = amulets, Engage, Crystallize, heal; pirate = Storm, Enhance, tokens; dragon = face and evolution face payoff, draw at 7+.

## Gap found
42 of 516 Rotation cards (8%) measure zero in all six roles, all with abilities: conditional amulets and spells (buffs, countdown amulets that act when the count ends, deck-condition spells), e.g. World of Games (combo elf core), Spilling Red, Encroached World. The roles sandbox plays a card once on an almost empty board for one round, so enablers that need allies, a countdown or a condition read as nothing. Their tags (listener, turn, cast) still carry some of it. Next: measure countdown amulets to the end of their count, and spells/amulets with allies on the field.

## What this does not show
Separating lists only says the description is distinct; whether weights built on it play well is step B (shared evaluator vs specialist, equal compute) and C (leave one deck out).
