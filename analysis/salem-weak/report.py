"""The weak-reference audit's report: disagreement (shallow v2 vs deep mcts:800) and paired regret by group.

    python3 <this> points.json results.jsonl

Groups: Salem's seat by his deck; the bot's seat (elf-t) by Salem's deck; the Version 14 games (05:46Z, 05:49Z:
the bot had no elf-t-nemesis-t model) and the original-level game apart; the control (league rerun after D,
bot vs bot) by pairing and by the deciding side's deck. Disagreement with a Wilson 95% interval; mean regret with
a 95% interval over points; points with regret >= 0.10. Condition: the opponent's 40-card list is known (order
and hand not).
"""
import json
import math
import sys

V14 = {"1791438391276", "1791438595615"}


def wilson(k, n, z=1.96):
    if n == 0:
        return 0, 0
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def line(label, rs):
    if not rs:
        return f"| {label} | 0 | — | — | — |"
    k = sum(r["differ"] for r in rs)
    lo, hi = wilson(k, len(rs))
    regs = [r.get("regret", 0.0) for r in rs]
    m = sum(regs) / len(regs)
    sd = math.sqrt(sum((x - m) ** 2 for x in regs) / max(len(regs) - 1, 1) / len(regs))
    big = sum(1 for x in regs if x >= 0.10)
    return f"| {label} | {len(rs)} | {k / len(rs):.1%}（{lo:.1%}～{hi:.1%}） | {m:+.4f} ± {1.96 * sd:.4f} | {big} |"


def main():
    pts = {(p["who"], p["id"]): p for p in json.load(open(sys.argv[1], encoding="utf-8"))}
    res = [json.loads(l) for l in open(sys.argv[2], encoding="utf-8") if l.strip()]
    for r in res:
        p = pts[(r["who"], r["id"])]
        r["_game"] = p["ref"].get("game")
        r["_salem_deck"] = p.get("salem_deck")
        r["_level"] = p.get("bot_level")
        r["_pair"] = p["ref"].get("pair")
        r["_deck"] = p.get("deck")
    main_games = lambda r: r["_game"] not in V14 and r["_level"] == "strong"
    print("条件：对手卡表已知（牌序、手牌未知）。弱参考（Salem 不熟的两套，约 1700 CR）：db-export-2026-10-08b 的 10 局；"
          "浅 = v2（100 次），深 = mcts:800，v2s 收完回合，同 8 个确定化，回合末估值配对；在 1cde857（模型同 Version 15）上跑。\n")
    print("| 组 | 点数 | 浅深分歧（Wilson 95%） | 平均遗憾（95%） | 遗憾 ≥ 0.10 |")
    print("|---|---|---|---|---|")
    S = [r for r in res if r["who"] == "Salem"]
    B = [r for r in res if r["who"] == "bot"]
    C = [r for r in res if r["who"] == "ctrl"]
    print(line("Salem 的座位，全部 10 局", S))
    for d in ("nemesis-t", "pirate-t"):
        print(line(f"Salem 的座位 · 他打 {d}", [r for r in S if r["_salem_deck"] == d]))
    print(line("bot（连击妖）的座位，强档 7 局（去掉 Version 14 两局和原始版那局）", [r for r in B if main_games(r)]))
    for d in ("nemesis-t", "pirate-t"):
        print(line(f"bot 的座位 · 对 {d}，强档", [r for r in B if main_games(r) and r["_salem_deck"] == d]))
    print(line("bot 的座位 · Version 14 两局（没有 elf-t-nemesis-t 模型）", [r for r in B if r["_game"] in V14]))
    print(line("bot 的座位 · 原始版档那一局（局面是原始版打出来的）", [r for r in B if r["_level"] == "original"]))
    for pair in ("elf-t/nemesis-t", "elf-t/pirate-t"):
        cs = [r for r in C if r["_pair"] == pair]
        print(line(f"对照 {pair}（联赛 after-D，bot 对 bot），两边合计", cs))
        print(line(f"对照 {pair} · 连击妖一方", [r for r in cs if r["_deck"] == "elf-t"]))
        opp = pair.split("/")[1]
        print(line(f"对照 {pair} · {opp} 一方", [r for r in cs if r["_deck"] == opp]))
    noise = [r for r in S if "noise_differ" in r]
    if noise:
        print(f"\n噪声底：{len(noise)} 个 Salem 的点上两个种子的深搜，选的步不同 {sum(r['noise_differ'] for r in noise)} 个。")
    cats = {}
    for r in res:
        if r.get("regret", 0) >= 0.10 and r["who"] in ("Salem", "bot"):
            cats.setdefault(r["category"], []).append(r["who"])
    if cats:
        print("\n遗憾 ≥ 0.10 的点（Salem + bot）按类型：" + "；".join(f"{c} {len(v)}（Salem {v.count('Salem')}、bot {v.count('bot')}）" for c, v in sorted(cats.items())))


if __name__ == "__main__":
    main()
