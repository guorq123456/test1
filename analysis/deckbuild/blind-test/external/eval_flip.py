"""Does the bot's hand-written evaluation hide the strength of the pros' new decks? Re-plays part of the simulator
league with the evaluation changed for both players, for the three classes where DFM's decks trail the bot's most
(巫师 = 增幅证据三轴土, 龙族, 超越者), and plays the bot's own deck of each class the same way on a fresh seed bank,
its baseline included. The question is a difference in differences: under a variant, does DFM's deck gain more
than the bot's deck of the same class, against the same opponents?

Variants (fixed 2026-10-31 22:30Z, before any game; deck-agnostic, never tuned on these results):
  discount  a card in hand is worth 0.4 more per point its cost is below its printed cost (spellboost and every
            other discount; 0.4 is what the evaluation gives a max PP point). The evaluation ignores it now.
  fused     a card in hand is worth 0.6 more per card fused into it (half a card in hand, 1.2): fusing now
            scores as losing the fused cards. Only 超越者 (DFM's 超越者 fuses; the bot's has no fusion card).
  pp        a max PP point is worth 1.2 (a card in hand) instead of 0.4: discarding a card for a max PP point
            no longer scores as a loss.
  base      the evaluation as it is: the bot's decks only (DFM's baseline is runs/external/dfm-cheap.jsonl).

Predictions written before the games (analysis/deckbuild/blind-test/external/EVAL-FLIP.md): the difference in
differences (DFM's gain minus the bot's) is +3 points or more for discount/巫师 (0.45), fused/超越者 (0.40),
pp/龙族 (0.30); no variant closes half of its class's gap (0.75).

Opponents: the 42 decks of the six Claude groups, 10 deals each (both seats), mcts:100+plan on both sides.
Seeds: DFM's decks keep league.py's seeds (paired with dfm-cheap.jsonl); the bot's decks use the fresh bank
85984000 + (i * 56 + j) * 10 + k, i = 0, 1, 2 for 巫师, 龙族, 超越者, j the roster index, k = 0..9
(85984000-85985679).

    python analysis/deckbuild/blind-test/external/eval_flip.py analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt \
        --variant base --out runs/external/eval-flip.jsonl
    python analysis/deckbuild/blind-test/external/eval_flip.py ... --report

Diagnosis only: no variant is installed in the bot, and nothing from the external decks enters search, self-play or
training (the rows carry labels, not deck codes). Condition: 对手卡表已知（牌序、手牌未知）.
"""
import argparse
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from svsim.search import evaluate as EV  # noqa: E402
from svsim.tools import deckbuild as DB  # noqa: E402
import league  # noqa: E402

BASE = Path("runs/external/dfm-cheap.jsonl")
BOT_SEED = 85984000
CLASSES = ("RUNE", "DRAGON", "PORTAL")
ZH = {"RUNE": "巫师", "DRAGON": "龙族", "PORTAL": "超越者"}
CLAUDE = ("g1", "g2", "g3", "p2-g1", "p2-g2", "p2-g3")
ONLY = {"fused": ("PORTAL",)}
_side_value = EV.side_value


def _discount(p, w=EV.DEFAULT):
    return _side_value(p, w) + 0.4 * sum(max(0, c.defn.cost - c.cost) for c in p.hand)


def _fused(p, w=EV.DEFAULT):
    return _side_value(p, w) + 0.6 * sum(len(EV_counters(c).get("fused", ())) for c in p.hand)


def _pp(p, w=EV.DEFAULT):
    return _side_value(p, w) + (1.2 - w.max_pp) * p.max_pp


def EV_counters(card):
    from svsim.core import effects as E
    return E.counters(card)


def apply(variant):
    if variant != "base":
        EV.side_value = {"discount": _discount, "fused": _fused, "pp": _pp}[variant]


def craft(label):
    return next((c for c in CLASSES if c in label.upper()), None)


def todo_jobs(ref, roster, deals, spec, variant):
    claude = [(j, l, ids) for j, (l, ids) in enumerate(roster) if l.split("/", 1)[0] in CLAUDE]
    classes = ONLY.get(variant, CLASSES)
    out = []
    if variant != "base":                                   # DFM's decks on league.py's seeds
        out += [j for j in league.jobs(ref, roster, deals, spec)
                if craft(j[0][0]) in classes and j[0][1].split("/", 1)[0] in CLAUDE]
    bots = {craft(l): (l, ids) for l, ids in roster if l.startswith("bot/") and craft(l)}
    for i, c in enumerate(CLASSES):                         # the bot's decks on the fresh bank
        if c not in classes:
            continue
        bl, bids = bots[c]
        out += [((bl, ol), bids, oids, BOT_SEED + (i * len(roster) + j) * 10 + k, spec)
                for k in range(deals) for j, ol, oids in claude]
    return out


def _per_opp(rows, base):
    """ref -> opp -> [variant score - base score] over the paired deals."""
    b = {(r["ref"], r["opp"], r["seed"]): r["score"] for r in base}
    out = {}
    for r in rows:
        k = (r["ref"], r["opp"], r["seed"])
        if k in b:
            out.setdefault(r["ref"], {}).setdefault(r["opp"], []).append((r["score"], b[k]))
    return out


def _mean_se(xs):
    m = sum(xs) / len(xs)
    return m, math.sqrt(sum((x - m) ** 2 for x in xs) / max(1, len(xs) - 1)) / math.sqrt(len(xs))


def report(rows):
    base = [json.loads(t) for t in BASE.read_text().splitlines() if t.strip()]
    base += [r for r in rows if r["variant"] == "base"]
    print("条件：对手卡表已知（牌序、手牌未知）；两边都由 mcts:100+plan 操作；对手是 Claude 六组 42 副，每副 10 个发牌（两个座位）")
    for variant in ("discount", "fused", "pp"):
        vr = [r for r in rows if r["variant"] == variant]
        if not vr:
            continue
        per = _per_opp(vr, base)
        print(f"\n== 评分改法：{variant}")
        for c in ONLY.get(variant, CLASSES):
            refs = {who: next((r for r in per if craft(r) == c and r.startswith(who)), None) for who in ("dfm/", "bot/")}
            if None in refs.values():
                continue
            line = []
            deltas = {}
            for who, ref in refs.items():
                opps = per[ref]
                d = {o: sum(x - y for x, y in v) / len(v) for o, v in opps.items()}
                deltas[who] = d
                new = [x for v in opps.values() for x, _ in v]
                old = [y for v in opps.values() for _, y in v]
                m, se = _mean_se(list(d.values()))
                line.append(f"{'DFM' if who == 'dfm/' else 'bot'} {100 * sum(old) / len(old):5.1f}→{100 * sum(new) / len(new):5.1f}"
                            f"（{100 * m:+5.1f}±{196 * se:4.1f}，{len(new)} 个发牌）")
            both = [deltas["dfm/"][o] - deltas["bot/"][o] for o in deltas["dfm/"] if o in deltas["bot/"]]
            m, se = _mean_se(both)
            verdict = ("找到" if m - 1.96 * se > 0 and m >= 0.03 else
                       "排除" if m - 1.96 * se > -0.03 and m + 1.96 * se < 0.03 else "说不清")
            print(f"{ZH[c]:4s} " + "；".join(line) +
                  f"；DFM 比 bot 多涨 {100 * m:+5.1f}±{196 * se:4.1f}（按 {len(both)} 个对手配对）→ {verdict}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ref")
    ap.add_argument("--variant", choices=("base", "discount", "fused", "pp"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--deals", type=int, default=10)
    ap.add_argument("--spec", default="mcts:100+plan")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    rows = [json.loads(t) for t in out.read_text().splitlines() if t.strip()] if out.exists() else []
    if args.report:
        report(rows)
        return
    apply(args.variant)
    ref = DB.read_seeds(args.ref)
    roster = DB.read_seeds(str(league.ROSTER))
    done = {(r["ref"], r["opp"], r["seed"]) for r in rows if r["variant"] == args.variant}
    todo = [j for j in todo_jobs(ref, roster, args.deals, args.spec, args.variant)
            if (j[0][0], j[0][1], j[3]) not in done]
    print(f"variant {args.variant}: {len(done)} done, {len(todo)} to play", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a") as fh, Pool(args.workers, initializer=DB._nice) as pool:
        for n, res in enumerate(pool.imap_unordered(DB.play_deal, todo, chunksize=2), 1):
            rl, ol = res["key"]
            fh.write(json.dumps({"ref": rl, "opp": ol, "seed": res["seed"], "spec": args.spec,
                                 "variant": args.variant, "points": res["points"],
                                 "score": sum(res["points"]) / 2}, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 100 == 0:
                print(f"{n}/{len(todo)}", flush=True)


if __name__ == "__main__":
    main()
