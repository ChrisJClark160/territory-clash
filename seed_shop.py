"""Seed shopping: find the most dramatic battles WITHOUT rendering them.

Runs the sim headless over many seeds (~0.5s each vs ~50s to render),
scores each battle on the drama metrics, and assigns the best distinct
seeds to the vs-themes. The sim is theme-independent - a seed produces the
same battle whatever the colours - so seeds are scored once and dealt out.

Scoring (see WORKING.md strategy levers):
    lead_changes * 3            uncertainty is the #1 lever
    max_swing * 0.6             big momentum reversals
    closeness bonus             photo finishes hold viewers to the end
    log2(biggest_power)         payoff size (+bonus at the 256 cap)
    early-action bonus          first lead change inside 10s = strong open
Floor: reject battles with < 3 lead changes or biggest hit < 32.

Usage:
    python seed_shop.py               # 80 seeds, 60s matches
    python seed_shop.py 200           # more seeds = better battles
    python seed_shop.py 200 40        # shop for 40s battles
    python seed_shop.py 200 40 output/best_genome.json   # evolved settings

Writes output/seed_shop.json; batch_render.py consumes it. Seeds are only
valid for the exact genome + match length they were shopped with.
"""

import json
import math
import os
import random
import sys
import time
from datetime import date

import main as sim
from themes import THEMES

FLOOR_LEAD_CHANGES = 3
FLOOR_BIGGEST = 32


def simulate(seed, match_seconds, genome=None):
    game = sim.Game(seed, match_seconds=match_seconds, genome=genome)
    while not game.finished:
        game.update(1 / sim.FPS)
    left, right = game.count_tiles()
    total = left + right
    return {
        "seed": seed,
        "final_score": [round(left * 100 / total), round(right * 100 / total)],
        "lead_changes": game.lead_changes,
        "lead_change_times": game.lead_change_times,
        "max_swing": game.max_swing,
        "biggest_power": game.biggest_hit["value"],
        "biggest_event": game.biggest_hit["type"],
        "biggest_hit_t": game.biggest_hit["t"],
    }


def raw_score(stats):
    """Drama score with no floor - evolve.py needs a smooth gradient."""
    closeness = max(0.0, 10.0 - abs(stats["final_score"][0]
                                    - stats["final_score"][1]) * 0.5)
    big = math.log2(max(1, stats["biggest_power"]))
    if stats["biggest_power"] >= sim.VALUE_CAP:
        big += 4
    early = 3.0 if (stats["lead_change_times"]
                    and stats["lead_change_times"][0] < 10) else 0.0
    return round(stats["lead_changes"] * 3 + stats["max_swing"] * 0.6
                 + closeness + big + early, 1)


def score(stats):
    """Drama score, or None if the battle fails the floor."""
    if (stats["lead_changes"] < FLOOR_LEAD_CHANGES
            or stats["biggest_power"] < FLOOR_BIGGEST):
        return None
    return raw_score(stats)


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    match_seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    genome = None
    if len(sys.argv) > 3:
        with open(sys.argv[3]) as f:
            genome = json.load(f)
        print(f"genome: {sys.argv[3]}")
    rng = random.Random(20260718)  # fixed meta-seed: rerun = same candidates
    seeds = rng.sample(range(1_000_000), n_seeds)

    print(f"shopping {n_seeds} seeds at {match_seconds}s...")
    t0 = time.time()
    ranked = []
    rejected = 0
    for k, seed in enumerate(seeds, 1):
        stats = simulate(seed, match_seconds, genome)
        s = score(stats)
        if s is None:
            rejected += 1
        else:
            stats["score"] = s
            ranked.append(stats)
        if k % 20 == 0:
            print(f"  {k}/{n_seeds} ({time.time() - t0:.0f}s), "
                  f"{len(ranked)} passed the floor")

    ranked.sort(key=lambda r: r["score"], reverse=True)
    print(f"\n{len(ranked)}/{n_seeds} passed the floor "
          f"({rejected} rejected) in {time.time() - t0:.0f}s\n")
    print(f"{'seed':>8} {'score':>6} {'leads':>5} {'swing':>5} "
          f"{'big':>4} {'final':>7} {'first':>6}")
    for r in ranked[:20]:
        first = r["lead_change_times"][0] if r["lead_change_times"] else "-"
        print(f"{r['seed']:>8} {r['score']:>6} {r['lead_changes']:>5} "
              f"{r['max_swing']:>5} {r['biggest_power']:>4} "
              f"{r['final_score'][0]:>3}-{r['final_score'][1]:<3} {first:>6}")

    themes = [n for n in THEMES if n != "classic"]
    assignments = {name: ranked[i] for i, name in enumerate(themes)
                   if i < len(ranked)}
    out = {
        "generated": date.today().isoformat(),
        "match_seconds": match_seconds,
        "n_seeds": n_seeds,
        "genome": genome,   # null = hand-tuned defaults
        "themes": assignments,
        "ranked": ranked[:40],
    }
    os.makedirs("output", exist_ok=True)
    path = os.path.join("output", "seed_shop.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nassigned top {len(assignments)} seeds to themes -> {path}")
    if len(assignments) < len(themes):
        print(f"WARNING: only {len(assignments)} bangers for "
              f"{len(themes)} themes - run with more seeds")


if __name__ == "__main__":
    main()
