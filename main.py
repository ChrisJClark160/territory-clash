"""Territory Clash - tile-flip arena (v3, engagement update).

Two teams, each starting with one roaming ball. Balls flip enemy tiles to
their colour on contact and ricochet. The scoreboard tracks tiles owned.

Engagement mechanics (the reason anyone keeps watching):
- Rubber-banding: the losing team's balls speed up, the leader's slow a touch,
  so the outcome stays uncertain and lead changes happen naturally.
- Powerups: pictographic pickups (+ = multiply, starburst = bomb,
  snowflake = freeze, bolt = speed) cause sudden dramatic swings.
- Escalation: everything speeds up toward the end - the finale is the most
  chaotic part, so the payoff is at the end of the video.
- Seeded randomness: every run is a unique battle; pass a seed to reproduce
  one (python main.py 12345).

No physics engine, no language: the only text on screen is percentages and
the timer.
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

LEFT, RIGHT = 0, 1

TILE_COLOR = {
    LEFT: (255, 45, 140),    # neon pink
    RIGHT: (45, 220, 255),   # neon cyan
}
BALL_COLOR = {
    LEFT: (255, 130, 195),
    RIGHT: (150, 240, 255),
}
BG_COLOR = (12, 12, 20)
GOLD = (255, 210, 70)
WHITE = (255, 255, 255)
ICE = (190, 230, 255)
GAP = 2

BALL_RADIUS = 22
BASE_SPEED = 7.0            # px per frame before multipliers
MATCH_SECONDS = 60
MAX_BALLS_PER_TEAM = 6
TRAIL_LEN = 9

PU_RADIUS = 26
PU_TYPES = ("multiply", "bomb", "freeze", "speed")
PU_WEIGHTS = (0.35, 0.30, 0.175, 0.175)
BOMB_TILES = 3.4            # blast radius in tiles
FREEZE_SECONDS = 2.5
BOOST_SECONDS = 4.0
BOOST_MULT = 1.6


def _normalize(vx, vy):
    m = math.hypot(vx, vy) or 1.0
    return vx / m, vy / m


def _rotate(vx, vy, a):
    ca, sa = math.cos(a), math.sin(a)
    return vx * ca - vy * sa, vx * sa + vy * ca


class Ball:
    def __init__(self, x, y, team, vx, vy):
        self.x = x
        self.y = y
        self.team = team
        self.dx, self.dy = _normalize(vx, vy)
        self.trail = []

    def step(self, game, speed):
        enemy = RIGHT if self.team == LEFT else LEFT

        self.x += self.dx * speed
        self.y += self.dy * speed

        # Arena walls
        if self.x < BALL_RADIUS:
            self.x, self.dx = BALL_RADIUS, abs(self.dx)
        elif self.x > WIDTH - BALL_RADIUS:
            self.x, self.dx = WIDTH - BALL_RADIUS, -abs(self.dx)
        if self.y < BALL_RADIUS:
            self.y, self.dy = BALL_RADIUS, abs(self.dy)
        elif self.y > HEIGHT - BALL_RADIUS:
            self.y, self.dy = HEIGHT - BALL_RADIUS, -abs(self.dy)

        # Sample circumference; flip enemy tiles and steer away (sign-based so
        # multiple hits on one side can't cancel into a non-bounce).
        bounced = False
        for deg in range(0, 360, 15):
            rad = math.radians(deg)
            ox, oy = math.cos(rad), math.sin(rad)
            ci = int((self.x + ox * BALL_RADIUS) // TILE)
            cj = int((self.y + oy * BALL_RADIUS) // TILE)
            if 0 <= ci < COLS and 0 <= cj < ROWS and game.grid[cj][ci] == enemy:
                game.flip_tile(ci, cj, self.team)
                if abs(ox) > abs(oy):
                    self.dx = -abs(self.dx) if ox > 0 else abs(self.dx)
                else:
                    self.dy = -abs(self.dy) if oy > 0 else abs(self.dy)
                bounced = True

        if bounced:
            self.dx, self.dy = _rotate(self.dx, self.dy, random.uniform(-0.15, 0.15))
            self.dx, self.dy = _normalize(self.dx, self.dy)

        self.trail.append((self.x, self.y))
        if len(self.trail) > TRAIL_LEN:
            self.trail.pop(0)


class Powerup:
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind
        self.age = 0.0


class Game:
    """Full simulation state, updatable headless (draw is separate)."""

    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randrange(1_000_000)
        random.seed(self.seed)

        self.grid = [[LEFT if c < COLS // 2 else RIGHT for c in range(COLS)]
                     for _ in range(ROWS)]
        self.balls = [
            Ball(WIDTH * 0.25, HEIGHT * 0.5, LEFT, 1, 1),
            Ball(WIDTH * 0.75, HEIGHT * 0.5, RIGHT, -1, -1),
        ]
        self.powerups = []
        self.next_pu = 4.0
        self.particles = []       # [x, y, vx, vy, life, colour, size]
        self.flash = {}           # (i, j) -> brightness 0..1, decays
        self.freeze_t = {LEFT: 0.0, RIGHT: 0.0}
        self.boost_t = {LEFT: 0.0, RIGHT: 0.0}
        self.shake_t = 0.0
        self.elapsed = 0.0
        self.finished = False
        self.winner = None
        self._confetti_spawned = False
        # Stats (used by headless verification and for judging drama)
        self.collected = {k: 0 for k in PU_TYPES}
        self.lead_signs = []
        self._lead_timer = 0.0

    # -- scoring ------------------------------------------------------------

    def count_tiles(self):
        left = sum(row.count(LEFT) for row in self.grid)
        return left, COLS * ROWS - left

    def flip_tile(self, i, j, team):
        self.grid[j][i] = team
        self.flash[(i, j)] = 1.0
        cx, cy = i * TILE + TILE / 2, j * TILE + TILE / 2
        for _ in range(2):
            a = random.uniform(0, math.tau)
            sp = random.uniform(30, 90)
            self.particles.append([cx, cy, math.cos(a) * sp, math.sin(a) * sp,
                                   random.uniform(0.2, 0.45), TILE_COLOR[team],
                                   random.uniform(2, 4)])

    # -- update -------------------------------------------------------------

    def update(self, dt):
        self._update_particles(dt)
        if self.finished:
            return

        self.elapsed += dt
        left, right = self.count_tiles()
        total = COLS * ROWS

        # Escalation: up to +50% pace by the end - finale is the wildest part
        esc = 1.0 + 0.5 * min(self.elapsed / MATCH_SECONDS, 1.0) ** 2

        # Rubber-band: losing side speeds up, leader slows - keeps the score
        # close and produces lead changes. The leader penalty fades out over
        # the final 10s ("no mercy") so the ending breaks open decisively.
        mercy = min(1.0, max(0.0, (MATCH_SECONDS - self.elapsed) / 10.0))
        n_balls = {t: max(1, sum(1 for b in self.balls if b.team == t))
                   for t in (LEFT, RIGHT)}
        speed = {}
        for team, owned in ((LEFT, left), (RIGHT, right)):
            share = owned / total
            rubber = (1.0 + 0.9 * max(0.0, 0.5 - share)
                      - 0.3 * mercy * max(0.0, share - 0.5))
            # Fewer balls -> each ball fights harder (damps multiply snowball)
            enemy = RIGHT if team == LEFT else LEFT
            equalizer = min(1.5, max(0.8, (n_balls[enemy] / n_balls[team]) ** 0.5))
            boost = BOOST_MULT if self.boost_t[team] > 0 else 1.0
            speed[team] = BASE_SPEED * esc * rubber * equalizer * boost

        for ball in self.balls:
            if self.freeze_t[ball.team] <= 0:
                ball.step(self, speed[ball.team])

        self._update_powerups(dt, esc)

        for team in (LEFT, RIGHT):
            self.freeze_t[team] = max(0.0, self.freeze_t[team] - dt)
            self.boost_t[team] = max(0.0, self.boost_t[team] - dt)
        self.shake_t = max(0.0, self.shake_t - dt * 3)
        for key in list(self.flash):
            self.flash[key] -= dt * 2.5
            if self.flash[key] <= 0:
                del self.flash[key]

        # Track the lead over time (drama metric: sign changes = lead changes)
        self._lead_timer += dt
        if self._lead_timer >= 0.5:
            self._lead_timer = 0.0
            self.lead_signs.append(0 if left == right else (1 if left > right else -1))

        left, right = self.count_tiles()
        if self.elapsed >= MATCH_SECONDS or left == 0 or right == 0:
            self.finished = True
            self.winner = LEFT if left > right else RIGHT if right > left else None
            self._spawn_confetti()

    def _update_powerups(self, dt, esc):
        self.next_pu -= dt * esc
        if self.next_pu <= 0 and len(self.powerups) < 2:
            margin = 90
            self.powerups.append(Powerup(
                random.uniform(margin, WIDTH - margin),
                random.uniform(margin + 80, HEIGHT - margin),
                random.choices(PU_TYPES, PU_WEIGHTS)[0],
            ))
            self.next_pu = random.uniform(5.0, 8.0)

        for pu in self.powerups:
            pu.age += dt
        for pu in self.powerups[:]:
            for ball in self.balls:
                if math.hypot(ball.x - pu.x, ball.y - pu.y) < BALL_RADIUS + PU_RADIUS:
                    self.powerups.remove(pu)
                    self._apply_powerup(pu, ball.team)
                    break

    def _apply_powerup(self, pu, team):
        self.collected[pu.kind] += 1
        self._burst(pu.x, pu.y, GOLD, n=24, speed=260)
        enemy = RIGHT if team == LEFT else LEFT

        if pu.kind == "multiply":
            have = sum(1 for b in self.balls if b.team == team)
            for _ in range(min(2, MAX_BALLS_PER_TEAM - have)):
                a = random.uniform(0, math.tau)
                self.balls.append(Ball(pu.x, pu.y, team, math.cos(a), math.sin(a)))
        elif pu.kind == "bomb":
            ci, cj = int(pu.x // TILE), int(pu.y // TILE)
            r = BOMB_TILES
            for j in range(max(0, int(cj - r)), min(ROWS, int(cj + r + 1))):
                for i in range(max(0, int(ci - r)), min(COLS, int(ci + r + 1))):
                    if math.hypot(i - ci, j - cj) <= r and self.grid[j][i] == enemy:
                        self.flip_tile(i, j, team)
            self.shake_t = 1.0
            self._burst(pu.x, pu.y, TILE_COLOR[team], n=40, speed=420)
        elif pu.kind == "freeze":
            self.freeze_t[enemy] = FREEZE_SECONDS
            self._burst(pu.x, pu.y, ICE, n=24, speed=200)
        elif pu.kind == "speed":
            self.boost_t[team] = BOOST_SECONDS
            self._burst(pu.x, pu.y, TILE_COLOR[team], n=20, speed=300)

    # -- particles ----------------------------------------------------------

    def _burst(self, x, y, colour, n, speed):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(speed * 0.3, speed)
            self.particles.append([x, y, math.cos(a) * sp, math.sin(a) * sp,
                                   random.uniform(0.3, 0.8), colour,
                                   random.uniform(3, 6)])

    def _spawn_confetti(self):
        if self._confetti_spawned:
            return
        self._confetti_spawned = True
        colours = [TILE_COLOR[LEFT], TILE_COLOR[RIGHT], GOLD, WHITE]
        for _ in range(160):
            self.particles.append([
                random.uniform(0, WIDTH), random.uniform(-300, 0),
                random.uniform(-40, 40), random.uniform(120, 320),
                random.uniform(1.5, 3.5), random.choice(colours),
                random.uniform(3, 7),
            ])

    def _update_particles(self, dt):
        for p in self.particles[:]:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt
            if p[4] <= 0:
                self.particles.remove(p)
        if len(self.particles) > 600:
            del self.particles[:len(self.particles) - 600]


# -- drawing (kept apart from sim so headless runs never touch it) ----------

def draw_icon(surf, kind, cx, cy, r):
    if kind == "multiply":
        w = max(3, r // 4)
        pygame.draw.rect(surf, WHITE, (cx - r * 0.65, cy - w / 2, r * 1.3, w))
        pygame.draw.rect(surf, WHITE, (cx - w / 2, cy - r * 0.65, w, r * 1.3))
    elif kind == "bomb":
        for k in range(8):
            a = math.radians(k * 45)
            ln = r * (0.9 if k % 2 == 0 else 0.55)
            pygame.draw.line(surf, WHITE, (cx, cy),
                             (cx + math.cos(a) * ln, cy + math.sin(a) * ln), 3)
        pygame.draw.circle(surf, WHITE, (cx, cy), max(3, r // 4))
    elif kind == "freeze":
        for k in range(6):
            a = math.radians(k * 60)
            pygame.draw.line(surf, WHITE, (cx, cy),
                             (cx + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.8), 3)
        pygame.draw.circle(surf, WHITE, (cx, cy), max(2, r // 5))
    elif kind == "speed":
        s = r / 10.0
        pts = [(2, -9), (-4, 1), (-1, 1), (-2, 9), (4, -1), (1, -1)]
        pygame.draw.polygon(surf, WHITE, [(cx + px * s, cy + py * s) for px, py in pts])


def draw_world(surf, game):
    surf.fill(BG_COLOR)

    for j in range(ROWS):
        for i in range(COLS):
            colour = TILE_COLOR[game.grid[j][i]]
            f = game.flash.get((i, j), 0.0)
            if f > 0:
                colour = tuple(int(c + (255 - c) * f * 0.7) for c in colour)
            pygame.draw.rect(surf, colour,
                             (i * TILE + GAP, j * TILE + GAP, TILE - GAP, TILE - GAP))

    for pu in game.powerups:
        pulse = 1.0 + 0.12 * math.sin(pu.age * 5)
        r = int(PU_RADIUS * pulse)
        pygame.draw.circle(surf, (25, 25, 35), (int(pu.x), int(pu.y)), r)
        pygame.draw.circle(surf, GOLD, (int(pu.x), int(pu.y)), r, 4)
        draw_icon(surf, pu.kind, int(pu.x), int(pu.y), int(r * 0.62))

    for p in game.particles:
        pygame.draw.circle(surf, p[5], (int(p[0]), int(p[1])), max(1, int(p[6] * min(1, p[4] * 2))))

    for ball in game.balls:
        for k, (tx, ty) in enumerate(ball.trail):
            frac = (k + 1) / len(ball.trail)
            r = int(BALL_RADIUS * frac * 0.7)
            if r > 0:
                t = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(t, BALL_COLOR[ball.team] + (int(110 * frac),), (r, r), r)
                surf.blit(t, (tx - r, ty - r))
        pygame.draw.circle(surf, BALL_COLOR[ball.team], (int(ball.x), int(ball.y)), BALL_RADIUS)
        ring = WHITE
        if game.freeze_t[ball.team] > 0:
            ring = ICE
        elif game.boost_t[ball.team] > 0:
            ring = GOLD
        pygame.draw.circle(surf, ring, (int(ball.x), int(ball.y)), BALL_RADIUS, 3)


def draw_hud(screen, game, font, big_font):
    left, right = game.count_tiles()
    total = left + right
    left_frac = left / total
    left_pct = round(left_frac * 100)

    bar_h, bar_w = 34, WIDTH - 40
    x0, y0 = 20, 20
    split = int(bar_w * left_frac)
    pygame.draw.rect(screen, TILE_COLOR[LEFT], (x0, y0, split, bar_h), border_radius=16)
    pygame.draw.rect(screen, TILE_COLOR[RIGHT], (x0 + split, y0, bar_w - split, bar_h),
                     border_radius=16)
    pygame.draw.rect(screen, WHITE, (x0 + split - 2, y0, 4, bar_h))

    screen.blit(big_font.render(f"{left_pct}%", True, WHITE), (x0 + 8, y0 + bar_h + 6))
    rbl = big_font.render(f"{100 - left_pct}%", True, WHITE)
    screen.blit(rbl, (x0 + bar_w - rbl.get_width() - 8, y0 + bar_h + 6))

    remaining = max(0, MATCH_SECONDS - game.elapsed)
    colour = GOLD if remaining <= 10 else (230, 230, 230)
    timer = font.render(f"{remaining:0.0f}", True, colour)
    screen.blit(timer, (WIDTH / 2 - timer.get_width() / 2, y0 + bar_h + 8))

    if game.finished:
        if game.winner is None:
            text, colour = "DRAW", WHITE
        else:
            text = "PINK WINS" if game.winner == LEFT else "CYAN WINS"
            colour = TILE_COLOR[game.winner]
        banner = big_font.render(text, True, colour)
        bg = pygame.Surface((WIDTH, 120), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 170))
        screen.blit(bg, (0, HEIGHT / 2 - 60))
        screen.blit(banner, (WIDTH / 2 - banner.get_width() / 2,
                             HEIGHT / 2 - banner.get_height() / 2))


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
    pygame.init()

    # Sim always runs at full 720x1280 (video output resolution); the window
    # is scaled down to fit whatever screen it's on.
    info = pygame.display.Info()
    scale = min(1.0, (info.current_h * 0.92) / HEIGHT, (info.current_w * 0.92) / WIDTH)
    win_w, win_h = int(WIDTH * scale), int(HEIGHT * scale)
    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption("Territory Clash - v3")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 26, bold=True)
    big_font = pygame.font.SysFont("arial", 44, bold=True)
    world = pygame.Surface((WIDTH, HEIGHT))
    canvas = pygame.Surface((WIDTH, HEIGHT))

    game = Game(seed)
    print(f"seed: {game.seed}")

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        game.update(1 / FPS)

        draw_world(world, game)
        ox = oy = 0
        if game.shake_t > 0:
            mag = game.shake_t * 10
            ox, oy = random.uniform(-mag, mag), random.uniform(-mag, mag)
        canvas.fill(BG_COLOR)
        canvas.blit(world, (ox, oy))
        draw_hud(canvas, game, font, big_font)
        if scale < 1.0:
            pygame.transform.smoothscale(canvas, (win_w, win_h), screen)
        else:
            screen.blit(canvas, (0, 0))
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
