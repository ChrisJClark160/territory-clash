# CLAUDE.md - Territory Clash

Loaded at session start. Protocols and pointers, not a full spec. Read
`WORKING.md` for current state, task board, and gotchas.

---

## What this project is

A 2D "territory wars" battle simulator that produces short-form videos
(Shorts/TikTok/Reels) for a YouTube channel in the [Marbles2D](https://www.youtube.com/@Marbles2D)
genre. Two teams (Pink vs Cyan) fight to own a tile arena; the colour bar tells
the whole story with no words.

**North star: an engaging video people are glued to - colourful, instantly
understandable, no language barrier, kid-watchable but not childish. The
outcome must stay uncertain and swing.** See `WORKING.md` for the design rules
this implies.

---

## Session protocol

1. Read `WORKING.md` first - current state, task board, gotchas.
2. Do the work. Prefer verifying behaviour (headless sim run), not just "it launches".
3. Before finishing: update `WORKING.md` (state + task board + date), then commit.

---

## Conventions

- **Language:** Python 3.14. **Use `pygame-ce`, never `pygame`** (no 3.14 wheel
  for stock pygame - it fails to compile).
- **No physics engine.** Core collision is custom circle-vs-grid maths. Do not
  reintroduce pymunk without a clear reason.
- **On-screen text is minimal by design** - percentages + timer only. Do not add
  explanatory copy; the visuals must carry it (no language barrier).
- Keep powerups to 4-6 total for v1; each must create a visible, dramatic swing.
- Vertical canvas: 720x1280.

## Verifying changes

Run the core logic headless before committing gameplay changes - drive the sim
for N frames and assert tiles are conserved and balls stay in bounds, rather
than only checking the window opens. (See how the v2 core was verified.)

## Commit / push

- Repo: `ChrisJClark160/territory-clash` (personal account).
- Push needs the ChrisJClark160 gh token active, not the work account MDUKChris.
- Commit when work is done and verified; keep messages factual.

---

## Key paths

| Item | Path |
|------|------|
| Repo root | `C:\Users\ChrisClark\Documents\GitHub\territory-clash` |
| Entry point | `main.py` |
| Working doc / tasks | `WORKING.md` |
| venv | `venv\` (activate: `venv\Scripts\activate`) |
