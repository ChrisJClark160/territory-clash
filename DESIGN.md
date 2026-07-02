# Design Notes - what we're learning from Lost Marbles 2D

Reference: [Lost Marbles 2D](https://www.youtube.com/@lostmarbles2d) -
1.3M+ views on a single battle video. This doc distils *why* it works and
maps it onto a roadmap for this project.

---

## Why it works

**1. The accumulate/release loop is the hook.**
Marbles carry a visible number that multiplies through green triggers
(2x, 4x, 8x, 16x) and is cashed in at red triggers - either a *burst attack*
(N rapid shots, each converting one pixel) or a *charged shot* (one huge shot
converting N pixels). This creates constant anticipation cycles: you can SEE
a marble carrying 32,768 drifting toward a trigger. Tension while it builds,
payoff when it releases. Our current sim flips tiles at a constant rate -
there is no build-up, so there is nothing to anticipate. This is the single
biggest thing to steal.

**2. Long-form, not (only) Shorts.**
The description credits seven NCS songs - these are 20-40 minute videos.
People watch marble battles like sport or leave them on like ASMR. Long-form
means watch-hours, which is what YouTube's algorithm actually pays for.
The economy of accumulation only shines with room to breathe.

**3. Four teams, not two.**
Four colours = simultaneous stories: the dominant leader, the underdog
comeback, the quiet corner survivor. Elimination + revival rules mean death
is dramatic but not final - a 1M+ charged shot can resurrect a dead player.

**4. Depth without a language barrier.**
Shields, revival costs, fire-rate curves - deep rules, yet everything on
screen is just numbers, colours and bars. A new viewer gets it instantly;
a regular understands the meta. Complexity in the *rules*, legibility in
the *presentation*.

**5. A living ruleset (patch notes as content).**
"New in this version: trigger spaces adjusted, new 16x trigger, idle marbles
shrink..." Each video is a balance patch; the audience follows the meta like
a game they play. Comment sections become balance debates. Discord + Patreon
close the loop. This turns a video series into a *game community*.

**6. Anti-stall design.**
"Every minute since a marble last triggered, it shrinks until it falls
through gaps" - stagnation is engineered out. Nothing is allowed to be
boring for long. (Our escalation ramp is a primitive version of this.)

**7. Free music, zero friction.**
NCS (NoCopyrightSounds) EDM - copyright-safe, high energy, free. Credits in
the description. That's the audio plan solved.

---

## Roadmap through that lens

### Phase A - "Multiply or Release" in the current 60s arena  <- NEXT
Keep the 2-team tile arena and Shorts format, add the accumulate/release loop:
- Balls carry a visible number (starts at 1).
- Green pads (x2, x4) multiply a ball's number. Pads relocate after use.
- Red pads cash it in, randomly as:
  - **Burst**: N rapid pellets sprayed out, each flipping one tile.
  - **Charged shot**: one big slow ball that flips a blob of N tiles on impact.
- The existing powerups/rubber-banding stay; bomb/freeze/speed become rarer.
- Why first: it's the genre's proven core loop, works in 60s, and directly
  fixes the "feels predetermined" problem - anticipation makes randomness felt.

### Phase A.5 - YouTube-ready polish test  <- NEXT (before Phase B)
The numbers already prove the sim is more exciting (bigger swings, more lead
changes). The open question is whether a cold viewer *feels* that without
being told. Four teams will make the board busier and change the viewer's
question from "who wins, pink or cyan?" to "what's happening and who do I
care about?" - don't add that complexity until the current 1v1 format is
proven to read clearly on a phone.

Build first, then test (build the payoff moments before judging pacing
against a version that doesn't have them yet):
- **Danger indicator**: a ball at 64/128/256 should visibly read as
  dangerous (glow -> pulsing outline -> warning ring), not just be a bigger
  number.
- **Red pad anticipation**: when a high-value ball closes on a red pad, add
  a beat - slight zoom, brief slow-mo, pad pulse, danger sound, on-screen
  "128 POWER!" flash. Sparingly, only for the biggest moments.
- **Winner screen payoff**: don't just stop. Show final territory split,
  biggest hit (value + burst/charged shot), lead changes.
- **Metadata output**: `render.py` emits a JSON sidecar per video
  (winner, final score, biggest_power, biggest_event, lead_changes,
  max_swing) so titles can be generated from what actually happened in that
  battle, not a generic template.
- **Audio**: pad/shot/explosion/winner sound cues, NCS track muxed in.

Then test with **outside eyes, not self-scoring** - you already know which
ball is "supposed to" feel dangerous, so your own read of hook/clarity/drama
will be optimistic. Render 10 unlisted Shorts (simple vs-themes: Red vs Blue,
Fire vs Ice, Cats vs Dogs, Pizza vs Burger, Xbox vs PlayStation, iPhone vs
Samsung, Minecraft vs Roblox, Marvel vs DC, Arsenal vs Liverpool, KFC vs
McDonald's) and get a few people who've never seen the sim to watch cold.
Score each out of 10 on: hook (first 2-3s), readability (numbers legible on
phone), mid-game drama, big payoff, clear winner, would-watch-to-the-end.

Only move to Phase B once that comes back solid.

### Phase B - four teams
Four corners, four colours, elimination when a team hits zero tiles, revival
via a big charged shot. More story shapes per video. Keep the first version
simple: 4 teams max, 1 ball per team to start, same x2/x4/red-pad system,
clear scoreboard, eliminate only when territory hits zero. No alliances,
no extra mechanics, no new powerups yet.

### Phase C - long-form flagship
Landscape 1080p (or square), pixel-level territory (fine grid), shields +
revival economy, 10-30 minute battles, NCS soundtrack layered in the render
pipeline, chapter-able narratives. This is the watch-hours product; Shorts
become the funnel that feeds it.

### Channel practices to copy from day one
- Patch-note style descriptions ("New in this version: ...").
- "Who will win?" framing + rules explained in the description, not on screen.
- NCS music credited in the description.
- Consistent colour identities for the teams across videos (fans pick sides).
