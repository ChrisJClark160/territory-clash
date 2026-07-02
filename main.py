"""Territory Clash - tile-flip arena (v2).

Two teams, each with a roaming ball. A ball flips enemy tiles to its own colour
on contact and ricochets off. The scoreboard tracks tiles owned - that is the
whole story of the video. No physics engine: collision is custom circle-vs-grid
maths, which is what this genre actually needs.
"""

import math
import random
import sys

import pygame

WIDTH, HEIGHT = 720, 1280  # vertical, matches Shorts/TikTok aspect
FPS = 60
TILE = 40
COLS = WIDTH // TILE
ROWS = HEIGHT // TILE

# Team ids
LEFT, RIGHT = 0, 1

# Vivid, high-contrast palette (readable small/muted on mobile)
TILE_COLOR = {
    LEFT: (255, 45, 140),    # neon pink
    RIGHT: (45, 220, 255),   # neon cyan
}
BALL_COLOR = {
    LEFT: (255, 130, 195),   # lighter pink so it pops on cyan territory
    RIGHT: (150, 240, 255),  # lighter cyan so it pops on pink territory
}
BG_COLOR = (12, 12, 20)
GAP = 2  # grout gap between tiles for a crisp grid look

BALL_RADIUS = int(TILE * 0.6)
SPEED = 7.0                 # constant pixels/frame
TRAIL_LEN = 8
MATCH_SECONDS = 90


class Ball:
    def __init__(self, x, y, team, vx, vy):
        self.x = x
        self.y = y
        self.team = team
        self.vx, self.vy = _normalize(vx, vy, SPEED)
        self.trail = []

    def step(self, grid):
        enemy = RIGHT if self.team == LEFT else LEFT

        # Move
        self.x += self.vx
        self.y += self.vy

        # Bounce off arena walls
        if self.x < BALL_RADIUS:
            self.x = BALL_RADIUS
            self.vx = abs(self.vx)
        elif self.x > WIDTH - BALL_RADIUS:
            self.x = WIDTH - BALL_RADIUS
            self.vx = -abs(self.vx)
        if self.y < BALL_RADIUS:
            self.y = BALL_RADIUS
            self.vy = abs(self.vy)
        elif self.y > HEIGHT - BALL_RADIUS:
            self.y = HEIGHT - BALL_RADIUS
            self.vy = -abs(self.vy)

        # Sample points around the circumference; flip enemy tiles and steer
        # the velocity away from them (sign-based, so multiple hits on the same
        # side can't cancel each other out into a non-bounce).
        bounced = False
        for deg in range(0, 360, 15):
            rad = math.radians(deg)
            dx, dy = math.cos(rad), math.sin(rad)
            ci = int((self.x + dx * BALL_RADIUS) // TILE)
            cj = int((self.y + dy * BALL_RADIUS) // TILE)
            if 0 <= ci < COLS and 0 <= cj < ROWS and grid[cj][ci] == enemy:
                grid[cj][ci] = self.team
                if abs(dx) > abs(dy):
                    self.vx = -abs(self.vx) if dx > 0 else abs(self.vx)
                else:
                    self.vy = -abs(self.vy) if dy > 0 else abs(self.vy)
                bounced = True

        # Small random nudge on bounce breaks repetitive orbits
        if bounced:
            self.vx, self.vy = _rotate(self.vx, self.vy, random.uniform(-0.15, 0.15))
            self.vx, self.vy = _normalize(self.vx, self.vy, SPEED)

        # Record trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > TRAIL_LEN:
            self.trail.pop(0)


def _normalize(vx, vy, speed):
    m = math.hypot(vx, vy) or 1.0
    return vx / m * speed, vy / m * speed


def _rotate(vx, vy, a):
    ca, sa = math.cos(a), math.sin(a)
    return vx * ca - vy * sa, vx * sa + vy * ca


def make_grid():
    """Left half owned by LEFT, right half by RIGHT."""
    grid = [[LEFT if c < COLS // 2 else RIGHT for c in range(COLS)] for _ in range(ROWS)]
    return grid


def count_tiles(grid):
    left = sum(row.count(LEFT) for row in grid)
    right = COLS * ROWS - left
    return left, right


def draw_grid(screen, grid):
    for j in range(ROWS):
        for i in range(COLS):
            color = TILE_COLOR[grid[j][i]]
            rect = (i * TILE + GAP, j * TILE + GAP, TILE - GAP, TILE - GAP)
            pygame.draw.rect(screen, color, rect)


def draw_ball(screen, ball):
    # Fading trail
    for k, (tx, ty) in enumerate(ball.trail):
        frac = (k + 1) / len(ball.trail)
        r = int(BALL_RADIUS * frac * 0.7)
        if r > 0:
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            col = BALL_COLOR[ball.team] + (int(120 * frac),)
            pygame.draw.circle(surf, col, (r, r), r)
            screen.blit(surf, (tx - r, ty - r))
    # Ball body with white ring so it reads on either territory
    pygame.draw.circle(screen, BALL_COLOR[ball.team], (int(ball.x), int(ball.y)), BALL_RADIUS)
    pygame.draw.circle(screen, (255, 255, 255), (int(ball.x), int(ball.y)), BALL_RADIUS, 3)


def draw_scoreboard(screen, font, big_font, left, right, seconds_left):
    total = left + right
    left_frac = left / total
    left_pct = round(left_frac * 100)
    right_pct = 100 - left_pct

    bar_h, bar_w = 34, WIDTH - 40
    x0, y0 = 20, 20
    split = int(bar_w * left_frac)
    pygame.draw.rect(screen, TILE_COLOR[LEFT], (x0, y0, split, bar_h), border_radius=16)
    pygame.draw.rect(screen, TILE_COLOR[RIGHT], (x0 + split, y0, bar_w - split, bar_h), border_radius=16)

    lbl = big_font.render(f"{left_pct}%", True, (255, 255, 255))
    screen.blit(lbl, (x0 + 8, y0 + bar_h + 6))
    rbl = big_font.render(f"{right_pct}%", True, (255, 255, 255))
    screen.blit(rbl, (x0 + bar_w - rbl.get_width() - 8, y0 + bar_h + 6))

    timer = font.render(f"{seconds_left:0.0f}s", True, (230, 230, 230))
    screen.blit(timer, (WIDTH / 2 - timer.get_width() / 2, y0 + bar_h + 8))


def draw_winner(screen, big_font, left, right):
    winner = "PINK" if left > right else "CYAN" if right > left else "DRAW"
    color = TILE_COLOR[LEFT] if left > right else TILE_COLOR[RIGHT] if right > left else (255, 255, 255)
    banner = big_font.render(f"{winner} WINS", True, color)
    bg = pygame.Surface((WIDTH, 120), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 170))
    screen.blit(bg, (0, HEIGHT / 2 - 60))
    screen.blit(banner, (WIDTH / 2 - banner.get_width() / 2, HEIGHT / 2 - banner.get_height() / 2))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Territory Clash - v2")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 26, bold=True)
    big_font = pygame.font.SysFont("arial", 44, bold=True)

    grid = make_grid()
    balls = [
        Ball(WIDTH * 0.25, HEIGHT * 0.5, LEFT, vx=1, vy=1),
        Ball(WIDTH * 0.75, HEIGHT * 0.5, RIGHT, vx=-1, vy=-1),
    ]

    elapsed = 0.0
    finished = False
    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        left, right = count_tiles(grid)
        if not finished:
            elapsed += dt
            for ball in balls:
                ball.step(grid)
            if elapsed >= MATCH_SECONDS or left == 0 or right == 0:
                finished = True

        screen.fill(BG_COLOR)
        draw_grid(screen, grid)
        for ball in balls:
            draw_ball(screen, ball)
        draw_scoreboard(screen, font, big_font, left, right, max(0, MATCH_SECONDS - elapsed))
        if finished:
            draw_winner(screen, big_font, left, right)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
