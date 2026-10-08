"""Does the opponent's real hand reach the installed evaluator? For positions of quick games (greedy+plan+learned
both sides), the same position is determinized twice with the same random numbers, as the search does it
(core.view.determinize: the opponent's hand drawn from hand + deck) and with +oracle (their real hand), and the
installed evaluation (learn.phased.PhasedLearned, ended and act) of the two is compared at the position itself, then
after the player plays the rest of the turn the same way in both (greedy), which is where the search's leaves are:
once with the random effects of that turn kept the same in both (the state's random number generator copied), so
only the opponent's hand differs, and once as the search has it (each determinization reseeds the state's generator
from the search's, and the two draw different numbers of them).

    cd <svsim checkout with +oracle (91aecd9 or later)> && PYTHONPATH=. python3 <this> [--games 6]

Condition: the opponent's 40-card list is known (order and hand not); +oracle is the experiment that knows the hand.
"""
import random
import sys


def main():
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.core.enums import Phase
    from svsim.core.view import determinize
    from svsim.learn.phased import PhasedLearned
    from svsim.tools.arena import make_agent
    from svsim.ui.session import DECKS
    games = int(sys.argv[sys.argv.index("--games") + 1]) if "--games" in sys.argv else 6
    ev = PhasedLearned()
    for deck, opp in (("ramp-t", "ramp-t"), ("elf-t", "nemesis-t")):
        n = same_hand = 0
        worst = {"root": 0.0, "turn, same random effects": 0.0, "turn, as searched": 0.0}
        for g in range(games):
            agents = [make_agent("greedy+plan+learned", 7 * g + i) for i in range(2)]
            state = new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opp][1]), seed=900 + g)
            step = 0
            while not state.over:
                me = state.active
                if state.phase == Phase.MAIN and step % 3 == 0:
                    for k in range(2):
                        a = determinize(state, me, random.Random(k))
                        b = determinize(state, me, random.Random(k), oracle=True)
                        same_hand += sorted(c.uid for c in a.players[1 - me].hand) == \
                            sorted(c.uid for c in b.players[1 - me].hand)
                        pairs = [("root", a, b)]
                        # the rest of this turn played the same way in both (the leaves of the search)
                        for label, sync in (("turn, same random effects", True), ("turn, as searched", False)):
                            a2, b2 = a.clone(), b.clone()
                            if sync:
                                b2.rng.setstate(a2.rng.getstate())
                            bot = make_agent("greedy+plan+learned", 11 * g + k)
                            while not a2.over and a2.active == me:
                                act = bot.act(a2, legal_actions(a2))
                                if act not in legal_actions(b2):
                                    break
                                apply(a2, act)
                                apply(b2, act)
                            if a2.active == b2.active and a2.over == b2.over:
                                pairs.append((label, a2, b2))
                        for label, x, y in pairs:
                            for nxt in (False, True):
                                worst[label] = max(worst[label], abs(ev.score(x, me, nxt) - ev.score(y, me, nxt)))
                            n += 1
                apply(state, agents[me].act(state, legal_actions(state)))
                step += 1
        print(f"{deck} vs {opp}: {n} position pairs, the sampled hand equal to the real one in {same_hand}; "
              f"largest |score(sampled) - score(oracle)| over ended and act (score / 8 = logit): "
              + "; ".join(f"{k} {v:.3g}" for k, v in worst.items()))


if __name__ == "__main__":
    main()
