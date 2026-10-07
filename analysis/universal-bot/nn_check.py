"""Does the measured deck description (svsim.learn.deckrep.deck_static) tell the tournament decks apart?

    cd <checkout> && PYTHONPATH=. python3 analysis/universal-bot/nn_check.py DIR [--out report.txt]

DIR: the meta research's decklists (analysis/meta/v2/ on claude/bot-architecture-design, or
/mnt/project-files/shadowverse/meta-research-2026-10-07/v2/), loaded as analysis/deck-inference/infer.py
does (ps/in_<archetype>.txt without the G8 lines, jcs.txt with ramp -> dragon, prison-bishop -> bishop).

Leave-one-out nearest neighbour over standardized deck vectors: is the closest other list of the same
archetype? Reported over all lists (class not given: the vector has no class, id or name) and within
the list's class (as in play, where the opponent's class is public). For reference the same with the
card ids themselves (shared cards), which any id-based model gets for free. Also: for each archetype,
the closest archetype of another class (what the description says the deck plays like).
"""
import argparse
import glob
import os
import re
from collections import Counter, defaultdict

import numpy as np

from svsim.cards import deckcode, library  # noqa: F401  (registers the scripts)
from svsim.cards.pool import POOL
from svsim.learn.deckrep import deck_names, deck_static

JCS_MAP = {"ramp": "dragon", "prison-bishop": "bishop"}


def load_lists(folder):
    out = []
    for path in sorted(glob.glob(os.path.join(folder, "ps", "in_*.txt"))):
        arch = re.sub(r".*/in_(.*)\.txt", r"\1", path)
        for line in open(path, encoding="utf-8"):
            if "|" not in line:
                continue
            src, h = line.strip().rsplit("|", 1)
            if src.startswith("G8"):
                continue
            _, craft, ids = deckcode.decode_deck(h.split("hash=")[-1].split("&")[0])
            out.append((arch, src, craft, ids))
    for line in open(os.path.join(folder, "jcs.txt"), encoding="utf-8"):
        line = line.strip()
        if line.count("|") < 3:
            continue
        player, _, arch, h = line.split("|", 3)
        _, craft, ids = deckcode.decode_deck(h)
        out.append((JCS_MAP.get(arch, arch), "JCS " + player, craft, ids))
    return out


def loo(dist, labels, crafts, same_craft):
    hits, n = 0, 0
    for i in range(len(labels)):
        d = dist[i].copy()
        d[i] = np.inf
        if same_craft:
            d[[j for j in range(len(labels)) if crafts[j] != crafts[i]]] = np.inf
        if sum(1 for j in range(len(labels)) if j != i and labels[j] == labels[i]) == 0:
            continue                     # an archetype with one list can't be matched
        n += 1
        hits += labels[int(np.argmin(d))] == labels[i]
    return hits, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out")
    a = ap.parse_args()
    lists = load_lists(a.folder)
    missing = Counter(i for *_, ids in lists for i in ids if i not in POOL)
    lists = [x for x in lists if all(i in POOL for i in x[3])]
    labels = [x[0] for x in lists]
    crafts = [x[2] for x in lists]
    X = np.array([deck_static([POOL[i] for i in x[3]]) for x in lists])
    mu, sd = X.mean(axis=0), X.std(axis=0)
    keep = sd > 1e-9
    Z = (X[:, keep] - mu[keep]) / sd[keep]
    dist = np.sqrt(((Z[:, None, :] - Z[None, :, :]) ** 2).sum(-1))
    vocab = sorted({i for x in lists for i in x[3]})
    C = np.array([[Counter(x[3])[i] for i in vocab] for x in lists], dtype=float)
    shared = np.minimum(C[:, None, :], C[None, :, :]).sum(-1)
    iddist = 40 - shared
    lines = [f"lists: {len(lists)} (dropped for unknown cards: {len(load_lists(a.folder)) - len(lists)}; {len(missing)} card ids)",
             f"archetypes: {dict(Counter(labels))}",
             f"vector: {int(keep.sum())} of {len(deck_names())} dimensions vary"]
    for name, d in (("measured description", dist), ("card ids (reference)", iddist)):
        for same in (False, True):
            h, n = loo(d, labels, crafts, same)
            lines.append(f"{name:22s} {'within class' if same else 'class not given':16s} top-1 {h}/{n} = {h / n:.1%}")
    # confusions of the measured description, class not given
    conf = Counter()
    for i in range(len(labels)):
        d = dist[i].copy(); d[i] = np.inf
        j = int(np.argmin(d))
        if labels[j] != labels[i]:
            conf[(labels[i], labels[j])] += 1
    lines.append("misses (class not given): " + ", ".join(f"{a}->{b} {k}" for (a, b), k in conf.most_common()))
    # archetype centroids and their closest archetype of another class
    archs = sorted(set(labels))
    cen = {ar: Z[[i for i, l in enumerate(labels) if l == ar]].mean(axis=0) for ar in archs}
    craft_of = {ar: Counter(c for l, c in zip(labels, crafts) if l == ar).most_common(1)[0][0] for ar in archs}
    lines.append("closest archetype of another class (centroid distance):")
    for ar in archs:
        others = sorted((np.linalg.norm(cen[ar] - cen[b]), b) for b in archs if craft_of[b] != craft_of[ar])
        lines.append(f"  {ar:10s} -> " + ", ".join(f"{b} {d:.1f}" for d, b in others[:3]))
    # what sets each archetype apart: the largest standardized centroid values
    names = [n for n, k in zip(deck_names(), keep) if k]
    lines.append("each archetype's most distinctive dimensions (z of its centroid):")
    for ar in archs:
        top = np.argsort(-np.abs(cen[ar]))[:6]
        lines.append(f"  {ar:10s} " + ", ".join(f"{names[t]} {cen[ar][t]:+.1f}" for t in top))
    text = "\n".join(lines)
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()
