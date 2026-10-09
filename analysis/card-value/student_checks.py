"""The student's four pre-gate checks (student-plan.md; the architecture thread 2026-10-09 02:10: 1 and 4 stop the
gate, 2 and 3 are reported only). The student enters as a feature of learn.features (EXTRA_FNS "hand_value",
refitted by learn.phased into a candidate folder); its marginal value of a card c in a position is
    dH(c) = hand_value(state) - hand_value(state with one copy of c taken out of the mover's hand),
read through learn.features.extra_features, so the checks need nothing from the student but the feature.

    cd <svsim checkout with the student> && PYTHONPATH=.:<this folder> python3 <this> unit --cand FOLDER
    ... <this> fidelity --selfplay selfplay.jsonl --positions positions.jsonl --teacher teacher.jsonl
                        [--gend val_gend.jsonl]
    ... <this> salem --games SALEM_GAMES --rows g_end.jsonl g_end2.jsonl --t teacher_rows.json --t teacher_rows2.json
    ... <this> pacing --a SPEC --b level-strong [--games 200] [--workers 16]

1 (stops the gate) unit: the refitted coefficient of hand_value must be > 0 (the architecture thread 02:19; else
  no gate: check first whether it is collinear with me_hand, --selfplay --positions); and Salem's top-10 #3 (1791317238047, action 53; the bot's seat, the original Ramp mirror),
  dH must have G_end's sign there (the fixed arms, the same as Salem's choice): Sagatsumatsu, Burnite, Sloth of the
  Crestpetal, Dragonewt Promoter kept (+), Fate of the World used (-); and each of the five cards' dH must differ
  between maximum play points 2 and 9 (the same position, play points set to 2 / 9). Also reported: the refitted
  coefficient of hand_value in the candidate's turn-end model and coefficient x dH (what the evaluator adds).
2 (reported) fidelity: Spearman(dH, T) on the held-out positions' keep:<card> labels (T = mean of the two
  seeds), the training positions beside it; with --gend, Spearman(dH, G_end) on the 400 validation items.
3 (reported) salem: the keep AUC by card on Salem's 27 games (the discrimination experiment's items, its exclusion
  rule), on the teacher's line items and on all items, beside T and Q, intervals by resampling Salem's turns.
4 (stops the gate) pacing: self-play of A and of B on the same seeds (data bank 65890000 + g); cards played and
  evolutions per player per game; A must not be lower than B by more than 5% in either.

Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import json
import random
from collections import defaultdict
from multiprocessing import Pool

from svsim.cards import library, decks  # noqa: F401
from svsim.core.actions import Evolve, PlayCard, from_dict
from svsim.core.engine import apply, legal_actions
from svsim.tools import records

EXTRA = "hand_value"
UNIT_GAME, UNIT_AT = "1791317238047", 53
UNIT_SIGNS = {"Sagatsumatsu, Fair Beheader": +1, "Burnite, Anathema of Ash": +1, "Sloth of the Crestpetal": +1,
              "Dragonewt Promoter": +1, "Fate of the World": -1}
PACING_SEED = 65890000


def _state_at(rec, at):
    st = records.start(rec)
    for a in rec["actions"][:at]:
        apply(st, from_dict(a))
    return st


def hand_value(st, me):
    from svsim.learn.features import extra_features
    return extra_features(st, me, (EXTRA,))[0]


def marginal(st, me, cid):
    """dH of one copy of card id cid in the mover's hand."""
    t = st.clone()
    hand = t.players[me].hand
    for i, c in enumerate(hand):
        if c.defn.card_id == cid:
            del hand[i]
            break
    else:
        raise ValueError(f"card {cid} not in hand")
    return hand_value(st, me) - hand_value(t, me)


def _spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for t in range(i, j + 1):
                r[o[t]] = (i + j) / 2
            i = j + 1
        return r
    a, b = rk(x), rk(y)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    c = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    va, vb = sum((p - ma) ** 2 for p in a) ** 0.5, sum((q - mb) ** 2 for q in b) ** 0.5
    return c / (va * vb) if va and vb else float("nan")


def unit(args):
    from svsim.learn.model import LinearValue
    from svsim.learn.phased import folder_of
    games = json.load(open(args.games, encoding="utf-8"))["records"]
    st = _state_at(games[UNIT_GAME], UNIT_AT)
    me = st.active
    coef = None
    if args.cand:
        m = LinearValue.load(folder_of(args.cand) / f"{args.pair}-ended.json")
        coef = m.weights_by_name().get(EXTRA)
    names = {c.defn.name: c.defn.card_id for c in st.players[me].hand}
    print(f"条件：对手卡表已知（牌序、手牌未知）。单元测试：Salem 前十题 #3（{UNIT_GAME} 第 {UNIT_AT} 步，bot 的座位）；"
          f"hand_value 在候选回合末模型里的系数 {coef if coef is not None else '（没给 --cand）'}\n")
    print("| 牌 | 应为（修好的 G_end = Salem） | ΔH | 系数 × ΔH | 符号对 | ΔH：PP 2 / PP 9 | 不同 |")
    print("|---|---|---|---|---|---|---|")
    ok_sign = ok_pp = True
    for name, want in UNIT_SIGNS.items():
        cid = names[name]
        d = marginal(st, me, cid)
        lo, hi = st.clone(), st.clone()
        for s_, pp in ((lo, 2), (hi, 9)):
            s_.players[me].max_pp = s_.players[me].pp = pp
        d2, d9 = marginal(lo, me, cid), marginal(hi, me, cid)
        good = (d > 0) if want > 0 else (d < 0)
        diff = abs(d2 - d9) > 1e-9
        ok_sign &= good
        ok_pp &= diff
        print(f"| {name} | {'+（留着更好）' if want > 0 else '−（用掉更好）'} | {d:+.4f} | "
              f"{(coef * d) if coef is not None else float('nan'):+.4f} | {'是' if good else '**否**'} | "
              f"{d2:+.4f} / {d9:+.4f} | {'是' if diff else '**否**'} |")
    ok_coef = coef is not None and coef > 0           # the architecture thread 02:19: part of the stop (with
    #                                                    coef > 0, coef x dH has dH's signs, so they match Salem's)
    print(f"\n符号五项全对：{'通过' if ok_sign else '**不通过**'}；2 PP 和 9 PP 五项都不同：{'通过' if ok_pp else '**不通过**'}；"
          f"拟合系数 > 0：{'通过' if ok_coef else ('**不通过**' if coef is not None else '**没给 --cand，判不了**')}"
          f" → 第 1 条{'通过' if ok_sign and ok_pp and ok_coef else '**不通过（挡门）**'}")
    if args.selfplay and args.positions:
        collinear(args)
    elif coef is not None and coef <= 0:
        print("系数 ≤ 0：按规矩先查它和 me_hand 张数是不是共线，请加 --selfplay --positions 再跑一次。")


def collinear(args):
    """hand_value against the base features on the training positions: its correlation with me_hand (cards in
    hand) and the R^2 of hand_value on all the base turn-end features (how much of it they already hold)."""
    import numpy as np
    from svsim.learn.features import features, names
    games = {str(r["g"]): r for r in (json.loads(x) for x in open(args.selfplay, encoding="utf-8") if x.strip())}
    pos = [p for p in (json.loads(x) for x in open(args.positions, encoding="utf-8") if x.strip())
           if p["split"] == "train"][:args.max_positions]
    hv, X = [], []
    for p in pos:
        st = _state_at(games[str(p["g"])], p["at"])
        me = st.active
        hv.append(hand_value(st, me))
        X.append(features(st, me, False, 2))
    hv, X = np.array(hv), np.array(X, dtype=float)
    cols = names(False, 2)
    i_hand = cols.index("me_hand")
    r_hand = float(np.corrcoef(hv, X[:, i_hand])[0, 1])
    keep = X.std(axis=0) > 0
    A = np.column_stack([X[:, keep], np.ones(len(X))])
    beta, *_ = np.linalg.lstsq(A, hv, rcond=None)
    r2 = 1 - float(np.sum((hv - A @ beta) ** 2) / np.sum((hv - hv.mean()) ** 2))
    print(f"\n**共线检查**（训练局面 {len(pos)} 个）：hand_value 和 me_hand（手牌张数）的相关 {r_hand:+.3f}；"
          f"hand_value 对全部现有回合末特征回归的 R² {r2:.3f}（越接近 1，它能给的新信息越少，系数越容易被挤成 ≤ 0）"
          + ("；局面数不到特征数的 5 倍，R² 不可信" if len(pos) < 5 * A.shape[1] else ""))


def fidelity(args):
    games = {str(r["g"]): r for r in (json.loads(x) for x in open(args.selfplay, encoding="utf-8") if x.strip())}
    pos = {p["n"]: p for p in (json.loads(x) for x in open(args.positions, encoding="utf-8") if x.strip())}
    T = defaultdict(list)
    for r in (json.loads(x) for x in open(args.teacher, encoding="utf-8") if x.strip()):
        for key, v in r["res"].items():
            if key.startswith("keep:"):
                T[(r["n"], int(key.split(":")[1]))].append((v["teacher"], v.get("se", 1.0)))
    out = {"train": ([], []), "val": ([], [])}
    cache, absent, null = {}, 0, 0
    for (n, cid), tse in sorted(T.items()):
        p = pos[n]
        if n not in cache:
            cache[n] = _state_at(games[str(p["g"])], p["at"])
        st = cache[n]
        if not any(c.defn.card_id == cid for c in st.players[st.active].hand):
            absent += 1                     # drawn or made during the turn: the student values the turn-start hand
            continue
        if all(t == 0 and se == 0 for t, se in tse):
            null += 1                       # the restriction changed nothing: left out as in the labels (02:38Z)
            continue
        ts = [t for t, _ in tse]
        out[p["split"]][0].append(marginal(st, st.active, cid))
        out[p["split"]][1].append(sum(ts) / len(ts))
    print("条件：对手卡表已知（牌序、手牌未知）。第 2 条（只报不挡）：学生的 ΔH 对老师 T（两个种子的平均）；"
          f"老师主线上、但回合开头不在手里的牌（本回合抽到或生成的）{absent} 个标签不算；"
          f"限制什么都没改变的（两个种子 se 和 T 都是 0）{null} 个也不算，同学生的标签\n")
    for split, (d, t) in out.items():
        print(f"- {'留出局面' if split == 'val' else '训练局面'}：{len(d)} 个（局面 × 牌）标签，Spearman(ΔH, T) = "
              f"{_spearman(d, t):.3f}" + ("（提议门槛 0.72，只报不挡；低于它建造线可以先改一轮学生）" if split == "val" else ""))
    if args.gend:
        items = [json.loads(x) for x in open(args.gend, encoding="utf-8") if x.strip()]
        d, g, half1, half2 = [], [], [], []
        for it in items:
            st = _state_at(games[str(it["g"])], it["at"])
            d.append(marginal(st, st.active, it["card"]))
            g.append(it["G_end"])
            half1.append(it["G_end1"])
            half2.append(it["G_end2"])
        rel = _spearman(half1, half2)
        print(f"- 验证集 {len(items)} 项：Spearman(ΔH, G_end) = {_spearman(d, g):.3f}；G_end 两组一致度 {rel:.3f}"
              f"（32 局的信度约 {2 * rel / (1 + rel):.3f}，上面的相关被它压低）")


def salem(args):
    import salem_discrim as D
    games = json.load(open(args.games, encoding="utf-8"))["records"]
    rows = [json.loads(x) for path in args.rows for x in open(path, encoding="utf-8") if x.strip()]
    T = defaultdict(list)
    for path in args.t:
        for r in json.load(open(path, encoding="utf-8")):
            if r["restriction"].startswith("keep:"):
                T[(r["game"], r["at"], int(r["restriction"].split(":")[1]))].append(r["teacher"])
    data, cache = [], {}
    for r in rows:
        if r["set"] not in ("salem80", "salem17") or r["use_arm_used"] < r["k"]:
            continue
        key = (r["game"], r["at"])
        if key not in cache:
            cache[key] = _state_at(games[r["game"]], r["at"])
        st = cache[key]
        t = T.get((r["game"], r["at"], r["card"]))
        data.append({**r, "S": marginal(st, st.active, r["card"]), "T": sum(t) / len(t) if t else None})
    line = [d for d in data if d["T"] is not None]
    turns = sorted({(d["game"], d["at"]) for d in data})
    rng = random.Random(13)
    picks = [[turns[rng.randrange(len(turns))] for _ in turns] for _ in range(args.boot)]

    def boot(sub, f):
        by = defaultdict(list)
        for d in sub:
            by[(d["game"], d["at"])].append(d)
        vals = sorted(v for v in (f([d for t in pk for d in by.get(t, [])]) for pk in picks) if v == v)
        return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]
    print("条件：对手卡表已知（牌序、手牌未知）。第 3 条（只报不挡）：Salem 27 局留牌 AUC（按牌），分辨实验的项和排除规则\n")
    print("| 项 | 个数 | 学生 ΔH | T | G_end | 学生 − T |")
    print("|---|---|---|---|---|---|")
    for title, sub, keys in (("老师主线上的项", line, ("S", "T", "G_end")), ("全部项", data, ("S", "G_end"))):
        cells = []
        for k in ("S", "T", "G_end"):
            if k not in keys:
                cells.append("—")
                continue
            a = D.auc(sub, k, "按牌")[0]
            lo, hi = boot(sub, lambda x, k=k: D.auc(x, k, "按牌")[0])
            cells.append(f"{a:.3f}（{lo:.3f}～{hi:.3f}）")
        if "T" in keys:
            a = D.auc(sub, "S", "按牌")[0] - D.auc(sub, "T", "按牌")[0]
            lo, hi = boot(sub, lambda x: D.auc(x, "S", "按牌")[0] - D.auc(x, "T", "按牌")[0])
            cells.append(f"{a:+.3f}（{lo:+.3f}～{hi:+.3f}）")
        else:
            cells.append("—")
        print(f"| {title} | {len(sub)} | " + " | ".join(cells) + " |")


def _pace_job(job):
    from svsim.core.engine import new_game
    from svsim.tools.arena import make_agent
    from svsim.ui.session import DECKS
    spec, deck, g, base = job
    cards = decks.build(DECKS[deck][1])
    seed = base + g
    st = new_game(cards, decks.build(DECKS[deck][1]), seed=seed)
    agents = [make_agent(spec, 10 * seed + i) for i in (0, 1)]
    plays, evos = [0, 0], [0, 0]
    while not st.over:
        a = agents[st.active].act(st, legal_actions(st))
        plays[st.active] += isinstance(a, PlayCard)
        evos[st.active] += isinstance(a, Evolve)
        apply(st, a)
    return spec, g, plays, evos


def pacing(args):
    jobs = [(spec, args.deck, g, args.seed) for spec in (args.a, args.b) for g in range(args.games)]
    acc = {args.a: [[], []], args.b: [[], []]}
    with Pool(args.workers) as pool:
        for spec, g, plays, evos in pool.imap_unordered(_pace_job, jobs, chunksize=2):
            acc[spec][0] += plays
            acc[spec][1] += evos
    mean = lambda v: sum(v) / len(v)
    pa, ea = mean(acc[args.a][0]), mean(acc[args.a][1])
    pb, eb = mean(acc[args.b][0]), mean(acc[args.b][1])
    ok = pa >= 0.95 * pb and ea >= 0.95 * eb
    print(f"条件：对手卡表已知（牌序、手牌未知）。第 4 条（挡门）：{args.deck} 镜像自对弈各 {args.games} 局，同样的种子"
          f"（{args.seed}～{args.seed + args.games - 1}）\n")
    print(f"- 每方每局出牌：A {pa:.2f}，B {pb:.2f}（A ÷ B = {pa / pb:.3f}）")
    print(f"- 每方每局进化：A {ea:.2f}，B {eb:.2f}（A ÷ B = {ea / eb if eb else float('nan'):.3f}）")
    print(f"→ 第 4 条{'通过' if ok else '**不通过（挡门）：A 比 B 少超过 5%**'}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("unit")
    a.add_argument("--games", default="analysis/mirror-regression/salem_games.json")
    a.add_argument("--cand", default=None)
    a.add_argument("--pair", default="ramp-ramp")
    a.add_argument("--selfplay", default=None, help="with --positions: the collinearity check")
    a.add_argument("--positions", default=None)
    a.add_argument("--max-positions", type=int, default=3000)
    b = sub.add_parser("fidelity")
    b.add_argument("--selfplay", required=True)
    b.add_argument("--positions", required=True)
    b.add_argument("--teacher", required=True)
    b.add_argument("--gend", default=None)
    c = sub.add_parser("salem")
    c.add_argument("--games", default="analysis/mirror-regression/salem_games.json")
    c.add_argument("--rows", nargs="+", required=True)
    c.add_argument("--t", action="append", required=True)
    c.add_argument("--boot", type=int, default=2000)
    d = sub.add_parser("pacing")
    d.add_argument("--a", required=True)
    d.add_argument("--b", default="level-strong")
    d.add_argument("--deck", default="ramp")
    d.add_argument("--games", type=int, default=200)
    d.add_argument("--workers", type=int, default=16)
    d.add_argument("--seed", type=int, default=PACING_SEED, help="65890000 for the student, 65990000 for the value net")
    args = ap.parse_args()
    {"unit": unit, "fidelity": fidelity, "salem": salem, "pacing": pacing}[args.cmd](args)


if __name__ == "__main__":
    main()
