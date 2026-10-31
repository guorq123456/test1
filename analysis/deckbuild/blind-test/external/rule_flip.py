"""How much would one external deck gain if an unconfirmed rule went the other way? Re-plays the deals of league.py
(same seeds, so each deal is paired with the baseline in runs/external/dfm-cheap.jsonl) with one rule flipped.

Flips (the open points of the set-10 audit, claude/set10-audit analysis/set10-audit/audit-2026-10-31.md):
  multi-engage   a Clue amulet may Engage more than once a turn (engine: once per amulet per turn)
  mugger-pp      Obliviationist Mugger always gains 1 max PP and Collection Manifest always draws (the JA text
                 puts them in their own sentence; the script follows the EN reading, only after a discarded Clue)

    python analysis/deckbuild/blind-test/external/rule_flip.py analysis/deckbuild/blind-test/external/dfm-2026-10-31.txt \
        --flip multi-engage --decks RUNE --out runs/external/flip-multi-engage.jsonl
    python analysis/deckbuild/blind-test/external/rule_flip.py ... --report

Sensitivity test only: the default rules are not changed. Condition: 对手卡表已知（牌序、手牌未知）.
"""
import argparse
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from svsim.core import engine  # noqa: E402
from svsim.cards import dragon  # noqa: E402
from svsim.cards import common  # noqa: E402,F401
from svsim.core import effects as E  # noqa: E402
from svsim.core.engine import Engage, _mode_sets, _target_sets, script_for  # noqa: E402
from svsim.tools import deckbuild as DB  # noqa: E402
import league  # noqa: E402

BASE = Path("runs/external/dfm-cheap.jsonl")


def _engage_any_number(state, p):
    actions = []
    for amulet in p.field:
        script = script_for(amulet.defn.card_id)
        if script.engage is None or script.engage_cost is None or script.engage_cost > p.pp:
            continue
        target_sets = _target_sets(state, p.index, script.engage_targets, required=False, source=amulet.uid)
        mode_sets = _mode_sets(script.engage_modes, False)
        actions += [Engage(amulet.uid, t, m) for t in target_sets for m in mode_sets]
    return actions


def _mugger_fanfare(self, ctx):
    dragon._discard_random_clue(ctx)
    E.gain_max_pp(ctx.state, ctx.controller)


def _manifest_cast(self, ctx):
    E.damage(ctx.state, dragon._random_enemy_follower(ctx), 4, ctx.source)
    dragon._discard_random_clue(ctx)
    E.draw_matching(ctx.state, ctx.controller, lambda c: c.defn.cost >= 5)


def apply(flip):
    if flip == "multi-engage":
        engine._engage_actions = _engage_any_number
    elif flip == "mugger-pp":
        dragon.ObliviationistMugger.fanfare = _mugger_fanfare
        dragon.CollectionManifest.cast = _manifest_cast
    else:
        raise SystemExit(f"unknown flip {flip}")


def paired(rows, base):
    b = {(r["ref"], r["opp"], r["seed"]): r["score"] for r in base}
    by = {}
    for r in rows:
        k = (r["ref"], r["opp"], r["seed"])
        if k in b:
            by.setdefault(r["ref"], {}).setdefault(r["opp"], []).append((r["score"], b[k]))
    for ref, opps in by.items():
        per = [sum(x - y for x, y in v) / len(v) for v in opps.values()]
        new = [x for v in opps.values() for x, _ in v]
        old = [y for v in opps.values() for _, y in v]
        m = sum(per) / len(per)
        se = math.sqrt(sum((p - m) ** 2 for p in per) / max(1, len(per) - 1)) / math.sqrt(len(per))
        print(f"{ref:24s} 基线 {100 * sum(old) / len(old):5.1f} → 翻转后 {100 * sum(new) / len(new):5.1f}，"
              f"变化 {100 * m:+5.1f} ± {196 * se:.1f}（{len(new)} 个发牌，按对手卡组配对）")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ref")
    ap.add_argument("--flip", required=True)
    ap.add_argument("--decks", nargs="*", default=[], help="classes of the reference decks to re-play")
    ap.add_argument("--out", required=True)
    ap.add_argument("--deals", type=int, default=10)
    ap.add_argument("--spec", default="mcts:100+plan")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    rows = [json.loads(t) for t in out.read_text().splitlines() if t.strip()] if out.exists() else []
    if args.report:
        paired(rows, [json.loads(t) for t in BASE.read_text().splitlines() if t.strip()])
        return
    apply(args.flip)
    ref = DB.read_seeds(args.ref)
    roster = DB.read_seeds(str(league.ROSTER))
    done = {(r["ref"], r["opp"], r["seed"]) for r in rows}
    todo = [j for j in league.jobs(ref, roster, args.deals, args.spec)
            if any(c in j[0][0] for c in args.decks) and (j[0][0], j[0][1], j[3]) not in done]
    print(f"flip {args.flip}: {len(done)} done, {len(todo)} to play", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a") as fh, Pool(args.workers, initializer=DB._nice) as pool:
        for n, res in enumerate(pool.imap_unordered(DB.play_deal, todo, chunksize=2), 1):
            rl, ol = res["key"]
            fh.write(json.dumps({"ref": rl, "opp": ol, "seed": res["seed"], "spec": args.spec, "flip": args.flip,
                                 "points": res["points"], "score": sum(res["points"]) / 2}, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 100 == 0:
                print(f"{n}/{len(todo)}", flush=True)


if __name__ == "__main__":
    main()
