"""Render the Phase A.5 test batch: one video per vs-theme, random seeds.

Usage:
    python batch_render.py            # all themes except "classic"
    python batch_render.py 3          # only the first 3 themes (quick test)

Outputs land in output/batch/<theme>.mp4 with a JSON sidecar each. Seeds are
random but recorded in the sidecars, so any battle can be re-rendered.
"""

import os
import sys

from render import render
from themes import THEMES


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    names = [n for n in THEMES if n != "classic"]
    if limit:
        names = names[:limit]

    out_dir = os.path.join("output", "batch")
    os.makedirs(out_dir, exist_ok=True)

    print(f"batch: {len(names)} themes -> {out_dir}\n")
    for i, name in enumerate(names, 1):
        print(f"[{i}/{len(names)}] {name}")
        render(seed=None, out_path=os.path.join(out_dir, f"{name}.mp4"),
               theme=THEMES[name])
        print()


if __name__ == "__main__":
    main()
