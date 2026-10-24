"""Reads of the Salem-preference fit (sp_fit.py; the architecture thread 2026-10-10 16:49Z).
Condition: the opponent's deck list is known (order and hand not).

1. Held-out games: each Ramp-mirror turn scored by the fold model that didn't see its game (the chosen lambda), the
   installed model and cand-kc; top-1 and pairwise against the bot; the difference from cand-kc with a 95% interval
   from 2000 resamples of games (seed 0). The other pairings (not fitted) read with the final model, descriptive.
2. The operations positions, all from Salem's games: k 329 / 455 (Salem's end against step 0's bot line and the
   runs' ends, analysis/puzzles3/data/rows_329_455.jsonl) and the bank's puzzles 2 and 3 (Salem's end, as the installed
   mcts:1043 plays it, against cand-kc mcts:997's), scored with the installed model, cand-kc, the final cand-sp and
   the fold model that left that game out.
3. Weights: the standardized coefficients (and per raw unit) of the defense, hand and board columns for the installed
   model, cand-kc and cand-sp.

    python3 sp_read.py TURNS.jsonl FOLDS.json STEP0_DIR ANA_DIR LABELS KC_DATA.npz
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis/salem-pref"))
sys.path.insert(0, str(ROOT / "analysis/puzzles3"))
GAMES = {329: "1791305347029", 455: "1791317476826", 518: "1791387160337", 445: "1791317238047"}
COLUMNS = ("hp", "hp_sqrt", "hp_low", "hand", "followers", "atk", "life", "board_threat", "ep", "sep", "max_pp")


def main():
    turns_path, folds_path, step0, ana = sys.argv[1:5]
    import sp_fit as F
    from svsim.learn.model import LinearValue
    folds = json.loads(Path(folds_path).read_text())
    lam = folds["lambda"]
    F.load(turns_path, sys.argv[5], sys.argv[6])
    D = F.D
    fw = {int(k.split("|")[1]): np.array(v, np.float32) for k, v in folds["fold_weights"].items()
          if float(k.split("|")[0]) == lam}
    kc_w = np.array(D["kc"]["coef"], np.float32)
    final = np.array(folds["final"], np.float32)
    # 1. per turn hits
    def hits(score):
        out = []
        for p in D["P"]:
            z = score(p)
            top = int(len(z) >= 2 and np.argmax(z) == p["s"] and np.sum(z == z[p["s"]]) == 1)
            vb = None if p["b"] is None or p["b"] == p["s"] else int(z[p["s"]] > z[p["b"]])
            out.append((p["game"], top if len(z) >= 2 else None, vb))
        return out
    H = {"installed": hits(lambda p: F._inst_logits(p["raw"])), "cand-kc": hits(lambda p: p["X"] @ kc_w),
         "cand-sp (held out)": hits(lambda p: p["X"] @ fw[p["fold"]])}
    games = sorted({g for g, _, _ in H["cand-kc"]})
    rng = np.random.default_rng(0)
    res = {}
    for m, h in H.items():
        res[m] = {"top1": round(np.mean([t for _, t, _ in h if t is not None]), 4),
                  "vs_bot": round(np.mean([b for _, _, b in h if b is not None]), 4),
                  "n_top1": sum(t is not None for _, t, _ in h), "n_vs_bot": sum(b is not None for _, _, b in h)}
    diffs = {"top1": [], "vs_bot": []}
    by_game = {m: {g: [x for x in h if x[0] == g] for g in games} for m, h in H.items()}
    for _ in range(2000):
        pick = rng.integers(0, len(games), len(games))
        for k, idx in (("top1", 1), ("vs_bot", 2)):
            a = [x[idx] for j in pick for x in by_game["cand-sp (held out)"][games[j]] if x[idx] is not None]
            b = [x[idx] for j in pick for x in by_game["cand-kc"][games[j]] if x[idx] is not None]
            diffs[k].append(100 * (np.mean(a) - np.mean(b)))
    res["cand-sp - cand-kc (points, 95%)"] = {k: [round(float(np.mean(v)), 2), round(float(np.quantile(v, 0.025)), 2),
                                                round(float(np.quantile(v, 0.975)), 2)] for k, v in diffs.items()}
    # other pairings, descriptive (the Ramp mirror's models on other decks)
    turns = [json.loads(l) for l in open(turns_path) if l.strip()]
    other = {}
    for t in turns:
        if t["pairing"] == F.RAMP:
            continue
        pair = "/".join(t["pairing"])
        xs = np.array([c["x"] for c in t["candidates"]], float)
        X = ((xs * D["keep"] - D["mean"]) / D["std"]).astype(np.float32)
        s = next(i for i, c in enumerate(t["candidates"]) if c["salem"])
        b = next((i for i, c in enumerate(t["candidates"]) if c["bot"]), None)
        o = other.setdefault(pair, {"turns": 0, "kc_vs_bot": [], "sp_vs_bot": []})
        o["turns"] += 1
        if b is not None and b != s:
            o["kc_vs_bot"].append(int((X @ kc_w)[s] > (X @ kc_w)[b]))
            o["sp_vs_bot"].append(int((X @ final)[s] > (X @ final)[b]))
    res["other pairings (descriptive, Ramp-mirror models)"] = {
        k: {"turns": v["turns"], "pairs": len(v["kc_vs_bot"]),
            "cand-kc vs bot": round(np.mean(v["kc_vs_bot"]), 3) if v["kc_vs_bot"] else None,
            "cand-sp vs bot": round(np.mean(v["sp_vs_bot"]), 3) if v["sp_vs_bot"] else None} for k, v in other.items()}
    # 2. operations positions
    def lv(w):
        return LinearValue([float(x) for x in w], D["kc"]["mean"], D["kc"]["std"], False, {}, version=2,
                           extras=("kclock",))
    inst = LinearValue.load(F.INSTALLED)
    kc = LinearValue.load(F.KC)
    sp = lv(final)
    import ops
    ops._init(step0, ana)
    import turn_level as TL
    from svsim.core.actions import EndTurn, from_dict
    from svsim.core.engine import apply, legal_actions
    from svsim.search.evaluate import after_end_of_turn
    from svsim.tools.arena import make_agent
    from svsim.tools.puzzles import puzzles
    rows = [json.loads(x) for x in open(ROOT / "analysis/puzzles3/data/rows_329_455.jsonl") if x.strip()]
    ops_out = {}
    for k in (329, 455):
        st = ops.G["starts"][k]
        state, rec = TL._start_state(st)
        me = state.active
        s_end = ops.turn_end(state, TL._salem_turn(rec, st["at"]))
        b_end = ops.turn_end(state, [from_dict(a) for a in next(p for p in ops.G["plans"][k]["plans"] if p["kind"] == "bot")["actions"]])
        runs = [ops.turn_end(state, [from_dict(a) for a in r["actions"]]) for r in rows if r["k"] == k]
        fold = D["fold_of"].get(GAMES[k])
        models = {"installed": inst, "cand-kc": kc, "cand-sp": sp}
        if fold is not None:
            models["cand-sp (fold without this game)"] = lv(fw[fold])
        ops_out[k] = {m: {"salem": round(mod.logit(s_end, me), 3), "bot": round(mod.logit(b_end, me), 3),
                          "right": mod.logit(s_end, me) > mod.logit(b_end, me),
                          "runs Salem beats": sum(mod.logit(s_end, me) > mod.logit(e, me) for e in runs), "runs": len(runs)}
                      for m, mod in models.items()}
    P = {n: b for n, b, a in puzzles()}
    def end_of(build, spec, seed=1):
        s = build(seed); me = s.active; ag = make_agent(spec, seed)
        while not s.over and s.active == me:
            a = ag.act(s, legal_actions(s))
            if isinstance(a, EndTurn):
                return after_end_of_turn(s), me
            apply(s, a)
        return s, me
    for name, k in (("ramp-erntz-normagdala", 518), ("ramp-erntz-spilling", 445)):
        s_end, me = end_of(P[name], "mcts:1043+plan+learned+phased")
        b_end, _ = end_of(P[name], "mcts:997+plan+learned+phased=cand-kc-ramp-ramp")
        fold = D["fold_of"].get(GAMES[k])
        models = {"installed": inst, "cand-kc": kc, "cand-sp": sp}
        if fold is not None:
            models["cand-sp (fold without this game)"] = lv(fw[fold])
        ops_out[name] = {m: {"salem": round(mod.logit(s_end, me), 3), "cand-kc 997 end": round(mod.logit(b_end, me), 3),
                             "right": mod.logit(s_end, me) > mod.logit(b_end, me)} for m, mod in models.items()}
    res["operations positions (ENDED logits)"] = ops_out
    # 3. weights
    names = D["names"]
    def coefs(model_names, coef, std):
        return {n: (round(c, 3), round(c / s, 4)) for n, c, s in zip(model_names, coef, std)}
    ci = coefs(inst.names(), inst.coef, inst.std)
    ck = coefs(names, kc.coef, kc.std)
    cs = coefs(names, sp.coef, sp.std)
    wt = {}
    for side in ("me", "op"):
        for c in COLUMNS:
            n = f"{side}_{c}"
            if n in ck:
                wt[n] = {"installed": ci.get(n), "cand-kc": ck[n], "cand-sp": cs[n]}
    res["weights (standardized, per raw unit)"] = wt
    res["lambda"] = lam
    print(json.dumps(res, ensure_ascii=False, indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else str(o)))


if __name__ == "__main__":
    main()
