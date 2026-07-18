"""Render a Territory Clash battle to a YouTube-ready MP4.

Runs the simulation headless (no window), draws every frame at full
720x1280@60fps, and pipes raw frames into ffmpeg (bundled via
imageio-ffmpeg, no system install needed). Output is H.264 / yuv420p with
faststart - exactly what YouTube wants.

Usage:
    python render.py                          # random battle, default theme
    python render.py 12345                    # reproduce a specific seed
    python render.py 12345 out.mp4            # choose the output path
    python render.py 12345 out.mp4 fire_vs_ice     # themed (see themes.py)
    python render.py 12345 out.mp4 fire_vs_ice 40  # 40s battle

The video opens on a baked-in title card (the matchup IS the hook), runs
the full match, and ends with a short winner banner + confetti.
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
import describe
import main as sim

OUTRO_SECONDS = 2   # winner banner + confetti; short - retention feeds loops
TITLE_SECONDS = 1.0  # opening matchup card, fades out over the last 0.3s
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


def _title_card(game):
    """Full-width matchup card: team A, VS, team B, with emoji. Baked into
    the first second of the video - the swipe-away decision happens before
    the bar and percentages mean anything, so the matchup must be instant."""
    card = pygame.Surface((sim.WIDTH, 420), pygame.SRCALPHA)
    card.fill((8, 8, 14, 235))
    pygame.draw.rect(card, sim.GOLD, (0, 0, sim.WIDTH, 420), 3)
    rows = (
        (game.team_names[sim.LEFT], game.tile_color[sim.LEFT],
         game.team_emoji[sim.LEFT], 46, 64),
        ("VS", sim.GOLD, "", 172, 76),
        (game.team_names[sim.RIGHT], game.tile_color[sim.RIGHT],
         game.team_emoji[sim.RIGHT], 292, 64),
    )
    for text, colour, emoji, y, size in rows:
        lbl = sim._font(size).render(text, True, colour)
        while lbl.get_width() > sim.WIDTH - 200 and size > 30:
            size -= 4
            lbl = sim._font(size).render(text, True, colour)
        icon = sim._emoji(emoji, size, sim.WHITE) if emoji else None
        w = lbl.get_width() + (icon.get_width() + 18 if icon else 0)
        x = (sim.WIDTH - w) / 2
        if icon:
            card.blit(icon, (x, y + (lbl.get_height() - icon.get_height()) / 2))
            x += icon.get_width() + 18
        card.blit(lbl, (x, y))
    return card


def render(seed=None, out_path=None, theme=None, match_seconds=None):
    pygame.init()
    pygame.display.set_mode((1, 1))  # dummy driver; needed for convert/fonts
    sim._fonts.clear()  # cached fonts die when pygame.quit()s between renders

    game = sim.Game(seed, theme=theme, match_seconds=match_seconds)
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

    max_frames = sim.FPS * (game.match_seconds + 30)  # hard safety stop
    outro_frames = sim.FPS * OUTRO_SECONDS
    frame = 0
    outro = 0
    audio_events = []  # (timestamp_seconds, cue) for the offline SFX track
    title_card = _title_card(game)
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

        t = frame / sim.FPS
        if t < TITLE_SECONDS:
            fade = 1.0 if t < TITLE_SECONDS - 0.3 else (TITLE_SECONDS - t) / 0.3
            title_card.set_alpha(int(255 * fade))
            canvas.blit(title_card,
                        (0, (sim.HEIGHT - title_card.get_height()) / 2))

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
    winner = (game.team_names[game.winner] if game.winner is not None else "DRAW")
    size_mb = os.path.getsize(out_path) / 1e6

    # Metadata sidecar: titles/descriptions get generated from what actually
    # happened in this battle, not a generic template (DESIGN.md Phase A.5).
    meta = {
        "seed": game.seed,
        "teams": list(game.team_names),
        "winner": winner,
        "final_score": [round(left * 100 / total), round(right * 100 / total)],
        "biggest_power": game.biggest_hit["value"],
        "biggest_event": game.biggest_hit["type"],
        "biggest_hit_t": game.biggest_hit["t"],
        "lead_changes": game.lead_changes,
        "lead_change_times": game.lead_change_times,
        "max_swing": game.max_swing,
        "match_seconds": game.match_seconds,
        "events": game.events,
        "powerups": game.collected,
        "timeline": game.event_log,
        "duration_s": frame // sim.FPS,
        "file": os.path.basename(out_path),
    }
    meta_path = os.path.splitext(out_path)[0] + ".json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    # Upload packaging: title/pinned comment/description generated from what
    # actually happened in this battle.
    txt_path = describe.write_for(meta, out_path,
                                  music=os.path.basename(music) if music else None)

    print(f"done: {frame} frames ({frame // sim.FPS}s), {winner} wins "
          f"{round(left * 100 / total)}/{round(right * 100 / total)}, "
          f"{size_mb:.1f} MB, took {time.time() - t0:.0f}s")
    print(f"meta: {meta_path}")
    print(f"text: {txt_path}")
    return out_path


if __name__ == "__main__":
    seed_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    path_arg = sys.argv[2] if len(sys.argv) > 2 else None
    theme_arg = None
    if len(sys.argv) > 3:
        from themes import THEMES
        theme_arg = THEMES[sys.argv[3]]
    seconds_arg = int(sys.argv[4]) if len(sys.argv) > 4 else None
    render(seed_arg, path_arg, theme_arg, seconds_arg)
