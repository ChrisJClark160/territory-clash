"""Headless invariant + determinism checks for the sim.

Determinism is the load-bearing property of the whole pipeline: seed
shopping, re-rendering a banger, and the future cold open all assume the
same seed always produces the same battle. Run this after ANY sim change.

Checks per seed:
- invariants sampled during the run: grid cells always LEFT/RIGHT, tile
  total conserved, balls inside the arena, ball values in [1, VALUE_CAP]
- the match actually finishes (no runaway loop)
- determinism: two runs of the same seed produce identical signatures
- default equivalence: Game(seed) == Game(seed, match_seconds=60)
- a 40s match finishes at ~40s (match_seconds actually shortens the battle)

Usage:
    python verify.py            # 5 seeds
    python verify.py 12         # more seeds
"""

import sys
import time

import main as sim

CHECK_EVERY = 30  # frames between invariant sweeps


def run(seed, match_seconds=None, genome=None):
    """Run one battle headless, asserting invariants; return a signature."""
    game = sim.Game(seed, match_seconds=match_seconds, genome=genome)
    limit = sim.FPS * (game.match_seconds + 30)
    frames = 0
    while not game.finished:
        game.update(1 / sim.FPS)
        frames += 1
        assert frames <= limit, f"seed {seed}: match never finished"
        if frames % CHECK_EVERY == 0:
            left, right = game.count_tiles()
            assert left + right == sim.COLS * sim.ROWS, "tiles not conserved"
            for row in game.grid:
                for cell in row:
                    assert cell in (sim.LEFT, sim.RIGHT), "invalid tile owner"
            for b in game.balls:
                assert -1 <= b.x <= sim.WIDTH + 1 and -1 <= b.y <= sim.HEIGHT + 1, \
                    f"ball out of bounds ({b.x:.0f},{b.y:.0f})"
                assert 1 <= b.value <= sim.VALUE_CAP, f"ball value {b.value}"

    left, right = game.count_tiles()
    return {
        "elapsed": round(game.elapsed, 3),
        "final": (left, right),
        "winner": game.winner,
        "pct_history": tuple(game.pct_history),
        "events": dict(game.events),
        "powerups": dict(game.collected),
        "lead_changes": game.lead_changes,
        "max_swing": game.max_swing,
        "biggest_hit": dict(game.biggest_hit),
        "n_balls": len(game.balls),
    }


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    seeds = [101 + i * 7919 for i in range(n_seeds)]  # spread, reproducible
    t0 = time.time()
    failures = 0

    for k, seed in enumerate(seeds):
        a = run(seed)
        b = run(seed)
        if a != b:
            failures += 1
            diff = {key for key in a if a[key] != b[key]}
            print(f"FAIL seed {seed}: not deterministic, differs in {diff}")
            continue
        c = run(seed, match_seconds=60)
        if a != c:
            failures += 1
            diff = {key for key in a if a[key] != c[key]}
            print(f"FAIL seed {seed}: match_seconds=60 != default, differs in {diff}")
            continue
        d = run(seed, genome=dict(sim.GENOME))
        if a != d:
            failures += 1
            diff = {key for key in a if a[key] != d[key]}
            print(f"FAIL seed {seed}: explicit default genome != default, "
                  f"differs in {diff}")
            continue
        print(f"ok seed {seed}: {a['final'][0]}-{a['final'][1]}, "
              f"{a['lead_changes']} lead changes, "
              f"biggest {a['biggest_hit']['value']}, {a['elapsed']:.0f}s")

    # match_seconds must actually shorten the battle (one seed is enough)
    short = run(seeds[0], match_seconds=40)
    if not (39.5 <= short["elapsed"] <= 41.0):
        failures += 1
        print(f"FAIL: 40s match ran {short['elapsed']:.1f}s")
    else:
        print(f"ok 40s variant: finished at {short['elapsed']:.1f}s, "
              f"{short['lead_changes']} lead changes")

    print(f"\n{len(seeds)} seeds in {time.time() - t0:.0f}s - "
          + ("ALL OK" if failures == 0 else f"{failures} FAILURES"))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
