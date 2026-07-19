"""Generate upload packaging from a battle's metadata sidecar.

Titles, the pinned comment and the description are written from what
actually happened in the battle (photo finish / comeback / blowout /
256-moment), never a generic template - the sidecar is the story.

Called by render.py after the sidecar is written; also usable standalone:
    python describe.py output/batch/cats_vs_dogs.json
"""

import json
import os
import sys

# Titles: several phrasings per story type, picked deterministically from
# the battle seed so re-runs are stable but the channel page never shows a
# wall of identical titles. Priority runs rarest story first - with the
# evolved genome a 256 hit is common, so it must NOT outrank everything.
MAX_VALUE = 256

DRAW_TITLES = (
    "{a} vs {b} ended in a PERFECT TIE - watch it happen",
    "{a} vs {b}: nobody won. Seriously.",
    "The {a} vs {b} battle that REFUSED to pick a winner",
)
PHOTO_TITLES = (
    "{a} vs {b} - decided by the FINAL tiles!",
    "{a} vs {b} came down to the very last second",
    "You won't guess who won {a} vs {b} (it was THAT close)",
    "{a} vs {b} - the ending nobody saw coming",
)
COMEBACK_TITLES = (
    "{w} came back from the DEAD against {l}",
    "{l} had it won... then {w} woke up",
    "The greatest comeback in {a} vs {b} history",
    "{w} refused to lose this one 🔥",
    "{w} was DOWN BAD... then this happened",
    "{w} flipped the whole map on {l}",
    "HOW did {w} win this?!",
)
LEADS_TITLES = (
    "{a} vs {b} swapped the lead {n} times 🤯",
    "{n} lead changes. One winner. {a} vs {b}",
    "{a} vs {b} could NOT make its mind up",
    "The lead changed {n} TIMES in this battle",
    "Nobody stayed in front: {a} vs {b}",
)
BIGHIT_TITLES = (
    "A {v} {kind} decided {a} vs {b} 😱",
    "{w} hit MAX POWER against {l} 💥",
    "{a} vs {b} - one shot changed EVERYTHING",
    "The biggest hit possible landed in {a} vs {b}",
    "{w} dropped the nuke on {l} ☢️",
    "One ball. {v} power. Goodbye {l}.",
)
BLOWOUT_TITLES = (
    "{w} DESTROYED {l}... or did they?",
    "{w} left NOTHING for {l} 💀",
    "Total domination: {w} vs {l}",
)
DEFAULT_TITLES = (
    "{a} vs {b} - who takes the territory?",
    "{a} vs {b}: pick your side before it ends",
    "Every tile counts: {a} vs {b}",
)


def _story(meta):
    a, b = meta["teams"]
    winner = meta["winner"]
    loser = b if winner == a else a
    diff = abs(meta["final_score"][0] - meta["final_score"][1])

    def pick(pool):
        # Knuth multiplicative hash: consecutive/clustered seeds still
        # spread evenly across the pool.
        idx = (meta.get("seed", 0) * 2654435761 >> 7) % len(pool)
        kind = "burst" if meta["biggest_event"] == "burst" else "charged shot"
        return pool[idx].format(a=a, b=b, w=winner, l=loser, kind=kind,
                                n=meta["lead_changes"], v=meta["biggest_power"])

    if winner == "DRAW":
        return pick(DRAW_TITLES)
    if diff <= 4:
        return pick(PHOTO_TITLES)
    if meta["lead_changes"] >= 8:
        return pick(LEADS_TITLES)
    if meta["max_swing"] >= 30:
        return pick(COMEBACK_TITLES)
    if meta["biggest_power"] >= MAX_VALUE:
        return pick(BIGHIT_TITLES)
    if diff >= 30:
        return pick(BLOWOUT_TITLES)
    return pick(DEFAULT_TITLES)


def describe(meta, music=None):
    """Return (title, pinned_comment, description)."""
    a, b = meta["teams"]
    title = _story(meta)

    pinned = f"Team {a} or Team {b}? Pick your side 👇"

    stats = []
    if meta["lead_changes"]:
        stats.append(f"{meta['lead_changes']} lead changes")
    if meta["biggest_power"] > 1:
        kind = "burst" if meta["biggest_event"] == "burst" else "charged shot"
        stats.append(f"biggest hit {meta['biggest_power']} ({kind})")
    stats.append(f"final score {meta['final_score'][0]}-{meta['final_score'][1]}")

    lines = [
        f"{a} vs {b} - territory battle. {', '.join(stats).capitalize()}.",
        "",
        "Every ball flips tiles to its colour. Green pads multiply a ball's "
        "power, red pads cash it in as a burst or a charged shot. "
        "Most territory when the timer ends wins.",
        "",
        "Who did you back? Pick your side in the comments 👇",
        "New battle every day.",
    ]
    if music:
        # Name music files with attribution built in, e.g.
        # "Raving Energy - Kevin MacLeod (incompetech.com CC BY 4.0).mp3"
        lines += ["", f"Music: {os.path.splitext(music)[0]}"]
    tags = ["#Shorts", "#battle", "#satisfying", "#simulation",
            f"#{a.lower().replace(' ', '')}", f"#{b.lower().replace(' ', '')}"]
    lines += ["", " ".join(tags)]
    return title, pinned, "\n".join(lines)


def write_for(meta, mp4_path, music=None):
    """Write <name>.txt next to the MP4; returns the path."""
    title, pinned, description = describe(meta, music=music)
    txt_path = os.path.splitext(mp4_path)[0] + ".txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"TITLE: {title}\n\nPINNED COMMENT: {pinned}\n\n"
                f"DESCRIPTION:\n{description}\n")
    return txt_path


def _current_music():
    """First audio file in music/ - same rule as render.py, duplicated here
    because render imports describe (avoiding a circular import)."""
    music_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")
    if not os.path.isdir(music_dir):
        return None
    for f in sorted(os.listdir(music_dir)):
        if f.lower().endswith((".mp3", ".wav", ".ogg", ".m4a", ".flac")):
            return f
    return None


if __name__ == "__main__":
    music = _current_music()
    for meta_path in sys.argv[1:]:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        mp4 = os.path.splitext(meta_path)[0] + ".mp4"
        print(write_for(meta, mp4, music=music))
