"""The pre-gate check, step 1 (../c3-threat/README.md section 14; the architecture thread 19:36): a feature
candidate against its base, per old feature: every coefficient whose sign flips, or whose size changes more than
twofold, in the turn-end (ended) and turn-start (act) models. No games; numbers only, it does not stop a gate.

    cd <checkout with the candidate folder> && PYTHONPATH=. python3 <this> --cand FOLDER --pair DECK-OPP
                                                                         [--base FOLDER]

--base defaults to the installed models (phased_models itself). Per raw unit, with each coefficient times the
feature's standard deviation in the base's training data (logit per SD) so the sizes compare. Listed:
  flip      both nonzero, opposite signs;
  on / off  zero in one model, nonzero in the other;
  x2        same sign, |candidate| > 2 |base| or < |base| / 2.

Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse

from svsim.learn.model import LinearValue
from svsim.learn.phased import folder_of


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True)
    ap.add_argument("--pair", required=True, help="e.g. ramp-t-pirate-t (the file names' deck-opponent)")
    ap.add_argument("--base", default=None)
    args = ap.parse_args()
    cand_dir = folder_of(args.cand)
    base_dir = folder_of(args.base) if args.base else cand_dir.parent
    print(f"条件：对手卡表已知（牌序、手牌未知）。候选 {args.cand} 对底 {args.base or '现装（phased_models）'}，配对 {args.pair}；"
          "每单位原始特征的系数，括号里是 × 底的训练数据标准差（每个标准差多少 logit）。\n")
    total_flips = 0
    for moment in ("ended", "act"):
        c = LinearValue.load(cand_dir / f"{args.pair}-{moment}.json")
        b = LinearValue.load(base_dir / f"{args.pair}-{moment}.json")
        wc, wb = c.weights_by_name(), b.weights_by_name()
        sd = dict(zip(b.names(), b.std))
        rows = []
        for n in b.names():
            if n == "bias":
                continue
            x, y = wb.get(n, 0.0), wc.get(n, 0.0)
            if x == 0 and y == 0:
                continue
            kind = None
            if x * y < 0:
                kind = "翻号"
            elif x == 0 or y == 0:
                kind = "新出现" if x == 0 else "变成 0"
            elif abs(y) > 2 * abs(x) or abs(y) < abs(x) / 2:
                kind = "超过 2 倍"
            if kind:
                rows.append((kind, n, x, y, sd.get(n, 0.0)))
        new = [n for n in c.names() if n not in set(b.names())]
        flips = [r for r in rows if r[0] == "翻号"]
        total_flips += len(flips)
        print(f"**{moment}**（新特征：{', '.join(new) or '无'}）：翻号 {len(flips)}，"
              f"新出现 / 变成 0 {sum(r[0] in ('新出现', '变成 0') for r in rows)}，超过 2 倍 {sum(r[0] == '超过 2 倍' for r in rows)}\n")
        if rows:
            print("| 类 | 旧特征 | 底 | 候选 |")
            print("|---|---|---|---|")
            order = {"翻号": 0, "新出现": 1, "变成 0": 1, "超过 2 倍": 2}
            for kind, n, x, y, s in sorted(rows, key=lambda r: (order[r[0]], -max(abs(r[2]), abs(r[3])) * r[4])):
                print(f"| {kind} | {n} | {x:+.4f}（{x * s:+.3f}） | {y:+.4f}（{y * s:+.3f}） |")
            print()
    print(f"翻号合计 {total_flips}：" + ("按第十四节第 2 步，开门前在这个配对上做一次并排重放分类。" if total_flips
                                    else "没有翻号，直接开门。"))


if __name__ == "__main__":
    main()
