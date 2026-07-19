"""Render the upload stockpile from seed-shopped battles.

Consumes output/seed_shop.json (run seed_shop.py first), where every theme
has a LIST of scored seeds. Each rendered video gets a collision-free name
(<theme>_<seed>.mp4) plus its sidecar and upload text, so repeated runs
only add - nothing is overwritten.

Usage:
    python batch_render.py                      # every assigned battle
    python batch_render.py --count 2            # at most 2 per theme
    python batch_render.py cats_vs_dogs         # just these themes
    python batch_render.py cats_vs_dogs --count 3

Outputs land in output/batch/.
"""

import json
import os
import sys

from render import render
from themes import THEMES

SHOP_PATH = os.path.join("output", "seed_shop.json")


def main():
    args = sys.argv[1:]
    count = None
    if "--count" in args:
        i = args.index("--count")
        count = int(args[i + 1])
        del args[i:i + 2]

    if not os.path.exists(SHOP_PATH):
        sys.exit(f"{SHOP_PATH} not found - run seed_shop.py first")
    with open(SHOP_PATH) as f:
        shop = json.load(f)

    wanted = args or list(shop["themes"])
    unknown = [n for n in wanted if n not in THEMES]
    if unknown:
        sys.exit(f"unknown theme(s): {', '.join(unknown)}")

    seconds = shop["match_seconds"]
    out_dir = os.path.join("output", "batch")
    os.makedirs(out_dir, exist_ok=True)

    jobs = []
    for name in wanted:
        picks = shop["themes"].get(name, [])
        if isinstance(picks, dict):  # pre-multi-seed shop file
            picks = [picks]
        for pick in picks[:count]:
            out_path = os.path.join(out_dir, f"{name}_{pick['seed']}.mp4")
            if not os.path.exists(out_path):
                jobs.append((name, pick, out_path))

    print(f"stockpile: {len(jobs)} new videos at {seconds}s "
          f"(shopped {shop['generated']} over {shop['n_seeds']} seeds)\n")
    for i, (name, pick, out_path) in enumerate(jobs, 1):
        print(f"[{i}/{len(jobs)}] {name} - seed {pick['seed']} "
              f"(score {pick['score']}, {pick['lead_changes']} leads, "
              f"biggest {pick['biggest_power']})")
        render(seed=pick["seed"], out_path=out_path,
               theme=THEMES[name], match_seconds=seconds,
               genome=shop.get("genome"))
        print()


if __name__ == "__main__":
    main()
