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

## dm-S10 (2026-10-30 02:1xZ, not kept)

- Same sizes (h 8/8, l2 1e-2), fitted on set 10's own searches: C rounds 0-10, D, the guided twin Cg; 208,082 deals.
  Held out within them: log loss 0.649 (constant 0.693).
- Ordering of first halving stages it never saw (Spearman per stage, mean ± SE), against dm-O-r1:

  | stages | dm-O-r1 | dm-S10 | paired difference |
  |---|---|---|---|
  | search F rounds 1-2 (14) | 0.102 ± 0.106 | -0.018 ± 0.140 | -0.120 ± 0.164 |
  | search F round 0, whole seed decks (7) | 0.226 ± 0.136 | 0.222 ± 0.150 | -0.004 ± 0.167 |
  | search A rounds 3-5 (26) | 0.108 ± 0.083 | 0.101 ± 0.072 | -0.007 ± 0.101 |

- Registered before (progress log 02:0xZ): dm-O-r1 about 0.10 on F, dm-S10 about 0.20, dm-S10 ahead by 2 SE with
  0.45. It is not ahead: ten times the deals of the pack itself do not order a deck's 1-3 card variants better. A deck
  is the mean of its cards' vectors here, and a swap of 1-3 cards barely moves that mean (review claim 5).
- Rule registered with it: no gain, and dm-O-r1 at 0.10 or more on F, so F is guided by dm-O-r1 from its next round.
