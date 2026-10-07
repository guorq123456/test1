"""Put bot versions on one scale from the gate's results (learn.league: Bradley–Terry).

    python -m svsim.tools.league --match NEW OLD gate-1234.jsonl --match NEWER NEW gate-5678.jsonl
    python -m svsim.tools.league --manifest league.json --anchor OLD=1700 --anchor salem=2050

Each --match names the gate's A and B (any labels) and its results file; a
manifest is a JSON list of {"a": ..., "b": ..., "file": ...}. Prints each
version's games, strength (logit, the reference version at 0) with a 95%
interval from resampling whole pairs, and a CR reading: CR = offset + slope *
strength, the slope fitted to two or more anchors, else --slope (default 200
per logit, the ladder's rule near even), the offset from one anchor, else the
reference at 0 (relative CR).
"""
from __future__ import annotations

import argparse
import json

from svsim.learn import league as L


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--match", nargs=3, action="append", default=[], metavar=("A", "B", "FILE"))
    parser.add_argument("--manifest", default=None, help='JSON list of {"a", "b", "file"}')
    parser.add_argument("--ref", default=None, help="the version held at 0 (default: the first named)")
    parser.add_argument("--anchor", action="append", default=[], metavar="NAME=CR")
    parser.add_argument("--slope", type=float, default=L.CR_PER_LOGIT, help="CR per logit without two anchors")
    parser.add_argument("--bootstrap", type=int, default=500, help="resamples for the intervals")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    entries = [{"a": a, "b": b, "file": f} for a, b, f in args.match]
    if args.manifest:
        entries += json.load(open(args.manifest, encoding="utf-8"))
    if not entries:
        parser.error("no matches: give --match A B FILE or --manifest")
    matches = [L.read_gate(e["file"], e["a"], e["b"]) for e in entries]
    if not L.connected(matches):
        print("警告：版本之间没有全部连通，不连通的部分之间的强度差没有意义。")
    anchors = {}
    for text in args.anchor:
        name, _, cr = text.partition("=")
        anchors[name] = float(cr)
    ratings = L.fit(matches, args.ref)
    ranges = L.bootstrap(matches, args.ref, args.bootstrap, args.seed)
    crs, slope, offset = L.to_cr(ratings, anchors, args.slope)
    games = {n: 0 for n in ratings}
    for m in matches:
        _, g = m.totals()
        games[m.a] += g
        games[m.b] += g
    ref = args.ref or next(iter(ratings))
    used = [n for n in anchors if n in ratings]
    how = (f"斜率按 {len(used)} 个锚点拟合：{slope:.0f} CR/logit" if len(used) >= 2 else
           f"斜率 {slope:.0f} CR/logit，偏移由锚点 {used[0]} 定" if used else
           f"斜率 {slope:.0f} CR/logit，相对 {ref}（记作 0）")
    print(f"{'版本':<40} {'局数':>6} {'强度 logit':>12} {'95% 区间':>18} {'CR':>8} {'CR 区间':>16}")
    for n in sorted(ratings, key=lambda x: -ratings[x]):
        lo, hi = ranges[n]
        print(f"{n:<40} {games[n]:>6} {ratings[n]:>+12.3f} {f'{lo:+.3f}～{hi:+.3f}':>18} "
              f"{crs[n]:>8.0f} {f'{offset + slope * lo:.0f}～{offset + slope * hi:.0f}':>16}")
    print(how)
    for m in matches:
        w, g = m.totals()
        print(f"  {m.a} 对 {m.b}：{g} 局，{m.a} 得分 {w / g:.1%}" if g else f"  {m.a} 对 {m.b}：0 局")


if __name__ == "__main__":
    main()
