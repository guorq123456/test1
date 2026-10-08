"""The ramp-t vs pirate-t turn-end models side by side: installed (B), B' (refit, no features added; level in
its gate) and the three candidates that lost in this cell (C2 hand, C3 six-dim board, C3 hpphase), per raw
feature unit. Lists the old features whose sign B and B' share while all three losing candidates have the
other sign, then the largest moves (numbers only; the architecture thread 18:39).

    cd <checkout with the candidate folders (a4deb96)> && PYTHONPATH=. python3 <this>

Condition: the opponent's 40-card list is known (order and hand not).
"""
from svsim.learn.model import LinearValue
from svsim.learn.phased import folder_of

PAIR = "ramp-t-pirate-t"
MODELS = [("B 现装", None), ("B′", "cand-bprime"), ("C2 hand", "cand-c2-hand"), ("C3 六维", "cand-c3-board"),
          ("C3 hpphase", "cand-c3-hpphase")]


def main():
    base = folder_of(f"cand-bprime-{PAIR}").parent
    W, S = {}, {}
    for name, folder in MODELS:
        m = LinearValue.load((base / f"{folder}-{PAIR}" if folder else base) / f"{PAIR}-ended.json")
        W[name] = m.weights_by_name()
        S[name] = dict(zip(m.names(), m.std))
    old = [n for n in W["B 现装"] if n != "bias" and S["B 现装"][n] > 0]
    lose = [n for n, _ in MODELS[2:]]
    print("条件：对手卡表已知（牌序、手牌未知）。ramp-t 对 pirate-t 的回合末模型，每单位原始特征的系数。"
          "B′ = 同数据、同留出、不加特征的重拟合（门里和现装持平）；后三个是在这格掉分的候选。\n")
    flip = [n for n in old if W["B 现装"][n] * W["B′"][n] > 0 and all(W[x][n] * W["B 现装"][n] < 0 for x in lose)]
    print(f"**B 和 B′ 同号、三个掉分候选全部反号的旧特征**：{len(flip)} 个\n")
    print("| 特征 | 训练数据里的标准差 | " + " | ".join(n for n, _ in MODELS) + " |")
    print("|---|---|" + "---|" * len(MODELS))
    for n in flip:
        print(f"| {n} | {S['B 现装'][n]:.3f} | " + " | ".join(f"{W[x][n]:+.3f}" for x, _ in MODELS) + " |")
    print("\n**系数 × 标准差变化最大的旧特征**（掉分候选三个的平均 − B′，按绝对值排前 12）\n")
    move = lambda n: sum(W[x][n] for x in lose) / 3 * S["B 现装"][n] - W["B′"][n] * S["B 现装"][n]
    print("| 特征 | 每标准差：B / B′ / 三候选平均 | " + " | ".join(n for n, _ in MODELS) + " |")
    print("|---|---|" + "---|" * len(MODELS))
    for n in sorted(old, key=lambda n: -abs(move(n)))[:12]:
        sd = S["B 现装"][n]
        print(f"| {n} | {W['B 现装'][n] * sd:+.3f} / {W['B′'][n] * sd:+.3f} / "
              f"{sum(W[x][n] for x in lose) / 3 * sd:+.3f} | " + " | ".join(f"{W[x][n]:+.3f}" for x, _ in MODELS) + " |")


if __name__ == "__main__":
    main()
