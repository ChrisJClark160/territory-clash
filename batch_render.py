"""Render the upload stockpile from seed-shopped battles.

Consumes output/seed_shop.json (run seed_shop.py first) so every rendered
video is a scored banger, not a random roll. Each theme gets its assigned
seed rendered at the shopped match length, with sidecar + upload text.

Usage:
    python batch_render.py                     # every assigned theme
    python batch_render.py cats_vs_dogs        # just these themes
    python batch_render.py cats_vs_dogs kfc_vs_mcdonalds

Outputs land in output/batch/<theme>.mp4 (+ .json sidecar + .txt packaging).
"""

import json
import os
import sys

from render import render
from themes import THEMES

SHOP_PATH = os.path.join("output", "seed_shop.json")


def main():
    if not os.path.exists(SHOP_PATH):
        sys.exit(f"{SHOP_PATH} not found - run seed_shop.py first")
    with open(SHOP_PATH) as f:
        shop = json.load(f)

    wanted = sys.argv[1:] or list(shop["themes"])
    unknown = [n for n in wanted if n not in THEMES]
    if unknown:
        sys.exit(f"unknown theme(s): {', '.join(unknown)}")
    missing = [n for n in wanted if n not in shop["themes"]]
    if missing:
        sys.exit(f"no shopped seed for: {', '.join(missing)} - "
                 f"re-run seed_shop.py with more seeds")

    seconds = shop["match_seconds"]
    out_dir = os.path.join("output", "batch")
    os.makedirs(out_dir, exist_ok=True)

    print(f"stockpile: {len(wanted)} themes at {seconds}s "
          f"(shopped {shop['generated']} over {shop['n_seeds']} seeds)\n")
    for i, name in enumerate(wanted, 1):
        pick = shop["themes"][name]
        print(f"[{i}/{len(wanted)}] {name} - seed {pick['seed']} "
              f"(score {pick['score']}, {pick['lead_changes']} leads, "
              f"biggest {pick['biggest_power']})")
        render(seed=pick["seed"],
               out_path=os.path.join(out_dir, f"{name}.mp4"),
               theme=THEMES[name], match_seconds=seconds)
        print()


if __name__ == "__main__":
    main()
