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
