"""Round-robin matches between agents, in parallel.

    python -m svsim.tools.arena --agents greedy mcts:200 --games 100
    python -m svsim.tools.arena --agents random lethal greedy mcts:200 mcts:800 --games 60

Agents: random, lethal (random + lethal search), greedy (one-ply greedy +
lethal search), mcts:N (ISMCTS with N iterations per decision + lethal search),
mcts-reply:N (the same, playing out the opponent's next turn at the leaves),
greedy-raw / mcts-raw:N (without the lethal search). A "+plan" suffix
(greedy+plan, mcts:200+plan) puts the resource-flow planner in front of the
lethal search; "+threat" makes the evaluation value the next turn's lethal
potential (evaluate.THREAT); "+hand" the same from the hand and amulets
only, leaving out followers the opponent may remove (evaluate.THREAT_HAND);
"+macro" lets the planner propose its most-damage line on turns without
lethal, played when the search's evaluation prefers it (ISMCTS agents only);
"+burst" plays that line when the race clock says it sets up next turn's kill
and holding doesn't (the player's "15 now, 5 next turn"); "+reserve" keeps the
search from spending the win condition (playing a finisher such as Killer
Rhinoceroach, or trading it with a follower) outside lethal and burst lines.
turn:N plans the whole turn (search.turnplan: the best line by the end-of-turn
evaluation, luck averaged, N positions at most) and follows it.
fuel:N plays each turn the line (the mcts:N agent's, digging first, the
planner's burst, passing) that leaves the most fuel: the most damage one turn
could deal after the opponent's reply and two more turns of digging
(agents.fuel_agent; the yardstick that picked the player's turns over the
AI's 39 to 16). impact:N chooses each turn among the mcts:N agent's lines by their impact on
winning (agents.impact_agent: the opponent's answer sampled, then the race
clocks); the other suffixes go to the mcts:N agent.
"+learned" uses each deck's learned evaluation (svsim.learn, tools.learn) where
there is one; "+net" the matchup's value network where there is one (learn.net:
fitted on every position the search scores, inside a turn and at its end);
"+lazy" (with mcts-reply) plays the opponent's turn out only from a turn-end
leaf's second visit on, scoring it as it stands the first time; "+focus" only
below the root's 3 most-visited moves and at most 20 times a decision;
"+gainK" multiplies the network's scores by K (it is calibrated, so its
differences between moves are smaller than the linear models'); "+avgK"
scores a leaf as the mean over K redraws of the cards drawn this turn
(search.mcts, average); "+prior" (or "+priorC") orders and weights the
root's moves by the matchup's policy head (learn.policy, bonus weight C,
0.3 by default); "+mimic=W" (or "+mimic=W:FOLDER", "+mimic=W:FOLDER:C") the same with learn.mimic's
prior, W x the player's head + (1 - W) x the self-play head (bonus weight C; an empty FOLDER is the installed one); "+endnow"
scores a position inside the turn as if the turn ended there (as the
linear models do), except a turn start reached by playing out the reply;
"+mean" backs values up as plain averages instead of the best own choice
(search.mcts, backup="mean"); "+vnet" turn ends scored by the pairing's value network (learn.vnet, from
svsim/learn/vnets; "+vnet=FOLDER" another folder's <deck>-<deck>-vnet.npz), the in-turn score unchanged; "+phased" linear models by moment (learn.phased:
turn ends, and turn starts reached by playing out the reply; "+phased=NAME" this agent's models from
the folder NAME, a path or svsim/learn/phased_models/NAME, learn.phased.folder_of; "+screen=N" the lethal search's budget for a position whose damage estimate falls short (the
estimate is no bound, search.lethal.damage_estimate), "+screen=N:N2:K" ... and N2 nodes when it is short by K or
less (default 200:1000:4, agents.lethal_agent.NEAR; "+screen=200" is the old default); a mirror without
models of its own uses its stand-in's, learn.model.ALIASES (the tournament Ramp Dragon's the Game8 build's),
on by default, "+noalias" off, "+alias" kept as a no-op); "+timing" adds what holding a card is worth until the turn the
player usually plays it (svsim.learn.timing, from their games); "+priced"
prices resources by what they buy (search.prices: the own followers at what
survives the opponent's turn, "+survive" alone; unused evolution points at the
damage they add to the next turn, "+points" alone); "+xprune" (or "+xprune=M:H:ORDER") keeps the search's
discard choices ("select a card in your hand and discard it") to the M most discardable hand cards (2; M + K - 1
for a choice of K) by a cross-turn judgment over H turns (3) of the play-point curve, ORDER when / cost / value
(search.xprune), off by
default. Combined: mcts:200+plan+macro+threat. Each pairing plays both seats and, for --decks starter or
rhino, both decks equally often. --decks rhino is Rhinoceroach Forest
(Unlimited) against Ramp Dragon. Prints win rates with a 95% margin, the
average thinking time per decision and the lethals each agent found.
"""
import argparse
from collections import Counter, defaultdict
from itertools import combinations
from multiprocessing import Pool
import random
import time

from svsim.agents.greedy_agent import GreedyAgent
from svsim.agents.lethal_agent import LethalAgent
from svsim.agents.mcts_agent import MCTSAgent
from svsim.agents.random_agent import RandomAgent
from svsim.cards import decks, library
from svsim.search.evaluate import DEFAULT, THREAT, THREAT_HAND
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Craft

assert library.__all__
CRAFTS = [c for c in Craft if c != Craft.NEUTRAL]


# Named versions (the gate's version table, docs/architecture.md): each passed the gate against the one before.
VERSIONS = {
    # 2026-10-07, against the installed mcts:100+plan+learned: 57.7% +- 3.3% over 600 games; but only even
    # with mcts:200 (49.5% +- 3.7%) at about 1.4x its time: the pipeline's baseline, the reply not shown to help
    "v1": "mcts-reply:100+plan+learned+phased+lazy+focus",
    # the gain of v1 without the reply (the refitted turn-end model, learn.phased), at equal time:
    "v2": "mcts:100+plan+learned+phased",      # vs mcts:100+plan+learned: 56.8% +- 3.5% over 600 games
    "v2s": "mcts:200+plan+learned+phased",     # vs mcts:200+plan+learned: 59.7% +- 3.5% over 600 games
    # v2 with the search's subtree kept between the moves of a turn (+reuse), at v2's time per move (115
    # iterations): vs v2 53.3% +- 2.8% over a fixed 600 games (after the sequential test's H1 at 150);
    # the same at strong (mcts:230+reuse vs v2s) is even (49.2% +- 2.2%), so there is no v2sr
    "v2r": "mcts:115+plan+learned+phased+reuse",
    # the ruler (2026-10-08): v2s with the models installed at 20bcfbe, frozen in phased_models/ruler-20261008 (the
    # CR calibration's fixed reference, never changed; the search code is the current one, see its README), with
    # the opening redraw it had then (elf-t by the rules; the code default went back at 05:27Z)
    "ruler20261008": "mcts:200+plan+learned+phased=ruler-20261008+mull=by:elf-t=rules",
    # the reference rolled with each trainer release (drift checks, comparisons three releases on): Version 15's
    # strong level, its models frozen in phased_models/ref-5558960 and its redraw (the default, elf-t D) pinned
    "ref5558960": "mcts:200+plan+learned+phased=ref-5558960+mull=default",
    # the trainer's normal level since C2 (the hand feature set) went into three pairings (2026-10-08, gated at the
    # strong level only): v2r on Version 15's frozen models and redraw, the same bot as before, until it is gated
    # at 115 iterations
    "v2r5558960": "mcts:115+plan+learned+phased=ref-5558960+reuse+mull=default",
    # the reference after C2 went in (352ae51): the strong level's 24 models frozen in phased_models/ref-352ae51
    "ref352ae51": "mcts:200+plan+learned+phased=ref-352ae51+mull=default",
    # the reference after C3 (hpphase) went into the ramp-t mirror (a6fdf0a): the strong level's models in phased_models/ref-a6fdf0a
    "refa6fdf0a": "mcts:200+plan+learned+phased=ref-a6fdf0a+mull=default",
    # the reference after C3 went into the elf-t mirror too (96790ad): the strong level's models in phased_models/ref-96790ad
    "ref96790ad": "mcts:200+plan+learned+phased=ref-96790ad+mull=default",
}
# The trainer's levels by name (level-fast / level-normal / level-strong / level-original): the specs in
# svsim.ui.session.LEVELS themselves, so a gate or the CR calibration can't play a hand-copied variant.
from svsim.ui.session import LEVELS as _LEVELS    # noqa: E402  (session imports this module only lazily)
VERSIONS.update({f"level-{level}": spec for level, spec in _LEVELS.items()})


def _prior_options(options) -> dict:
    """+prior (or +priorC: weight C of the bonus): the matchup's policy head as the root prior.
    +mimic=W[:FOLDER[:C]]: learn.mimic's mixture, W the player's share, as the root prior (bonus weight C)."""
    mimic = [o for o in options if o.startswith("mimic=")]
    if mimic:
        from svsim.learn.mimic import MimicPrior
        w, folder, c = (mimic[0][len("mimic="):].split(":") + ["", ""])[:3]
        return {"prior": MimicPrior(float(w), folder or None), **({"c_prior": float(c)} if c else {})}
    chosen = [o for o in options if o.startswith("prior")]
    if not chosen:
        return {}
    from svsim.learn.policy import MatchupPrior
    rest = chosen[0][5:]
    return {"prior": MatchupPrior(), **({"c_prior": float(rest)} if rest else {})}


# +complex's calibration (analysis/puzzles3/README.md): K so a turn's compute matches level-strong's (whole turns on
# 300 step-1 starts 1.023, 20 gate pairs 0.993), BETA the share of the turn's first width its later decisions keep.
COMPLEX_K, COMPLEX_BETA = 21.4, 0.4


def _par_options(name: str, options) -> dict:
    """+par=K: the search runs K root-parallel trees in a resident process pool, each built from the same spec
    without +par (search.parallel)."""
    par = [o for o in options if o.startswith("par=")]
    if not par:
        return {}
    k = int(par[0][len("par="):])
    return {"parallel": k, "par_spec": "+".join([name] + [o for o in options if not o.startswith("par=")])}


def _alloc_option(options) -> tuple | None:
    """+alloc=legal:K[:LO:HI]: each decision searches clip(round(K x legal moves), LO, HI) iterations (LO 50, HI
    800) instead of the spec's fixed count, the same compute on average once K is set by tools.search_cost.
    +alloc=bank[:CHUNK:STOP:CAP]: the spec's count per decision, in chunks, stopping once settled and keeping
    what's left for the turn's later decisions (search.mcts ISMCTS._bank_budget); N set by search_cost --games.
    +alloc=self:C[:W:LO:HI]: C x N x legal moves / this game's mean so far (search.mcts ISMCTS._self_budget)."""
    chosen = [o[len("alloc="):] for o in options if o.startswith("alloc=")]
    if not chosen and "complex" in options:        # +complex: alloc=complex at its calibration (analysis/puzzles3)
        return ("complex", COMPLEX_K, COMPLEX_BETA, 50, 1500)
    if not chosen:
        return None
    kind, *args = chosen[0].split(":")
    if kind == "self" and len(args) in (1, 4):     # +alloc=self:C[:W:LO:HI] (W 10, LO 50, HI 800)
        w, lo, hi = (float(args[1]), int(args[2]), int(args[3])) if len(args) == 4 else (10.0, 50, 800)
        return ("self", float(args[0]), w, lo, hi)
    if kind == "complex" and len(args) in (2, 4):  # +alloc=complex:K:BETA[:LO:HI] (LO 50, HI 1500)
        lo, hi = (int(args[2]), int(args[3])) if len(args) == 4 else (50, 1500)
        return ("complex", float(args[0]), float(args[1]), lo, hi)
    if kind == "bank" and len(args) in (0, 3):     # +alloc=bank[:CHUNK:STOP:CAP] (50, 0.8, 400; at most 800)
        chunk, stop, cap = (int(args[0]), float(args[1]), int(args[2])) if args else (50, 0.8, 400)
        return ("bank", chunk, stop, cap, 800)
    if kind != "legal" or len(args) not in (1, 3):
        raise ValueError(f"alloc=legal:K[:LO:HI], alloc=self:C[:W:LO:HI], alloc=complex:K:BETA[:LO:HI] or alloc=bank[:CHUNK:STOP:CAP], "
                         f"not {chosen[0]!r}")
    lo, hi = (int(args[1]), int(args[2])) if len(args) == 3 else (50, 800)
    return ("legal", float(args[0]), lo, hi)


def _infer_option(options) -> tuple | None:
    """+infer=ALPHA[:TAU]: the opponent's hand drawn with weight ALPHA on what they could and clearly should have
    played last turn (search.infer; TAU in evaluation points, default 0)."""
    chosen = [o[len("infer="):].split(":") for o in options if o.startswith("infer=")]
    if not chosen:
        return None
    return (float(chosen[0][0]), float(chosen[0][1]) if len(chosen[0]) > 1 else 0.0)


def make_agent(spec: str, seed: int):
    """The agent `spec` names; "+mull=WAY" redraws its opening hand that way (agents.mulligan.decide:
    default, rules[:VARIANT,...], sim[:N[:H]]) and changes nothing else."""
    parts = spec.split("+")
    if parts[0] in VERSIONS:                       # a version first: its own options may set the redraw (the ruler)
        parts = VERSIONS[parts[0]].split("+") + parts[1:]
    mull = [p[len("mull="):] for p in parts if p.startswith("mull=")]
    agent = _make_agent("+".join(p for p in parts if not p.startswith("mull=")), seed)
    if mull:
        from svsim.agents.mulligan import MulliganMode
        agent = MulliganMode(agent, mull[0], seed)
    return agent


def _make_agent(spec: str, seed: int):
    if spec.split("+")[0] in VERSIONS:                         # v1+X: the version with X added
        head, *rest = spec.split("+")
        spec = "+".join([VERSIONS[head]] + rest)
    spec, *options = spec.split("+")
    unknown = set(options) - {"plan", "threat", "hand", "macro", "learned", "timing", "burst", "reserve", "ready",
                              "pace", "burst2", "patient", "dig", "dig2", "survive", "points", "priced", "enhance", "net", "lazy", "focus", "endnow", "mean", "phased", "reuse", "alias", "noalias", "oracle", "vnet", "tick", "lethal2", "lethal3", "plannerfix", "eot", "discard", "adaptive", "abs", "abs0", "complex", "xprune"} - {o for o in options if o.startswith(("hp", "gain", "avg", "prior", "cross", "pick", "phased=", "screen=", "mimic=", "alloc=", "infer=", "vnet=", "par=", "xprune="))}
    if unknown:
        raise ValueError(f"unknown agent options {sorted(unknown)}")
    planner = "plan" in options
    weights = THREAT_HAND if "hand" in options else THREAT if "threat" in options else DEFAULT
    if "ready" in options:                         # the hand's next-turn damage by the player's formula
        from dataclasses import replace
        weights = replace(weights, ready=0.5, ready_lethal=6.0)
    from svsim.learn.model import ALIASES
    aliases = None if "noalias" in options else ALIASES    # a mirror without models plays its stand-in's
    if "learned" in options:                       # each deck's learned evaluation (svsim.learn)
        from svsim.learn.model import Learned
        weights = Learned(fallback=weights, aliases=aliases)
    phased = [o for o in options if o == "phased" or o.startswith("phased=")]
    if phased:                                     # linear models by moment (learn.phased, $SVSIM_PHASED)
        from svsim.learn.phased import PhasedLearned, folder_of, load
        name = phased[0][len("phased="):]          # phased=NAME: that folder's models, for this agent only
        weights = PhasedLearned(models=load(folder_of(name)) if name else None,
                                fallback=weights if "learned" in options else None, aliases=aliases)
    if "net" in options:                           # the matchup's value network, any moment of a turn (learn.net)
        from svsim.learn.net import NetLearned
        gain = [float(o[4:]) for o in options if o.startswith("gain")]
        weights = NetLearned(fallback=weights if "learned" in options else None, gain=gain[0] if gain else 1.0,
                             end_now="endnow" in options)
    vnet = [o for o in options if o == "vnet" or o.startswith("vnet=")]
    if vnet:                                       # turn ends by the pairing's value network (learn.vnet); the
        from svsim.learn.vnet import VNETS, VNetEnded, load_vnets   # in-turn score as before
        name = vnet[0][len("vnet="):]
        if name:
            from svsim.learn.phased import folder_of
            nets = load_vnets(folder_of(name))
        else:
            nets = load_vnets(VNETS)
        weights = VNetEnded(weights, nets, aliases)
    if "timing" in options:                        # holding cards until the player would play them
        from svsim.learn.timing import Timed
        weights = Timed(base=weights)
    if {"survive", "points", "priced"} & set(options):   # shadow prices (search.prices)
        from svsim.search.prices import Priced
        weights = Priced(base=weights, survival=bool({"survive", "priced"} & set(options)),
                         points=bool({"points", "priced"} & set(options)))
    name, _, arg = spec.partition(":")
    if name == "random":
        return RandomAgent(seed, 0.2)
    if name == "lethal":
        return LethalAgent(RandomAgent(seed, 0.2), seed=seed, planner=planner)
    if name == "greedy-raw":
        return GreedyAgent(seed, weights=weights)
    if name == "greedy":
        return LethalAgent(GreedyAgent(seed, weights=weights), seed=seed, planner=planner)
    if name == "turn":                             # whole-turn planner (search.turnplan)
        from svsim.search.turnplan import TurnPlanAgent
        return LethalAgent(TurnPlanAgent(int(arg or 5000), seed=seed, weights=weights), seed=seed,
                           planner=planner)
    if name == "turns":                            # cross-turn planning (agents.turns_agent)
        from svsim.agents.turns_agent import TurnsAgent
        base = make_agent("+".join([f"mcts:{arg or 200}"] + options), seed)
        return TurnsAgent(base, seed=seed)
    if name == "fuel":                             # each turn's line by the fuel it leaves (agents.fuel_agent)
        from svsim.agents.fuel_agent import FuelAgent
        hp = [o for o in options if o.startswith("hp")]
        base = make_agent("+".join([f"mcts:{arg or 100}"] + [o for o in options if o not in hp]), seed)
        return FuelAgent(base, seed=seed, hp_weight=float(hp[0][2:]) if hp else 0.0)
    if name == "impact":                           # turns chosen by their impact (agents.impact_agent)
        from svsim.agents.impact_agent import ImpactAgent
        base = make_agent("+".join([f"mcts:{arg or 200}"] + options), seed)
        return ImpactAgent(base, seed=seed)
    if name in ("mcts", "mcts-raw", "mcts-reply"):
        vetoes = []
        if "pace" in options:                      # not before the player's usual turn (learn.timing.Pace)
            from svsim.learn.timing import Pace
            vetoes.append(Pace())
        if "patient" in options:                   # a Combo card waits for its Combo (search.moves.wasted_combo)
            from svsim.search.moves import wasted_combo
            vetoes.append(wasted_combo)
        if "enhance" in options:                   # an Enhance card waits for its Enhance (search.moves.wasted_enhance)
            from svsim.search.moves import wasted_enhance
            vetoes.append(wasted_enhance)
        xprune = [o for o in options if o == "xprune" or o.startswith("xprune=")]
        if xprune:                                 # discard choices kept to the most discardable cards (search.xprune)
            from svsim.search.xprune import XPrune
            parts = xprune[0][len("xprune="):].split(":") if "=" in xprune[0] else []
            vetoes.append(XPrune(*[int(x) if i < 2 else x for i, x in enumerate(parts)]))   # M:H:ORDER
        veto = (lambda s, a: any(v(s, a) for v in vetoes)) if vetoes else None
        agent = MCTSAgent(int(arg or 400), seed=seed, reply=name == "mcts-reply", weights=weights,
                          backup="mean" if "mean" in options else "max",
                          reserve="reserve" in options, veto=veto, reply_after=1 if "lazy" in options else 0,
                          reply_top=3 if "focus" in options else 0, reply_budget=20 if "focus" in options else 0,
                          average=next((int(o[3:]) for o in options if o.startswith("avg")), 1),
                          reuse="reuse" in options, alloc=_alloc_option(options), infer=_infer_option(options),
                          oracle="oracle" in options,          # an experiment only: sees the opponent's hand
                          **({"center": False, "normalize": True} if "abs" in options else {}),   # +abs
                          **({"center": False} if "abs0" in options else {}),   # +abs0: absolute values only
                          **_par_options(spec, options),       # +par=K: K root-parallel trees (search.parallel)
                          **_prior_options(options))
        cross = [o for o in options if o.startswith("cross")]
        if cross:                                  # keep a card / PP / evolution for later (agents.crossturn_agent)
            from svsim.agents.crossturn_agent import CrossTurnAgent
            import re
            # +crossnK: score after the own next turn (ENDED model); +crosssK: no play-out, the own turn's end
            # (a control); ...zZ: switch only past Z standard errors; ...rN: a restriction's turn from its own
            # search of N iterations
            # ...k<letters>: only these restrictions (k keep a card, s keep the bonus PP, e don't evolve)
            # ...rt: a restriction's turn from the base search's own tree; ...mN: keep candidates for the
            # line's N dearest cards only
            # ...k<letters>: n don't super-evolve, o super-evolve another follower instead; ...gG: play out only
            # when the root's two best moves are within G or a resource decision is open; ...pP: P own turns;
            # ...qQ: only candidates whose one-turn Q (agents.crossturn_agent.one_turn_q) is within Q;
            # ...cC: the winner must beat the line again on new determinizations by C standard errors
            m = re.fullmatch(r"cross([ns]?)(\d*)(?:z([\d.]+))?(?:r(\d+|t))?(?:k([ksenoxvy]+))?(?:m(\d+))?"
                             r"(?:g([\d.]+))?(?:p(\d+))?(?:q([\d.]+))?(?:c([\d.]+))?", cross[0])
            if m is None:
                raise ValueError(f"unknown agent option {cross[0]!r}")
            mode, k, z, r, only, most, gap, pairs, qgap, confirm = m.groups()
            # (x: play-and-super-evolve another follower first, v: play-and-evolve another first, y: play-and-
            # super-evolve a follower in a turn the line doesn't super-evolve in)
            kinds = [{"k": "keep", "s": "save", "e": "noevo", "n": "nosuper", "o": "superonly", "x": "super",
                      "v": "evo", "y": "superany"}[c]
                     for c in only] if only else None
            agent = CrossTurnAgent(agent, samples=int(k or 4), seed=seed, next_turn=mode == "n",
                                   static=mode == "s", z=float(z or 0), research="tree" if r == "t" else int(r or 0),
                                   max_keeps=int(most or 0), gap=float(gap) if gap else None,
                                   pairs=int(pairs or 1), qgap=float(qgap) if qgap else None,
                                   confirm=float(confirm or 0),
                                   **({"kinds": kinds} if kinds else {}))
        pick = [o for o in options if o.startswith("pick")]
        if pick:                                   # the whole turn picked among plans (agents.turnpick_agent)
            from svsim.agents.turnpick_agent import TurnPickAgent
            import re
            # +pick[dD][iI][mM][zZ][k<letters>]: D shared determinizations (8), the plans' own searches of I
            # iterations (100), switch past margin M (0) and Z paired standard errors (1); kinds beside "bot":
            # s second, t third, r race (default str), k keep a card, p keep the bonus PP, e don't evolve
            m = re.fullmatch(r"pick(?:d(\d+))?(?:i(\d+))?(?:m([\d.]+))?(?:z([\d.]+))?(?:k([strkpe]+))?", pick[0])
            if m is None or cross:
                raise ValueError(f"unknown agent option {pick[0]!r}" if m is None else "+pick and +cross together")
            d, it, margin, z, only = m.groups()
            letters = {"s": "second", "t": "third", "r": "race", "k": "keep", "p": "save", "e": "noevo"}
            kinds = ("bot",) + tuple(letters[c] for c in (only or "str"))
            plan_spec = "+".join([f"mcts:{int(it or 100)}"] + [o for o in options if not o.startswith(("pick", "cross"))])
            agent = TurnPickAgent(agent, plan_spec, samples=int(d or 8), margin=float(margin or 0), z=float(z or 1),
                                  kinds=kinds, seed=seed)
        if name == "mcts-raw":
            return agent
        screen = [[int(x) for x in o[len("screen="):].split(":")] for o in options if o.startswith("screen=")]
        if screen and len(screen[0]) not in (1, 3):
            raise ValueError("screen=N or screen=N:N2:K")
        # +tick: the planner models allied countdown amulets that hit the enemy leader (search.combo tickers);
        # +lethal2 (the architecture thread 2026-10-10 04:57Z; analysis/speed/LETHAL.md): +tick, and a deeper screen:
        # near-lethal 2000 nodes within 4, 3000 nodes unscreened (not in any level: a gate first)
        # +lethal3 (the architecture thread 2026-10-10 06:27Z): the lethal package, +lethal2 with +plannerfix and +eot
        lethal3 = "lethal3" in options
        lethal2 = "lethal2" in options or lethal3
        if lethal2 and screen:
            raise ValueError("+lethal2 / +lethal3 set the screen themselves")
        # +plannerfix: the plain planner's two fixes (cards at the play points there, face-first realize)
        agent = LethalAgent(agent, seed=seed, planner=planner, tickers="tick" in options or lethal2,
                            plannerfix="plannerfix" in options or lethal3,
                            eot="eot" in options or lethal3,            # +eot: the planner counts end-of-turn damage
                            discard="discard" in options,               # +discard: plays that discard pick the card
                            adaptive="adaptive" in options,             # +adaptive: plan-level check, re-realized
                            **({"max_nodes": 3000, "near": (2000, 4)} if lethal2 else {}),
                            **({"screen": screen[0][0]} if screen else {}),
                            **({"near": tuple(screen[0][1:]) if len(screen[0]) == 3 else None} if screen else {}),
                                                            macro="macro" in options,
                                                            burst="burst" in options or "burst2" in options,
                                                            burst_reply=2 if "burst2" in options else 0,
                                                            dig="dig" in options or "dig2" in options)
        if "dig2" in options:
            agent.dig_slack = None
        return agent
    raise ValueError(f"unknown agent {spec!r}")


def play_one(job) -> tuple:
    """One game; returns (winner spec or None, {spec: (seconds, decisions)})."""
    a, b, g, deck_kind, seed = job
    rng = random.Random(seed * 100003 + g)
    if deck_kind in ("starter", "rhino"):
        first = decks.build(decks.PIRATE_SWORD if deck_kind == "starter" else decks.RHINO_FOREST)
        ramp = decks.build(decks.RAMP_DRAGON)
        d0, d1 = (first, ramp) if g % 2 == 0 else (ramp, first)
    else:
        d0, d1 = (decks.random_deck(rng.choice(CRAFTS), rng) for _ in range(2))
    specs = (a, b) if (g // 2) % 2 == 0 else (b, a)
    agents = [make_agent(spec, seed * 1000 + g * 2 + i) for i, spec in enumerate(specs)]
    state = new_game(d0, d1, seed=seed * 100003 + g)
    clock = {a: [0.0, 0, 0], b: [0.0, 0, 0]}
    while not state.over:
        start = time.perf_counter()
        action = agents[state.active].act(state, legal_actions(state))
        clock[specs[state.active]][0] += time.perf_counter() - start
        clock[specs[state.active]][1] += 1
        apply(state, action)
    for spec, agent in zip(specs, agents):
        clock[spec][2] += getattr(agent, "lethals", 0)
    winner = specs[state.winner] if state.winner in (0, 1) else None
    return a, b, winner, clock


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--agents", nargs="+", required=True)
    parser.add_argument("--games", type=int, default=100, help="games per pairing")
    parser.add_argument("--decks", choices=("starter", "random", "rhino"), default="starter")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    jobs = [(a, b, g, args.decks, args.seed) for a, b in combinations(args.agents, 2)
            for g in range(args.games)]
    results, clock = defaultdict(Counter), defaultdict(lambda: [0.0, 0, 0])
    start = time.perf_counter()
    with Pool(args.workers) as pool:
        for a, b, winner, game_clock in pool.imap_unordered(play_one, jobs):
            results[(a, b)][winner] += 1
            for spec, (secs, n, lethals) in game_clock.items():
                clock[spec][0] += secs
                clock[spec][1] += n
                clock[spec][2] += lethals
    print(f"{len(jobs)} games in {time.perf_counter() - start:.0f}s ({args.decks} decks)")
    for a, b in combinations(args.agents, 2):
        r = results[(a, b)]
        n = r[a] + r[b] + r[None]
        p = (r[a] + 0.5 * r[None]) / n
        margin = 1.96 * (p * (1 - p) / n) ** 0.5
        print(f"  {a:>12} vs {b:<12} {r[a]:>4}-{r[b]:<4} draws {r[None]:<3} "
              f"{a} wins {p:.0%} ± {margin:.0%}")
    for spec in args.agents:
        secs, n, lethals = clock[spec]
        print(f"  {spec:>12}: {secs / max(n, 1) * 1000:.0f} ms per decision, {lethals} lethals found")


if __name__ == "__main__":
    main()
