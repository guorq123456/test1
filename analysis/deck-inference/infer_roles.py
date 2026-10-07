"""E step, second version: how far the inferred roles of the opponent's unseen cards are from the true ones.

    cd <svsim checkout> && PYTHONPATH=.:<test1>/analysis/deck-inference python3 <this> --lists DIR GAMES... \
        [--prior lists|uniform] [--max-turn 12] [--svg OUT.svg] [--json OUT.json]

Why (the architecture thread, from the general-bot design thread): the bot's evaluation reads the
opponent's unseen cards through their roles (learn.roles: face, removal, heal, draw, ramp, body;
features.resources: the hand's roles as its share of the unseen cards' roles), not through an
archetype label. So two variants sharing most cards (ramp dragon and drag58) cost little to confuse,
and what decides the strength lost by "inferred deck" against "known 40-card list" is how far the
inferred roles are from the true ones.

Measured, for each game and each side as the observer, at the end of the opponent's own turn t
(games still going): the cards the opponent has played so far (R, as in infer.py), and
- truth: the true unseen cards under the current condition, the opponent's 40-card list minus R;
- inferred: the posterior mixture over the tournament lists of its class (infer.py's likelihood;
  each list's weight prior(A) / m_A * P(R | L), m_A the lists of archetype A), each list minus R;
- two references: the prior mixture (the same lists, weights not updated by R: what reading the
  shown cards adds), and the single most likely list (MAP).
For each, the unseen cards' roles per card (the role sums over the unseen cards divided by their
number: the evaluation's hand features are this times the hand size), and its L1 distance to the
truth summed over the 6 roles; also relative to the truth's own L1 size. Split by whether the
observer went first. Kept as auxiliaries: top-1 archetype and "right with posterior >= 0.9".
Cards the simulator plays as vanilla (no script) get the sandbox's roles of a vanilla card.
Condition being replaced: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import json
import math
from collections import Counter, defaultdict

from infer import games_of, load_lists, log_like, shown_by_turn
from svsim.cards.pool import POOL
from svsim.learn.roles import ROLES, card_roles

_RV = {}


def records_of(path):
    """Game records from a JSON / JSON-lines file (infer.py) or a gzipped league file (deck-league/league.py)."""
    if path.endswith(".gz"):
        import gzip
        out = [json.loads(line) for line in gzip.open(path, "rt", encoding="utf-8") if line.strip()]
    else:
        out = games_of(path)
    return [r.get("record", r) for r in out]


def roles_of(cid):
    if cid not in _RV:
        _RV[cid] = card_roles(POOL[cid]) if cid in POOL else (0.0,) * 6
    return _RV[cid]


def per_card(rem):
    n = sum(rem.values())
    if n == 0:
        return [0.0] * 6
    out = [0.0] * 6
    for cid, k in rem.items():
        for i, v in enumerate(roles_of(cid)):
            out[i] += k * v
    return [v / n for v in out]


def l1(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


def list_weights(seen, archs, prior, n_cards):
    """Posterior over the individual lists: [(archetype, list, weight)]."""
    logs = []
    for arch, ls in archs.items():
        for d in ls:
            logs.append((arch, d, math.log(prior[arch] / len(ls)) + log_like(seen, d, n_cards)))
    top = max(x for _, _, x in logs)
    z = sum(math.exp(x - top) for _, _, x in logs)
    return [(a, d, math.exp(x - top) / z) for a, d, x in logs]


def mix(weighted, seen):
    out = [0.0] * 6
    for _, d, w in weighted:
        for i, v in enumerate(per_card(d - seen)):
            out[i] += w * v
    return out


def svg_curves(curves, path, max_turn):
    """A plain line chart: curves = {label: {t: value}}; no plotting library needed."""
    w, h, left, bottom, top_pad = 640, 360, 56, 40, 20
    ymax = max(v for c in curves.values() for v in c.values()) * 1.1 or 1.0
    x = lambda t: left + (w - left - 16) * t / max_turn
    y = lambda v: h - bottom - (h - bottom - top_pad) * v / ymax
    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#8c564b"]
    dashes = ["", "6,4"]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" font-family="sans-serif" font-size="12">',
             f'<rect width="{w}" height="{h}" fill="white"/>',
             f'<line x1="{left}" y1="{h - bottom}" x2="{w - 16}" y2="{h - bottom}" stroke="black"/>',
             f'<line x1="{left}" y1="{top_pad}" x2="{left}" y2="{h - bottom}" stroke="black"/>']
    for t in range(0, max_turn + 1, 2):
        parts.append(f'<text x="{x(t):.0f}" y="{h - bottom + 16}" text-anchor="middle">{t}</text>')
    for k in range(5):
        v = ymax * k / 4
        parts.append(f'<text x="{left - 6}" y="{y(v) + 4:.0f}" text-anchor="end">{v:.2f}</text>')
        parts.append(f'<line x1="{left}" y1="{y(v):.0f}" x2="{w - 16}" y2="{y(v):.0f}" stroke="#ddd"/>')
    parts.append(f'<text x="{(w + left) / 2:.0f}" y="{h - 6}" text-anchor="middle">对手自己的回合</text>')
    parts.append(f'<text x="14" y="{(h - bottom + top_pad) / 2:.0f}" text-anchor="middle" '
                 f'transform="rotate(-90 14 {(h - bottom + top_pad) / 2:.0f})">L1（每张未见牌的 6 个角色）</text>')
    for n, (label, c) in enumerate(curves.items()):
        pts = " ".join(f"{x(t):.1f},{y(v):.1f}" for t, v in sorted(c.items()))
        col, dash = colors[(n // 2) % len(colors)], dashes[n % 2]
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2"'
                     + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
        parts.append(f'<line x1="{w - 210}" y1="{top_pad + 6 + 16 * n}" x2="{w - 186}" y2="{top_pad + 6 + 16 * n}" '
                     f'stroke="{col}" stroke-width="2"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
        parts.append(f'<text x="{w - 180}" y="{top_pad + 10 + 16 * n}">{label}</text>')
    parts.append("</svg>")
    open(path, "w", encoding="utf-8").write("\n".join(parts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("games", nargs="+")
    ap.add_argument("--lists", required=True)
    ap.add_argument("--prior", default="lists", choices=("lists", "uniform"))
    ap.add_argument("--max-turn", type=int, default=12)
    ap.add_argument("--svg", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--limit", type=int, default=0, help="first N games of each file (a quick check)")
    args = ap.parse_args()
    lists = load_lists(args.lists)
    craft_of = {a: Counter(c for _, _, c in ls).most_common(1)[0][0] for a, ls in lists.items()}
    by_craft = defaultdict(dict)
    for a, ls in lists.items():
        by_craft[craft_of[a]][a] = [d for _, d, _ in ls]
    total = {cr: sum(len(v) for v in archs.values()) for cr, archs in by_craft.items()}
    # (true deck name, observer first?) -> t -> sums
    acc = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    rows = []
    for path in args.games:
        for rec in records_of(path)[:args.limit or None]:
            shown, last = shown_by_turn(rec)
            names = rec.get("names") or ["?", "?"]
            for me in (0, 1):
                foe = 1 - me
                deck = Counter(rec["decks"][foe])
                cr = max(by_craft, key=lambda c: max(sum((deck & d).values()) for ds in by_craft[c].values() for d in ds))
                archs = by_craft[cr]
                truth_arch = max(((a, sum((deck & d).values())) for a, ds in archs.items() for d in ds), key=lambda x: x[1])[0]
                valid = {c for ds in archs.values() for d in ds for c in d}
                prior = {a: (len(ds) / total[cr] if args.prior == "lists" else 1 / len(archs)) for a, ds in archs.items()}
                pri_w = [(a, d, prior[a] / len(ds)) for a, ds in archs.items() for d in ds]
                first = rec["first"] == me
                seen_all, seen = Counter(), Counter()
                for t in range(0, args.max_turn + 1):
                    if t > last[foe]:
                        break
                    seen_all.update(shown[foe].get(t, []))
                    seen.update(c for c in shown[foe].get(t, []) if c in valid)
                    truth = per_card(deck - seen_all)
                    post_w = list_weights(seen, archs, prior, len(valid))
                    inferred = mix(post_w, seen)
                    prior_mix = mix(pri_w, seen)
                    a_map, d_map, _ = max(post_w, key=lambda x: x[2])
                    map_v = per_card(d_map - seen)
                    arch_post = defaultdict(float)
                    for a, _, w in post_w:
                        arch_post[a] += w
                    top = max(arch_post.values())
                    tied = [a for a, v in arch_post.items() if v >= top - 1e-9]
                    s = acc[(names[foe], first)][t]
                    s["n"] += 1
                    s["post"] += l1(inferred, truth)
                    s["prior"] += l1(prior_mix, truth)
                    s["map"] += l1(map_v, truth)
                    s["size"] += sum(truth)
                    s["top1"] += (truth_arch in tied) / len(tied)
                    s["sure"] += arch_post[truth_arch] >= 0.9
                    for i in range(6):
                        s[f"err_{i}"] += abs(inferred[i] - truth[i])
                    rows.append({"deck": names[foe], "first": first, "t": t, "l1_post": l1(inferred, truth),
                                 "l1_prior": l1(prior_mix, truth), "l1_map": l1(map_v, truth), "truth": truth,
                                 "inferred": inferred, "truth_arch": truth_arch, "map_arch": a_map})
    print("条件：现在的评测是对手卡表已知（牌序、手牌未知）；这里量的是不知道卡表、按比赛卡表推断时差多少。")
    print(f"每张未见牌的角色（{', '.join(ROLES)}）取平均；L1 是 6 个角色的绝对差之和。先验：{args.prior}。\n")
    curves = {}
    for (deck, first), by_t in sorted(acc.items()):
        print(f"== 对手 {deck}，观察方{'先' if first else '后'}手")
        print("  对手回合  局面   后验混合 L1（相对）   先验混合 L1   最可能那张 L1   top-1   对且≥0.9   各角色误差（后验混合）")
        for t in sorted(by_t):
            s = by_t[t]
            n = int(s["n"])
            if n < 10:
                continue
            errs = " ".join(f"{ROLES[i]} {s[f'err_{i}'] / n:.3f}" for i in range(6))
            print(f"  {t:>6}   {n:>5}   {s['post'] / n:.3f}（{s['post'] / max(s['size'], 1e-9):.1%}）"
                  f"      {s['prior'] / n:.3f}        {s['map'] / n:.3f}      {s['top1'] / n:>5.0%}   {s['sure'] / n:>5.0%}    {errs}")
        curves[f"{deck} {'先' if first else '后'}手"] = {t: s["post"] / s["n"] for t, s in by_t.items() if s["n"] >= 10}
        print()
    if args.svg:
        svg_curves(curves, args.svg, args.max_turn)
    if args.json:
        json.dump(rows, open(args.json, "w"))


if __name__ == "__main__":
    main()
