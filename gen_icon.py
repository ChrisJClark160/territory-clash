"""Render the channel avatar: the game's split-territory look as an icon.

800x800 PNG (YouTube's recommended avatar size). Pink vs cyan halves with
a jagged tile frontline, subtle grid, one ball per side - the exact visual
a viewer sees in every video, so the avatar IS the brand. No text: it has
to read at 98px.

Usage: python gen_icon.py  -> icon.png
"""

import math
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

S = 800
TILE = 50
PINK = (255, 45, 140)
CYAN = (45, 220, 255)
BG = (12, 12, 20)
WHITE = (255, 255, 255)

pygame.init()
surf = pygame.Surface((S, S))
surf.fill(BG)

rng = random.Random(4)  # seed chosen for a nice-looking frontline
cols = rows = S // TILE

# Jagged frontline: column of the boundary per row, wandering around centre
boundary = []
b = cols // 2
for _ in range(rows):
    b = max(3, min(cols - 3, b + rng.choice((-1, 0, 0, 1))))
    boundary.append(b)

gap = 3
for j in range(rows):
    for i in range(cols):
        colour = PINK if i < boundary[j] else CYAN
        pygame.draw.rect(surf, colour,
                         (i * TILE + gap, j * TILE + gap,
                          TILE - gap, TILE - gap), border_radius=6)

# One ball per side, white ring, like the game
for (bx, by, side) in ((0.26, 0.30, PINK), (0.74, 0.68, CYAN)):
    x, y = int(bx * S), int(by * S)
    lighter = tuple(int(v + (255 - v) * 0.45) for v in side)
    pygame.draw.circle(surf, lighter, (x, y), 74)
    pygame.draw.circle(surf, WHITE, (x, y), 74, 10)

pygame.image.save(surf, "icon.png")
print("icon.png written")
