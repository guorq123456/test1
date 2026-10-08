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
(search.mcts, backup="mean"); "+phased" linear models by moment (learn.phased:
turn ends, and turn starts reached by playing out the reply; "+phased=NAME" this agent's models from
the folder NAME, a path or svsim/learn/phased_models/NAME, learn.phased.folder_of; "+screen=N" the lethal search's budget for a position whose damage estimate falls short (the
estimate is no bound, search.lethal.damage_estimate), "+screen=N:N2:K" ... and N2 nodes when it is short by K or
less (default 200:1000:4, agents.lethal_agent.NEAR; "+screen=200" is the old default); a mirror without
models of its own uses its stand-in's, learn.model.ALIASES (the tournament Ramp Dragon's the Game8 build's),
on by default, "+noalias" off, "+alias" kept as a no-op); "+timing" adds what holding a card is worth until the turn the
player usually plays it (svsim.learn.timing, from their games); "+priced"
prices resources by what they buy (search.prices: the own followers at what
survives the opponent's turn, "+survive" alone; unused evolution points at the
damage they add to the next turn, "+points" alone). Combined: mcts:200+plan+macro+threat. Each pairing plays both seats and, for --decks starter or
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
    # CR calibration's fixed reference, never changed; the search code is the current one, see its README)
    "ruler20261008": "mcts:200+plan+learned+phased=ruler-20261008",
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


def make_agent(spec: str, seed: int):
    """The agent `spec` names; "+mull=WAY" redraws its opening hand that way (agents.mulligan.decide:
    default, rules[:VARIANT,...], sim[:N[:H]]) and changes nothing else."""
    parts = spec.split("+")
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
                              "pace", "burst2", "patient", "dig", "dig2", "survive", "points", "priced", "enhance", "net", "lazy", "focus", "endnow", "mean", "phased", "reuse", "alias", "noalias"} - {o for o in options if o.startswith(("hp", "gain", "avg", "prior", "cross", "phased=", "screen=", "mimic="))}
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
        veto = (lambda s, a: any(v(s, a) for v in vetoes)) if vetoes else None
        agent = MCTSAgent(int(arg or 400), seed=seed, reply=name == "mcts-reply", weights=weights,
                          backup="mean" if "mean" in options else "max",
                          reserve="reserve" in options, veto=veto, reply_after=1 if "lazy" in options else 0,
                          reply_top=3 if "focus" in options else 0, reply_budget=20 if "focus" in options else 0,
                          average=next((int(o[3:]) for o in options if o.startswith("avg")), 1),
                          reuse="reuse" in options,
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
        if name == "mcts-raw":
            return agent
        screen = [[int(x) for x in o[len("screen="):].split(":")] for o in options if o.startswith("screen=")]
        if screen and len(screen[0]) not in (1, 3):
            raise ValueError("screen=N or screen=N:N2:K")
        agent = LethalAgent(agent, seed=seed, planner=planner, **({"screen": screen[0][0]} if screen else {}),
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
