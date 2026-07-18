"""Evolve the sim's engagement genome (see GENOME in main.py).

Chris's framing: change the settings of the sim, and let a fitness test
pick the winners. Two fitness phases:

- NOW (offline surrogate): mean drama score over a shared set of battle
  seeds. Common random numbers - every genome fights the exact same
  battles, so fitness differences are the genome's doing, not seed luck.
- LATER (real audience): every render's sidecar records its genome, so
  once 20-30 uploads have YouTube analytics, swap `fitness()` for one that
  averages avg-percent-viewed per genome and re-run. Views are noisy and
  1 video/day makes generations slow - retention percent, not raw views,
  and expect a generation to take a week+. The offline phase gets the
  genome into the right neighbourhood first.

Usage:
    python evolve.py               # 6 generations, pop 10, 12 battles each
    python evolve.py 8 12 16       # generations pop battles_per_genome

Writes output/evolution.json (history) + output/best_genome.json, which
seed_shop.py accepts: python seed_shop.py 200 40 output/best_genome.json
"""

import json
import os
import random
import sys
import time
from datetime import date

import main as sim
from seed_shop import raw_score, simulate

BOUNDS = {
    "base_speed": (5.0, 9.5),
    "escalation": (0.1, 1.2),
    "rubber": (0.3, 1.6),
    "leader_brake": (0.0, 0.6),
    "no_mercy_s": (4.0, 20.0),
    "pu_rate": (0.5, 1.8),
    "green_pads": (2, 5),
    "red_pads": (1, 4),
    "max_balls": (3, 9),
    "burst_cone_deg": (30, 130),
}
INT_GENES = {"green_pads", "red_pads", "max_balls"}

ELITES = 2          # best genomes survive unchanged
MUTATE_P = 0.4      # per-gene mutation probability
SIGMA = 0.18        # mutation size as a fraction of the gene's range


def _clamp(name, v):
    lo, hi = BOUNDS[name]
    v = max(lo, min(hi, v))
    return int(round(v)) if name in INT_GENES else round(v, 3)


def mutate(genome, rng):
    child = dict(genome)
    for name in BOUNDS:
        if rng.random() < MUTATE_P:
            lo, hi = BOUNDS[name]
            child[name] = _clamp(name, child[name] + rng.gauss(0, SIGMA * (hi - lo)))
    return child


def crossover(a, b, rng):
    return {name: (a if rng.random() < 0.5 else b)[name] for name in BOUNDS}


def fitness(genome, battle_seeds, match_seconds):
    return round(sum(raw_score(simulate(s, match_seconds, genome))
                     for s in battle_seeds) / len(battle_seeds), 2)


def main():
    generations = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    pop_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    n_battles = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    match_seconds = 40  # the Shorts target length

    rng = random.Random(20260718)
    battle_seeds = rng.sample(range(1_000_000), n_battles)

    # Gen 0: the hand-tuned genome plus mutants of it
    defaults = {k: sim.GENOME[k] for k in BOUNDS}
    population = [defaults] + [mutate(defaults, rng) for _ in range(pop_size - 1)]

    cache = {}  # genome (as sorted tuple) -> fitness, saves elite re-evals

    def evaluate(g):
        key = tuple(sorted(g.items()))
        if key not in cache:
            cache[key] = fitness(g, battle_seeds, match_seconds)
        return cache[key]

    history = []
    t0 = time.time()
    print(f"evolving: {generations} generations, pop {pop_size}, "
          f"{n_battles} battles/genome, {match_seconds}s matches")
    print(f"(baseline = hand-tuned defaults)\n")

    for gen in range(generations):
        scored = sorted(((evaluate(g), g) for g in population),
                        key=lambda x: x[0], reverse=True)
        best_f, best_g = scored[0]
        mean_f = round(sum(f for f, _ in scored) / len(scored), 2)
        base_f = evaluate(defaults)
        history.append({"generation": gen, "best": best_f, "mean": mean_f,
                        "best_genome": best_g})
        print(f"gen {gen}: best {best_f}  mean {mean_f}  "
              f"(defaults {base_f})  [{time.time() - t0:.0f}s]")

        if gen == generations - 1:
            break
        # Elites survive; the rest are children of the top half
        parents = [g for _, g in scored[:max(2, pop_size // 2)]]
        population = [g for _, g in scored[:ELITES]]
        while len(population) < pop_size:
            a, b = rng.sample(parents, 2)
            population.append(mutate(crossover(a, b, rng), rng))

    winner = history[-1]["best_genome"]
    os.makedirs("output", exist_ok=True)
    with open(os.path.join("output", "evolution.json"), "w") as f:
        json.dump({"generated": date.today().isoformat(),
                   "match_seconds": match_seconds,
                   "battle_seeds": battle_seeds,
                   "fitness": "surrogate drama score (see seed_shop.raw_score)",
                   "history": history}, f, indent=2)
    with open(os.path.join("output", "best_genome.json"), "w") as f:
        json.dump(winner, f, indent=2)

    print(f"\nwinner (fitness {history[-1]['best']} "
          f"vs defaults {evaluate(defaults)}):")
    for k in BOUNDS:
        marker = "  *" if winner[k] != defaults[k] else ""
        print(f"  {k:>15}: {winner[k]}{marker}")
    print("\n-> output/best_genome.json  "
          "(next: seed_shop.py N 40 output/best_genome.json)")


if __name__ == "__main__":
    main()
