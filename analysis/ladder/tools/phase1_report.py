"""Tables for the phase-1 report from a RUNS directory written by tools/phase1_checks.py (finished or partial).

    python tools/phase1_report.py --runs RUNS [--out report.md]

Reads each step's summary.json and the game logs under it; writes markdown (Chinese) to --out (default
RUNS/report.md) and the same numbers as RUNS/report.json. Single process, reads only: safe to run on Salem's
computer after the checks have finished. Head-to-head intervals are recomputed from the logs (Wilson), since the
checks' own normal-approximation interval can run past 0 or 1 on few games.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import phase1_checks as C  # noqa: E402

STEPS = ("baseline", "replay", "gate", "known", "known2", "fluct")   # `known` only in the 11-21 run (p1)
ZH = {"baseline": "基线天梯", "replay": "重放", "gate": "把关工具自检", "known": "已知强弱（第一轮，粗）",
      "fluct": "波动", "known2": "已知强弱（第二轮，细）"}


def logs(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def groups(runs: Path) -> dict[str, tuple[tuple[int, int], list[Path]]]:
    """Game logs by seed segment: name -> ((lo, hi), files)."""
    g = {"baseline": (C.LADDER_SEEDS, [runs / "baseline" / "pool" / "games.jsonl"]),
         "gate": (C.GATE_SEEDS, sorted((runs / "gate").glob("G-*/games.jsonl"))),
         "fluct": (C.FLUCT_SEEDS, sorted((runs / "fluct").glob("eval-*/games.jsonl")))}
    for step, cfg in C.KNOWN.items():
        g[f"{step} pools"] = ((cfg["pools"]["all-1500"][0], cfg["pools"]["reversed"][1]),
                              [runs / step / n / "games.jsonl" for n in cfg["pools"]])
        g[f"{step} head-to-head"] = (cfg["h2h"], sorted((runs / step).glob("h2h-*.jsonl")))
        g[f"{step} evaluator"] = ((cfg["eval"], cfg["eval"] + cfg["eval_span"] * len(cfg["eps"])),
                                  sorted((runs / step).glob("eval-*/games.jsonl")))
    return {k: (r, [f for f in fs if f.exists()]) for k, (r, fs) in g.items()}


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def scan(name, rng, files) -> dict:
    res, seeds, turns, og, cpu, wall_game, machines, limits = Counter(), Counter(), [], [0, 0], [], [], set(), set()
    reruns = 0
    for f in files:
        for r in logs(f):
            res[r.get("result")] += 1
            seeds[r["seed"]] += 1
            reruns += bool((r.get("labels") or {}).get("rerun"))
            if r.get("result") in ("normal", "draw"):
                turns.append(r.get("turns", 0))
                og[0] += sum(r.get("out_of_guess") or [])
                og[1] += 1
                default = [i for i, s in enumerate(r.get("strategies", [])) if s == C.DEFAULT]
                w = 0
                for seat, comp, wall_us in r.get("steps", []):
                    w += wall_us
                    if seat in default:      # wall time per step (ms): CPU is in ns on Linux, cycles on Windows
                        cpu.append(wall_us / 1e3)
                wall_game.append(w / 1e6)
            p = r.get("provenance") or {}
            machines.add((p.get("commit", "")[:7], p.get("dirty"), p.get("python"), p.get("os")))
            limits.add(json.dumps(r.get("limits"), sort_keys=True))
    lo, hi = rng
    multi = Counter(seeds.values())
    return {"files": len(files), "records": sum(res.values()), "results": dict(res),
            "seeds_unique": len(seeds), "seed_min": min(seeds) if seeds else None,
            "seed_max": max(seeds) if seeds else None, "segment": [lo, hi - 1],
            "inside": all(lo <= s < hi for s in seeds), "times_used": dict(sorted(multi.items())),
            "reruns": reruns, "turns_mean": round(st.mean(turns), 2) if turns else None,
            "out_of_guess_per_game": round(og[0] / og[1], 3) if og[1] else None,
            "default_step_ms": {"steps": len(cpu), "mean": round(st.mean(cpu), 2) if cpu else None,
                                "median": round(pct(cpu, .5), 2) if cpu else None,
                                "p90": round(pct(cpu, .9), 2) if cpu else None,
                                "max": round(max(cpu), 1) if cpu else None},
            "game_seconds_mean": round(st.mean(wall_game), 2) if wall_game else None,
            "machines": sorted(map(list, machines), key=str), "limits": sorted(limits)}


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return round(c - h, 4), round(c + h, 4)


def h2h_from_logs(runs: Path, step: str) -> list[dict]:
    out = []
    for f in sorted((runs / step).glob("h2h-*.jsonl")):
        dec = [r for r in logs(f) if r.get("winner") in (0, 1)]
        k = sum(r["winner"] == r["labels"]["better_seat"] for r in dec)
        draws = sum(1 for r in logs(f) if r.get("result") == "draw")
        out.append({"file": f.name, "decided": len(dec), "better_wins": k, "draws": draws,
                    "win_rate": round(k / len(dec), 4) if dec else None, "wilson": wilson(k, len(dec))})
    return out


def fmt_ci(ci):
    return f"[{ci[0]:+.0f}, {ci[1]:+.0f}]" if ci and ci[0] is not None else "—"


def render(runs: Path, rep: dict) -> str:
    s, out = rep["steps"], []
    w = out.append
    w(f"# 阶段 1 健全性检查：数字（自动生成，{runs}）\n")
    w("| 步骤 | 状态 | 判定 |\n|---|---|---|")
    for k in STEPS:
        d = s.get(k)
        if k == "known" and d is None:
            continue
        ok = "—" if d is None else ("过" if d.get("ok", d.get("zero_sum", {}).get("ok")) else "**没过**")
        if k in C.KNOWN and d:
            ok = "排序过（量值另看）" if all(d["order_right_leaderboard"]) and d["order_right_evaluator"] and all(d["runs_agree"]) \
                else "**没过**"
        w(f"| {ZH[k]} | {'跑完' if d else '没有结果'} | {ok} |")
    if b := s.get("baseline"):
        w(f"\n## 基线天梯\n\n分出胜负 {b['games']} 局，平局 {b['draws']} 局，用时 {b['seconds'] / 3600:.1f} 小时，μ = {b['mu']}。"
          f"零和：变化之和 {b['zero_sum']['sum_of_changes']}，移出带走 {b['zero_sum']['lost_to_removal']}，"
          f"总分 {b['zero_sum']['total_cr']} / 应为 {b['zero_sum']['expected_total']}。\n")
        w("| 职业 | 成员 | 局数 | 相对 CR | 95% 区间 | 自相关时间（局） | 冻结 CR |\n|---|---|---|---|---|---|---|")
        fz = {f["member"]: f["cr"] for f in b["frozen"]}
        for r in sorted(b["board"], key=lambda r: -r["rel_cr"]):
            w(f"| {r['craft']} | {r['member']} | {r['games']} | {r['rel_cr']:+.0f} | {fmt_ci(r['ci'])} | {r['tau']} "
              f"| {fz.get(r['member'], '—')} |")
        w(f"\n冻结快照 hash {b['frozen_hash']}（各成员最后 1000 局的平均 CR）。")
        if "matching" in b:
            iso = "、".join(b["isolated_at_end"]) or "没有"
            short = "、".join(f"{x['member']}（{x['games']} 局，CR {x['cr']}）" for x in b["short"]) or "没有"
            w(f"匹配规则 {b['matching']}；没用 11-21 基线打过的种子 {b.get('excluded_seeds', 0)} 个。"
              f"结束时够不着任何人（200 以内没人）的：{iso}；因此没打满的：{short}。")
    if r := s.get("replay"):
        w(f"\n## 重放\n\n抽 {r['checked']} 局，逐步重放和逐个决策重放，不一致 {len(r['failed'])} 局。")
    if g := s.get("gate"):
        w("\n## 把关工具自检（真对局）\n\n| 检查 | 结论 | 用了几对 | 预期几对 | 不同局占比 | 不同局 新胜 / 旧胜 | 算力比 |\n"
          "|---|---|---|---|---|---|---|")
        for x in g["results"]:
            dc = x["discordant"] or {}
            w(f"| {x['check']} | {x['verdict']} | {x['pairs']} | {x['expected_pairs'] or '—'} | {x['share'] or '—'} "
              f"| {dc.get('new', '—')} / {dc.get('old', '—')} | {x['compute_ratio']} |")
    for step in C.KNOWN:
        k = s.get(step)
        if not k:
            continue
        eps_list = k.get("eps") or C.KNOWN[step]["eps"]
        w(f"\n## {ZH[step]}：皇家护卫基线卡表，默认打法按比例随机走一步\n\n"
          "| 随机比例 | 天梯：都从 1500 起 | 天梯：起点倒过来 | 两次一致 | 冻结池评估（3 次重复） |\n|---|---|---|---|---|")
        for i, e in enumerate(eps_list):
            a, b2, ev = k["leaderboard"]["all-1500"][i], k["leaderboard"]["reversed"][i], k["evaluator"][i]
            w(f"| {e:.0%} | {a['rel_cr']:+.0f} {fmt_ci(a['ci'])} | {b2['rel_cr']:+.0f} {fmt_ci(b2['ci'])} "
              f"| {'是' if k['runs_agree'][i] else '**否**'} | {ev['rel_cr']:+.0f} {fmt_ci(ev['ci'])} |")
        w(f"\n排序对：天梯 {k['order_right_leaderboard']}，评估 {k['order_right_evaluator']}。\n")
        w("| 相邻两档 | 直接对打局数 | 强的一方胜率 | 95% 区间（Wilson） | 按 §3 折成的分差（8 分 / 点） | "
          "池里的分差（都从 1500 起） |\n|---|---|---|---|---|---|")
        for x, h in zip(k["head_to_head"], rep.get("h2h", {}).get(step, [])):
            lo, hi = h["wilson"]
            w(f"| {x['pair']} | {h['decided']} | {h['win_rate']:.1%} | [{lo:.1%}, {hi:.1%}] | "
              f"{x['cr_gap_8_per_pp']:+.0f} | {x['pool_gap']:+.0f} |")
        if dr := k.get("drift"):
            w("\n各成员窗口前一半、后一半的平均相对 CR（差得多就是还在漂）：\n\n| 成员 | 都从 1500 起 | 起点倒过来 |\n|---|---|---|")
            for m in dr["all-1500"]:
                cells = []
                for run in ("all-1500", "reversed"):
                    x = dr.get(run, {}).get(m)
                    cells.append(f"{x['halves'][0]:+.0f} → {x['halves'][1]:+.0f}（τ {x['tau']}）" if x else "—")
                w(f"| {m} | {cells[0]} | {cells[1]} |")
    if f := s.get("fluct"):
        means = [e["rel_cr"] for e in f["evaluations"]]
        tot = st.mean(means)
        cover = sum(abs(e["rel_cr"] - tot) <= C.L.t975(4) * e["se"] for e in f["evaluations"])   # 5 repeats
        w(f"\n## 波动（皇家护卫基线，冻结池评估 {len(means)} 次）\n\n"
          f"{len(means)} 次结果的标准差 {f['sd_of_evaluations']}，自报标准误的平均 {f['mean_reported_se']}，"
          f"比值 **{f['ratio']}**（合格线 0.7～1.4）。结果从 {min(means):+.1f} 到 {max(means):+.1f}，"
          f"平均 {tot:+.1f}。各次的 95% 区间盖住总平均：{cover} / {len(means)} 次。")
    w("\n## 局、种子和算力\n\n| 部分 | 局 | 结果 | 种子段 | 都在段内 | 每个种子用了几次（次数: 种子数） | 重跑 | "
      "默认打法每步用时（毫秒，均值 / 中位 / p90 / 最长） | 每局用时（秒） | 每局猜测外的牌 |\n"
      "|---|---|---|---|---|---|---|---|---|---|")
    for name, x in rep["games"].items():
        if not x["records"]:
            continue
        c = x["default_step_ms"]
        w(f"| {name} | {x['records']} | {x['results']} | {x['segment'][0]}–{x['segment'][1]} | "
          f"{'是' if x['inside'] else '**否**'} | {x['times_used']} | {x['reruns']} | "
          f"{c['mean']} / {c['median']} / {c['p90']} / {c['max']} | {x['game_seconds_mean']} | "
          f"{x['out_of_guess_per_game']} |")
    mach = sorted({tuple(m) for x in rep["games"].values() for m in x["machines"]})
    lim = sorted({l for x in rep["games"].values() for l in x["limits"]})
    w(f"\n机器和代码（对局日志里记的）：{mach}；限制：{lim}。")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):              # Windows: stdout to a file is cp1252 and can't take 中文
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    runs = Path(a.runs)
    rep = {"steps": {}, "games": {}}
    for k in STEPS:
        p = runs / k / "summary.json"
        if p.exists():
            rep["steps"][k] = json.loads(p.read_text(encoding="utf-8"))
    for name, (rng, files) in groups(runs).items():
        rep["games"][name] = scan(name, rng, files)
    rep["h2h"] = {step: h2h_from_logs(runs, step) for step in C.KNOWN}
    (runs / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    md = render(runs, rep)
    Path(a.out or runs / "report.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
