"""The audit's high-regret points (third design, regret >= 0.10): what the end-of-turn evaluation sees between
the shallow line and the deep one, feature by feature.

    cd <svsim checkout at 9a6ea1c> && PYTHONPATH=. python3 <this> \
        --results analysis/ramp-benchmark/salem_games_shallow_deep_results.jsonl \
        --points analysis/ramp-benchmark/salem_games_shallow_deep_points.json \
        --salem analysis/mirror-regression/salem_games.json --ctrl games_s400.jsonl.gz --out regret_features.jsonl
    python3 <this> --report regret_features.jsonl

At each point the audit's shallow (v2) and deep (mcts:800) moves are chosen again with the audit's seeds
(checked against the stored descriptions); on the same 8 determinizations each line is played to the end of
the turn by v2s with the audit's seeds; at the end the installed "ended" model of the pairing (here the
original ramp mirror's ramp-ramp) is read feature by feature: the standardized value times the coefficient is
that feature's share of the logit. Per point: the logit difference (deep - shallow) averaged over the 8, and
the features with the largest share of it, with the raw difference. The audit's regret is the same evaluation
squashed, so a point with regret >= 0.10 is by construction one the evaluation already tells apart.
Condition: the opponent's 40-card list is known (order and hand not).
"""
import gzip
import json
import math
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/ramp-benchmark")
import shallow_deep as sd  # noqa: E402


def model_for(state, p):
    from svsim.learn.model import ALIASES, matchup_keys
    from svsim.learn.phased import PhasedLearned
    global _PH
    if "_PH" not in globals():
        _PH = PhasedLearned()
    return next(_PH.models[k + ("ended",)] for k in matchup_keys(state, p, ALIASES) if k + ("ended",) in _PH.models)


def shares(model, state, p):
    x = model.inputs(state, p) if hasattr(model, "inputs") else None
    if x is None:
        from svsim.learn.features import features
        x = features(state, p, model.potential, model.version)
    z = [(v - m) / s for v, m, s in zip(x, model.mean, model.std)]
    return list(x), [c * v for c, v in zip(model.coef, z)]


def end_of_turn(agent, search, s, move, seed, p):
    from svsim.core.engine import apply, legal_actions
    t = s.clone()
    apply(t, move)
    search.rng = random.Random(seed)
    search._next = None
    while not t.over and t.active == p:
        apply(t, agent.act(t, legal_actions(t)))
    return t


def job(pt):
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply, legal_actions
    from svsim.core.view import determinize
    from svsim.tools import records
    from svsim.tools.arena import make_agent
    rec, p, seed = pt["record"], pt["side"], sd.SAMPLE_SEED * 1000 + pt["id"]
    st = records.start(rec)
    for a in rec["actions"][:pt["at"]]:
        apply(st, from_dict(a))
    legal = legal_actions(st)
    shallow = make_agent(sd.SHALLOW, 2 * seed).act(st.clone(), legal)
    deep = make_agent(sd.DEEP, 2 * seed + 1).act(st.clone(), legal)
    finish = make_agent(sd.FINISH, 7)
    search = sd.inner_search(finish)
    out = {"id": pt["id"], "who": pt["who"], "stage": pt["stage"], "own_turn": pt["own_turn"],
           "shallow": sd.describe(st, shallow, sd.plain_name), "deep": sd.describe(st, deep, sd.plain_name),
           "stored": pt["stored"]}
    model = model_for(st, p)
    from svsim.learn.features import names
    out["names"] = model.names() if hasattr(model, "names") and callable(model.names) else names(model.potential, model.version)
    xs, xd, cs, cd, ended = [], [], [], [], 0
    for j in range(sd.K):
        d = determinize(st, p, random.Random(seed * 1000 + 500 + j))
        ts = end_of_turn(finish, search, d, shallow, seed * 1000 + 700 + j, p)
        td = end_of_turn(finish, search, d, deep, seed * 1000 + 700 + j, p)
        if ts.over or td.over:
            ended += 1
            continue
        a, b = shares(model, ts, p)
        c, e = shares(model, td, p)
        xs.append(a); cs.append(b); xd.append(c); cd.append(e)
    n = len(xs)
    out["ended_games"] = ended
    if n:
        mean = lambda rows: [sum(col) / n for col in zip(*rows)]
        out["dx"] = [b - a for a, b in zip(mean(xs), mean(xd))]
        out["dshare"] = [b - a for a, b in zip(mean(cs), mean(cd))]
        out["dlogit"] = sum(out["dshare"])
    return out


def load_points(a):
    res = {(r["who"], r["id"]): r for r in map(json.loads, open(a["results"], encoding="utf-8")) if r.get("regret", 0) >= 0.10}
    pts = json.load(open(a["points"], encoding="utf-8"))
    salem = json.load(open(a["salem"], encoding="utf-8"))["records"]
    ctrl = {}
    for line in gzip.open(a["ctrl"], "rt", encoding="utf-8"):
        g = json.loads(line)
        ctrl[(g["seed"], g.get("g"))] = g
    out = []
    for pt in pts:
        r = res.get((pt["who"], pt["id"]))
        if r is None:
            continue
        pt = dict(pt)
        pt["record"] = salem[pt["ref"]["game"]] if pt["source"] == "salem27" else ctrl[(pt["ref"]["seed"], pt["ref"]["g"])]
        pt["stored"] = {k: r[k] for k in ("shallow", "deep", "regret", "category", "v_shallow", "v_deep")}
        out.append(pt)
    return out


def report(path):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    print("条件：对手卡表已知（牌序、手牌未知）。第三版审计里遗憾 ≥ 0.10 的点；同 8 个确定化，浅、深两条线由 v2s 收完回合，"
          "回合末按装机的 ended 模型（原版跳费龙镜像 ramp-ramp）逐个特征读：份额 = 标准化值 × 系数；差 = 深 − 浅，8 个平均。\n")
    tot = {}
    for r in sorted(rows, key=lambda r: -r["stored"]["regret"]):
        same = r["shallow"] == r["stored"]["shallow"] and r["deep"] == r["stored"]["deep"]
        top = sorted(range(len(r.get("dshare", []))), key=lambda i: -abs(r["dshare"][i]))[:5]
        print(f"- **{r['who']} #{r['id']}**（{r['stage']}，{r['stored']['category']}，遗憾 {r['stored']['regret']:+.3f}，"
              f"logit 差 {r.get('dlogit', float('nan')):+.2f}{'' if same else '，**选的步和审计记录不同**'}"
              f"{'，' + str(r['ended_games']) + ' 个确定化回合内终局' if r['ended_games'] else ''}）：浅「{r['shallow']}」，深「{r['deep']}」")
        for i in top:
            print(f"  - {r['names'][i]}：份额差 {r['dshare'][i]:+.3f}，原值差 {r['dx'][i]:+.2f}")
        for i, v in enumerate(r.get("dshare", [])):
            tot.setdefault(r["stored"]["category"], {}).setdefault(r["names"][i], []).append(v)
    print("\n**按类型：份额差的平均（取绝对值最大的 6 个特征）**\n")
    for cat, feats in sorted(tot.items()):
        avg = {k: sum(v) / len(v) for k, v in feats.items()}
        top = sorted(avg, key=lambda k: -abs(avg[k]))[:6]
        n = len(next(iter(feats.values())))
        print(f"- {cat}（{n} 点）：" + "；".join(f"{k} {avg[k]:+.3f}" for k in top))


def main():
    if "--report" in sys.argv:
        report(sys.argv[sys.argv.index("--report") + 1])
        return
    arg = lambda k: sys.argv[sys.argv.index(k) + 1]
    pts = load_points({k: arg("--" + k) for k in ("results", "points", "salem", "ctrl")})
    workers = int(arg("--workers")) if "--workers" in sys.argv else 4
    with Pool(workers) as pool, open(arg("--out"), "w", encoding="utf-8") as fh:
        for r in pool.imap_unordered(job, pts, chunksize=1):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
    print(f"{len(pts)} 个点")


if __name__ == "__main__":
    main()
