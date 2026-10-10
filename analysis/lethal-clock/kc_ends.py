"""The lethal-clock candidate's offline checks (1) and (2) (the architecture thread 2026-10-10 10:38Z): which turn end
each evaluator rates higher, Salem's or the bot's, at the evaluation starts k 329 and 455 (check 1: both should turn
right) and at puzzles 2 and 3, k 518 and 445 (check 2: already right under the installed evaluation, must not turn
wrong). The positions and ends are analysis/puzzles3's (ops.py): Salem's turn end against step 0's bot line, and
against every run's end of its rows (level-strong / mcts:1043 / mcts:3000, 8 seeds each).
Evaluators: the installed (level-strong), cand-tl-ramp-ramp (the recipe's control) and cand-kc-ramp-ramp.
Condition: the opponent's deck list is known (order and hand not).

    python3 kc_ends.py STEP0_DIR ANA_DIR ROWS.jsonl [ROWS.jsonl ...]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis/puzzles3"))
EVALS = {"installed": "level-strong",
         "cand-tl": "mcts:200+plan+learned+phased=cand-tl-ramp-ramp",
         "cand-kc": "mcts:200+plan+learned+phased=cand-kc-ramp-ramp",
         "cand-nl": "mcts:200+plan+learned+phased=cand-nl-ramp-ramp"}
KS = {329: "evaluation (check 1)", 455: "evaluation (check 1)", 518: "puzzle 2 (check 2)", 445: "puzzle 3 (check 2)"}


def main():
    import ops
    step0, ana, rows_paths = sys.argv[1], sys.argv[2], sys.argv[3:]
    ops._init(step0, ana)
    import turn_level as TL
    from svsim.core.actions import from_dict
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    W = {e: _search(make_agent(spec, 0)).weights for e, spec in EVALS.items()}
    rows = [json.loads(x) for p in rows_paths for x in open(p) if x.strip()]
    out = {}
    print("条件：对手卡表已知（牌序、手牌未知）。")
    for k, what in KS.items():
        st = ops.G["starts"][k]
        state, rec = TL._start_state(st)
        me = state.active
        salem = TL._salem_turn(rec, st["at"])
        bot0 = [from_dict(a) for a in next(p for p in ops.G["plans"][k]["plans"] if p["kind"] == "bot")["actions"]]
        s_end, b_end = ops.turn_end(state, salem), ops.turn_end(state, bot0)
        runs = [ops.turn_end(state, [from_dict(a) for a in r["actions"]]) for r in rows if r["k"] == k]
        res = {}
        for e, w in W.items():
            ps = ops.judge_end(s_end, me, w)[0]
            pb = ops.judge_end(b_end, me, w)[0]
            pr = [ops.judge_end(x, me, w)[0] for x in runs]
            res[e] = {"salem": round(ps, 3), "bot (step 0)": round(pb, 3), "right vs step 0": ps > pb,
                      "runs": len(pr), "runs Salem beats": sum(ps > p for p in pr),
                      "runs mean": round(sum(pr) / len(pr), 3) if pr else None}
        from svsim.learn.features import extra_features, extra_names
        names = extra_names(("kclock",))
        fs, fb = ops.judge_end(s_end, me, W["cand-kc"])[1], ops.judge_end(b_end, me, W["cand-kc"])[1]
        res["kclock"] = {"salem": dict(zip(names, [round(v, 2) for v in extra_features(s_end, me, ("kclock",))])),
                         "bot (step 0)": dict(zip(names, [round(v, 2) for v in extra_features(b_end, me, ("kclock",))])),
                         "logit Salem - bot, kclock columns": round(sum(fs[n] - fb[n] for n in names), 4) if fs and fb else None,
                         "logit Salem - bot, all": round(sum(fs.values()) - sum(fb.values()), 4) if fs and fb else None,
                         "largest (Salem - bot)": [(n, round(fs[n] - fb[n], 3)) for n in sorted(fs, key=lambda n: -abs(fs[n] - fb[n]))[:6]] if fs and fb else None}
        out[k] = res
        print(f"\nk {k}（{what}）")
        for e, r in res.items():
            if e == "kclock":
                print(f"  kclock：Salem {r['salem']}\n          bot   {r['bot (step 0)']}\n          "
                      f"logit 差（Salem − bot）时钟列 {r['logit Salem - bot, kclock columns']}，全部 {r['logit Salem - bot, all']}；"
                      f"差最大的 {r['largest (Salem - bot)']}")
                continue
            print(f"  {e:9s} Salem {r['salem']:.3f} / bot {r['bot (step 0)']:.3f} → "
                  f"{'对' if r['right vs step 0'] else '错'}；各次运行的回合末 {r['runs']} 个，Salem 高过 "
                  f"{r['runs Salem beats']} 个（平均 {r['runs mean']}）")
    print("\n" + json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
