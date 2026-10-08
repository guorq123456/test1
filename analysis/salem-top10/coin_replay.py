"""#9's turn 1, replayed in pairs (the architecture thread 17:30; reference only): from the bot's first turn of
Salem's game 21 (1791384258804, action 3), arm A = bonus PP, Polaris, end turn (what the bot did) and arm B = end turn
keeping the bonus PP; then both sides play v19 level-strong to the end. Pair i (seed 65200000 + i): the hidden
information redrawn once from the bot's view (core.view.determinize: Salem's hand from his hand + deck, both decks
shuffled, later random effects reseeded), the same redraw and the same agent seeds in both arms.

    cd <svsim checkout (64ab2fe)> && PYTHONPATH=. python3 <this> <analysis dir> --out pairs.jsonl [--pairs 200] [--workers 4]
    python3 <this> --report pairs.jsonl

Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import random
import sys
from multiprocessing import Pool

BASE = 65200000
GAME, AT = "1791384258804", 3


def start(adir):
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply
    from svsim.tools import records
    rec = json.load(open(f"{adir}/mirror-regression/salem_games.json", encoding="utf-8"))["records"][GAME]
    st = records.start(rec)
    for a in rec["actions"][:AT]:
        apply(st, from_dict(a))
    return st


def job(args):
    adir, i = args
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.core.view import determinize
    from svsim.tools.arena import make_agent
    st = start(adir)
    bot = st.active
    assert bot == 1 and st.players[bot].turns_taken == 1
    seed = BASE + i
    d = determinize(st, bot, random.Random(seed))
    out = {"i": i, "seed": seed}
    for arm in ("coin", "keep"):
        s = d.clone()
        if arm == "coin":
            apply(s, next(a for a in legal_actions(s) if type(a).__name__ == "UseBonusPP"))
            play = [a for a in legal_actions(s) if type(a).__name__ == "PlayCard"
                    and (s.in_hand(bot, a.uid).defn.name_zh or "").startswith("古旧天刀")]
            assert play, "Polaris not playable"
            apply(s, play[0])
        apply(s, EndTurn())
        agents = [make_agent("level-strong", 2 * seed + k) for k in range(2)]
        while not s.over:
            apply(s, agents[s.active].act(s, legal_actions(s)))
        out[arm] = 0.5 if s.winner is None else float(s.winner == bot)
        out[arm + "_turns"] = s.turn
    return out


def report(path):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    n = len(rows)
    seeds = sorted(r["seed"] for r in rows)
    keep = sum(r["keep"] for r in rows) / n
    coin = sum(r["coin"] for r in rows) / n
    d = [r["keep"] - r["coin"] for r in rows]
    m = sum(d) / n
    sd = (sum((x - m) ** 2 for x in d) / (n - 1)) ** 0.5
    h = 1.96 * sd / n ** 0.5
    same = sum(1 for r in rows if r["keep"] == r["coin"])
    print("条件：对手卡表已知（牌序、手牌未知）。Salem 27 局第 21 局，bot 第 1 回合；两臂之后双方第 19 版 level-strong 打到终局。\n")
    print(f"{n} 对，种子 {seeds[0]}～{seeds[-1]}（{len(set(seeds))} 个不重复）。\n")
    print("| 臂 | bot 胜率 |")
    print("|---|---|")
    print(f"| 跳币：用额外 PP 出波菈莱（当时的走法） | {coin:.1%} |")
    print(f"| 留着：不用额外 PP，直接结束 | {keep:.1%} |")
    print(f"\n**留着 − 跳币 = {m:+.1%}（95%，按对：{m - h:+.1%}～{m + h:+.1%}）**；两臂结果相同的对 {same} / {n}。")


def main():
    if "--report" in sys.argv:
        report(sys.argv[sys.argv.index("--report") + 1])
        return
    adir = sys.argv[1]
    out = sys.argv[sys.argv.index("--out") + 1]
    n = int(sys.argv[sys.argv.index("--pairs") + 1]) if "--pairs" in sys.argv else 200
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    done = set()
    try:
        done = {json.loads(line)["i"] for line in open(out, encoding="utf-8") if line.strip()}
    except FileNotFoundError:
        pass
    todo = [(adir, i) for i in range(n) if i not in done]
    with open(out, "a", encoding="utf-8") as f, Pool(workers) as pool:
        for r in pool.imap_unordered(job, todo):
            f.write(json.dumps(r) + "\n")
            f.flush()


if __name__ == "__main__":
    main()
