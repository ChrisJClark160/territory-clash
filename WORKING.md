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

**Current: v2 - tile-flip arena core, committed (`78e5e41`).**

Bounded 18x32 tile arena, left half pink / right half cyan. One ball per team
roams and flips enemy tiles on contact, ricocheting off. Scoreboard tracks
tiles owned. Fading trail, white ring, timer, winner banner. Verified headless:
tiles conserved, balls stay in bounds.

**Known issue:** with one ball per side at constant speed the score barely moves
(~48/52 over 90s). Correct skeleton, but too flat to be engaging yet. Tuning +
powerups are what make it a watchable video.

---

## Task Board

### Done
- [x] Repo created + cloned locally, pushed to GitHub
- [x] v1 scaffold (guns + pymunk) - superseded
- [x] Reviewed v1, found scoring was position-based and incoherent
- [x] v2 rebuild as tile-flip arena, pymunk dropped
- [x] Headless verification of the core mechanic

### Next (in priority order)
- [ ] **Tune for drama** - 2-3 balls per side, higher speed, so the board churns
- [ ] **Multiply powerup** - pickups spawn on the board; a ball hitting one
      spawns +2 balls for its team. Core engagement mechanic, highest priority.
- [ ] **Visual juice** - flash on tile flip, pulse/screen-shake on powerup
- [ ] More powerups - Freeze (pause enemy balls), Steal (convert a chunk),
      Big Ball, Speed, Shield. Keep to 4-6 total for v1.
- [ ] **Render pipeline** - headless render frames -> ffmpeg -> MP4, seeded
      so every render is a unique battle
- [ ] Title/thumbnail template, outro CTA ("who won? comment below")
- [ ] First batch of videos, test on platform before scaling cadence

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
