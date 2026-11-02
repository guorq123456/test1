"""Run any value net and/or any move prior (and always the hand-set evaluation) over the acceptance library and
print each item and the pass rate per scoring and per tier (clear / marginal; marginal items never gate alone).

    python analysis/acceptance/run.py [--net NET.npz] [--prior PRIOR.npz] [--deck LABEL] [--only ID ...]

Replaces analysis/resource-value/acceptance.py (claude/deck-search) and analysis/pilot/prior_acceptance.py: the same
positions, now rebuilt from stored action lists (lib.py), plus Salem's 11-01 bunny board. A position whose rebuild no
longer matches its fingerprint is reported and not scored. Checks only: never search, self-play or training data.
Condition: 对手卡表已知（牌序、手牌未知）.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

NAMES = {"turn_end": "回合末", "mid_turn": "回合中", "prior": "先验第一步", "handset": "手写评估"}


def run(net_path=None, prior_path=None, deck=None, only=None, out=print) -> dict:
    net = prior = None
    if net_path:
        from svsim.learn.setnet import load_cached
        net = load_cached(net_path)
    if prior_path:
        from svsim.learn.setpolicy import load_cached as load_prior
        prior = load_prior(prior_path)
    rows, moved = [], []
    for pos in lib.load():
        if deck and pos["deck"] != deck:
            continue
        if only and pos["id"] not in only:
            continue
        try:
            judged = lib.judge(pos, net=net, prior=prior)
        except lib.Moved as e:
            moved.append(pos["id"])
            out(f"位置变了，不计分：{e}")
            continue
        rows.append((pos, judged))
        for name, r in judged.items():
            out(f"{'过' if r['pass'] else '没过'}  {pos['title']}［{NAMES[name]}，{pos.get('tier', 'unassigned')}］："
                f"Salem {r['salem']:.3f}，错的一方 {r['wrong']:.3f}")
    tally = lib.tally(rows)
    for name in lib.SCORINGS:
        if name in tally:
            parts = [f"{tier} {p}/{n}" for tier, (p, n) in sorted(tally[name].items())]
            out(f"通过率［{NAMES[name]}］：" + "，".join(parts))
    if moved:
        out(f"{len(moved)} 个位置变了没计分：{', '.join(moved)}")
    return {"tally": tally, "moved": moved}


def summary_line(net_path=None, prior_path=None, deck=None) -> str | None:
    """One line for a gate report (tools.herogate): the hero deck's pass rates, or None when it has no positions."""
    if not any(p["deck"] == deck for p in lib.load()):
        return None
    lines = []
    res = run(net_path, prior_path, deck=deck, out=lambda s: None)
    for name in lib.SCORINGS:
        if name in res["tally"]:
            lines.append(f"{NAMES[name]} " + " ".join(f"{t} {p}/{n}" for t, (p, n) in sorted(res["tally"][name].items())))
    tail = f"；{len(res['moved'])} 个位置变了没计分" if res["moved"] else ""
    return "验收库（" + deck + "）：" + "；".join(lines) + tail


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--net", default=None)
    ap.add_argument("--prior", default=None)
    ap.add_argument("--deck", default=None, help="only the positions of this deck label")
    ap.add_argument("--only", nargs="*", default=None, help="only these position ids")
    args = ap.parse_args()
    print(f"验收库：{lib.POSITIONS}；网络 {args.net or '-'}；先验 {args.prior or '-'}；对手卡表已知（牌序、手牌未知）")
    run(args.net, args.prior, args.deck, args.only)


if __name__ == "__main__":
    main()
