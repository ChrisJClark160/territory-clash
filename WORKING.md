# Territory Clash - Working Document

Living status + task doc. Update at the end of each working session.

Last updated: 2026-07-18 (launch-plan build items 1-6 DONE + sim fixes +
lead-change beat + title card. Remaining: cold open, music track, channel.)

**⚠️ Sim changed 2026-07-18: old seeds produce DIFFERENT battles now** (burst
cone aim, aftershocks, anticipation direction check changed rng consumption).
The pre-18-Jul renders in output/batch/ and their sidecar metrics are stale -
re-render everything via seed_shop.py + batch_render.py.

**Verdict (Chris, 2026-07-02): current format approved for YouTube Shorts,
and worth extending to longer videos (Phase C interest confirmed).**

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

## YouTube Launch Plan (agreed 2026-07-02, Chris approved public test uploads)

**Decisions:** upload publicly; channel does NOT exist yet (needs creating -
working name Territory Clash / @TerritoryClash, Chris to confirm); judge the
test on ~30 uploads over 30 days, not week-one views; mirror every MP4 to
TikTok + Reels unchanged.

**Slate flow (2026-07-18, supersedes the old batch notes):** the 2-Jul
renders are stale (sim changed). New flow for any slate:
`seed_shop.py 200 40` then `batch_render.py` - every video comes out
pre-scored with sidecar + upload text. First test render: cats_vs_dogs
seed 364825, 10 lead changes, 52-48, five lead changes in the last 8s.

**Strategy levers (why the changes below):** Shorts feed rewards low
swipe-away in the first 1-3s, high avg % viewed, comments. So: open hot
(early-action seeds + cold open), shorter battles (40s variant, retention %),
2s outro not 4s, comment-bait titles + pinned "pick your side" comment,
1/day cadence from a pre-rendered stockpile, single-niche channel. After
20-30 uploads: correlate YT retention stats against sidecar drama metrics
and make seed_shop optimise for what measurably retains.

### Build list (items 1-6 DONE 2026-07-18)

1. [x] **match_seconds + event timestamps** - `update()`/`draw_hud`/powerup
   cadence all use `self.match_seconds`/`self._pace`; 60s default verified
   identical to explicit 60. `event_log` ({t,type,value}), `lead_change_times`,
   `biggest_hit["t"]` (burst: at release; charge: at impact) all recorded.
2. [x] **seed_shop.py** - headless scorer per the agreed formula + floor.
   Sim is theme-independent, so seeds are scored once and the top distinct
   seeds dealt out to themes -> `output/seed_shop.json`. ~0.4s/seed: 80 seeds
   at 40s took 31s, 25/80 passed the floor, top seeds 9-10 lead changes.
3. [x] **OUTRO_SECONDS 4 -> 2.**
4. [x] **render.py passthrough** - `match_seconds` CLI arg; sidecar gains
   match_seconds, biggest_hit_t, lead_change_times, timeline (full event log).
5. [x] **batch_render.py rework** - consumes seed_shop.json (errors if
   missing), renders assigned seed per theme at the shopped length; theme
   names as args. Verified: rendered battle matches shopped metrics exactly.
6. [x] **describe.py** - title (256-moment > photo finish > comeback >
   blowout > default) + pinned comment + description + hashtags from the
   sidecar; render.py writes `<name>.txt` beside every MP4.
7. [ ] **render.py - cold open (fiddly, do last).** Probe run (same seed,
   sim-only) finds `biggest_hit["t"]`; second Game fast-forwards sim-only to
   t-0.35s, draws ~60 frames (1s) written BEFORE the battle frames; battle
   audio events offset by 1s; add "anticipation" riser cue at t=0. Skip if
   biggest hit < 32. Determinism makes this safe (private game.rng).
   NOTE: the opening title card (below) now occupies the first 1.0s -
   integrate the cold open UNDER the card, or shorten the card.
8. **Not code:** drop an NCS track in `music/` before rendering the slate
   (current batch is SFX-only); create channel; upload slate; pin comment;
   schedule 1/day; TikTok + Reels mirrors; after 20-30 uploads pull YT
   analytics and close the loop.

### Also done 2026-07-18 (sim fixes + presentation, beyond the plan)

- [x] **verify.py** - invariants + determinism + default-equivalence + 40s
  check. Run after ANY sim change; seed shopping and re-renders depend on it.
- [x] **Anticipation direction fix** - the slow-mo beat only arms when the
  ball is moving TOWARD the red pad (was: distance only, so beats fired on
  receding balls and paid off with nothing).
- [x] **Burst cone aim** - burst pellets spray in a +/-70 degree cone toward
  the enemy tile centroid (was: 360 spray wasted half a big burst on walls).
- [x] **Top-tier payoff ladder** - SHOT_MAX_BLOB 6.5 -> 9.5 (256 is now
  visually bigger than 133, was capped identical) and releases >= 128 chain
  2 aftershock explosions (3 at 256) striking enemy pockets near the impact.
- [x] **Lead-change beat** - live sign flip at the 0.5s sampler triggers a
  white bar flash + gold "NEW LEADER!" + new `lead_flip` SFX cue. Lead
  changes were the #1 drama metric yet had zero on-screen presence.
- [x] **Opening title card (render only)** - first 1.0s shows a gold-bordered
  "CATS 🐱 / VS / 🐶 DOGS" card (team colours + emoji, shrink-to-fit), fades
  out over 0.3s. The swipe decision happens before the HUD means anything.

### Evolution layer (Chris's idea, built 2026-07-18)

Frame the sim settings as a genome and evolve them; fitness = what holds
viewers. Two phases:

- **Phase 1 (live now, offline):** `GENOME` in main.py exposes 10 engagement
  levers (speeds, rubber-banding, escalation, pad counts, powerup cadence,
  burst cone...). Defaults reproduce the hand-tuned sim EXACTLY (verify.py
  asserts it). `evolve.py` runs a genetic loop - gaussian mutation, uniform
  crossover, 2 elites - with fitness = mean drama score over a SHARED set of
  battle seeds (common random numbers, so fitness differences are the
  genome's doing, not seed luck). Output: `output/best_genome.json`, which
  seed_shop.py takes as an optional 3rd arg and batch_render passes through
  to every render.
- **Phase 2 (after 20-30 uploads):** every sidecar records its genome, so
  real audience data can replace the surrogate: fitness = mean avg-percent-
  viewed per genome from YT analytics (retention, NOT raw views - views are
  confounded by theme/title/thumbnail and algorithm mood). At 1 upload/day a
  generation takes a week+, so mutate ONE gene at a time from the phase-1
  winner and keep themes balanced across variants. Close the loop the plan
  already called for, just with the machinery ready.

### Old Phase A.5 list (superseded by the build list above)
- [ ] Eyeball a few full 60s runs on screen; tune anything that feels off
      (pad cadence, blob size, pellet spray, trail length)
- [x] Render 10 test Shorts (2026-07-02): done, `output/batch/`. Standouts:
      pizza_vs_burger (10 lead changes, 256 charge, 52-48), marvel_vs_dc
      (7 leads, 256 burst), kfc_vs_mcdonalds (50-50 photo finish). Weakest:
      arsenal_vs_liverpool (0 leads, biggest hit 16) - a flat battle happens
      sometimes; re-render weak themes with a fresh seed before uploading.
- [ ] Get outside eyes to score cold (don't self-score - you already know
      what's "supposed to" be exciting). Score /10 each: hook, readability,
      mid-game drama, big payoff, clear winner, would-watch-to-the-end
- [ ] Title/thumbnail template; patch-note style descriptions, "Who will win?"
- [ ] Only once A.5 scores well: Phase B - four teams + elimination/revival
      (DESIGN.md - keep v1 simple, no alliances/extra mechanics)
- [ ] Phase C: long-form flagship, pixel territory, shields (DESIGN.md)

### Done - Phase A.5 audio (2026-07-02)
- [x] `audio.py`: all 9 SFX cues synthesized procedurally (pure stdlib) into
      `assets/sfx/` on first use - green/red pads, burst, charge, explosion,
      anticipation riser, winner arpeggio, powerup, freeze
- [x] Live playback in the window via pygame.mixer
- [x] `render.py` mixes timestamped cues into an SFX track and muxes it into
      the MP4 (AAC). Drop an NCS file in `music/` and it loops under the SFX
      at 30% volume automatically (see `music/README.md`)

### Done - Phase A.5 presentation layer (2026-07-02)
- [x] Danger indicator: 16+ soft team glow; 64+ pulsing red ring; 128+ second
      ring; 256 third gold ring, pulse speeds up per tier
- [x] Red pad anticipation beat: slow-mo + camera zoom toward the pad + pad
      throb + "128 POWER!" flash (64+ balls only, 4s cooldown keeps it rare)
- [x] Winner screen payoff: winner, final %, biggest hit (value + type),
      lead changes
- [x] JSON metadata sidecar per render (seed, winner, final_score,
      biggest_power/event, lead_changes, max_swing, events, powerups)
- [x] **Determinism fix**: sim now uses a private RNG (`game.rng`) so
      presentation randomness (shake) can't change outcomes. Proven: headless
      and drawn runs of the same seed match exactly; rendered seed 3 matches
      headless (256 charge, 5 lead changes). Without this, seeds didn't
      reproduce - re-render a banger would have produced a different battle.

### Done - Phase A: Multiply or Release (2026-07-02)
- [x] Balls carry a visible value (starts 1, cap 256). Green pads (two x2,
      one x4 guaranteed per board) multiply it; red pads cash it in 50/50 as
      a **burst** (N pellets, each flips one tile) or a **charged shot** (big
      ball aimed at enemy territory, flips a blob of ~N tiles, screen shake).
      Pads relocate after every trigger. Old powerups made rarer (8-12s).
      Verified: swings grew from ~10pts to 20-40pts, up to 7 lead changes,
      finals ranging 30-71. Invariants hold.

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
