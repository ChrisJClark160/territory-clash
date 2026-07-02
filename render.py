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

import json
import os
import subprocess
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import imageio_ffmpeg
import pygame

import audio
import main as sim

OUTRO_SECONDS = 4  # winner banner + confetti after the match ends
MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")
MUSIC_VOLUME = 0.30  # music bed sits under the SFX


def _find_music():
    """First audio file in music/ (drop an NCS mp3 there), else None."""
    if not os.path.isdir(MUSIC_DIR):
        return None
    for f in sorted(os.listdir(MUSIC_DIR)):
        if f.lower().endswith((".mp3", ".wav", ".ogg", ".m4a", ".flac")):
            return os.path.join(MUSIC_DIR, f)
    return None


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
    video_tmp = out_path + ".video.mp4"
    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{sim.WIDTH}x{sim.HEIGHT}", "-r", str(sim.FPS),
        "-i", "-",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        video_tmp,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    max_frames = sim.FPS * (sim.MATCH_SECONDS + 30)  # hard safety stop
    outro_frames = sim.FPS * OUTRO_SECONDS
    frame = 0
    outro = 0
    audio_events = []  # (timestamp_seconds, cue) for the offline SFX track
    t0 = time.time()
    print(f"seed: {game.seed}")
    print(f"rendering -> {out_path}")

    while outro < outro_frames and frame < max_frames:
        game.update(1 / sim.FPS)
        for cue in game.sound_events:
            audio_events.append((frame / sim.FPS, cue))
        if game.finished:
            outro += 1

        sim.draw_world(world, game)
        sim.compose_frame(world, canvas, game)
        sim.draw_hud(canvas, game, font, big_font)

        proc.stdin.write(pygame.image.tobytes(canvas, "RGB"))
        frame += 1
        if frame % (sim.FPS * 10) == 0:
            print(f"  {frame // sim.FPS}s simulated "
                  f"({frame / (time.time() - t0):.0f} fps render speed)")

    proc.stdin.close()
    proc.wait()
    pygame.quit()

    # Build the SFX track and mux audio (+ optional music bed) into the video
    duration = frame / sim.FPS
    sfx_wav = out_path + ".sfx.wav"
    audio.build_track(audio_events, duration, sfx_wav)
    music = _find_music()
    if music:
        mux = [ffmpeg, "-y", "-i", video_tmp, "-i", sfx_wav,
               "-stream_loop", "-1", "-i", music,
               "-filter_complex",
               f"[2:a]volume={MUSIC_VOLUME}[m];"
               f"[1:a][m]amix=inputs=2:duration=first[a]",
               "-map", "0:v", "-map", "[a]",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
               "-shortest", "-movflags", "+faststart", out_path]
        print(f"music bed: {os.path.basename(music)}")
    else:
        mux = [ffmpeg, "-y", "-i", video_tmp, "-i", sfx_wav,
               "-map", "0:v", "-map", "1:a",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
               "-shortest", "-movflags", "+faststart", out_path]
    subprocess.run(mux, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(video_tmp)
    os.remove(sfx_wav)

    left, right = game.count_tiles()
    total = left + right
    winner = ("PINK" if game.winner == sim.LEFT else
              "CYAN" if game.winner == sim.RIGHT else "DRAW")
    size_mb = os.path.getsize(out_path) / 1e6

    # Metadata sidecar: titles/descriptions get generated from what actually
    # happened in this battle, not a generic template (DESIGN.md Phase A.5).
    meta = {
        "seed": game.seed,
        "winner": winner,
        "final_score": [round(left * 100 / total), round(right * 100 / total)],
        "biggest_power": game.biggest_hit["value"],
        "biggest_event": game.biggest_hit["type"],
        "lead_changes": game.lead_changes,
        "max_swing": game.max_swing,
        "events": game.events,
        "powerups": game.collected,
        "duration_s": frame // sim.FPS,
        "file": os.path.basename(out_path),
    }
    meta_path = os.path.splitext(out_path)[0] + ".json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"done: {frame} frames ({frame // sim.FPS}s), {winner} wins "
          f"{round(left * 100 / total)}/{round(right * 100 / total)}, "
          f"{size_mb:.1f} MB, took {time.time() - t0:.0f}s")
    print(f"meta: {meta_path}")
    return out_path


if __name__ == "__main__":
    seed_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    path_arg = sys.argv[2] if len(sys.argv) > 2 else None
    render(seed_arg, path_arg)
