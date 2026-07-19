"""Render the channel banner: 2048x1152 (YouTube minimum), with everything
important inside the 1235x338 centre "safe area" that survives every crop
(TV shows the full image, desktop a wide strip, mobile just the middle).

Design: the game board as the backdrop - pink vs cyan tiles with a jagged
frontline running the full width - and the wordmark dead centre.

Usage: python gen_banner.py  -> banner.png
"""

import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

W, H = 2048, 1152
TILE = 64
PINK = (255, 45, 140)
CYAN = (45, 220, 255)
BG = (12, 12, 20)
WHITE = (255, 255, 255)
GOLD = (255, 210, 70)

pygame.init()
surf = pygame.Surface((W, H))
surf.fill(BG)

rng = random.Random(11)
cols, rows = W // TILE, H // TILE

# Vertical frontline wandering across the middle of the banner
boundary = []
b = cols // 2
for _ in range(rows):
    b = max(6, min(cols - 6, b + rng.choice((-1, -1, 0, 1, 1))))
    boundary.append(b)

gap = 4
for j in range(rows):
    for i in range(cols):
        colour = PINK if i < boundary[j] else CYAN
        pygame.draw.rect(surf, colour,
                         (i * TILE + gap, j * TILE + gap,
                          TILE - gap, TILE - gap), border_radius=8)

# A few balls scattered like mid-battle
for (bx, by, side) in ((0.14, 0.30, PINK), (0.30, 0.72, PINK),
                       (0.72, 0.25, CYAN), (0.87, 0.65, CYAN)):
    x, y = int(bx * W), int(by * H)
    lighter = tuple(int(v + (255 - v) * 0.45) for v in side)
    pygame.draw.circle(surf, lighter, (x, y), 56)
    pygame.draw.circle(surf, WHITE, (x, y), 56, 8)

# Safe area: 1235x338 centred. Dark plate + wordmark + tagline inside it.
sw, sh = 1235, 338
sx, sy = (W - sw) // 2, (H - sh) // 2
plate = pygame.Surface((sw, sh), pygame.SRCALPHA)
plate.fill((8, 8, 14, 215))
surf.blit(plate, (sx, sy))
pygame.draw.rect(surf, GOLD, (sx, sy, sw, sh), 5)

font_big = pygame.font.SysFont("arial", 120, bold=True)
font_small = pygame.font.SysFont("arial", 44, bold=True)

def outlined_at(text, font, colour, x, cy):
    lbl = font.render(text, True, colour)
    dark = font.render(text, True, BG)
    y = cy - lbl.get_height() // 2
    for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4)):
        surf.blit(dark, (x + dx, y + dy))
    surf.blit(lbl, (x, y))
    return lbl.get_width()

# Measure the two words + gap, centre the pair as one unit inside the plate
gap_px = 70
w1 = font_big.render("TERRITORY", True, PINK).get_width()
w2 = font_big.render("CLASH", True, CYAN).get_width()
x0 = W // 2 - (w1 + gap_px + w2) // 2
outlined_at("TERRITORY", font_big, PINK, x0, H // 2 - 40)
outlined_at("CLASH", font_big, CYAN, x0 + w1 + gap_px, H // 2 - 40)

tag = font_small.render("NEW BATTLE EVERY DAY  -  PICK YOUR SIDE", True, GOLD)
outlined_at("NEW BATTLE EVERY DAY  -  PICK YOUR SIDE", font_small, GOLD,
            W // 2 - tag.get_width() // 2, H // 2 + 100)

pygame.image.save(surf, "banner.png")
print("banner.png written")
