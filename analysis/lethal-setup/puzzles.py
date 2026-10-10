"""Operations puzzles picked from M4 (README-puzzles.md): read the re-test and pick the puzzles; show each puzzle.
Condition: the opponent's deck list is known (order and hand not).

    python puzzles.py read puzzles/retest_rows.jsonl --pick puzzles/pick.json --out puzzles/retest.txt
    python puzzles.py show <stage-0 dir> --retest puzzles/retest.json --out puzzles/puzzles.md
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "turn-level"))
import setup_prob as SP          # noqa: E402
import turn_level as TL          # noqa: E402


def _paired(s, b, n_boot=2000):
    """Mean of salem_j - bot_j over the paired seeds and its percentile interval (seeds resampled in pairs)."""
    d = [x - y for x, y in zip(s, b)]
    rng = random.Random(0)
    bs = sorted(sum(d[rng.randrange(len(d))] for _ in d) / len(d) for _ in range(n_boot))
    return sum(d) / len(d), bs[int(0.025 * n_boot) - 1], bs[int(0.975 * n_boot) - 1]


def read(args):
    rows = SP._lines(args.rows)
    pick = json.load(open(args.pick, encoding="utf-8"))
    by = {(r["k"], r["line"]): r for r in rows if r["direction"] == "default"}
    out, res = [], []
    out.append("条件：对手卡表已知（牌序、手牌未知）。运营局面题：6 个候选的复测（default 方向，两条线各 K = 48，配对）\n")
    out.append("| k | M4 的号 i | 自己的第几回合 | M3 类 | M4 的 d（K = 12） | 复测 Salem 的线 | 复测 bot 的线 | **配对差（区间）** | 入选 |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for p in pick:
        s, b = by[(p["k"], "salem")], by[(p["k"], "bot")]
        assert s["status"] == b["status"] == "ended" and s["seed"] == b["seed"] == 67000000 + 500 * p["i"]
        assert len(s["samples"]) == len(b["samples"]) == 48
        m, lo, hi = _paired(s["samples"], b["samples"])
        ok = m > 0 and lo > 0
        res.append({**p, "re_salem": s["win"], "re_bot": b["win"], "diff": m, "lo": lo, "hi": hi, "ok": ok,
                    "seed": s["seed"]})
        out.append(f"| {p['k']} | {p['i']} | {p['own_turn']} | {p['cls']} | {p['d']:+.3f} | {s['win']:.3f} | {b['win']:.3f} | "
                   f"**{m:+.3f}（{lo:+.3f}～{hi:+.3f}）** | {'是' if ok else '否'} |")
    keep = sorted([r for r in res if r["ok"]], key=lambda r: (-r["diff"], -r["lo"], r["k"]))[:3]
    out.append("")
    out.append(f"- 配对差 > 0 且下沿 > 0 的：{sum(r['ok'] for r in res)} 个")
    out.append("- **定题**（按配对差取前 3）：" + ("、".join(f"k = {r['k']}（{r['diff']:+.3f}）" for r in keep) if keep
                                          else "一个都没剩，照实报，不放宽"))
    out.append(f"- M4 的 d 平均 {sum(p['d'] for p in pick) / len(pick):+.3f} → 复测的配对差平均 "
               f"{sum(r['diff'] for r in res) / len(res):+.3f}（挑最大值带进来的噪声回落多少）")
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    json.dump({"all": res, "puzzles": [r["k"] for r in keep]}, open(os.path.splitext(args.out)[0] + ".json", "w"),
              ensure_ascii=False, indent=1)
    print(text)


def _names():
    """Card names as players call them: analysis/card-glossary.md's common name (the architecture session's
    naming thread; the same parse as svsim.tools.glossary), else the part of the official name after "·"."""
    import re
    from svsim.ui import text as T
    row = re.compile(r"^\|\s*\*\*(?P<common>[^*]+)\*\*\s*\|\s*(?P<stats>[^|]+?)\s*\|\s*(?P<full>[^|]+?)\s*\|")
    names = {}
    for line in open(os.path.join(HERE, "..", "card-glossary.md"), encoding="utf-8"):
        m = row.match(line)
        if m:
            names[m["full"]] = m["common"].strip()
    plain = T.card_name

    def common(defn):
        full = defn.name_zh or defn.name
        name = names.get(full, full.split("·")[-1].strip())
        return plain(defn).replace(full, name)
    T.card_name = common
    return T


def show(args):
    T = _names()
    TL.REC.update(TL._records(os.path.join(args.step0, "selfplay.jsonl")))
    starts, plans = SP._starts(args.step0)
    st_by = {st["k"]: st for st in starts}
    rt = json.load(open(args.retest, encoding="utf-8"))
    info = {r["k"]: r for r in rt["all"]}
    ks = rt["puzzles"] if not args.all else [r["k"] for r in rt["all"]]
    out = ["# 运营局面题（从 M4 自动挑，复测过的；README-puzzles.md）", "",
           "**条件**：对手卡表已知（牌序、手牌未知）。", ""]
    if not ks:
        out.append("复测以后一个都没剩（配对差 > 0 且下沿 > 0 的没有），照实报。")
    for n, k in enumerate(ks, 1):
        st, r = st_by[k], info[k]
        state, rec = TL._start_state(st)
        me = state.active
        salem = TL._salem_turn(rec, st["at"])
        bot = [a for a in next(p for p in plans[k]["plans"] if p["kind"] == "bot")["actions"]]
        (fs, ss), (fb, sb) = SP.turn_end(state, salem), SP.turn_end(state, bot)
        opp = state.players[1 - me]
        out += [f"## 题 {n}：k = {k}", "",
                f"- **对局**：Salem 第 {st['batch']} 批，对局号 {st['game']}，动作序号 {st['at']}；Salem 坐 {st['seat']} 号位。",
                f"- **回合**：全局第 {state.turn} 回合，Salem 自己的第 {st['own_turn']} 回合；M3 归类 {r['cls']}。",
                f"- **复测**（default 方向，各 48 局，种子 {r['seed']} 派生）：Salem 的线 {r['re_salem']:.3f}，bot 的线 {r['re_bot']:.3f}，"
                f"配对差 **{r['diff']:+.3f}**（{r['lo']:+.3f}～{r['hi']:+.3f}）。M4 里 K = 12 时的差 {r['d']:+.3f}。", "",
                "**当时的局面**（Salem 视角）", "", "```", T.render_state(state, me),
                "  对手手牌（Salem 当时看不到）：" + ("；".join(T.card_line(state, c, in_hand=True) for c in opp.hand) or "（空）"),
                "```", "",
                "**Salem 这回合的打法**", ""]
        out += [f"{i}. {line}" for i, line in enumerate(T.describe_line(state, salem), 1)]
        out += ["", "**bot（`mcts:100+plan+learned+phased`，第 0 步的计划）这回合的打法**", ""]
        out += [f"{i}. {line}" for i, line in enumerate(T.describe_line(state, SP_acts(bot)), 1)]
        for label, (f, s) in (("Salem 的线", (fs, ss)), ("bot 的线", (fb, sb))):
            out += ["", f"**{label}打完以后**（{f}；Salem 视角，对手要行动）", "", "```", T.render_state(s, me), "```"]
        out.append("")
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


def SP_acts(actions):
    from svsim.core.actions import from_dict
    return [from_dict(a) if isinstance(a, dict) else a for a in actions]


P1_K, P1_BANK, P1_START = 48, 67100000, 320
SPEC = "mcts:100+plan+learned+phased"


def _p1_seeds(bank, k):
    rng = random.Random(bank)
    return [rng.randrange(2 ** 31) for _ in range(k)]


def _p1_job(job):
    """Puzzle 1's Kimika line, one game: determinize (Salem's deck re-shuffled, so Kimika's draw is re-dealt), play
    Salem's first action (Kimika choosing Vorlalai), level-strong finishes the turn, default to the end."""
    from svsim.core.engine import apply, legal_actions
    from svsim.core.view import determinize
    from svsim.search.foresight import direction_rollout
    from svsim.tools.arena import make_agent
    from svsim.ui import text as T
    j, sd, st = job
    state, rec = TL._start_state(st)
    me = state.active
    first = TL._salem_turn(rec, st["at"])[0]
    s = determinize(state, me, random.Random(sd))
    before = {c.uid for c in s.players[me].hand}
    apply(s, first)
    new_cards = [c for c in s.players[me].hand if c.uid not in before]
    sag = any("相枛津" in (c.defn.name_zh or "") for c in new_cards)
    _names()
    drawn = [T.card_name(c.defn) for c in new_cards]
    agent, n = make_agent("level-strong", sd), 0
    while not s.over and s.active == me and n < 200:
        apply(s, agent.act(s, legal_actions(s)))
        n += 1
    erntz = [c for c in s.players[1 - me].field if (c.defn.name_zh or "").endswith("伊兰翠")]
    out = direction_rollout(s, direction="default", k=1, seed=sd, opp_spec=SPEC, our_spec=SPEC)["default"]
    return {"j": j, "seed": sd, "drawn": drawn, "sag": sag, "enemy_erntz_left": bool(erntz), "over_in_turn": s.over,
            "my_hp": s.players[me].leader_hp, "enemy_hp": s.players[1 - me].leader_hp, "result": out["samples"][0]}


def _p1_bot_job(job):
    from svsim.search.foresight import direction_rollout
    st, plans_k, bank, k = job
    state, _ = TL._start_state(st)
    acts = next(p for p in plans_k["plans"] if p["kind"] == "bot")["actions"]
    status, end = SP.turn_end(state, acts)
    return direction_rollout(end, direction="default", k=k, seed=bank, opp_spec=SPEC, our_spec=SPEC)["default"]


def p1run(args):
    from multiprocessing import Pool
    recs = TL._records(os.path.join(args.step0, "selfplay.jsonl"))
    starts, plans = SP._starts(args.step0)
    st = next(x for x in starts if x["k"] == P1_START)
    seeds = _p1_seeds(args.bank, args.k)
    with Pool(args.workers, initializer=SP._init, initargs=(recs,)) as pool, \
            open(args.out, "w", encoding="utf-8") as fh:
        for row in pool.imap(_p1_job, [(j, sd, st) for j, sd in enumerate(seeds)]):
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
        if not args.no_bot:
            bot = pool.apply(_p1_bot_job, ((st, plans[P1_START], args.bank, args.k),))
            fh.write(json.dumps({"bot_line": True, "seed": args.bank, "samples": bot["samples"]}) + "\n")
    print(f"写进了 {args.out}")


def p1read(args):
    from collections import Counter
    rows = SP._lines(args.rows)
    kim = sorted([r for r in rows if "j" in r], key=lambda r: r["j"])
    bot_new = next((r["samples"] for r in rows if r.get("bot_line")), None)
    old = next(r for r in SP._lines(args.retest_rows) if r["k"] == P1_START and r["line"] == "bot")
    assert len(kim) == P1_K and [r["seed"] for r in kim] == _p1_seeds(P1_BANK, P1_K) and len(old["samples"]) == P1_K
    res = [r["result"] for r in kim]
    m, lo, hi = _paired(res, old["samples"])
    out = ["条件：对手卡表已知（牌序、手牌未知）。运营局面题 题 1（k = 320）的复测：先下琪米卡、抽牌重新发（README-puzzles.md）\n",
           f"- 先下琪米卡这条线 {len(kim)} 局：胜率 {sum(res) / len(res):.3f}（{sum(r == 1.0 for r in res)} 胜）",
           f"- **主读数**：对 bot 原来那条线（复测 {sum(old['samples']):.0f} / {len(old['samples'])}，种子 {old['seed']} 派生）逐局配对，"
           f"配对差 **{m:+.3f}（{lo:+.3f}～{hi:+.3f}）**",
           f"- **J46**（配对差区间不含 0，且 > 0，置信 65%）→ {'对' if lo > 0 else '错'}"]
    if bot_new:
        m2, lo2, hi2 = _paired(res, bot_new)
        out.append(f"- 另报：bot 的线用这次的种子再打 {len(bot_new)} 局，胜率 {sum(bot_new) / len(bot_new):.3f}；"
                   f"和琪米卡线逐局配对，差 {m2:+.3f}（{lo2:+.3f}～{hi2:+.3f}）")
    drawn = Counter(d for r in kim for d in r["drawn"])
    sag = [r for r in kim if r["sag"]]
    out.append(f"- 琪米卡抽到的牌：" + "、".join(f"{k} {v}" for k, v in drawn.most_common()))
    out.append(f"- 抽到口人魔的 {len(sag)} 局：胜率 {sum(r['result'] for r in sag) / len(sag) if sag else float('nan'):.3f}；"
               f"没抽到的 {len(kim) - len(sag)} 局：胜率 "
               f"{sum(r['result'] for r in kim if r not in sag) / max(1, len(kim) - len(sag)):.3f}")
    out.append(f"- level-strong 打完这回合，对手的正义还在场上：{sum(r['enemy_erntz_left'] for r in kim)} / {len(kim)} 局")
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("read")
    a.add_argument("rows")
    a.add_argument("--pick", required=True)
    a.add_argument("--out", required=True)
    a = sub.add_parser("show")
    a.add_argument("step0")
    a.add_argument("--retest", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--all", action="store_true", help="all 6 candidates, not only the puzzles")
    a = sub.add_parser("p1run")
    a.add_argument("step0")
    a.add_argument("--out", required=True)
    a.add_argument("--bank", type=int, default=P1_BANK)
    a.add_argument("--k", type=int, default=P1_K)
    a.add_argument("--workers", type=int, default=1)
    a.add_argument("--no-bot", action="store_true")
    a = sub.add_parser("p1read")
    a.add_argument("rows")
    a.add_argument("--retest-rows", required=True)
    a.add_argument("--out", required=True)
    args = ap.parse_args()
    {"read": read, "show": show, "p1run": p1run, "p1read": p1read}[args.cmd](args)


if __name__ == "__main__":
    main()
