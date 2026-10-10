"""The stacked gate's extra report (README-stack.md): its point estimate minus each pooled reading (cand-kc's two
gates, +xprune's two gates), and minus the 'fully additive' reference 50 + (kc - 50) + (xprune - 50). Readings are
taken from pooled.py's last line ('pooled pair by pair ...: X% (lo%..hi%)'); SE = interval width / 3.92; the gates'
seeds are independent, so a difference's SE is the root sum of squares, 95% interval normal.
Condition: the opponent's deck list is known (order and hand not).

    python3 stack_read.py ../gates/stack/gate_pooled.txt ../gates/clock/kc_two_gates_pooled.txt ../gates/xprune/two_gates_pooled.txt
"""
import math
import re
import sys


def reading(path):
    line = [x for x in open(path, encoding="utf-8") if x.startswith("pooled pair by pair")][-1]
    p, lo, hi = (float(x) for x in re.search(r": ([\d.]+)% \(([\d.]+)%\.\.([\d.]+)%\)", line).groups())
    return p, (hi - lo) / 3.92


def main():
    s, kc, xp = (reading(p) for p in sys.argv[1:4])
    print("条件：对手卡表已知（牌序、手牌未知）。叠起来那道门的另报（README-stack.md；只作描述）\n")
    print(f"- 本门 {s[0]:.1f}%（SE {s[1]:.2f}）；cand-kc 两门合并 {kc[0]:.1f}%（SE {kc[1]:.2f}）；xprune 两门合并 {xp[0]:.1f}%（SE {xp[1]:.2f}）")
    for name, r in (("cand-kc 两门合并", kc), ("xprune 两门合并", xp)):
        d = s[0] - r[0]
        se = math.hypot(s[1], r[1])
        print(f"- 本门 − {name}：{d:+.1f} 个百分点（{d - 1.96 * se:+.1f}～{d + 1.96 * se:+.1f}）")
    add = 50 + (kc[0] - 50) + (xp[0] - 50)
    se = math.sqrt(s[1] ** 2 + kc[1] ** 2 + xp[1] ** 2)
    d = s[0] - add
    print(f"- 「两样完全相加」的参照 {add:.1f}%；本门 − 参照：{d:+.1f} 个百分点（{d - 1.96 * se:+.1f}～{d + 1.96 * se:+.1f}）")


if __name__ == "__main__":
    main()
