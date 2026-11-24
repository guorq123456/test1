"""S31 (Salem 11-24 20:48Z, decision card 「改，3 份记成没过」): a strategy update whose gate stopped with the old
gate tool's error "a gap of D pp can't happen with a discordant share of S" (S <= D / 100: H1 can't happen, the fixed
ladder/gate.py says "not passed" at once) is recorded as not passed, without new games. Period 2: S-0046, S-0054,
S-0061 (LD-77). Nothing is played, no seed is used.

    python analysis/ladder/tools/gate_settle.py S-0046 S-0054 S-0061 --out OUT [--host C:\\claude\\ladder-host]
                                                [--players C:\\claude\\ladder-players] [--write]

Without --write it only reads and says what it would write (OUT/summary.json). For each receipt it checks:
- an accepted update (收下, kind update) with no "gated" line yet, and a gate-failed line of the collection loop
  (SUBS/collect.jsonl) holding that error; D must be the period's delta (HOST/gates/delta-P<period>.json);
- the stopped attempt in the gate ledger (HOST/gates/gates.jsonl; one stopped after its games but before its line is
  named first, as the next gate would: gate.record_interrupted): its member and new version are the receipt's; if it
  played the share pre-run, the share is worked out again from its games (gate.Gate._outcome, floor 0.05) and must
  be S; with no games, S must be a share the ledger already held for the member (the gate takes the last one);
- the version it was against: the attempt's "old" and the pool's history at the time of the error must agree;
- S <= D / 100.
With --write, under the submissions ledger's lock, for each: a gate-ledger line (the next G- number, kind better,
verdict "not passed", pairs 0, seeds_used [], settles = the attempt; GATES.md row by gate.append_ledger), a "gated"
line in the submissions ledger (as submit.gate_update writes it, plus settled S31 and the attempt), the player's
gate note; then submit.deliver hands the notes and status to the players' receipts folders. Run it once: a receipt
that already has a "gated" line is refused.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LADDER = HERE.parent
ROOT = LADDER.parents[1]
sys.path[:0] = [str(LADDER), str(ROOT)]

ERROR = re.compile(r"a gap of ([0-9.]+) pp can't happen with a discordant share of ([0-9.eE+-]+)")


class SettleError(Exception):
    pass


def _jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def pre_share(games: Path) -> tuple[float, int, int] | None:
    """The discordant share of an attempt's share pre-run, as the gate worked it out: (max(0.05, discordant / valid),
    discordant, valid); None if it played no pre pair."""
    by = {}
    for l in games.read_text(encoding="utf-8", errors="replace").splitlines():
        l = l.strip(" \t\r\n\x00")
        if not l:
            continue
        try:
            g = json.loads(l)
        except ValueError:
            continue
        lab = g.get("labels") or {}
        if "-pre" not in str(g.get("id", "")) or "pair" not in lab:
            continue
        by.setdefault(lab["pair"], {})[lab["side"]] = (g, lab.get("member_seat"))
    if not by:
        return None
    disc = valid = 0
    for sides in by.values():
        if set(sides) != {"new", "old"}:
            continue                                   # a pair still out when it stopped: the gate had no outcome
        (a, seat), (b, _) = sides["new"], sides["old"]
        if a["result"] == "void" or b["result"] == "void":
            continue
        won = [(r["winner"] == seat) if r["winner"] in (0, 1) else None for r in (a, b)]
        valid += 1
        if won[0] != won[1]:
            disc += 1
    return max(0.05, disc / max(1, valid)), disc, valid


def plan(host: Path, rids: list[str], name_stopped: bool) -> dict:
    """What would be written for each receipt, or the problems. `name_stopped`: write the gate-ledger line of an
    attempt stopped before its line (only with --write; the dry run names it in memory)."""
    from ladder import gate as G
    from ladder.pool import Pool
    from ladder.submit import code_fingerprint, ledger
    subs, gates = host / "subs", host / "gates"
    lines = ledger(subs)
    log = _jsonl(subs / "collect.jsonl")
    gl = G.read_ledger(gates)
    if name_stopped:
        named = G.record_interrupted(gates, gl, gates)
    else:                                              # the same, on a scratch copy of the ledger
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            for f in ("gates.jsonl", "GATES.md"):
                if (gates / f).exists():
                    shutil.copy(gates / f, Path(t) / f)
            named = G.record_interrupted(gates, list(gl), Path(t))
    gl = gl + named
    pool = Pool(host / "pool")
    out, problems, next_n = [], [], len(gl) + 1
    for rid in rids:
        bad = []
        rec = next((l for l in lines if l.get("ev") == "receipt" and l.get("id") == rid), None)
        if rec is None or rec.get("verdict") != "收下" or rec.get("kind") != "update":
            problems.append(f"{rid}：不是收下的打法更新")
            continue
        if any(l.get("ev") == "gated" and l.get("receipt") == rid for l in lines):
            problems.append(f"{rid}：已经有检验结果了，不再补记")
            continue
        fails = [l for l in log if l.get("ev") == "gate-failed" and l.get("receipt") == rid]
        hit = [(l, ERROR.search(l.get("error", ""))) for l in fails]
        hit = [(l, m) for l, m in hit if m]
        if not hit:
            problems.append(f"{rid}：collect.jsonl 里没有这个错误（{[l.get('error', '')[-120:] for l in fails]}）")
            continue
        fail, m = hit[-1]
        gap, share = float(m.group(1)), float(m.group(2))
        delta = json.loads((gates / f"delta-P{rec['period']}.json").read_text(encoding="utf-8"))["delta"]
        if abs(gap - delta) > 1e-9:
            bad.append(f"出错时的 H1 {gap} pp 不是这一期的 delta {delta}")
        if delta / 100 < share:
            bad.append(f"不同局占比 {share} 大于 delta {delta} pp：修好的工具会照常检验，不能补记")
        mid, spec = rec["mid"], rec["spec"]
        att = [r for r in gl if r.get("interrupted") and r.get("member") == mid and r.get("new") == spec]
        attempt, how = None, {}
        if len(att) > 1:
            bad.append(f"停下的检验有 {len(att)} 次：{[r['gate'] for r in att]}")
        elif att:
            attempt = att[0]
            ps = pre_share(gates / attempt["gate"] / "games.jsonl")
            if ps is None:
                bad.append(f"{attempt['gate']} 有局但没有测占比的对")
            else:
                how = {"measured_on": ps[2], "discordant": ps[1]}
                if abs(ps[0] - share) > 1e-9:
                    bad.append(f"{attempt['gate']} 的局算出来的占比 {ps[0]:.4f}，和出错时的 {share} 不一样")
        else:                                          # no game played: the share came from the ledger
            held = [r for r in gl if r.get("member") == mid and r.get("discordant_share")]
            if not any(abs(r["discordant_share"] - share) < 1e-9 for r in held):
                bad.append(f"没有局，台账里这个成员也没有 {share} 这个占比")
            how = {"from_ledger": [r["gate"] for r in held if abs(r["discordant_share"] - share) < 1e-9][-1:]}
        # the version it was against: the pool's history at the time of the error
        mem = pool.members.get(mid)
        if mem is None:
            problems.append(f"{rid}：池子里没有 {mid}")
            continue
        passed_at = {l["gate"]: l["time"] for l in lines if l.get("ev") == "gated" and l.get("verdict") == "passed"
                     and l.get("gate")}
        then = [h for h in mem.history if h[4] is None or passed_at.get(h[4], "9999") < fail["time"]]
        old = then[-1][1] if then else None
        if attempt is not None and attempt.get("old") != old:
            bad.append(f"停下的那次和旧版 {attempt.get('old')} 比，池子的记录那时是 {old}")
        meta = json.loads((subs / rid / "submission.json").read_text(encoding="utf-8"))
        change, prediction = meta["change"], meta["prediction"]
        route = rec.get("route") or {}
        if route:
            change = f"多步改法（{route['steps']} 步，停在第 {route['step']} 步）：{change}"
        if attempt is not None and (attempt.get("change"), attempt.get("prediction")) != (change, prediction):
            bad.append("停下的那次记的改动说明、预测和回执的不一样")
        if bad:
            problems += [f"{rid}：{b}" for b in bad]
            continue
        failed = {l["receipt"]: l["gate"] for l in lines if l.get("ev") == "gated" and l.get("mid") == mid
                  and l.get("gate") and l.get("verdict") != "passed" and l.get("old") == old}
        fp = code_fingerprint((subs / "code" / f"{spec.split(':')[1]}.py").read_text(encoding="utf-8"),
                              spec.split(":")[2])
        gid = f"G-{next_n:04d}"
        next_n += 1
        src = attempt["gate"] if attempt else "（没打局，占比是台账里的）"
        g = {"gate": gid, "date": time.strftime("%m-%d"), "member": mid, "anon": mem.anon, "craft": mem.craft,
             "kind": "better", "new": spec, "old": old, "change": change, "prediction": prediction,
             "resubmit_of": failed.get(meta.get("resubmit_of")), "since": str(meta.get("since") or ""),
             "hypotheses": f"H0 +0 pp / H1 {delta:+g} pp，不同局占比 {share:.3f}", "discordant_share": round(share, 4),
             "llr": None, "discordant": None, "verdict": "not passed",
             "estimate_note": (f"补记（S31）：{src} 在旧的检验工具里出错停了（{fail['time']}），没有结论；不同局占比只有 "
                               f"{share:.3f}，全赢也最多 {100 * share:.1f} pp，到不了 {delta:g} pp 的假设：直接判没过，不再打"),
             "seed_note": "没有新打的局（S31 补记）", "opponents_note": "—", "opponents": {}, "opponents_discordant": {},
             "seeds_used": [], "pairs": 0, "pre_pairs": 0, "settles": attempt["gate"] if attempt else None,
             "share_source": how, "settled_by": "S31"}
        s = {"ev": "gated", "receipt": rid, "player": rec["player"], "member": rec["member"], "mid": mid,
             "gate": gid, "verdict": "not passed", "old": old, "new": spec, "fingerprint": fp,
             "settled": "S31", "attempt": attempt["gate"] if attempt else None, "failed_at": fail["time"]}
        out.append({"receipt": rid, "player": rec["player"], "gate_line": g, "subs_line": s})
    return {"settle": out, "problems": problems, "named_stopped": [r["gate"] for r in named]}


NOTE = ("第 2 期截止后检验这一份时，主持方的检验工具出错停了，当时没有结论，现在补记。"
        "结论：检验没过，池子里还是原来那一版。新旧两版打出来的结果几乎都一样，结果不一样的对局太少，"
        "就算这些全赢，提升也到不了这一期要求的幅度，所以不再打，直接判没过（Salem 定的）。"
        "再交这个成员的更新，要写 resubmit_of（{rid}）和 since（实质改了什么），见 submit.md 第一节。")


def settle(host: Path, players: Path, rids: list[str], write: bool) -> dict:
    from ladder import gate as G
    from ladder.submit import _append, _ledger_lock, deliver, gate_note
    subs = host / "subs"
    if not write:
        return dict(plan(host, rids, name_stopped=False), written=False)
    with _ledger_lock(subs.resolve()):
        res = plan(host, rids, name_stopped=True)
        if res["problems"]:
            return dict(res, written=False)
        for x in res["settle"]:
            G.append_ledger(x["gate_line"], host / "gates")
            _append(subs, dict(x["subs_line"], time=datetime.now(timezone.utc).isoformat(timespec="seconds")))
            gate_note(subs, x["receipt"], NOTE.format(rid=x["receipt"]))
    res["delivered"] = deliver(subs, host / "pool", players)
    return dict(res, written=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("receipts", nargs="+")
    ap.add_argument("--host", type=Path, default=Path(r"C:\claude\ladder-host"))
    ap.add_argument("--players", type=Path, default=Path(r"C:\claude\ladder-players"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--write", action="store_true", help="write (without it: only say what would be written)")
    a = ap.parse_args(argv)
    res = settle(a.host, a.players, a.receipts, a.write)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in res["settle"]:
        print(f"{x['receipt']}（{x['player']}）→ {x['gate_line']['gate']} 没过；停下的那次 {x['gate_line']['settles']}，"
              f"占比 {x['gate_line']['discordant_share']}")
    for p in res["problems"]:
        print("问题：" + p)
    print(("写好了" if res["written"] else "没写（" + ("有问题" if res["problems"] else "空跑，加 --write 才写") + "）")
          + f"：{a.out / 'summary.json'}")
    return 0 if not res["problems"] else 1


if __name__ == "__main__":
    sys.exit(main())
