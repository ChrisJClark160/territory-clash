# Territory Clash - Working Document

Living status + task doc. Update at the end of each working session.

Last updated: 2026-07-02

---

## The Goal

A YouTube channel (Shorts/TikTok/Reels format) in the "territory wars" simulation
genre - same lane as [Marbles2D](https://www.youtube.com/@Marbles2D).

The video must be:
- **Engaging - glued to watching.** Momentum and reversals: someone's winning,
  then it swings. Uncertain outcome to the last second.
- **Lots of colour, eye-catching.** Vivid neon, satisfying spreading-paint look,
  impact flashes and powerup pulses.
- **Instantly understandable, no language barrier.** The colour bar and two
  percentages tell the whole story. No sentences needed.
- **Watchable by a kid, but not childish.** Clean, tense, slightly hypnotic.
  A 6-year-old and a 40-year-old both get it in one second.

**The single most important lever: the outcome must stay uncertain and swing.**
Powerups (multiply, steal, freeze) are the "oh!" moments that stop the scroll.

---

## Design Rules (derived from the goal)

- Only on-screen text = the two percentages + a timer. Nothing else.
- Pink vs Cyan. High contrast, readable when small/muted on a phone.
- Drama comes from: more balls, balls that speed up, and powerups that cause
  sudden swings. A flat 49/51 stalemate is the enemy - it must churn.
- Every flip/impact/powerup should have visual juice (flash, pulse, particles).

---

## Tech Stack

- **Python 3.14 + pygame-ce** (NOT `pygame` - see gotchas).
- Core collision is **custom circle-vs-grid maths**, no physics engine.
  (pymunk was used in v1, removed in v2 - it got in the way of tile-flipping.)
- Planned: **ffmpeg** for headless batch render-to-video.

### Run it
```
cd C:\Users\ChrisClark\Documents\GitHub\territory-clash
venv\Scripts\activate
python main.py
```
ESC or window close to quit.

---

## Where We Are

**Current: v3 - engagement update. Powerups, rubber-banding, escalation, juice.**

On top of the v2 tile-flip arena:
- **4 powerups**, pictographic icons, gold pulsing pickups: multiply (+2 balls,
  cap 6/team), bomb (blast-converts tiles in radius, screen shake), freeze
  (enemy balls stop 2.5s, ice ring), speed (+60% for 4s, gold ring).
- **Rubber-banding**: losing side's balls speed up, leader's slow down; a team
  with fewer balls gets faster balls (damps the multiply snowball). The leader
  penalty fades over the final 10s ("no mercy") so endings break open.
- **Escalation**: pace ramps up to +50% by the end - finale is the wildest part.
- **Juice**: tile-flip flash + sparks, pickup bursts, screen shake, confetti on
  the winner banner, timer goes gold in the last 10s.
- **Seeded**: `python main.py 12345` reproduces a battle; seed printed each run.
- 60s matches.

Verified headless across 5 seeds: tiles conserved, balls in bounds, and the
drama metrics show a healthy mix of narratives - comeback nailbiters (4 lead
changes, 51/48 finishes) and dominant wins where the loser still never drops
below ~39%. Mixed story shapes across videos is deliberate: it is the novelty
between videos.

---

## Task Board

### Done
- [x] Repo created + cloned locally, pushed to GitHub
- [x] v1 scaffold (guns + pymunk) - superseded
- [x] Reviewed v1, found scoring was position-based and incoherent
- [x] v2 rebuild as tile-flip arena, pymunk dropped
- [x] Headless verification of the core mechanic

### Next (in priority order)
- [ ] **Phase A: "Multiply or Release"** - balls carry a visible multiplying
      number, cashed in at red pads as a burst attack or charged shot.
      See DESIGN.md. Fixes the "feels predetermined" problem via anticipation.
- [ ] Eyeball a few full 60s runs on screen; tune anything that feels off
      (powerup cadence, bomb size, trail length)
- [ ] NCS music track muxed in at the ffmpeg stage (see DESIGN.md - audio plan)
- [ ] Title/thumbnail template; patch-note style descriptions, "Who will win?"
- [ ] First batch of videos, test on platform before scaling cadence
- [ ] Phase B: four teams + elimination/revival (DESIGN.md)
- [ ] Phase C: long-form flagship, pixel territory, shields (DESIGN.md)

### Done - render pipeline (2026-07-02)
- [x] `render.py`: headless sim -> ffmpeg (bundled, no install) -> MP4.
      H.264/yuv420p/720x1280/60fps/faststart, 4s winner outro. A 64s battle
      renders in ~49s. Usage: `python render.py [seed] [out.mp4]`,
      output lands in `output/`.

### Done in v3 (2026-07-02)
- [x] Tune for drama - rubber-banding + ball-count equalizer + escalation
- [x] Multiply powerup (+ bomb, freeze, speed)
- [x] Visual juice - flip flash, sparks, bursts, shake, confetti, gold timer

### Later / ideas
- Themed skins (space, medieval, sports colours)
- Tournament brackets, viewer-suggested powerup combos
- If hand-tuning per video becomes the bottleneck, that's the trigger to invest
  more in batch automation

---

## Gotchas / Notes

- **Use `pygame-ce`, not `pygame`.** Python 3.14 has no prebuilt `pygame` wheel;
  it tries to compile from source and fails. `pygame-ce` has a 3.14 wheel.
- **GitHub auth:** this repo is under the personal account `ChrisJClark160`.
  The machine also has the work account `MDUKChris`. Pushes need the
  ChrisJClark160 token active (`gh auth switch --user ChrisJClark160`). The
  plaintext `~/.git-credentials` store currently points at ChrisJClark160.
