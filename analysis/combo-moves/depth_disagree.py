"""Where the strong level's search picks differently at 200 and 800 iterations in ordinary games, and what the 800
move starts with (the architecture thread 18:12; numbers only). Method and seeds in README.md.

    cd <svsim checkout (b9f2aca)> && PYTHONPATH=. python3 <this> PART1+PART2+PART3 --out rows.jsonl [--workers 4]
    python3 <this> --report rows.jsonl

Condition: the opponent's 40-card list is known (order and hand not).
"""
import gzip
import json
import random
import sys
from collections import Counter
from multiprocessing import Pool

BANK = 65400000
PER_SIDE = 50
MODELED = {("elf-t", "elf-t"), ("elf-t", "nemesis-t"), ("elf-t", "ramp-t"), ("nemesis-t", "elf-t"),
           ("nemesis-t", "ramp-t"), ("pirate-t", "elf-t"), ("pirate-t", "pirate-t"), ("ramp-t", "elf-t"),
           ("ramp-t", "nemesis-t"), ("ramp-t", "pirate-t"), ("ramp-t", "ramp-t")}
KINDS = {"UseBonusPP": "用额外 PP", "Evolve": "进化 / 超进化", "PlayCard": "出牌", "Attack": "攻击",
         "EndTurn": "结束回合"}


def sample(paths):
    """(side, game record, action index) for 50 positions per modelled side, at most one per game."""
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply, legal_actions
    from svsim.core.enums import Phase
    from svsim.tools import records
    games = [json.loads(line) for p in paths for line in gzip.open(p, "rt", encoding="utf-8")]
    rng = random.Random(BANK)
    rng.shuffle(games)
    need = {s: PER_SIDE for s in MODELED}
    out = []
    for g in games:
        if not any(need.values()):
            break
        rec = g["record"]
        names = rec["names"]
        st = records.start(rec)
        cands = []
        for k, a in enumerate(rec["actions"]):
            p = st.active
            side = (names[p], names[1 - p])
            if st.phase == Phase.MAIN and need.get(side, 0) > 0 and len(legal_actions(st)) > 1:
                cands.append((k, side))
            apply(st, from_dict(a))
        if not cands:
            continue
        k, side = cands[rng.randrange(len(cands))]
        if need[side] > 0:
            need[side] -= 1
            out.append((side, rec, k))
    return out


def job(args):
    i, side, rec, k = args
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply, legal_actions
    from svsim.search.mcts import _locator, action_key
    from svsim.tools import records
    from svsim.tools.arena import make_agent
    st = records.start(rec)
    for a in rec["actions"][:k]:
        apply(st, from_dict(a))
    p = st.active
    where = _locator(st, p)
    legal = legal_actions(st)
    picks = {}
    for n, offs in ((200, (0, 1, 2)), (800, (5, 6, 7))):
        picks[n] = []
        for s in offs:
            a = make_agent(f"mcts:{n}+plan+learned+phased", BANK + 10 * i + s).act(st.clone(), legal)
            picks[n].append((repr(action_key(st, a, where)), type(a).__name__))
    return {"i": i, "deck": side[0], "opp": side[1], "at": k, "own_turn": st.players[p].turns_taken,
            "legal": len(legal), "p200": picks[200], "p800": picks[800]}


def majority(picks):
    c = Counter(key for key, _ in picks)
    key, n = c.most_common(1)[0]
    if n < 2:
        return None, None
    return key, next(kind for kk, kind in picks if kk == key)


def report(path):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    n = len(rows)
    dis, nomaj, kinds = 0, 0, Counter()
    by_side = Counter()
    noise = {200: 0, 800: 0}
    for r in rows:
        m2, _ = majority(r["p200"])
        m8, k8 = majority(r["p800"])
        for nn in (200, 800):
            if len({key for key, _ in r[f"p{nn}"]}) > 1:
                noise[nn] += 1
        if m2 is None or m8 is None:
            nomaj += 1
            continue
        if m2 != m8:
            dis += 1
            kinds[KINDS.get(k8, k8)] += 1
            by_side[(r["deck"], r["opp"])] += 1
    print(f"条件：对手卡表已知（牌序、手牌未知）。{n} 个局面（11 个一方各 {n // 11} 个左右），现装第 22 版强档，每个 N 3 个种子。\n")
    print(f"- **200 次和 800 次多数票不一致**：{dis} / {n}（{dis / n:.1%}）；有一边没有多数（3 个种子各不相同）的 {nomaj} 个，另记。")
    print(f"- 噪声对照：同一个 N 的 3 个种子不全相同的局面，200 次 {noise[200]} 个（{noise[200] / n:.1%}），"
          f"800 次 {noise[800]} 个（{noise[800] / n:.1%}）。\n")
    print("**不一致时，800 次多数选的第一步**\n")
    print("| 第一步 | 个数 | 占不一致的 |")
    print("|---|---|---|")
    for kname in ("用额外 PP", "进化 / 超进化", "出牌", "攻击", "结束回合"):
        print(f"| {kname} | {kinds[kname]} | {kinds[kname] / dis:.0%} |" if dis else f"| {kname} | 0 | — |")
    print("\n**逐个一方**\n")
    print("| 一方（对手） | 局面 | 不一致 |")
    print("|---|---|---|")
    for side in sorted({(r["deck"], r["opp"]) for r in rows}):
        m = sum(1 for r in rows if (r["deck"], r["opp"]) == side)
        print(f"| {side[0]}（对 {side[1]}） | {m} | {by_side[side]}（{by_side[side] / m:.0%}） |")


def main():
    if "--report" in sys.argv:
        report(sys.argv[sys.argv.index("--report") + 1])
        return
    paths = sys.argv[1].split("+")
    out = sys.argv[sys.argv.index("--out") + 1]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    pts = sample(paths)
    jobs = [(i, side, rec, k) for i, (side, rec, k) in enumerate(pts)]
    with open(out, "w", encoding="utf-8") as f, Pool(workers) as pool:
        for r in pool.imap_unordered(job, jobs, chunksize=2):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()


if __name__ == "__main__":
    main()
