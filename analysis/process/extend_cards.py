"""Add static rows to a token folder's cards.npz for the cards a decision set (dec-*.npz) has and it lacks.

    python analysis/process/extend_cards.py DEC_DIR CARDS_IN CARDS_OUT

setpolicy fit refuses decisions whose cards have no static row. A card can turn up only at a decision point (the
梦魇 hero's Ghost token, 90051130, on 2026-11-05) and never in the value net's encoded positions, so the value
encode's cards.npz lacks it. The rows added are learn.tokens.static of the card, the same function the encode uses.
CARDS_IN is left untouched.
"""
import glob
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import svsim.tools.arena  # noqa: F401  (card scripts)
from svsim.cards.pool import card
from svsim.learn import tokens as T


def main(dec_dir, cards_in, cards_out):
    with np.load(cards_in) as z:
        c = {k: z[k] for k in z.files}
    have = {int(x): i for i, x in enumerate(c["card_id"])}
    need = set()
    for f in sorted(glob.glob(os.path.join(dec_dir, "dec-*.npz"))):
        with np.load(f) as z:
            need |= {int(x) for x in np.unique(z["cards"])}
    missing = sorted(need - set(have))
    rows = {cid: c["static"][i] for cid, i in have.items()}
    for cid in missing:
        rows[cid] = T.static(card(cid)).astype(c["static"].dtype)
        if rows[cid].shape != c["static"].shape[1:]:
            raise SystemExit(f"card {cid}: static width {rows[cid].shape} differs from {c['static'].shape[1:]}")
    ids = sorted(rows)
    c["card_id"] = np.asarray(ids, c["card_id"].dtype)
    c["static"] = np.stack([rows[i] for i in ids])
    np.savez_compressed(cards_out, **c)
    print(f"{len(have)} cards in {cards_in}; the decisions use {len(need)}; added {len(missing)}: "
          + ", ".join(f"{cid} {card(cid).name}" for cid in missing), flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:4])
