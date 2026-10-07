"""One mirror of the league before and after a change, paired by seed: first-player rate and game length.

    python3 <this> --pair elf-t/elf-t base=league_v2s_f631e14.jsonl.gz+league_v2s_f631e14_mirror2.jsonl.gz \
        nomodel=league_v2s_3effa47_elfmirror_noelfmodel.jsonl.gz model=league_v2s_3effa47_elfmirror.jsonl.gz

Each version is one or more league files (a later file replaces a game of the same pairing, pair and seat,
as in league.py's report). A pair is one seed's two games on one deal; when they are the same game move for
move it counts once. Per version: the first player's score and the game length (turns, both sides), each
averaged within a pair, then over pairs with a 95% interval; between consecutive versions (and the last
against the first), the paired difference over the seeds both have. In a mirror both sides change together,
so this reads the first-player rate and the length, not a score between versions (the architecture thread,
22:58Z). Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import gzip
import json
import math


def load(paths, pairing):
    latest = {}
    for path in paths:
        for line in gzip.open(path, "rt", encoding="utf-8"):
            g = json.loads(line)
            if g["pair"] == pairing:
                latest[(g["k"], g["seat_a"])] = g
    by_k = {}
    for (k, _), g in latest.items():
        by_k.setdefault(k, []).append(g)
    out = {}
    for k, gs in by_k.items():
        if len(gs) == 2 and gs[0]["record"]["actions"] == gs[1]["record"]["actions"]:
            gs = gs[:1]
        fw = [1.0 if g["winner"] == g["first"] else 0.5 if g["winner"] is None else 0.0 for g in gs]
        out[k] = (sum(fw) / len(fw), sum(g["turns"] for g in gs) / len(gs), len(gs))
    return out


def ci(xs):
    n = len(xs)
    m = sum(xs) / n
    return m, 1.96 * math.sqrt(sum((x - m) ** 2 for x in xs) / max(n - 1, 1) / n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("versions", nargs="+", help="label=file[+file...]")
    args = ap.parse_args()
    versions = [(v.split("=", 1)[0], load(v.split("=", 1)[1].split("+"), args.pair)) for v in args.versions]
    print(f"条件：对手卡表已知（牌序、手牌未知）。{args.pair}，按对（同一副发牌）算，同一局的重复只算一次。\n")
    print(f"{'版本':<10}{'对数':>6}{'不重复局':>9}   先手得分（95%）      局长（双方回合合计，95%）")
    for label, v in versions:
        f, hf = ci([x[0] for x in v.values()])
        t, ht = ci([x[1] for x in v.values()])
        print(f"{label:<10}{len(v):>6}{sum(x[2] for x in v.values()):>9}   {f:.1%} ± {hf:.1%}         {t:.1f} ± {ht:.1f}")
    print("\n配对差（同一批种子）：")
    pairs = list(zip(versions, versions[1:])) + ([(versions[0], versions[-1])] if len(versions) > 2 else [])
    for (la, a), (lb, b) in pairs:
        ks = sorted(set(a) & set(b))
        df, hf = ci([b[k][0] - a[k][0] for k in ks])
        dt, ht = ci([b[k][1] - a[k][1] for k in ks])
        same = sum(a[k] == b[k] for k in ks)
        print(f"  {lb} − {la}：{len(ks)} 对，先手得分 {df:+.1%} ± {hf:.1%}，局长 {dt:+.1f} ± {ht:.1f}"
              f"（{same} 对先手得分和局长都没变）")


if __name__ == "__main__":
    main()
