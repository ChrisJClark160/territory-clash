import random
import sys

import pygame
import pymunk

WIDTH, HEIGHT = 720, 1280  # vertical, matches Shorts/TikTok aspect
FPS = 60

LEFT_COLOR = (255, 45, 140)   # neon pink
RIGHT_COLOR = (45, 220, 255)  # neon cyan
BG_COLOR = (15, 15, 25)

BALL_RADIUS = 10
GRAVITY = 900
FIRE_INTERVAL_RANGE = (0.4, 0.9)  # seconds between shots, per gun


class Gun:
    def __init__(self, x, y, color, aim_dx, side):
        self.x = x
        self.y = y
        self.color = color
        self.aim_dx = aim_dx  # base horizontal aim direction
        self.side = side  # "left" or "right"
        self.next_fire = random.uniform(*FIRE_INTERVAL_RANGE)

    def update(self, dt, space, balls):
        self.next_fire -= dt
        if self.next_fire <= 0:
            self.fire(space, balls)
            self.next_fire = random.uniform(*FIRE_INTERVAL_RANGE)

    def fire(self, space, balls):
        body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL_RADIUS))
        body.position = (self.x, self.y)
        speed = random.uniform(500, 700)
        angle_jitter = random.uniform(-0.3, 0.3)
        vx = self.aim_dx * speed
        vy = -speed * 0.6 + angle_jitter * speed
        body.velocity = (vx, vy)

        shape = pymunk.Circle(body, BALL_RADIUS)
        shape.elasticity = 0.4
        shape.friction = 0.6
        shape.color = self.color
        shape.owner = self.side
        space.add(body, shape)
        balls.append(shape)


def make_space():
    space = pymunk.Space()
    space.gravity = (0, GRAVITY)

    floor = pymunk.Segment(space.static_body, (0, HEIGHT - 5), (WIDTH, HEIGHT - 5), 5)
    floor.elasticity = 0.3
    floor.friction = 0.8
    left_wall = pymunk.Segment(space.static_body, (5, 0), (5, HEIGHT), 5)
    right_wall = pymunk.Segment(space.static_body, (WIDTH - 5, 0), (WIDTH - 5, HEIGHT), 5)
    for wall in (left_wall, right_wall):
        wall.elasticity = 0.5
        wall.friction = 0.5
    space.add(floor, left_wall, right_wall)
    return space


def count_territory(balls):
    left = sum(1 for b in balls if b.body.position.x < WIDTH / 2)
    right = len(balls) - left
    return left, right


def draw_scoreboard(screen, font, left, right):
    total = max(left + right, 1)
    left_frac = left / total
    bar_h = 28
    bar_w = WIDTH - 40
    x0, y0 = 20, 20

    pygame.draw.rect(screen, (40, 40, 55), (x0, y0, bar_w, bar_h), border_radius=14)
    pygame.draw.rect(screen, LEFT_COLOR, (x0, y0, int(bar_w * left_frac), bar_h), border_radius=14)
    pygame.draw.rect(
        screen, RIGHT_COLOR,
        (x0 + int(bar_w * left_frac), y0, bar_w - int(bar_w * left_frac), bar_h),
        border_radius=14,
    )

    label = font.render(f"{left}  |  {right}", True, (255, 255, 255))
    screen.blit(label, (WIDTH / 2 - label.get_width() / 2, y0 + bar_h + 8))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Territory Clash - v1")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 28, bold=True)

    space = make_space()
    balls = []

    guns = [
        Gun(60, HEIGHT - 100, LEFT_COLOR, aim_dx=1, side="left"),
        Gun(WIDTH - 60, HEIGHT - 100, RIGHT_COLOR, aim_dx=-1, side="right"),
    ]

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        for gun in guns:
            gun.update(dt, space, balls)

        space.step(1 / FPS)

        screen.fill(BG_COLOR)
        pygame.draw.line(screen, (60, 60, 75), (WIDTH / 2, 0), (WIDTH / 2, HEIGHT), 2)

        for shape in balls:
            pos = shape.body.position
            pygame.draw.circle(screen, shape.color, (int(pos.x), int(pos.y)), BALL_RADIUS)

        for gun in guns:
            pygame.draw.circle(screen, gun.color, (gun.x, gun.y), 18)

        left, right = count_territory(balls)
        draw_scoreboard(screen, font, left, right)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
