# Territory Clash

2D battle simulator for short-form video content. Two guns fire balls at each
other across a split screen; balls settle and claim territory by color.
Random powerups (multiply, freeze, steal, etc.) shake up the outcome.

## Status

v1: two guns, projectile physics, live left/right territory split. No
powerups yet.

## Setup

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Roadmap

1. Core sim: guns, projectiles, territory counter — **current**
2. Visual polish: colors, particles, glow/trails
3. Powerups: multiply, freeze, steal, shield, speed
4. Headless render-to-video pipeline (ffmpeg) for batch content production
