"""Which deck is the opponent playing: Bayesian inference from the cards it has shown, against tournament lists.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> --lists DIR GAMES... [--prior lists|uniform] [--json out.json]

DIR holds the tournament decklists of the meta research (architecture branch 2fa8180,
analysis/meta/v2/): ps/in_<archetype>.txt (source|hash per line; the攻略站 lines starting with G8 are
left out, as in analysis/tournament_decks.py) and jcs.txt (player|group|archetype|hash). An archetype
is one file (JCS labels mapped onto them: ramp -> dragon, prison-bishop -> bishop). GAMES are game
records: a JSON file with "records" (salem_games.json, positions.json) or JSON lines (learn.netdata).

The opponent's class is public from the first turn, so only the archetypes of its class compete. For
an archetype A with lists L1..Lm (40 cards each), after the opponent has played the multiset R of
cards (collectible cards seen in some list of that class; tokens and cards made by effects are left
out):
    P(R | L) = prod_c (L[c] + eps)_(k_c) / (40 + eps * N)_(n)     (falling factorials: R drawn from L)
    P(A | R) ∝ prior(A) * mean_i P(R | L_i)
with eps = 0.05 for cards a list does not run (a tech card, a list not in the data), N the number of
distinct cards of the class. The prior is the archetype's share of the tournament lists (--prior
lists) or uniform. The truth for a game is the archetype of the tournament list closest to the
opponent's 40 cards (most cards in common). Reported: by the opponent's own turn t, among the games
still going, how often the most likely archetype is the true one (top-1), the mean posterior of the
true one, and the first turn where top-1 reaches 90%.
"""
import argparse
import glob
import json
import math
import os
import re
from collections import Counter, defaultdict

from svsim.cards import deckcode, library, decks  # noqa: F401
from svsim.core.actions import from_dict
from svsim.core.engine import apply
from svsim.tools import records

EPS = 0.05
JCS_MAP = {"ramp": "dragon", "prison-bishop": "bishop"}


def load_lists(folder):
    lists = defaultdict(list)                  # archetype -> [(source, Counter of card ids, craft)]
    for path in glob.glob(os.path.join(folder, "ps", "in_*.txt")) + glob.glob(os.path.join(folder, "in_*.txt")):
        arch = re.sub(r".*/in_(.*)\.txt", r"\1", path)
        for line in open(path, encoding="utf-8"):
            if "|" not in line:
                continue
            src, h = line.strip().rsplit("|", 1)
            if src.startswith("G8"):
                continue
            _, craft, ids = deckcode.decode_deck(h.split("hash=")[-1].split("&")[0])
            lists[arch].append((src, Counter(ids), craft))
    jcs = os.path.join(folder, "jcs.txt")
    if os.path.exists(jcs):
        for line in open(jcs, encoding="utf-8"):
            line = line.strip()
            if line.count("|") < 3:
                continue
            player, _, arch, h = line.split("|", 3)
            _, craft, ids = deckcode.decode_deck(h)
            lists[JCS_MAP.get(arch, arch)].append(("JCS " + player, Counter(ids), craft))
    return lists


def falling(x, k):
    return math.prod(x - i for i in range(k))


def log_like(seen, deck, n_cards):
    n = sum(seen.values())
    num = sum(math.log(max(falling(deck.get(c, 0) + EPS, k), 1e-300)) for c, k in seen.items())
    return num - math.log(falling(40 + EPS * n_cards, n))


def posterior(seen, by_arch, prior, n_cards):
    logs = {}
    for arch, decks_ in by_arch.items():
        ls = [log_like(seen, d, n_cards) for d in decks_]
        top = max(ls)
        logs[arch] = math.log(prior[arch]) + top + math.log(sum(math.exp(x - top) for x in ls) / len(ls))
    top = max(logs.values())
    z = sum(math.exp(v - top) for v in logs.values())
    return {a: math.exp(v - top) / z for a, v in logs.items()}


def games_of(path):
    text = open(path, encoding="utf-8").read()
    if text.lstrip().startswith("{") and '"records"' in text[:2000]:
        return list(json.loads(text)["records"].values())
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def shown_by_turn(rec):
    """For each seat: the cards it played, by its own turn number (the turn they were played on)."""
    st = records.start(rec)
    out = {0: defaultdict(list), 1: defaultdict(list)}
    for data in rec["actions"]:
        a = from_dict(data)
        if type(a).__name__ == "PlayCard" and st.phase.name == "MAIN":
            c = st.in_hand(st.active, a.uid)
            if c is not None:
                out[st.active][st.players[st.active].turns_taken].append(c.defn.card_id)
        apply(st, a)
        if st.over:
            break
    last = {p: st.players[p].turns_taken for p in (0, 1)}
    return out, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("games", nargs="+")
    ap.add_argument("--lists", required=True)
    ap.add_argument("--prior", default="lists", choices=("lists", "uniform"))
    ap.add_argument("--max-turn", type=int, default=12)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    lists = load_lists(args.lists)
    craft_of = {a: Counter(c for _, _, c in ls).most_common(1)[0][0] for a, ls in lists.items()}
    by_craft = defaultdict(dict)
    for a, ls in lists.items():
        by_craft[craft_of[a]][a] = [d for _, d, _ in ls]
    total = {cr: sum(len(v) for v in archs.values()) for cr, archs in by_craft.items()}
    print("各职业里互相竞争的卡组（比赛卡表套数）：")
    for cr, archs in sorted(by_craft.items()):
        print(f"  职业 {cr}：" + "，".join(f"{a} {len(v)}" for a, v in archs.items()))
    stats = defaultdict(lambda: defaultdict(lambda: [0, 0.0, 0.0, 0]))   # truth -> turn -> [n, top1, mass, sure]
    truths = Counter()
    rows = []
    for path in args.games:
        for rec in games_of(path):
            shown, last = shown_by_turn(rec)
            for me in (0, 1):
                foe = 1 - me
                deck = Counter(rec["decks"][foe])
                craft = None
                for cr, archs in by_craft.items():
                    if any(deck & d for ds in archs.values() for d in ds):
                        overlap = max(sum((deck & d).values()) for ds in archs.values() for d in ds)
                        if craft is None or overlap > craft[1]:
                            craft = (cr, overlap)
                cr = craft[0]
                archs = by_craft[cr]
                truth = max(((a, sum((deck & d).values())) for a, ds in archs.items() for d in ds), key=lambda x: x[1])[0]
                truths[truth] += 1
                valid = {c for ds in archs.values() for d in ds for c in d}
                prior = {a: (len(ds) / total[cr] if args.prior == "lists" else 1 / len(archs)) for a, ds in archs.items()}
                seen = Counter()
                for t in range(0, args.max_turn + 1):
                    seen.update(c for c in shown[foe].get(t, []) if c in valid)
                    if t > last[foe]:
                        break
                    post = posterior(seen, archs, prior, len(valid))
                    top = max(post.values())
                    tied = [a for a, v in post.items() if v >= top - 1e-9]
                    hit = (truth in tied) / len(tied)          # a tie counts 1/k
                    s = stats[truth][t]
                    s[0] += 1
                    s[1] += hit
                    s[2] += post[truth]
                    s[3] += post[truth] >= 0.9
                    rows.append({"truth": truth, "t": t, "top1": hit, "p_true": post[truth], "shown": sum(seen.values())})
    print(f"\n真实卡组（按最接近的比赛卡表）：" + "，".join(f"{a} {n}" for a, n in truths.items()) + f"；先验：{args.prior}")
    for truth, by_t in stats.items():
        print(f"\n对手是 {truth}（同职业里和它竞争的：{', '.join(a for a in by_craft[craft_of[truth]] if a != truth) or '无'}）")
        print("  对手自己的回合   局面数   top-1 正确   真卡组的平均后验   真卡组后验 ≥ 0.9")
        reached = sure90 = None
        for t in sorted(by_t):
            n, ok, mass, sure = by_t[t]
            if n < 10:
                continue
            if reached is None and ok / n >= 0.9:
                reached = t
            if sure90 is None and sure / n >= 0.9:
                sure90 = t
            print(f"  {t:>8}      {n:>5}     {ok / n:>6.0%}      {mass / n:.3f}         {sure / n:>6.0%}")
        print(f"  top-1 第一次到 90% 的回合：{reached if reached is not None else '没到'}；"
              f"九成局面里真卡组后验 ≥ 0.9 的回合：{sure90 if sure90 is not None else '没到'}"
              f"（第 0 回合 = 对手还没出牌，只看职业；平局按 1/k 计）")
    if args.json:
        json.dump(rows, open(args.json, "w"))


if __name__ == "__main__":
    main()
