"""Audio for Territory Clash - procedural SFX, offline track building.

All sound effects are synthesized in pure stdlib (wave + math) into
assets/sfx/ on first use - no external assets, nothing to license.

Two consumers:
- main.py plays cues live through pygame.mixer.
- render.py collects (timestamp, cue) pairs during the sim and calls
  build_track() to mix them into a WAV that ffmpeg muxes under the video,
  optionally with a music bed from music/ (drop an NCS mp3 there and credit
  it in the video description - see DESIGN.md).
"""

import array
import math
import os
import random
import wave

SR = 44100
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sfx")

CUES = ("pad_green", "pad_red", "burst", "charge", "explosion",
        "anticipation", "winner", "powerup", "freeze", "lead_flip")


# -- synthesis ---------------------------------------------------------------

def _env(i, n, attack=0.01, decay=4.0):
    t = i / n
    a = min(1.0, t / attack) if attack > 0 else 1.0
    return a * math.exp(-decay * t)


def _sweep(f0, f1, dur, vol=0.5, decay=4.0, wave_fn=math.sin):
    n = int(SR * dur)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / n
        f = f0 + (f1 - f0) * t
        phase += 2 * math.pi * f / SR
        out.append(wave_fn(phase) * vol * _env(i, n, decay=decay))
    return out


def _noise(dur, vol=0.5, decay=5.0, gate_hz=0.0):
    rng = random.Random(1234)
    n = int(SR * dur)
    out = []
    prev = 0.0
    for i in range(n):
        raw = rng.random() * 2 - 1
        prev = prev * 0.7 + raw * 0.3          # crude lowpass, softer noise
        s = prev * vol * _env(i, n, decay=decay)
        if gate_hz:                             # amplitude gate = machine-gun
            s *= 0.5 + 0.5 * math.copysign(1, math.sin(2 * math.pi * gate_hz * i / SR))
        out.append(s)
    return out


def _tone(freq, dur, vol=0.4, decay=3.0):
    return _sweep(freq, freq, dur, vol, decay)


def _mix(*parts):
    n = max(len(p) for p in parts)
    out = [0.0] * n
    for p in parts:
        for i, s in enumerate(p):
            out[i] += s
    return out


def _concat(*parts):
    out = []
    for p in parts:
        out.extend(p)
    return out


def _build_cue(name):
    if name == "pad_green":
        return _concat(_tone(660, 0.07, 0.35), _tone(990, 0.10, 0.35))
    if name == "pad_red":
        return _concat(_tone(440, 0.09, 0.45), _tone(330, 0.16, 0.45))
    if name == "burst":
        return _noise(0.45, 0.5, decay=3.0, gate_hz=14)
    if name == "charge":
        return _sweep(320, 70, 0.5, 0.55, decay=2.5)
    if name == "explosion":
        return _mix(_noise(0.6, 0.7, decay=4.5), _sweep(120, 40, 0.5, 0.4, decay=3.0))
    if name == "anticipation":
        return _sweep(220, 1300, 0.9, 0.30, decay=0.4)
    if name == "winner":
        notes = [523, 659, 784, 1047]
        return _concat(*[_tone(f, 0.16, 0.4, decay=2.0) for f in notes])
    if name == "powerup":
        return _concat(_tone(880, 0.06, 0.3), _tone(1175, 0.09, 0.3))
    if name == "freeze":
        return _sweep(1400, 500, 0.35, 0.35, decay=2.0)
    if name == "lead_flip":
        return _concat(_tone(700, 0.07, 0.4), _tone(1050, 0.13, 0.4))
    raise ValueError(name)


def _write_wav(path, samples):
    a = array.array("h", (int(max(-1.0, min(1.0, s)) * 32000) for s in samples))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(a.tobytes())


def ensure_sfx():
    """Generate all cue WAVs into assets/sfx/ if not already present."""
    os.makedirs(SFX_DIR, exist_ok=True)
    for name in CUES:
        path = os.path.join(SFX_DIR, f"{name}.wav")
        if not os.path.exists(path):
            _write_wav(path, _build_cue(name))
    return SFX_DIR


# -- offline track building (render.py) --------------------------------------

def _read_wav(path):
    with wave.open(path, "rb") as w:
        raw = w.readframes(w.getnframes())
    a = array.array("h")
    a.frombytes(raw)
    return [s / 32768.0 for s in a]


def build_track(events, duration_s, out_path):
    """Mix (timestamp_seconds, cue_name) events into a mono WAV."""
    ensure_sfx()
    cache = {}
    total = int(SR * duration_s)
    mix = array.array("f", bytes(4 * total))  # zeros

    last_at = {}  # cue -> last timestamp placed, to avoid harsh stacking
    for t, name in events:
        if name not in CUES:
            continue
        if t - last_at.get(name, -1.0) < 0.06:
            continue
        last_at[name] = t
        if name not in cache:
            cache[name] = _read_wav(os.path.join(SFX_DIR, f"{name}.wav"))
        start = int(t * SR)
        cue = cache[name]
        for i, s in enumerate(cue):
            j = start + i
            if j >= total:
                break
            mix[j] += s

    _write_wav(out_path, mix)
    return out_path


# -- live playback (main.py) --------------------------------------------------

def load_sounds():
    """Load cues as pygame Sounds. Returns {} if the mixer is unavailable."""
    import pygame
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except pygame.error:
        return {}
    ensure_sfx()
    return {name: pygame.mixer.Sound(os.path.join(SFX_DIR, f"{name}.wav"))
            for name in CUES}
