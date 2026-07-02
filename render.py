"""Render a Territory Clash battle to a YouTube-ready MP4.

Runs the simulation headless (no window), draws every frame at full
720x1280@60fps, and pipes raw frames into ffmpeg (bundled via
imageio-ffmpeg, no system install needed). Output is H.264 / yuv420p with
faststart - exactly what YouTube wants.

Usage:
    python render.py                # random battle -> output/battle_<seed>.mp4
    python render.py 12345          # reproduce a specific seed
    python render.py 12345 out.mp4  # choose the output path

The video runs the full match plus a few seconds of the winner banner and
confetti so the payoff isn't cut off.
"""

import os
import random
import subprocess
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import imageio_ffmpeg
import pygame

import main as sim

OUTRO_SECONDS = 4  # winner banner + confetti after the match ends


def render(seed=None, out_path=None):
    pygame.init()
    pygame.display.set_mode((1, 1))  # dummy driver; needed for convert/fonts

    game = sim.Game(seed)
    if out_path is None:
        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", f"battle_{game.seed}.mp4")

    font = pygame.font.SysFont("arial", 26, bold=True)
    big_font = pygame.font.SysFont("arial", 44, bold=True)
    world = pygame.Surface((sim.WIDTH, sim.HEIGHT))
    canvas = pygame.Surface((sim.WIDTH, sim.HEIGHT))

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{sim.WIDTH}x{sim.HEIGHT}", "-r", str(sim.FPS),
        "-i", "-",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    max_frames = sim.FPS * (sim.MATCH_SECONDS + 30)  # hard safety stop
    outro_frames = sim.FPS * OUTRO_SECONDS
    frame = 0
    outro = 0
    t0 = time.time()
    print(f"seed: {game.seed}")
    print(f"rendering -> {out_path}")

    while outro < outro_frames and frame < max_frames:
        game.update(1 / sim.FPS)
        if game.finished:
            outro += 1

        sim.draw_world(world, game)
        ox = oy = 0
        if game.shake_t > 0:
            mag = game.shake_t * 10
            ox, oy = random.uniform(-mag, mag), random.uniform(-mag, mag)
        canvas.fill(sim.BG_COLOR)
        canvas.blit(world, (ox, oy))
        sim.draw_hud(canvas, game, font, big_font)

        proc.stdin.write(pygame.image.tobytes(canvas, "RGB"))
        frame += 1
        if frame % (sim.FPS * 10) == 0:
            print(f"  {frame // sim.FPS}s simulated "
                  f"({frame / (time.time() - t0):.0f} fps render speed)")

    proc.stdin.close()
    proc.wait()
    pygame.quit()

    left, right = game.count_tiles()
    total = left + right
    winner = ("PINK" if game.winner == sim.LEFT else
              "CYAN" if game.winner == sim.RIGHT else "DRAW")
    size_mb = os.path.getsize(out_path) / 1e6
    print(f"done: {frame} frames ({frame // sim.FPS}s), {winner} wins "
          f"{round(left * 100 / total)}/{round(right * 100 / total)}, "
          f"{size_mb:.1f} MB, took {time.time() - t0:.0f}s")
    return out_path


if __name__ == "__main__":
    seed_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    path_arg = sys.argv[2] if len(sys.argv) > 2 else None
    render(seed_arg, path_arg)
