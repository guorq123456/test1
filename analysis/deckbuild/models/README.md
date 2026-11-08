# Deck models (learn.deckmodel)

Condition of every label: the opponent's deck list is known (order and hand not); both sides mcts:100+plan.

## dm-O-r1.npz (2026-10-29 06:43Z)

- Fitted on the old-pool search O only (`deckbuild --sets pre10`, seed 85101000): its rounds 0-1, 16,634 deals with
  both lists, mirrored; a tenth of the seeds held out. No set-10 card in any training deck.
- Size and regularization chosen without new-pool labels, by leaving one class out of O (`loco.py`; that class's
  cards are never seen in training, as a new pack's would be). Unseen-class log loss, mean over the 7 classes
  (a constant scores 0.693):

  | h / h2 | l2 | log loss |
  |---|---|---|
  | 32 / 32 | 1e-4 | 0.719 |
  | 16 / 16 | 3e-3 | 0.685 |
  | 8 / 8 | 1e-3 | 0.685 |
  | 8 / 8 | 1e-2 | **0.682** |
  | 4 / 4 | 1e-2 | 0.685 |

- Held out within O: log loss 0.631 (constant 0.691).
- On the new pool, once (search C rounds 0-3, claude/deck-runs-C 8d776e3, 47,568 deals, about 65% set-10 cards in
  round 0's decks): log loss 0.672 (constant 0.693); ordering of each first halving stage's decks, Spearman
  0.13 +- 0.07 over 31 stages; the model's best is the games' best in 26% of stages (chance 10%).
- Registered before (plan section 10.3): offline Spearman 0.05-0.25, above 0.2 with 0.4. Inside the range, below 0.2.
