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

# Default theme; themes.py has the full vs-theme catalogue. A theme is
# {"names": (left, right), "colors": {LEFT: rgb, RIGHT: rgb}} - ball colours
# are derived automatically (lightened tiles) so they pop on enemy territory.
DEFAULT_THEME = {
    "names": ("PINK", "CYAN"),
    "colors": {LEFT: (255, 45, 140), RIGHT: (45, 220, 255)},
}


def _lighten(c, f=0.45):
    return tuple(int(v + (255 - v) * f) for v in c)


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

# Multiply or Release (Phase A - see DESIGN.md)
PAD_RADIUS = 30
N_GREEN_PADS = 3
N_RED_PADS = 2
VALUE_CAP = 256
GREEN = (60, 230, 110)
RED = (255, 80, 80)
PELLET_SPEED = 14           # px per frame
PELLETS_PER_FRAME = 6       # burst fire rate
SHOT_SPEED = 5              # charged shot px per frame
SHOT_MAX_BLOB = 6.5         # cap blast radius in tiles

# Red pad anticipation (Phase A.5 - see DESIGN.md): a beat that makes a big
# ball closing on a red pad feel dangerous instead of just a bigger number.
ANTICIPATION_VALUE = 64        # minimum ball value that triggers a beat
ANTICIPATION_RADIUS = 170      # px from a red pad that arms the beat
ANTICIPATION_SECONDS = 0.9     # beat duration
ANTICIPATION_COOLDOWN = 4.0    # min gap between beats, keeps it rare
ANTICIPATION_SLOWMO = 0.4      # ball speed multiplier during the beat
ANTICIPATION_ZOOM = 0.10       # extra camera zoom fraction at beat start


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
        self.value = 1  # multiplied by green pads, cashed in at red pads

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
            self.dx, self.dy = _rotate(self.dx, self.dy, game.rng.uniform(-0.15, 0.15))
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


class Pad:
    """Multiply-or-release trigger. kind: 2 or 4 (green multiplier) or
    "release" (red - cash the ball's value in as a burst or charged shot)."""

    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind
        self.age = 0.0


class Game:
    """Full simulation state, updatable headless (draw is separate)."""

    def __init__(self, seed=None, theme=None, match_seconds=None):
        t = theme or DEFAULT_THEME
        self.match_seconds = match_seconds or MATCH_SECONDS
        # Absolute cadences (powerup spawns) scale with match length so a
        # short match is a compressed battle, not a diluted one.
        self._pace = self.match_seconds / MATCH_SECONDS
        self.team_names = t["names"]
        self.team_emoji = t.get("emoji", ("", ""))
        self.tile_color = dict(t["colors"])
        self.ball_color = {k: _lighten(v) for k, v in self.tile_color.items()}
        self.seed = seed if seed is not None else random.randrange(1_000_000)
        # Private RNG: sim randomness must never share a stream with
        # presentation randomness (screen shake etc), or rendering a game
        # would change its outcome and seeds wouldn't reproduce.
        self.rng = random.Random(self.seed)

        self.grid = [[LEFT if c < COLS // 2 else RIGHT for c in range(COLS)]
                     for _ in range(ROWS)]
        # Random opening: each ball starts somewhere in its own half heading
        # in a random direction, so no two games look alike from frame one.
        a1 = self.rng.uniform(0, math.tau)
        a2 = self.rng.uniform(0, math.tau)
        self.balls = [
            Ball(self.rng.uniform(WIDTH * 0.15, WIDTH * 0.35),
                 self.rng.uniform(HEIGHT * 0.25, HEIGHT * 0.75),
                 LEFT, math.cos(a1), math.sin(a1)),
            Ball(self.rng.uniform(WIDTH * 0.65, WIDTH * 0.85),
                 self.rng.uniform(HEIGHT * 0.25, HEIGHT * 0.75),
                 RIGHT, math.cos(a2), math.sin(a2)),
        ]
        self.powerups = []
        self.next_pu = 6.0
        # Always two x2 pads and one x4 - the big multiplier is a guaranteed
        # part of every board, not a coin flip
        self.pads = ([Pad(*self._pad_pos(), k) for k in (2, 2, 4)]
                     + [Pad(*self._pad_pos(), "release") for _ in range(N_RED_PADS)])
        self.pellets = []         # [x, y, dx, dy, team]
        self.shots = []           # charged shots: dicts
        self.burst_queue = []     # {"x","y","team","remaining"}
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
        self.events = {"x2": 0, "x4": 0, "burst": 0, "charge": 0}
        self.lead_signs = []
        self.pct_history = []
        self._lead_timer = 0.0
        self.lead_changes = 0
        self.max_swing = 0
        self.biggest_hit = {"value": 0, "type": None}
        # Red pad anticipation beat state (Phase A.5)
        self.anticipation = None       # {"value","team","x","y","t"} or None
        self.anticipation_cooldown = 0.0
        # Per-frame cue names for a future audio layer to consume and play
        # (e.g. "pad_green", "burst", "charge", "explosion", "winner"). Reset
        # every update() call - poll it once per frame, same as game.finished.
        self.sound_events = []

    def _pad_pos(self):
        margin = 80
        return (self.rng.uniform(margin, WIDTH - margin),
                self.rng.uniform(margin + 100, HEIGHT - margin))

    # -- scoring ------------------------------------------------------------

    def count_tiles(self):
        left = sum(row.count(LEFT) for row in self.grid)
        return left, COLS * ROWS - left

    def flip_tile(self, i, j, team):
        self.grid[j][i] = team
        self.flash[(i, j)] = 1.0
        cx, cy = i * TILE + TILE / 2, j * TILE + TILE / 2
        for _ in range(2):
            a = self.rng.uniform(0, math.tau)
            sp = self.rng.uniform(30, 90)
            self.particles.append([cx, cy, math.cos(a) * sp, math.sin(a) * sp,
                                   self.rng.uniform(0.2, 0.45), self.tile_color[team],
                                   self.rng.uniform(2, 4)])

    # -- update -------------------------------------------------------------

    def update(self, dt):
        self.sound_events = []
        self._update_particles(dt)
        if self.finished:
            return

        # Anticipation beat runs on real time, independent of match pacing.
        self.anticipation_cooldown = max(0.0, self.anticipation_cooldown - dt)
        if self.anticipation:
            self.anticipation["t"] -= dt
            if self.anticipation["t"] <= 0:
                self.anticipation = None

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
        slowmo = ANTICIPATION_SLOWMO if self.anticipation else 1.0
        speed = {}
        for team, owned in ((LEFT, left), (RIGHT, right)):
            share = owned / total
            rubber = (1.0 + 0.9 * max(0.0, 0.5 - share)
                      - 0.3 * mercy * max(0.0, share - 0.5))
            # Fewer balls -> each ball fights harder (damps multiply snowball)
            enemy = RIGHT if team == LEFT else LEFT
            equalizer = min(1.5, max(0.8, (n_balls[enemy] / n_balls[team]) ** 0.5))
            boost = BOOST_MULT if self.boost_t[team] > 0 else 1.0
            speed[team] = BASE_SPEED * esc * rubber * equalizer * boost * slowmo

        for ball in self.balls:
            if self.freeze_t[ball.team] <= 0:
                ball.step(self, speed[ball.team])

        self._check_anticipation()
        self._update_pads(dt)
        self._update_bursts()
        self._update_pellets()
        self._update_shots()
        self._update_powerups(dt, esc)

        for team in (LEFT, RIGHT):
            self.freeze_t[team] = max(0.0, self.freeze_t[team] - dt)
            self.boost_t[team] = max(0.0, self.boost_t[team] - dt)
        self.shake_t = max(0.0, self.shake_t - dt * 3)
        for key in list(self.flash):
            self.flash[key] -= dt * 2.5
            if self.flash[key] <= 0:
                del self.flash[key]

        left, right = self.count_tiles()

        # Track the lead over time (drama metric: sign changes = lead
        # changes, biggest peak-to-trough run = max swing).
        self._lead_timer += dt
        if self._lead_timer >= 0.5:
            self._lead_timer = 0.0
            self.pct_history.append(round(100 * left / total))
            self.lead_signs.append(0 if left == right else (1 if left > right else -1))

        if self.elapsed >= MATCH_SECONDS or left == 0 or right == 0:
            self.finished = True
            self.winner = LEFT if left > right else RIGHT if right > left else None
            self._compute_drama_stats()
            self.sound_events.append("winner")
            self._spawn_confetti()

    def _check_anticipation(self):
        """Arm a slow-mo/zoom beat when a big ball closes on a red pad."""
        if self.anticipation or self.anticipation_cooldown > 0:
            return
        for ball in self.balls:
            if ball.value < ANTICIPATION_VALUE:
                continue
            for pad in self.pads:
                if pad.kind != "release":
                    continue
                if math.hypot(ball.x - pad.x, ball.y - pad.y) <= ANTICIPATION_RADIUS:
                    self.anticipation = {
                        "value": ball.value, "team": ball.team,
                        "x": pad.x, "y": pad.y, "t": ANTICIPATION_SECONDS,
                    }
                    self.anticipation_cooldown = ANTICIPATION_COOLDOWN
                    self.sound_events.append("anticipation")
                    return

    def _compute_drama_stats(self):
        """Lead changes + biggest single momentum swing, for the winner
        screen and the render.py metadata sidecar."""
        signs = [s for s in self.lead_signs if s != 0]
        self.lead_changes = sum(1 for a, b in zip(signs, signs[1:]) if a != b)

        self.max_swing = 0
        if self.pct_history:
            run_start = prev = self.pct_history[0]
            direction = 0
            for pct in self.pct_history[1:]:
                step = pct - prev
                if step != 0:
                    step_dir = 1 if step > 0 else -1
                    if direction and step_dir != direction:
                        self.max_swing = max(self.max_swing, abs(prev - run_start))
                        run_start = prev
                    direction = step_dir
                prev = pct
            self.max_swing = max(self.max_swing, abs(prev - run_start))

    # -- multiply or release --------------------------------------------------

    def _update_pads(self, dt):
        for pad in self.pads:
            pad.age += dt
            for ball in self.balls:
                if math.hypot(ball.x - pad.x, ball.y - pad.y) > BALL_RADIUS + PAD_RADIUS:
                    continue
                if pad.kind == "release":
                    if ball.value <= 1:
                        continue
                    self._release(pad, ball)
                else:
                    ball.value = min(VALUE_CAP, ball.value * pad.kind)
                    self.events[f"x{pad.kind}"] += 1
                    self._burst(pad.x, pad.y, GREEN, n=14, speed=220)
                    self.sound_events.append("pad_green")
                pad.x, pad.y = self._pad_pos()  # relocate after any trigger
                pad.age = 0.0
                break

    def _release(self, pad, ball):
        value = ball.value
        ball.value = 1
        team = ball.team
        self._burst(pad.x, pad.y, RED, n=26, speed=320)
        self.sound_events.append("pad_red")
        if value > self.biggest_hit["value"]:
            self.biggest_hit = {"value": value, "type": None}  # type set below
        if self.rng.random() < 0.5:
            self.events["burst"] += 1
            if value >= self.biggest_hit["value"]:
                self.biggest_hit = {"value": value, "type": "burst"}
            self.burst_queue.append(
                {"x": pad.x, "y": pad.y, "team": team, "remaining": value})
            self.sound_events.append("burst")
        else:
            self.events["charge"] += 1
            if value >= self.biggest_hit["value"]:
                self.biggest_hit = {"value": value, "type": "charge"}
            target = self._random_enemy_tile(team)
            a = (math.atan2(target[1] - pad.y, target[0] - pad.x)
                 if target else self.rng.uniform(0, math.tau))
            self.shots.append({
                "x": pad.x, "y": pad.y,
                "dx": math.cos(a), "dy": math.sin(a),
                "team": team, "power": value,
            })
            self.sound_events.append("charge")

    def _random_enemy_tile(self, team):
        enemy = RIGHT if team == LEFT else LEFT
        options = [(i, j) for j in range(ROWS) for i in range(COLS)
                   if self.grid[j][i] == enemy]
        if not options:
            return None
        i, j = self.rng.choice(options)
        return (i * TILE + TILE / 2, j * TILE + TILE / 2)

    def _update_bursts(self):
        for q in self.burst_queue[:]:
            n = min(PELLETS_PER_FRAME, q["remaining"])
            q["remaining"] -= n
            for _ in range(n):
                a = self.rng.uniform(0, math.tau)
                self.pellets.append(
                    [q["x"], q["y"], math.cos(a), math.sin(a), q["team"]])
            if q["remaining"] <= 0:
                self.burst_queue.remove(q)

    def _update_pellets(self):
        for p in self.pellets[:]:
            p[0] += p[2] * PELLET_SPEED
            p[1] += p[3] * PELLET_SPEED
            if not (0 <= p[0] < WIDTH and 0 <= p[1] < HEIGHT):
                self.pellets.remove(p)
                continue
            i, j = int(p[0] // TILE), int(p[1] // TILE)
            enemy = RIGHT if p[4] == LEFT else LEFT
            if 0 <= i < COLS and 0 <= j < ROWS and self.grid[j][i] == enemy:
                self.flip_tile(i, j, p[4])
                self.pellets.remove(p)

    def _update_shots(self):
        for s in self.shots[:]:
            s["x"] += s["dx"] * SHOT_SPEED
            s["y"] += s["dy"] * SHOT_SPEED
            i, j = int(s["x"] // TILE), int(s["y"] // TILE)
            enemy = RIGHT if s["team"] == LEFT else LEFT
            hit_wall = not (BALL_RADIUS <= s["x"] <= WIDTH - BALL_RADIUS
                            and BALL_RADIUS <= s["y"] <= HEIGHT - BALL_RADIUS)
            hit_enemy = (0 <= i < COLS and 0 <= j < ROWS
                         and self.grid[j][i] == enemy)
            if not (hit_wall or hit_enemy):
                continue
            r = min(SHOT_MAX_BLOB, max(1.2, math.sqrt(s["power"] / math.pi)))
            ci, cj = max(0, min(COLS - 1, i)), max(0, min(ROWS - 1, j))
            for jj in range(max(0, int(cj - r)), min(ROWS, int(cj + r + 1))):
                for ii in range(max(0, int(ci - r)), min(COLS, int(ci + r + 1))):
                    if (math.hypot(ii - ci, jj - cj) <= r
                            and self.grid[jj][ii] == enemy):
                        self.flip_tile(ii, jj, s["team"])
            self.shake_t = min(1.0, 0.4 + s["power"] / 400)
            self._burst(s["x"], s["y"], self.tile_color[s["team"]], n=36, speed=380)
            self.sound_events.append("explosion")
            self.shots.remove(s)

    # -- powerups -------------------------------------------------------------

    def _update_powerups(self, dt, esc):
        self.next_pu -= dt * esc
        if self.next_pu <= 0 and len(self.powerups) < 2:
            margin = 90
            self.powerups.append(Powerup(
                self.rng.uniform(margin, WIDTH - margin),
                self.rng.uniform(margin + 80, HEIGHT - margin),
                self.rng.choices(PU_TYPES, PU_WEIGHTS)[0],
            ))
            # Rarer than pre-Phase-A: pads are the main drama engine now
            self.next_pu = self.rng.uniform(8.0, 12.0)

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
        self.sound_events.append(
            "explosion" if pu.kind == "bomb"
            else "freeze" if pu.kind == "freeze" else "powerup")
        enemy = RIGHT if team == LEFT else LEFT

        if pu.kind == "multiply":
            have = sum(1 for b in self.balls if b.team == team)
            for _ in range(min(2, MAX_BALLS_PER_TEAM - have)):
                a = self.rng.uniform(0, math.tau)
                self.balls.append(Ball(pu.x, pu.y, team, math.cos(a), math.sin(a)))
        elif pu.kind == "bomb":
            ci, cj = int(pu.x // TILE), int(pu.y // TILE)
            r = BOMB_TILES
            for j in range(max(0, int(cj - r)), min(ROWS, int(cj + r + 1))):
                for i in range(max(0, int(ci - r)), min(COLS, int(ci + r + 1))):
                    if math.hypot(i - ci, j - cj) <= r and self.grid[j][i] == enemy:
                        self.flip_tile(i, j, team)
            self.shake_t = 1.0
            self._burst(pu.x, pu.y, self.tile_color[team], n=40, speed=420)
        elif pu.kind == "freeze":
            self.freeze_t[enemy] = FREEZE_SECONDS
            self._burst(pu.x, pu.y, ICE, n=24, speed=200)
        elif pu.kind == "speed":
            self.boost_t[team] = BOOST_SECONDS
            self._burst(pu.x, pu.y, self.tile_color[team], n=20, speed=300)

    # -- particles ----------------------------------------------------------

    def _burst(self, x, y, colour, n, speed):
        for _ in range(n):
            a = self.rng.uniform(0, math.tau)
            sp = self.rng.uniform(speed * 0.3, speed)
            self.particles.append([x, y, math.cos(a) * sp, math.sin(a) * sp,
                                   self.rng.uniform(0.3, 0.8), colour,
                                   self.rng.uniform(3, 6)])

    def _spawn_confetti(self):
        if self._confetti_spawned:
            return
        self._confetti_spawned = True
        colours = [self.tile_color[LEFT], self.tile_color[RIGHT], GOLD, WHITE]
        for _ in range(160):
            self.particles.append([
                self.rng.uniform(0, WIDTH), self.rng.uniform(-300, 0),
                self.rng.uniform(-40, 40), self.rng.uniform(120, 320),
                self.rng.uniform(1.5, 3.5), self.rng.choice(colours),
                self.rng.uniform(3, 7),
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

_fonts = {}


def _font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont("arial", size, bold=True)
    return _fonts[size]


def _emoji(char, size, colour):
    """Render an emoji as a monochrome pictogram. None if unavailable."""
    if not char:
        return None
    key = ("emoji", char, size, colour)
    if key not in _fonts:
        try:
            font = pygame.font.SysFont("segoeuiemoji", size)
            _fonts[key] = font.render(char, True, colour)
        except Exception:
            _fonts[key] = None
    return _fonts[key]


def _outlined(screen, surf_white, surf_black, x, y):
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        screen.blit(surf_black, (x + dx, y + dy))
    screen.blit(surf_white, (x, y))


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
            colour = game.tile_color[game.grid[j][i]]
            f = game.flash.get((i, j), 0.0)
            if f > 0:
                colour = tuple(int(c + (255 - c) * f * 0.7) for c in colour)
            pygame.draw.rect(surf, colour,
                             (i * TILE + GAP, j * TILE + GAP, TILE - GAP, TILE - GAP))

    for pad in game.pads:
        pulse = 1.0 + 0.08 * math.sin(pad.age * 4)
        r = int(PAD_RADIUS * pulse)
        px, py = int(pad.x), int(pad.y)
        if pad.kind == "release":
            if game.anticipation:  # beat: the red pad throbs urgently
                r = int(r * (1.1 + 0.15 * math.sin(pad.age * 18)))
            pygame.draw.circle(surf, (60, 18, 22), (px, py), r)
            pygame.draw.circle(surf, RED, (px, py), r, 4)
            draw_icon(surf, "bomb", px, py, int(r * 0.6))
        else:
            pygame.draw.circle(surf, (16, 50, 30), (px, py), r)
            pygame.draw.circle(surf, GREEN, (px, py), r, 4)
            lbl = _font(24).render(f"x{pad.kind}", True, WHITE)
            surf.blit(lbl, (px - lbl.get_width() / 2, py - lbl.get_height() / 2))

    for pu in game.powerups:
        pulse = 1.0 + 0.12 * math.sin(pu.age * 5)
        r = int(PU_RADIUS * pulse)
        pygame.draw.circle(surf, (25, 25, 35), (int(pu.x), int(pu.y)), r)
        pygame.draw.circle(surf, GOLD, (int(pu.x), int(pu.y)), r, 4)
        draw_icon(surf, pu.kind, int(pu.x), int(pu.y), int(r * 0.62))

    for p in game.particles:
        pygame.draw.circle(surf, p[5], (int(p[0]), int(p[1])), max(1, int(p[6] * min(1, p[4] * 2))))

    for p in game.pellets:
        pygame.draw.circle(surf, game.ball_color[p[4]], (int(p[0]), int(p[1])), 5)
        pygame.draw.circle(surf, WHITE, (int(p[0]), int(p[1])), 5, 1)

    for s in game.shots:
        r = BALL_RADIUS + min(18, int(s["power"] ** 0.5))
        pygame.draw.circle(surf, game.tile_color[s["team"]], (int(s["x"]), int(s["y"])), r)
        pygame.draw.circle(surf, WHITE, (int(s["x"]), int(s["y"])), r, 3)
        lbl = _font(22).render(str(s["power"]), True, WHITE)
        surf.blit(lbl, (s["x"] - lbl.get_width() / 2, s["y"] - lbl.get_height() / 2))

    for ball in game.balls:
        for k, (tx, ty) in enumerate(ball.trail):
            frac = (k + 1) / len(ball.trail)
            r = int(BALL_RADIUS * frac * 0.7)
            if r > 0:
                t = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(t, game.ball_color[ball.team] + (int(110 * frac),), (r, r), r)
                surf.blit(t, (tx - r, ty - r))
        bx, by = int(ball.x), int(ball.y)

        # Danger indicator: high-value balls must LOOK dangerous at a glance.
        # 16+: soft team glow. 64+: pulsing red ring. 128+: second ring.
        # 256: third ring in gold. Pulse speeds up with the tier.
        if ball.value >= 16:
            glow_r = BALL_RADIUS + 14
            g = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(g, game.ball_color[ball.team] + (70,), (glow_r, glow_r), glow_r)
            surf.blit(g, (bx - glow_r, by - glow_r))
        if ball.value >= ANTICIPATION_VALUE:
            tier = 1 + (ball.value >= 128) + (ball.value >= 256)
            pulse = 0.5 + 0.5 * math.sin(game.elapsed * (5 + 2 * tier))
            for k in range(tier):
                colour = GOLD if (k == 2) else RED
                rr = BALL_RADIUS + 6 + k * 6 + int(pulse * 4)
                pygame.draw.circle(surf, colour, (bx, by), rr, 2 + (k == 0))

        pygame.draw.circle(surf, game.ball_color[ball.team], (bx, by), BALL_RADIUS)
        ring = WHITE
        if game.freeze_t[ball.team] > 0:
            ring = ICE
        elif game.boost_t[ball.team] > 0:
            ring = GOLD
        pygame.draw.circle(surf, ring, (bx, by), BALL_RADIUS, 3)
        # Identity when idle, threat when charged: theme emoji at value 1,
        # the carried number once the ball is worth something.
        icon = None
        if ball.value <= 1:
            icon = _emoji(game.team_emoji[ball.team], 30, (10, 10, 16))
        if icon is not None:
            surf.blit(icon, (bx - icon.get_width() / 2, by - icon.get_height() / 2))
        else:
            size = 20 if ball.value < 100 else 16
            lbl = _font(size).render(str(ball.value), True, (10, 10, 16))
            surf.blit(lbl, (ball.x - lbl.get_width() / 2, ball.y - lbl.get_height() / 2))


def compose_frame(world, canvas, game):
    """World -> canvas with camera effects (anticipation zoom + screen shake).
    Shared by the live window and render.py so videos match the preview."""
    src = world
    if game.anticipation:
        a = game.anticipation
        frac = a["t"] / ANTICIPATION_SECONDS          # 1 -> 0 over the beat
        z = 1.0 + ANTICIPATION_ZOOM * math.sin(frac * math.pi)
        cw, ch = int(WIDTH / z), int(HEIGHT / z)
        cx = min(max(int(a["x"] - cw / 2), 0), WIDTH - cw)
        cy = min(max(int(a["y"] - ch / 2), 0), HEIGHT - ch)
        src = pygame.transform.smoothscale(
            world.subsurface((cx, cy, cw, ch)), (WIDTH, HEIGHT))
    ox = oy = 0
    if game.shake_t > 0:
        mag = game.shake_t * 10
        ox, oy = random.uniform(-mag, mag), random.uniform(-mag, mag)
    canvas.fill(BG_COLOR)
    canvas.blit(src, (ox, oy))


def draw_hud(screen, game, font, big_font):
    left, right = game.count_tiles()
    total = left + right
    left_frac = left / total
    left_pct = round(left_frac * 100)

    bar_h, bar_w = 34, WIDTH - 40
    x0, y0 = 20, 20
    split = int(bar_w * left_frac)
    pygame.draw.rect(screen, game.tile_color[LEFT], (x0, y0, split, bar_h), border_radius=16)
    pygame.draw.rect(screen, game.tile_color[RIGHT], (x0 + split, y0, bar_w - split, bar_h),
                     border_radius=16)
    pygame.draw.rect(screen, WHITE, (x0 + split - 2, y0, 4, bar_h))

    # Team names live on the bar for the whole video - the matchup IS the
    # hook, it can't only appear at the winner screen. Outlined for contrast
    # on any bar colour.
    for team, align in ((LEFT, "l"), (RIGHT, "r")):
        name = game.team_names[team]
        w_surf = _font(20).render(name, True, WHITE)
        b_surf = _font(20).render(name, True, (10, 10, 16))
        nx = x0 + 12 if align == "l" else x0 + bar_w - w_surf.get_width() - 12
        _outlined(screen, w_surf, b_surf, nx, y0 + bar_h / 2 - w_surf.get_height() / 2)

    screen.blit(big_font.render(f"{left_pct}%", True, WHITE), (x0 + 8, y0 + bar_h + 6))
    rbl = big_font.render(f"{100 - left_pct}%", True, WHITE)
    screen.blit(rbl, (x0 + bar_w - rbl.get_width() - 8, y0 + bar_h + 6))

    remaining = max(0, MATCH_SECONDS - game.elapsed)
    colour = GOLD if remaining <= 10 else (230, 230, 230)
    timer = font.render(f"{remaining:0.0f}", True, colour)
    screen.blit(timer, (WIDTH / 2 - timer.get_width() / 2, y0 + bar_h + 8))

    # Anticipation beat: "128 POWER!" flash in the team's colour
    if game.anticipation:
        a = game.anticipation
        frac = a["t"] / ANTICIPATION_SECONDS
        grow = 1.0 + 0.25 * math.sin(frac * math.pi)
        lbl = _font(int(56 * grow)).render(
            f"{a['value']} POWER!", True, game.tile_color[a["team"]])
        outline = _font(int(56 * grow)).render(f"{a['value']} POWER!", True, WHITE)
        x = WIDTH / 2 - lbl.get_width() / 2
        y = HEIGHT * 0.18
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            screen.blit(outline, (x + dx, y + dy))
        screen.blit(lbl, (x, y))

    if game.finished:
        # Winner screen payoff: not just a banner - the match's stats are
        # the story (final split, biggest hit, lead changes).
        bg = pygame.Surface((WIDTH, 340), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 185))
        top = HEIGHT / 2 - 170
        screen.blit(bg, (0, top))

        if game.winner is None:
            text, colour = "DRAW", WHITE
        else:
            text = f"{game.team_names[game.winner]} WINS"
            colour = game.tile_color[game.winner]
        size = 64
        banner = _font(size).render(text, True, colour)
        while banner.get_width() > WIDTH - 40 and size > 28:  # long team names
            size -= 4
            banner = _font(size).render(text, True, colour)
        screen.blit(banner, (WIDTH / 2 - banner.get_width() / 2, top + 24))

        lp = round(100 * left / total)
        score = _font(48).render(f"{lp}%  -  {100 - lp}%", True, WHITE)
        screen.blit(score, (WIDTH / 2 - score.get_width() / 2, top + 116))

        if game.biggest_hit["value"] > 1:
            kind = "BURST" if game.biggest_hit["type"] == "burst" else "CHARGED"
            hit = _font(32).render(
                f"BIGGEST HIT  {game.biggest_hit['value']}  ({kind})", True, GOLD)
            screen.blit(hit, (WIDTH / 2 - hit.get_width() / 2, top + 196))

        lc = _font(32).render(f"LEAD CHANGES  {game.lead_changes}", True, (210, 210, 220))
        screen.blit(lc, (WIDTH / 2 - lc.get_width() / 2, top + 248))


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

    import audio
    sounds = audio.load_sounds()

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        game.update(1 / FPS)
        for cue in game.sound_events:
            if cue in sounds:
                sounds[cue].play()

        draw_world(world, game)
        compose_frame(world, canvas, game)
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
